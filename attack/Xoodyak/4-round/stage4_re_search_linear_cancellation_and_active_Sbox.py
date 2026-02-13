import gurobipy as gp
from gurobipy import GRB
from base_MILP.Xoodyak_re_search_MILP  import *
from output.re_search_write_in_file_Xoodyak import *
from attack.Xoodyak.final_result import initial_state_output,intermediate_states_output

# Create Gurobi model
model = gp.Model("Xoodyak_MILP_Automation")
model.setParam('MIPFocus', 2)
model.setParam('MIPGap', 0.0)  # Set optimality gap to 0

# 1. Initialize state
print("Initializing Xoodyak state...")

# Create 4x3x32 initial state
initial_state = [[[Bit(model, 'constant', 'uc') for x in range(4)] for y in range(3)] for z in range(32)]

num_rounds = 4  # Number of rounds-1

# Initialize state bits
for z in range(32):
    for x in range(4):
        for y in range(3):
            if initial_state_output[0][x][y][z]=='lr':
                initial_state[z][y][x].r = 1
                initial_state[z][y][x].b = 0
            elif initial_state_output[0][x][y][z]=='lb':
                initial_state[z][y][x].r = 0
                initial_state[z][y][x].b = 1
            elif initial_state_output[0][x][y][z] == 'c':
                initial_state[z][y][x].r = 0
                initial_state[z][y][x].b = 0
                initial_state[z][y][x].cond = model.addVar(vtype=GRB.BINARY,name = f'cond_{x}_{y}_{z}')
            else:
                print(initial_state_output[0][z][y][x])
                exit(1)


# 2. Apply round functions
print("Applying round functions...")

# Save intermediate states
intermediate_states = []
current_state = initial_state
def set_type(var,type):
    if type == 'lr':
        model.addConstr(var.ul == 0)
        model.addConstr(var.r == 1)
        model.addConstr(var.b == 0)
    elif type == 'lb':
        model.addConstr(var.ul == 0)
        model.addConstr(var.r == 0)
        model.addConstr(var.b == 1)
    elif type == 'c':
        model.addConstr(var.ul == 0)
        model.addConstr(var.r == 0)
        model.addConstr(var.b == 0)
    elif type == 'ur':
        model.addConstr(var.ul == 1)
        model.addConstr(var.r == 1)
        model.addConstr(var.b == 0)
    elif type == 'lg':
        model.addConstr(var.ul == 0)
        model.addConstr(var.r == 1)
        model.addConstr(var.b == 1)
    elif type == 'ug':
        model.addConstr(var.ul == 1)
        model.addConstr(var.r == 1)
        model.addConstr(var.b == 1)
# Apply multiple rounds
for round_num in range(num_rounds):

    print(f"Applying round {round_num + 1}")

    # Theta operation
    print(f"  Round {round_num + 1}: Theta operation")
    # Choose different Theta operation implementation based on round number
    if round_num == 0:
        theta_state, C, D, theta_vars,linear_cancel = create_first_theta_operation(model,current_state,f"round{round_num}_theta")
    else:
        theta_state, C, D, theta_vars,linear_cancel= create_theta_operation(model, current_state, f"round{round_num}_theta")
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
            'round_num': round_num,
            "linear_cancel":linear_cancel,
            "without_place": None,
            "linear_cancel_chi": None

        })
        current_state = theta_state
        break
    rho_west_state = rho_west(theta_state)
    if round_num == 0:
        chi_state, chi_vars,without_place,linear_cancel_chi  = create_first_chi_operation(model, rho_west_state, f"round{round_num}_chi")
    else:
        chi_state, chi_vars,without_place,linear_cancel_chi  = create_chi_operation(model,rho_west_state,f"round{round_num}_chi")
    rho_east_state = rho_east(chi_state)
    if round_num==0:
        inter_state = intermediate_states_output[round_num]
        for z in range(32):
            for x in range(4):
                set_type(C[z][x],inter_state['C'][0][x][z])
                set_type(D[z][x], inter_state['D'][0][x][z])
                for y in range(3):
                    set_type(theta_state[z][y][x], inter_state['theta_state'][0][x][y][z])
                    set_type(chi_state[z][y][x], inter_state['chi_state'][0][x][y][z])


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
        'round_num': round_num,
        "linear_cancel": linear_cancel,
        "without_place":without_place,
        "linear_cancel_chi":linear_cancel_chi
    })

    current_state = rho_east_state

