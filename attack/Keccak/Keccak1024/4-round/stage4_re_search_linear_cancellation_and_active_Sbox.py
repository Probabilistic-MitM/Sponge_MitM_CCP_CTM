from gurobipy import GRB
from base_MILP.Keccak_re_search_MILP import *
from output.re_search_write_in_file_slice_64 import *
from attack.Keccak.Keccak1024.final_result.SHA3_512_round_4_preimage import initial_state_output, intermediate_states_output

# Create Gurobi model
model = gp.Model("Keccak_MILP_Automation")
model.setParam('MIPFocus', 1)

# 1. Initialize state
print("Initializing Keccak state...")

# Create 5x5x64 initial state
initial_state = [[[Bit(model, 'constant', 'uc') for x in range(5)] for y in range(5)] for z in range(64)]

num_rounds = 3  # Number of rounds-1

# Initialize state bits
for z in range(64):
    for x in range(5):
        for y in range(5):
            if initial_state_output[0][x][y][z] == 'lr':
                initial_state[z][y][x].r = 1
                initial_state[z][y][x].b = 0
            elif initial_state_output[0][x][y][z] == 'lb':
                initial_state[z][y][x].r = 0
                initial_state[z][y][x].b = 1
            elif initial_state_output[0][x][y][z] == 'c':
                initial_state[z][y][x].r = 0
                initial_state[z][y][x].b = 0
            else:
                print(initial_state_output[0][z][y][x])
                exit(1)

# 2. Apply round functions
print("Applying round functions...")

# Save intermediate states
intermediate_states = []
current_state = initial_state


def set_type(var, type):
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
    inter_state = intermediate_states_output[round_num]
    print(f"Applying round {round_num + 1}")

    # Theta operation
    print(f"  Round {round_num + 1}: Theta operation")
    if round_num == 0:
        theta_state, C, D, theta_vars, linear_cancel = create_first_theta_operation(model, current_state, f"round{round_num}_theta")
    elif round_num == 1:
        theta_state, C, D, theta_vars, linear_cancel = create_second_theta_operation(model, current_state, f"round{round_num}_theta")
    else:
        theta_state, C, D, theta_vars, linear_cancel = create_theta_operation(model, current_state, f"round{round_num}_theta")

    # Rho operation (bit rotation)
    print(f"  Round {round_num + 1}: Rho operation")
    rho_state = rho(theta_state)

    # Pi operation (position permutation)
    print(f"  Round {round_num + 1}: Pi operation")
    pi_state = pi(rho_state)

    # Chi operation
    print(f"  Round {round_num + 1}: Chi operation")

    if round_num == 0:
        chi_state, chi_vars, without_place, linear_cancel_chi = create_first_chi_operation_512(model, pi_state, f"round{round_num}_chi")
    elif round_num == 1:
        chi_state, chi_vars, without_place, linear_cancel_chi = create_second_chi_operation(model, pi_state, f"round{round_num}_chi")
    else:
        chi_state, chi_vars, without_place, linear_cancel_chi = create_chi_operation(model, pi_state, f"round{round_num}_chi")

    if round_num<=1:
        for z in range(64):
            for x in range(5):
                set_type(C[z][x], inter_state['C'][0][x][z])
                set_type(D[z][x], inter_state['D'][0][x][z])
                for y in range(5):
                    set_type(theta_state[z][y][x], inter_state['theta'][0][x][y][z])
                    set_type(chi_state[z][y][x], inter_state['chi'][0][x][y][z])

    intermediate_states.append({
        'theta': theta_state,
        'C': C,
        'D': D,
        'theta_var': theta_vars,
        'rho': rho_state,
        'pi': pi_state,
        'chi': chi_state,
        'chi_var': chi_vars,
        'without_place': without_place,
        "linear_cancel": linear_cancel,
        'round_number': round_num,
        "linear_cancel_chi": linear_cancel_chi
    })

    # Update current state
    current_state = chi_state

final_state = current_state
print(f"Completed {num_rounds} rounds application")

# 3. Calculate equation count and variable statistics
print("Calculating equation count...")

# Count variable types in initial state
red_vars_count = gp.quicksum(initial_state[z][y][x].r for z in range(64) for y in range(5) for x in range(5))
blue_vars_count = gp.quicksum(initial_state[z][y][x].b for z in range(64) for y in range(5) for x in range(5))

