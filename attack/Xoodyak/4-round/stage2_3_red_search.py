import gurobipy as gp
from gurobipy import GRB
from base_MILP.Xoodyak_MILP import *
from output.write_in_file_Xoodyak import *
from attack.Xoodyak.blue_result.all_best_Xoodyak_blue_bits import all_solutions

best_obj = 0
for key in all_solutions.keys():
    blue_number = -1
    for blue_scheme in all_solutions[key]:
        blue_number += 1
        if (key,blue_number) not in [(15,3),(16,3)]:
            continue
        # Create Gurobi model
        model = gp.Model("Ascon_MILP_Automation")

        model.setParam('MIPGap', 0.67)  # Set optimality gap to 0.67

        # 1. Initialize state
        print("正在初始化Ascon状态... - Initializing Ascon state...")

        # Create 32x3x4 initial state
        initial_state = [[[None for _ in range(4)] for __ in range(3)] for ___ in range(32)]

        # Define hash parameters
        # For Ascon-XOF: rate = 64 bits, capacity = 256 bits
        # Total state 320 bits = 64x5 (Note: Xoodyak state is 32x3x4 = 384 bits? The comment seems outdated but keep as is)
        rate_bits = 64   # Rate part size
        capacity_bits = 256 # Capacity part size
        padding_bits = 2    # Number of padding bits
        num_rounds = 4      # Number of rounds

        # Initialize state bits
        number = 0
        for z in range(32):
            for y in range(3):
                for x in range(4):
                    if y in (0, 1):
                        # capacity planes: fixed 0 (if you do not allow capacity to have cond)
                        initial_state[z][y][x] = Bit(model, f"init_z{z}_y{y}_x{x}", (0, 0, 0, '*'))
                    else:
                        # y==2 rate plane
                        if z >= 30 and x == 3:
                            # padding bits fixed
                            initial_state[z][2][x] = Bit(model, f"init_z{z}_y2_x{x}", (0, 0, 0, 0))
                        elif blue_scheme[z][2][x] >= 0.5:
                            # fixed blue
                            initial_state[z][2][x] = Bit(model, f"init_z{z}_y2_x{x}", (0, 0, 1, 0))
                        else:
                            # red candidate: r/cond are variables (Bit has constraints like cond+r<=1)
                            initial_state[z][2][x] = Bit(model, f"init_z{z}_y2_x{x}", (0, '*', 0, '*'))
                    number += 1
        print("number",number)
        print("状态初始化完成 - State initialization completed")

        # 2. Apply round functions
        print("正在应用轮函数... - Applying round functions...")

        # Save intermediate states
        intermediate_states = []
        current_state = initial_state
        # Apply multiple rounds
        for round_num in range(num_rounds):
            print(f"应用第{round_num + 1}轮 - Applying round {round_num + 1}")
            if round_num == 0:
                theta_state, C, D, theta_vars = create_first_theta_operation(model,current_state,f"round{round_num}_theta")
            else:
                theta_state, C, D, theta_vars = create_theta_operation(model, current_state, f"round{round_num}_theta")
            if round_num == num_rounds-1:
                intermediate_states.append({
                    'theta_state': theta_state,
                    'theta_vars': theta_vars,
                    'C':C,
                    'D':D,
                    'rho_west_state': None,
                    'chi_state': None,
                    'chi_vars': None,
                    'rho_east_state': None,
                    'round_num': round_num
                })
                current_state = theta_state
                break
            rho_west_state = rho_west(theta_state)
            if round_num == 0:
                chi_state, chi_vars = create_first_chi_operation(model,rho_west_state,f"round{round_num}_chi")
            else:
                chi_state, chi_vars = create_chi_operation(model,rho_west_state,f"round{round_num}_chi")
            rho_east_state = rho_east(chi_state)

            # Save current round state
            intermediate_states.append({
                'theta_state': theta_state,
                'theta_vars': theta_vars,
                'rho_west_state': rho_west_state,
                'chi_state': chi_state,
                'chi_vars': chi_vars,
                'rho_east_state': rho_east_state,
                'C': C,
                'D': D,
                'round_num':round_num
            })

            current_state = rho_east_state

        final_state = current_state
        print(f"完成{num_rounds}轮函数应用 - Completed {num_rounds} rounds application")

        # 3. Calculate equation count and variable statistics
        print("正在计算方程个数... - Calculating equation count...")

        # Count variable types in initial state
        red_vars_count = gp.quicksum(initial_state[z][2][x].r for x in range(4) for z in range(32))
        blue_vars_count = gp.quicksum(initial_state[z][2][x].b for x in range(4) for z in range(32))
        # model.addConstr(5>=second_blue_vars_count)

        # Count intervention variables in round functions
        delta_total_r = 0
        delta_total_b = 0
        sum_const_cond = 0
        capacity_cond = 0
        quad_sum = 0
        for z in range(32):
            for y in range(2):
                for x in range(4):
                    capacity_cond += initial_state[z][y][x].cond

        for round_state in intermediate_states:

            theta_vars = round_state['theta_vars']
            # Count variables in Theta operation
            for z in range(32):
                for x in range(4):
                    delta_total_r += theta_vars[f"C_x{x}_z{z}"]['delta_r']
                    delta_total_b += theta_vars[f"C_x{x}_z{z}"]['delta_b']
                    sum_const_cond += theta_vars[f"C_x{x}_z{z}"]['new_cond']

                    delta_total_r += theta_vars[f"D_x{x}_z{z}"]['delta_r']
                    delta_total_b += theta_vars[f"D_x{x}_z{z}"]['delta_b']
                    sum_const_cond += theta_vars[f"D_x{x}_z{z}"]['new_cond']

                    for y in range(3):
                        delta_total_r += theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_r']
                        delta_total_b += theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_b']
                        sum_const_cond += theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond']

            # Count variables in Chi operation
            chi_vars = round_state['chi_vars']
            if chi_vars == None:
                continue
            for z in range(32):
                for y in range(3):
                    for x in range(4):
                        delta_total_r += chi_vars[f"new_z{z}_y{y}_x{x}"]['delta_r']
                        delta_total_b += chi_vars[f"new_z{z}_y{y}_x{x}"]['delta_b']
                        sum_const_cond += chi_vars[f"new_z{z}_y{y}_x{x}"]['new_cond']
                        quad_sum += chi_vars[f"and_z{z}_y{y}_x{x}"]['quad']

        model.addConstr(quad_sum<=5)
        # Total equations variable
        hash_output_bits = []
        # Loss on red/blue sets due to probabilistic path
        bit_cut = []
        for z in range(32):
            for x in range(4):
                equation = model.addVar(vtype=GRB.BINARY,name = f"equation_for_{z}_{x}")
                model.addConstr(equation <= (1 - final_state[z][0][x].ul)+final_state[z][0][x].r+final_state[z][0][x].b)
                model.addConstr(equation <= (1 - final_state[z][1][x].ul)+final_state[z][1][x].r+final_state[z][1][x].b)
                model.addConstr(equation <= (1 - final_state[z][2][x].ul)+final_state[z][2][x].r+final_state[z][2][x].b)
                model.addConstr(equation <= (2 - final_state[z][0][x].r - final_state[z][1][x].b))
                model.addConstr(equation <= (2 - final_state[z][0][x].b - final_state[z][1][x].r))
                hash_output_bits.append(equation)
                equation2 = model.addVar(vtype=GRB.BINARY, name=f"equation2_for_{z}_{x}")
                model.addConstr(equation2 <= (1 - final_state[z][2][x].ul) + final_state[z][2][x].r + final_state[z][2][x].b)
                model.addConstr(equation+equation2<=1)
                hash_output_bits.append(0.58*equation2)
                bit_cut.append(0.42*(equation2))

        print("方程计算完成 - Equation calculation completed")

        # 4. Set constraints and objective function
        print("正在设置约束和目标函数... - Setting constraints and objective function...")

        # Set objective function: minimize attack complexity
        temp_degree = model.addVar(vtype=GRB.CONTINUOUS,lb=0, name='complexity')
        degree_from_c = model.addVar(vtype=GRB.INTEGER,lb=0, name='complexity')
        # Attack complexity constraints
        model.addConstr(temp_degree <= red_vars_count - delta_total_r-gp.quicksum(bit_cut))
        model.addConstr(temp_degree <= blue_vars_count - delta_total_b-gp.quicksum(bit_cut))
        model.addConstr(temp_degree <= gp.quicksum(hash_output_bits))
        model.addConstr(capacity_cond+degree_from_c<=128-temp_degree)
        model.addConstr(128<=128-2-sum_const_cond+degree_from_c)
        # Set objective
        model.setObjective(temp_degree, GRB.MAXIMIZE)

        print("约束和目标函数设置完成 - Constraints and objective function set")

        # Solve model
        print("开始求解模型... - Starting model solution...")

        model.optimize()

        # Output state information for LaTeX documentation
        f = open(f"./result/Xoodyak_round_{num_rounds}_preimage_{key}_{blue_number}.py", 'w')

        # Output statistical results
        f.write(f"Red_variables={red_vars_count.getValue() - delta_total_r.getValue()}\n")
        f.write(f"Blue_variables={blue_vars_count.getValue() - delta_total_b.getValue()}\n")
        f.write(f"sum_const_cond = {sum_const_cond.getValue()}\n")

        print("Keccak MILP自动化建模完成 - Keccak MILP automation modeling completed")

        # Output state information for LaTeX documentation
        row_num = 0
        temp = write_row(initial_state, row_num, '$A$')
        f.write(f"initial_state_output = {temp}\n")
        intermediate_states_output = []

        index = 1
        for round_state in intermediate_states:
            round_state_output = dict()
            theta_vars = round_state['theta_vars']
            chi_vars = round_state['chi_vars']
            row_num += 1
            C = round_state['C']
            temp = write_row_C(C, row_num, theta_vars, f'$C_{index}$')
            round_state_output['C'] = temp
            row_num += 0.4
            D = round_state['D']
            temp = write_row_D(D, row_num, theta_vars, f'$D_{index}$')
            round_state_output['D'] = temp
            row_num += 0.4
            theta = round_state['theta_state']
            temp = write_row_theta(theta, row_num, theta_vars, f'$\\theta_{index}$')
            round_state_output['theta_state'] = temp

            rho_west_state = round_state['rho_west_state']
            if rho_west_state==None:
                intermediate_states_output.append(round_state_output)
                continue
            row_num += 1
            temp = write_row(rho_west_state, row_num, f'$\\rho_west_state{index}$')
            round_state_output['rho_west_state'] = temp
            row_num += 1
            chi = round_state['chi_state']
            temp = write_row_chi(chi, row_num, chi_vars, f'$\\chi_{index}$')
            round_state_output['chi_state'] = temp
            row_num += 1
            rho_east_state = round_state['rho_east_state']
            temp = write_row(rho_east_state, row_num, f'$\\rho_east_state{index}$')
            round_state_output['rho_east_state'] = temp

            index += 1
            intermediate_states_output.append(round_state_output)

        f.write(f"intermediate_states_output={intermediate_states_output}")

        if key - temp_degree.x<0.01:
            break