final_state = current_state
print(f"Completed {num_rounds} rounds application")

# 3. Calculate equation count and variable statistics
print("Calculating equation count...")

# Count variable types in initial state
red_vars_count = gp.quicksum(initial_state[z][2][x].r for x in range(4) for z in range(32))
blue_vars_count = gp.quicksum(initial_state[z][2][x].b for x in range(4) for z in range(32))

# Count intervention variables in round functions

delta_total_r = 0
delta_total_b = 0
sum_const_cond = 0
capacity_cond = 0
CT_sum = 0
sum_without_place = 0
sum_linear_cancel = 0
for z in range(32):
    for y in range(3):
        for x in range(4):
            capacity_cond += initial_state[z][y][x].cond
            sum_const_cond +=0.5 * initial_state[z][y][x].cond

for round_state in intermediate_states:
    round_number = round_state['round_num']
    theta_vars = round_state['theta_vars']
    linear_cancel = round_state['linear_cancel']
    # Count variables in Theta operation
    for z in range(32):
        for x in range(4):
            delta_total_r += theta_vars[f"C_x{x}_z{z}"]['delta_r']
            delta_total_b += theta_vars[f"C_x{x}_z{z}"]['delta_b']
            sum_const_cond += theta_vars[f"C_x{x}_z{z}"]['new_cond']
            sum_linear_cancel += linear_cancel[f"C_x{x}_z{z}"]

            delta_total_r += theta_vars[f"D_x{x}_z{z}"]['delta_r']
            delta_total_b += theta_vars[f"D_x{x}_z{z}"]['delta_b']
            sum_const_cond += theta_vars[f"D_x{x}_z{z}"]['new_cond']
            sum_linear_cancel += linear_cancel[f"D_x{x}_z{z}"]

            for y in range(3):
                delta_total_r += theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_r']
                delta_total_b += theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_b']
                sum_const_cond += theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond']
                sum_linear_cancel += linear_cancel[f"new_z{z}_y{y}_x{x}"]

    # Count variables in Chi operation
    chi_vars = round_state['chi_vars']
    without_place = round_state['without_place']
    linear_cancel_chi = round_state['linear_cancel_chi']
    if chi_vars == None:
        continue
    for z in range(32):
        for x in range(4):
            sum_without_place += without_place[z][x]
            for y in range(3):
                delta_total_r += chi_vars[f"new_z{z}_y{y}_x{x}"]['delta_r']
                delta_total_b += chi_vars[f"new_z{z}_y{y}_x{x}"]['delta_b']
                sum_const_cond += chi_vars[f"new_z{z}_y{y}_x{x}"]['new_cond']
                CT_sum += chi_vars[f"and_z{z}_y{y}_x{x}"]['CT']
                sum_linear_cancel += linear_cancel_chi[f"new_z{z}_y{y}_x{x}"]

model.addConstr(CT_sum<=5)
# Total equations variable
hash_output_bits = []
# Loss on red/blue sets due to probability paths
bit_cut = []
for z in range(32):
    for x in range(4):
        equation = model.addVar(vtype=GRB.BINARY, name=f"equation_for_{z}_{x}")
        model.addConstr(equation <= (1 - final_state[z][0][x].ul) + final_state[z][0][x].r + final_state[z][0][x].b)
        model.addConstr(equation <= (1 - final_state[z][1][x].ul) + final_state[z][1][x].r + final_state[z][1][x].b)
        model.addConstr(equation <= (1 - final_state[z][2][x].ul) + final_state[z][2][x].r + final_state[z][2][x].b)
        model.addConstr(equation <= (2 - final_state[z][0][x].r - final_state[z][1][x].b))
        model.addConstr(equation <= (2 - final_state[z][0][x].b - final_state[z][1][x].r))
        hash_output_bits.append(equation)
        equation2 = model.addVar(vtype=GRB.BINARY, name=f"equation2_for_{z}_{x}")
        model.addConstr(equation2 <= (1 - final_state[z][2][x].ul) + final_state[z][2][x].r + final_state[z][2][x].b)
        model.addConstr(equation + equation2 <= 1)
        hash_output_bits.append(0.58 * equation2)
        bit_cut.append(0.42 * (equation2))

print("Equation calculation completed")