# Count intervention variables in round functions
delta_total_r = 0
delta_total_b = 0
sum_const_cond = 0
sum_CT = 0
sum_without_place = 0
sum_linear_cancel = 0
for round_state in intermediate_states:
    round_number = round_state['round_number']
    theta_vars = round_state['theta_var']
    linear_cancel = round_state['linear_cancel']

    for z in range(64):
        for x in range(5):
            delta_total_r += theta_vars[f"C_x{x}_z{z}"]['delta_r']
            delta_total_b += theta_vars[f"C_x{x}_z{z}"]['delta_b']
            sum_const_cond += theta_vars[f"C_x{x}_z{z}"]['new_cond']
            if round_number > 0:
                sum_linear_cancel += linear_cancel[f"C_x{x}_z{z}"]

            delta_total_r += theta_vars[f"D_x{x}_z{z}"]['delta_r']
            delta_total_b += theta_vars[f"D_x{x}_z{z}"]['delta_b']
            sum_const_cond += theta_vars[f"D_x{x}_z{z}"]['new_cond']
            if round_number > 0:
                sum_linear_cancel += linear_cancel[f"D_x{x}_z{z}"]

            for y in range(5):
                delta_total_r += theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_r']
                delta_total_b += theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_b']
                sum_const_cond += theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond']
                if round_number > 0:
                    sum_linear_cancel += linear_cancel[f"new_z{z}_y{y}_x{x}"]

    chi_vars = round_state['chi_var']
    without_place = round_state['without_place']
    linear_cancel_chi = round_state['linear_cancel_chi']
    for z in range(64):
        for y in range(5):
            sum_without_place += without_place[z][y]
            for x in range(5):
                delta_total_r += chi_vars[f"new_z{z}_y{y}_x{x}"]['delta_r']
                delta_total_b += chi_vars[f"new_z{z}_y{y}_x{x}"]['delta_b']
                sum_const_cond += chi_vars[f"new_z{z}_y{y}_x{x}"]['new_cond']
                sum_CT += chi_vars[f"and_z{z}_y{y}_x{x}"]['CT']
                if round_number > 0:
                    sum_linear_cancel += linear_cancel_chi[f"new_z{z}_y{y}_x{x}"]

# Add constraints
model.addConstr(sum_CT <= 6)

# Calculate hash output bits
hash_output_bits = []
cut_bits = []

equations = []
for z in range(64):
    # Equation 1 constraints
    equation1 = model.addVar(vtype=GRB.BINARY, name=f'equation1_{z}')
    model.addConstr(equation1 <= 1 - final_state[z][0][3].ul + final_state[z][0][3].r + final_state[z][0][3].b)
    model.addConstr(equation1 <= 1 - final_state[z][3][3].ul + final_state[z][3][3].r + final_state[z][3][3].b)
    model.addConstr(equation1 <= 1 - final_state[(z - 39) % 64][2][0].ul + final_state[(z - 39) % 64][2][0].r +
                    final_state[(z - 39) % 64][2][0].b)
    model.addConstr(equation1 <= 1 - final_state[(z - 39) % 64][0][0].ul + final_state[(z - 39) % 64][0][0].r +
                    final_state[(z - 39) % 64][0][0].b)
    hash_output_bits.append(equation1)

    # Equation 2 constraints
    equation2 = model.addVar(vtype=GRB.BINARY, name=f'equation2_{z}')
    model.addConstr(equation2 <= 1 - final_state[z][1][4].ul + final_state[z][1][4].r + final_state[z][1][4].b)
    model.addConstr(equation2 <= 1 - final_state[z][4][4].ul + final_state[z][4][4].r + final_state[z][4][4].b)
    model.addConstr(equation2 <= 1 - final_state[(z - 25) % 64][3][1].ul + final_state[(z - 25) % 64][3][1].r +
                    final_state[(z - 25) % 64][3][1].b)
    model.addConstr(equation2 <= 1 - final_state[(z - 25) % 64][1][1].ul + final_state[(z - 25) % 64][1][1].r +
                    final_state[(z - 25) % 64][1][1].b)
    hash_output_bits.append(equation2)

    equation3 = model.addVar(vtype=GRB.BINARY, name=f'equation3_{z}')
    model.addConstr(equation3 <= 1 - final_state[z][0][3].ul + final_state[z][0][3].r + final_state[z][0][3].b)
    model.addConstr(equation3 <= 1 - final_state[z][3][3].ul + final_state[z][3][3].r + final_state[z][3][3].b)
    hash_output_bits.append(0.58 * equation3)
    cut_bits.append(0.42 * equation3)

    equation4 = model.addVar(vtype=GRB.BINARY, name=f'equation4_{z}')
    model.addConstr(equation4 <= 1 - final_state[z][1][4].ul + final_state[z][1][4].r + final_state[z][1][4].b)
    model.addConstr(equation4 <= 1 - final_state[z][4][4].ul + final_state[z][4][4].r + final_state[z][4][4].b)
    hash_output_bits.append(0.58 * equation4)
    cut_bits.append(0.42 * equation4)
    equations.append([equation1, equation2, equation3, equation4])

    model.addConstr(equation1 + equation3 <= 1)
    model.addConstr(equation2 + equation4 <= 1)

