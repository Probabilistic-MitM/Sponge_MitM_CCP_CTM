import gurobipy as gp
from gurobipy import GRB
from base_MILP.Ascon_re_search_MILP import *
from output.re_search_write_in_file_slice_32 import *
from attack.Ascon.AsconHash.search_result.Ascon_Hash_round_4_collision import *
import os

# Create Gurobi model
model = gp.Model("Ascon_MILP_Automation")
model.setParam('MIPFocus', 2)
model.setParam('MIPGap', 0.0)  # Set optimality gap to 0

# 1. Initialize Ascon hash state
print("Initializing Ascon state...")

# Create 64x5 initial state matrix, each element is a Bit object
initial_state = [[Bit(model, f"init_z{_}_x{__}", (0, 0, 0, 0)) for _ in range(5)] for __ in range(slice_number)]

num_rounds = 3  # Number of rounds - 1
for z in range(slice_number):
    x = 0
    if initial_state_output[0][x][z] == 'lb':
        initial_state[z][x].b = 1
    elif initial_state_output[0][x][z] == 'lr':
        initial_state[z][x].r = 1

print("State initialization completed")

# 2. Apply Ascon round functions
print("Applying round functions...")

# Save intermediate states for analysis and output
intermediate_states = []
current_state = initial_state

# Apply multiple rounds
for round_num in range(num_rounds):
    print(f"Applying round {round_num + 1}")

    # P_S operation
    print(f"  Round {round_num + 1}: P_S operation")

    # Execute P_S operation
    # First round uses special initialization function
    without_place, linear_cancel_chi = None, None
    if round_num == 0:
        ps_state, ps_vars = create_first_P_S_operation_first_one_constant_cond(
            model, current_state, f"round{round_num}_PS"
        )
        temp_state_1 = None
        temp_state_2 = None
    elif round_num == 1:
        temp_state_1, temp_state_2, ps_state, ps_vars, without_place, linear_cancel_chi = create_second_P_S_operation(
            model, current_state, f"round{round_num}_PS"
        )
    else:
        # Subsequent rounds use standard P_S operation function
        temp_state_1, temp_state_2, ps_state, ps_vars, without_place, linear_cancel_chi = create_P_S_operation(
            model, current_state, f"round{round_num}_PS"
        )

    # P_L operation (linear layer)
    print(f"  Round {round_num + 1}: P_L operation")

    # Choose different P_L operation implementation based on round number
    if round_num == 0:
        pl_state, pl_vars, linear_cancel = create_first_P_L_operation(model, ps_state, f"round{round_num}_PL")
    else:
        pl_state, pl_vars, linear_cancel = create_P_L_operation(model, ps_state, f"round{round_num}_PL")

    # Helper function to set variable type
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

    if round_num == 0:
        inter_state = intermediate_states_output[round_num]
        for z in range(32):
            for x in range(5):
                set_type(ps_state[z][x], inter_state['ps_state'][0][x][z])
                set_type(pl_state[z][x], inter_state['pl_state'][0][x][z])
    if round_num == 1:
        inter_state = intermediate_states_output[round_num]
        for z in range(32):
            for x in range(5):
                set_type(ps_state[z][x], inter_state['ps_state'][0][x][z])

    # Save all states and variables of current round
    intermediate_states.append({
        'temp_state_1': temp_state_1,
        'temp_state_2': temp_state_2,
        'ps_state': ps_state,
        'ps_vars': ps_vars,
        'pl_state': pl_state,
        'pl_vars': pl_vars,
        'round_num': round_num,
        "linear_cancel": linear_cancel,
        "linear_cancel_chi": linear_cancel_chi,
        "without_place": without_place
    })

    # Update current state to state after P_L operation
    current_state = pl_state

# Final state is the state after last P_L operation
final_state = current_state
print(f"Completed {num_rounds} rounds application")

# 3. Calculate equation count and variable statistics
print("Calculating equation count...")

# Count red and blue variables in initial state
red_vars_count = gp.quicksum(initial_state[z][0].r for z in range(slice_number))
blue_vars_count = gp.quicksum(initial_state[z][0].b for z in range(slice_number))
# model.addConstr(13>=second_blue_vars_count)  # Optional blue variable upper bound constraint

# Count intervention variables in round functions
delta_total_r = 0  # Total reduction in red variables
delta_total_b = 0  # Total reduction in blue variables
sum_const_cond = 0  # Total conditional constraints
capacity_cond = 0  # Total capacity conditions
sum_CT = 0  # Total CTratic constraints
const_cond_sum = 0
sum_without_bits = 0
sum_linear_cancel = 0