# 4. Set constraints and objective function
print("Setting constraints and objective function...")


# Set objective function: minimize attack complexity
temp_degree = model.addVar(vtype=GRB.CONTINUOUS,lb=0, name='complexity')
degree_from_c = model.addVar(vtype=GRB.INTEGER,lb=0, name='complexity')
# Attack complexity constraints
model.addConstr(temp_degree <= red_vars_count - delta_total_r - gp.quicksum(bit_cut) + 1)
model.addConstr(temp_degree <= blue_vars_count - delta_total_b - gp.quicksum(bit_cut) + 1)
model.addConstr(temp_degree <= gp.quicksum(hash_output_bits))
model.addConstr(capacity_cond + degree_from_c <= 128 - temp_degree)
model.addConstr(128 <= 128 - 2 - sum_const_cond + capacity_cond + degree_from_c)
# Set objective
model.setObjectiveN(-1*temp_degree + 0.01*sum_const_cond + 0.01*capacity_cond, index=0, priority=3, name="PrimaryObjective")
model.setObjectiveN(-1*sum_without_place, index=1, priority=2, name="SecondaryObjective")
model.setObjectiveN(-1*sum_linear_cancel, index=2, priority=1, name="ThirdObjective")

print("Constraints and objective function set")

# Solve model
print("Starting model solution...")
model.optimize()

# Output results to file
with open(f"../final_result/Xoodyak_round_{num_rounds}_preimage_for_painting.py", 'w') as f:
    # Output statistical results
    f.write(f"Red_variables={red_vars_count.getValue() - delta_total_r.getValue()}\n")
    f.write(f"Blue_variables={blue_vars_count.getValue() - delta_total_b.getValue()}\n")
    f.write(f"sum_const_cond = {sum_const_cond.getValue()}\n")
    f.write(f"sum_without_place={sum_without_place.getValue()}\n")
    f.write(f"sum_linear_cancel = {sum_linear_cancel.getValue()}\n")
    f.write(f"temp_degree={temp_degree.x}\n")

    print("Xoodyak MILP automation modeling completed")

    # Output state information for LaTeX documentation
    row_num = 0
    initial_state_output = write_row(initial_state, row_num, '$A$')
    f.write(f"initial_state_output = {initial_state_output}\n")

    intermediate_states_output = []
    index = 0

    for round_state in intermediate_states:
        round_state_output = dict()
        theta_vars = round_state['theta_vars']
        chi_vars = round_state['chi_vars']
        linear_cancel = round_state['linear_cancel']
        linear_cancel_chi = round_state['linear_cancel_chi']
        row_num += 1

        C = round_state['C']
        temp = write_row_C(C, row_num, theta_vars, linear_cancel, f'$C^{{({index})}}$')
        round_state_output['C'] = temp
        row_num += 0.4
        D = round_state['D']
        temp = write_row_D(D, row_num, theta_vars, linear_cancel, f'$D^{{({index})}}$')
        round_state_output['D'] = temp
        row_num += 0.4
        theta = round_state['theta_state']
        temp = write_row_theta(theta, row_num, theta_vars, linear_cancel, f'$\\theta^{{({index})}}$')
        round_state_output['theta_state'] = temp

        rho_west = round_state['rho_west_state']
        if rho_west==None:
            intermediate_states_output.append(round_state_output)
            continue
        row_num += 1
        temp = write_row(rho_west, row_num, f'${{\\rho_{{west}}}}^{{({index})}}$')
        round_state_output['rho_west_state'] = temp
        row_num += 0.8
        chi = round_state['chi_state']
        temp = write_row_chi(chi, row_num, chi_vars, linear_cancel_chi, f'$\\chi^{{({index})}}$')
        round_state_output['chi_state'] = temp
        row_num += 1
        rho_east = round_state['rho_east_state']
        temp = write_row(rho_east, row_num, f'${{\\rho_{{east}}}}^{{({index})}}$')
        round_state_output['rho_east_state'] = temp

        without_place = round_state['without_place']
        temp = [[0 for x in range(4)] for z in range(32)]
        for z in range(32):
            for x in range(4):
                if type(without_place[z][x]) != int and without_place[z][x].x > 0.5:
                    temp[z][x] = 1
        round_state_output['without_place'] = temp

        index += 1
        intermediate_states_output.append(round_state_output)

    f.write(f"intermediate_states_output={intermediate_states_output}")