import gurobipy as gp
from gurobipy import GRB
from base_MILP.Ascon_MILP import *
from output.write_in_file_slice_32 import *
import os

# Create Gurobi model
model = gp.Model("Ascon_MILP_Automation")
# model.setParam('MIPGap', 0.0)  # Set optimality gap to 0

# 1. Initialize Ascon hash state
print("Initializing Ascon state...")
best_obj = 0

# Create 64x5 initial state matrix
# Each element is a Bit object
initial_state = [[Bit(model, f"init_z{__}_x{_}", (0, 0, 0, 0)) for _ in range(5)] for __ in range(slice_number)]

num_rounds = 3  # Number of rounds - 1

initial_state[0][0] = Bit(model, f"init_z{0}_x{0}", (0, 0, 1, 0))

# Initialize state bits
for z in range(1, slice_number):
    x = 0  # Rate part corresponds to x=0

    # Create bit variables for rate part
    # ul=0, cond=0
    initial_state[z][x] = Bit(model, f"init_z{z}_x{x}", (0, '*', '*', 0))

    # Add mutually exclusive constraint for r and b
    # A bit cannot be both red and blue variable
    model.addConstr(initial_state[z][x].r + initial_state[z][x].b <= 1,
                    f"rate_r_b_exclusive_z{z}_x{x}")

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
    if round_num == 0:
        ps_state, ps_vars = create_first_P_S_operation_first_one_constant_cond(
            model, current_state, f"round{round_num}_PS"
        )
        temp_state_1 = None
        temp_state_2 = None
    elif round_num == 1:
        temp_state_1, temp_state_2, ps_state, ps_vars = create_second_P_S_operation(
            model, current_state, f"round{round_num}_PS"
        )
    else:
        # Subsequent rounds use standard P_S operation function
        temp_state_1, temp_state_2, ps_state, ps_vars = create_P_S_operation(
            model, current_state, f"round{round_num}_PS"
        )

    # P_L operation
    print(f"  Round {round_num + 1}: P_L operation")

    # Choose different P_L operation implementation based on round number
    if round_num == 0:
        pl_state, pl_vars = create_first_P_L_operation(model, ps_state, f"round{round_num}_PL")
    else:
        pl_state, pl_vars = create_P_L_operation(model, ps_state, f"round{round_num}_PL")

    # Save all states and variables of current round
    intermediate_states.append({
        'temp_state_1': temp_state_1,  # Temporary state 1
        'temp_state_2': temp_state_2,  # Temporary state 2
        'ps_state': ps_state,          # State after P_S operation
        'ps_vars': ps_vars,            # Variables for P_S operation
        'pl_state': pl_state,          # State after P_L operation
        'pl_vars': pl_vars,            # Variables for P_L operation
        'round_num': round_num         # Round number index
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
capacity_cond = 0   # Total capacity conditions
sum_CT = 0        # Total CTratic constraints

for round_state in intermediate_states:
    ps_vars = round_state['ps_vars']

    if round_state['round_num'] == 0:
        # Variable statistics for first round
        for z in range(slice_number):
            capacity_cond += ps_vars[f'{z}_vars'][0]
            capacity_cond += ps_vars[f'{z}_vars'][1]
            for x in range(5):
                sum_const_cond += ps_vars[f'{z}_constant_cond_{x}']
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

                if f"temp2_z{z}_x{x}" in ps_vars:
                    delta_total_r += ps_vars[f"temp2_z{z}_x{x}"]['delta_r']
                    delta_total_b += ps_vars[f"temp2_z{z}_x{x}"]['delta_b']
                    sum_const_cond += ps_vars[f"temp2_z{z}_x{x}"]['new_cond']

                if f"new_z{z}_x{x}" in ps_vars:
                    delta_total_r += ps_vars[f"new_z{z}_x{x}"]['delta_r']
                    delta_total_b += ps_vars[f"new_z{z}_x{x}"]['delta_b']
                    sum_const_cond += ps_vars[f"new_z{z}_x{x}"]['new_cond']

                # Count AND operation variables
                if f"and_z{z}_x{x}" in ps_vars:
                    sum_CT += ps_vars[f"and_z{z}_x{x}"]['CT']

    # Count variables in P_L operation
    pl_vars = round_state['pl_vars']
    for z in range(slice_number):
        for x in range(5):
            if f"new_z{z}_x{x}" in pl_vars:
                delta_total_r += pl_vars[f"new_z{z}_x{x}"]['delta_r']
                delta_total_b += pl_vars[f"new_z{z}_x{x}"]['delta_b']
                sum_const_cond += pl_vars[f"new_z{z}_x{x}"]['new_cond']

# Add upper bound for total CTratic constraints
model.addConstr(sum_CT <= 3)

# Calculate equation count for hash output bits
hash_output_bits = []
P_Svars = new_simple_Hash_collision(model, final_state)

cut_bits = []
for z in range(slice_number):
    hash_output_bits.append(1.5 * P_Svars[f'{z}_vars'][0])
    hash_output_bits.append(2.0 * P_Svars[f'{z}_vars'][1])
    hash_output_bits.append(1.5 * P_Svars[f'{z}_vars'][2])

    cut_bits.append(2.5 * P_Svars[f'{z}_vars'][0])
    cut_bits.append(2.0 * P_Svars[f'{z}_vars'][1])
    cut_bits.append(1.5 * P_Svars[f'{z}_vars'][2])

print("Equation calculation completed")

# 4. Set optimization constraints and objective function
print("Setting constraints and objective function...")

# Add attack complexity variable
temp_degree = model.addVar(vtype=GRB.CONTINUOUS, name='complexity')
degree_from_c = model.addVar(vtype=GRB.INTEGER, name='degree_from_first_c')

# Attack complexity constraints
model.addConstr(temp_degree <= red_vars_count - delta_total_r - gp.quicksum(cut_bits) + 1.5)
model.addConstr(temp_degree <= blue_vars_count - delta_total_b - gp.quicksum(cut_bits) + 1.5)
model.addConstr(temp_degree <= gp.quicksum(hash_output_bits))

# Capacity and conditional constraints
model.addConstr(capacity_cond + degree_from_c <= 128 * slice_number / 64 - temp_degree)
model.addConstr((128) * slice_number / 64 <= 64 * slice_number / 64 - sum_const_cond + degree_from_c)

# Set objective function
model.setObjective(temp_degree, GRB.MAXIMIZE)

print("Constraints and objective function set")

# 5. Solve MILP model
print("Starting model solution...")

model.optimize()

# 6. Output results to file
output_file = open(f"./search_result/Ascon_Hash_round_{num_rounds + 1}_collision.py", 'w')

# Output statistical results
output_file.write(f"Red_variables={red_vars_count.getValue() - delta_total_r.getValue()}\n")
output_file.write(f"Blue_variables={blue_vars_count.getValue() - delta_total_b.getValue()}\n")

print("Ascon MILP automation modeling completed")

# 7. Generate state information for LaTeX documentation
row_num = 0
initial_state_latex = write_Ascon_initial(initial_state, slice_number, row_num, dict(), '$A$')
output_file.write(f"initial_state_output = {initial_state_latex}\n")

intermediate_states_output = []
state_index = 1

for round_state in intermediate_states:
    round_state_output = dict()
    round_state_output['round_num'] = round_state['round_num']
    ps_vars = round_state['ps_vars']
    pl_vars = round_state['pl_vars']

    if round_state['round_num'] > 0:
        # Process temporary state 1
        row_num += 0.4
        temp_state_1 = round_state['temp_state_1']
        temp1_latex = write_Ascon_temp_s1(temp_state_1, slice_number, row_num, ps_vars, f'$t_1{state_index}$')
        round_state_output['temp_state_1'] = temp1_latex

        # Process temporary state 2
        row_num += 0.4
        temp_state_2 = round_state['temp_state_2']
        temp2_latex = write_Ascon_temp_s2(temp_state_2, slice_number, row_num, ps_vars, f'$t_2{state_index}$')
        round_state_output['temp_state_2'] = temp2_latex

        # Process P_S operation state
        row_num += 0.4
        ps_state = round_state['ps_state']
        ps_latex = write_Ascon_P(ps_state, slice_number, row_num, ps_vars, f'$P_S{state_index}$')
        round_state_output['ps_state'] = ps_latex
    else:
        # Special handling for first round
        row_num += 0.4
        ps_state = round_state['ps_state']
        ps_latex = write_Ascon_initial(ps_state, slice_number, row_num, ps_vars, f'$P_S{state_index}$')
        round_state_output['ps_state'] = ps_latex

    # Process P_L operation state
    row_num += 0.4
    pl_state = round_state['pl_state']
    pl_latex = write_Ascon_P(pl_state, slice_number, row_num, pl_vars, f'$P_L{state_index}$')
    round_state_output['pl_state'] = pl_latex

    intermediate_states_output.append(round_state_output)
    state_index += 1

# Write intermediate states output
output_file.write(f"intermediate_states_output={intermediate_states_output}")

output_file.close()
print("Results saved to file")