for round_state in intermediate_states:
    ps_vars = round_state['ps_vars']
    linear_cancel_chi = round_state['linear_cancel_chi']
    if round_state['round_num'] == 0:
        # Variable statistics for first round
        for z in range(slice_number):
            capacity_cond += ps_vars[f'{z}_vars'][0]
            capacity_cond += ps_vars[f'{z}_vars'][1]
            for x in range(5):
                capacity_cond += ps_vars[f'{z}_constant_cond_{x}']
    else:
        # Variable statistics for subsequent rounds
        for z in range(slice_number):
            for x in range(5):
                # Count XOR operation variables
                if f"temp1_z{z}_x{x}" in ps_vars:
                    delta_total_r += ps_vars[f"temp1_z{z}_x{x}"]['delta_r']
                    delta_total_b += ps_vars[f"temp1_z{z}_x{x}"]['delta_b']
                    sum_const_cond += ps_vars[f"temp1_z{z}_x{x}"]['new_cond']
                    sum_linear_cancel += linear_cancel_chi[f"temp1_z{z}_x{x}"]

                if f"temp2_z{z}_x{x}" in ps_vars:
                    delta_total_r += ps_vars[f"temp2_z{z}_x{x}"]['delta_r']
                    delta_total_b += ps_vars[f"temp2_z{z}_x{x}"]['delta_b']
                    sum_const_cond += ps_vars[f"temp2_z{z}_x{x}"]['new_cond']
                    sum_linear_cancel += linear_cancel_chi[f"temp2_z{z}_x{x}"]

                if f"new_z{z}_x{x}" in ps_vars:
                    delta_total_r += ps_vars[f"new_z{z}_x{x}"]['delta_r']
                    delta_total_b += ps_vars[f"new_z{z}_x{x}"]['delta_b']
                    sum_const_cond += ps_vars[f"new_z{z}_x{x}"]['new_cond']
                    sum_linear_cancel += linear_cancel_chi[f"new_z{z}_x{x}"]

                # Count AND operation variables
                if f"and_z{z}_x{x}" in ps_vars:
                    sum_CT += ps_vars[f"and_z{z}_x{x}"]['CT']
                    const_cond_sum += ps_vars[f"and_z{z}_x{x}"]['const_cond']

    # Count variables in P_L operation
    pl_vars = round_state['pl_vars']
    linear_cancel = round_state['linear_cancel']
    without_place = round_state['without_place']
    for z in range(slice_number):
        for x in range(5):
            if f"new_z{z}_x{x}" in pl_vars:
                delta_total_r += pl_vars[f"new_z{z}_x{x}"]['delta_r']
                delta_total_b += pl_vars[f"new_z{z}_x{x}"]['delta_b']
                sum_const_cond += pl_vars[f"new_z{z}_x{x}"]['new_cond']
                sum_linear_cancel += linear_cancel[f"new_z{z}_x{x}"]
            if round_state['round_num'] > 0:
                sum_without_bits += without_place[z][x]

# Add upper bound for total CTratic constraints
model.addConstr(sum_CT <= 3)

# Calculate equation count for hash output bits
hash_output_bits = []
P_Svars = new_Hash_collision(model, final_state)

cut_bits = []
equation = []
for z in range(slice_number):
    hash_output_bits.append(0.2 * P_Svars[f'{z}_vars'][0])
    hash_output_bits.append(0.6 * P_Svars[f'{z}_vars'][1])
    hash_output_bits.append(1.0 * P_Svars[f'{z}_vars'][2])
    hash_output_bits.append(1.5 * P_Svars[f'{z}_vars'][3])
    hash_output_bits.append(2.0 * P_Svars[f'{z}_vars'][4])
    hash_output_bits.append(1.5 * P_Svars[f'{z}_vars'][5])
    equation.append([P_Svars[f'{z}_vars'][0], P_Svars[f'{z}_vars'][1], P_Svars[f'{z}_vars'][2],
                     P_Svars[f'{z}_vars'][3], P_Svars[f'{z}_vars'][4], P_Svars[f'{z}_vars'][5]])

    cut_bits.append(0.8 * P_Svars[f'{z}_vars'][0])
    cut_bits.append(1.4 * P_Svars[f'{z}_vars'][1])
    cut_bits.append(2.0 * P_Svars[f'{z}_vars'][2])
    cut_bits.append(2.5 * P_Svars[f'{z}_vars'][3])
    cut_bits.append(2.0 * P_Svars[f'{z}_vars'][4])
    cut_bits.append(1.5 * P_Svars[f'{z}_vars'][5])

print("Equation calculation completed")

# 4. Set optimization constraints and objective function
print("Setting constraints and objective function...")