# Total equations
total_equations = gp.quicksum(hash_output_bits)

print("Equation calculation completed")

# 4. Set constraints and objective function
print("Setting constraints and objective function...")

# Complexity variable
temp_degree = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name='complexity')

# Attack complexity constraints
model.addConstr(temp_degree <= red_vars_count - delta_total_r - gp.quicksum(cut_bits))
model.addConstr(temp_degree <= blue_vars_count - delta_total_b - gp.quicksum(cut_bits))
model.addConstr(temp_degree <= total_equations)

# Set objectives
model.setObjectiveN(-1 * temp_degree + 0.01 * sum_const_cond, index=0, priority=3, name="PrimaryObjective")
model.setObjectiveN(-1 * sum_without_place, index=1, priority=2, name="SecondaryObjective")
model.setObjectiveN(-1 * sum_linear_cancel, index=3, priority=1, name="ThirdObjective")

print("Constraints and objective function set")

# Solve model
print("Starting model solution...")
model.optimize()

# Output results to file
with open(f"../final_result/SHA3_512_round_{num_rounds + 1}_preimage_for_painting.py", 'w') as f:
    # Output statistical results
    f.write(f"Red_variables={red_vars_count.getValue() - delta_total_r.getValue()}\n")
    f.write(f"Blue_variables={blue_vars_count.getValue() - delta_total_b.getValue()}\n")
    f.write(f"sum_const_cond = {sum_const_cond.getValue()}\n")
    f.write(f"sum_without_place={sum_without_place.getValue()}\n")
    f.write(f"sum_linear_cancel = {sum_linear_cancel.getValue()}\n")
    f.write(f"temp_degree={temp_degree.x}\n")

    print("Keccak MILP automation modeling completed")

    # Output state information for LaTeX documentation
    row_num = 0
    initial_state_output = write_row(initial_state, row_num, '$A$')
    f.write(f"initial_state_output = {initial_state_output}\n")

    intermediate_states_output = []
    index = 0

    for round_state in intermediate_states:
        round_state_output = dict()
        theta_vars = round_state['theta_var']
        chi_vars = round_state['chi_var']
        linear_cancel = round_state['linear_cancel']
        linear_cancel_chi = round_state['linear_cancel_chi']
        row_num += 1

        C = round_state['C']
        C_output = write_row_C(C, row_num, theta_vars, linear_cancel, f'$C^{{({index})}}$')
        round_state_output['C'] = C_output
        row_num += 0.4

        D = round_state['D']
        D_output = write_row_D(D, row_num, theta_vars, linear_cancel, f'$D^{{({index})}}$')
        round_state_output['D'] = D_output
        row_num += 0.4

        theta = round_state['theta']
        theta_output = write_row_theta(theta, row_num, theta_vars, linear_cancel, f'$\\theta^{{({index})}}$')
        round_state_output['theta'] = theta_output
        row_num += 0.8

        rho_state = round_state['rho']
        rho_output = write_row(rho_state, row_num, f'$\\rho^{{({index})}}$')
        round_state_output['rho'] = rho_output
        row_num += 0.8

        pi_state = round_state['pi']
        pi_output = write_row(pi_state, row_num, f'$\\pi^{{({index})}}$')
        round_state_output['pi'] = pi_output
        row_num += 0.8

        chi = round_state['chi']
        chi_output = write_row_chi(chi, row_num, chi_vars, linear_cancel_chi, f'$\\chi^{{({index})}}$')
        round_state_output['chi'] = chi_output

        without_place = round_state['without_place']
        temp = [[0 for y in range(5)] for z in range(64)]
        for z in range(64):
            for y in range(5):
                if type(without_place[z][y]) != int and without_place[z][y].x > 0.5:
                    temp[z][y] = 1
        round_state_output['without_place'] = temp

        index += 1
        intermediate_states_output.append(round_state_output)

    f.write(f"intermediate_states_output={intermediate_states_output}\n")