# Add attack complexity variable
temp_degree = model.addVar(vtype=GRB.CONTINUOUS, name='complexity')
degree_from_c = model.addVar(vtype=GRB.INTEGER, name='degree_from_first_c')
# Attack complexity constraints
model.addConstr(temp_degree <= red_vars_count - delta_total_r - gp.quicksum(cut_bits) + 2)
model.addConstr(temp_degree <= blue_vars_count - delta_total_b - gp.quicksum(cut_bits) + 3)
model.addConstr(temp_degree <= gp.quicksum(hash_output_bits))

# Capacity and conditional constraints
model.addConstr(capacity_cond + degree_from_c <= 128 * slice_number / 64 - temp_degree)
model.addConstr((128) * slice_number / 64 <= 64 * slice_number / 64 - sum_const_cond + degree_from_c)

# Set objective function (multi-objective)
model.setObjectiveN(-1 * temp_degree + 0.01 * sum_const_cond, index=0, priority=2, name="PrimaryObjective")
model.setObjectiveN(-1 * sum_without_bits, index=1, priority=1, name="SecondaryObjective")
model.setObjectiveN(-1 * sum_linear_cancel, index=2, priority=0, name="ThirdObjective")

print("Constraints and objective function set")

# 5. Solve MILP model
print("Starting model solution...")

model.optimize()

# 6. Output results to file
output_file = open(f"./final_result/Ascon_Hash_round_{num_rounds + 1}_collision_for_painting.py", 'w')

# Output statistical results
output_file.write(f"Red_variables={red_vars_count.getValue() - delta_total_r.getValue()}\n")
output_file.write(f"Blue_variables={blue_vars_count.getValue() - delta_total_b.getValue()}\n")
output_file.write(f"capacity_cond={capacity_cond.getValue()}\n")
output_file.write(f"degree_from_first_c={degree_from_c.x}\n")

print("Ascon MILP automation modeling completed")

# 7. Generate state information for LaTeX documentation
row_num = 0
initial_state_latex = write_Ascon_initial(initial_state, slice_number, row_num, dict(), '$A^{(0)}$')
output_file.write(f"initial_state_output = {initial_state_latex}\n")

intermediate_states_output = []
state_index = 0

for round_state in intermediate_states:
    round_state_output = dict()
    round_state_output['round_num'] = round_state['round_num']
    ps_vars = round_state['ps_vars']
    pl_vars = round_state['pl_vars']
    linear_cancel = round_state['linear_cancel']
    linear_cancel_chi = round_state['linear_cancel_chi']

    if round_state['round_num'] > 0:
        # Process temporary state 1
        row_num += 0.4
        temp_state_1 = round_state['temp_state_1']
        temp1_latex = write_Ascon_temp_s1(temp_state_1, slice_number, linear_cancel_chi, row_num, ps_vars,
                                          f'$1/3{{P_S}}^{{({state_index})}}$')
        round_state_output['temp_state_1'] = temp1_latex

        # Process temporary state 2
        row_num += 0.4
        temp_state_2 = round_state['temp_state_2']
        temp2_latex = write_Ascon_temp_s2(temp_state_2, slice_number, linear_cancel_chi, row_num, ps_vars,
                                          f'$2/3{{P_S}}^{{({state_index})}}$')
        round_state_output['temp_state_2'] = temp2_latex

        # Process P_S operation state
        row_num += 0.4
        ps_state = round_state['ps_state']
        ps_latex = write_Ascon_P(ps_state, slice_number, linear_cancel_chi, row_num, ps_vars,
                                 f'$3/3{{P_S}}^{{({state_index})}}$')
        round_state_output['ps_state'] = ps_latex
    else:
        # Special handling for first round
        row_num += 0.4
        ps_state = round_state['ps_state']
        ps_latex = write_Ascon_initial(ps_state, slice_number, row_num, ps_vars, f'${{P_S}}^{{({state_index})}}$')
        round_state_output['ps_state'] = ps_latex

    # Process P_L operation state
    row_num += 0.4
    pl_state = round_state['pl_state']
    pl_latex = write_Ascon_P(pl_state, slice_number, linear_cancel, row_num, pl_vars, f'${{P_L}}^{{({state_index})}}$')
    round_state_output['pl_state'] = pl_latex

    without_place = round_state['without_place']
    temp = [[0 for x in range(5)] for z in range(32)]
    if without_place is not None:
        for z in range(32):
            for x in range(5):
                if type(without_place[z][x]) != int and without_place[z][x].x > 0.5:
                    temp[z][x] = 1
    round_state_output['without_place'] = temp

    intermediate_states_output.append(round_state_output)
    state_index += 1

# Write intermediate states output
output_file.write(f"intermediate_states_output={intermediate_states_output}")

output_file.close()
print("Results saved to file")
