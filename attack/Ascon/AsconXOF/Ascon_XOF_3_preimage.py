import gurobipy as gp
from gurobipy import GRB
from base_MILP.Ascon_MILP import *
from output.write_in_file_slice_32 import *


# Create Gurobi model
model = gp.Model("Ascon_MILP_Automation")
# model.setParam('MIPGap', 0.0)  # Set optimality gap to 0

# 1. Initialize Ascon-XOF preimage attack state
print("Initializing Ascon state...")

# Create 64x5 initial state matrix
# Each element is a Bit object
initial_state = [[Bit(model, f"init_z{__}_x{_}", (0, 0, 0, 0)) for _ in range(5)] for __ in range(slice_number)]

num_rounds = 2  # Number of rounds - 1

# Initialize state bits
for z in range(slice_number):
    x = 0  # Rate part corresponds to x=0
    if z >= slice_number - 1:  # Padding part
        # Use undetermined constant for specific positions
        initial_state[z][x] = Bit(model, f"init_z{z}_x{x}", (0, 0, 0, 0))
    else:
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
        ps_state, ps_vars = create_first_P_S_operation_first_one_constant_cond_padding_three_stage(
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

    # P_L operation (linear layer)
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

# Add blue variable count constraint (upper bound 11)
model.addConstr(10 >= blue_vars_count)

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
            initial_p_s = ps_vars
            capacity_cond += ps_vars[f'{z}_vars'][0]
            capacity_cond += ps_vars[f'{z}_vars'][1]
            capacity_cond += ps_vars[f'{z}_vars'][2]
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

# Calculate quality indicator variables for hash output bits
hash_output_bits = []
cut_bit = []
for z in range(slice_number):
    temp = model.addVar(vtype=GRB.BINARY, name='good_slice')
    new_temp = model.addVar(vtype=GRB.BINARY, name='new_good_slice')
    new_temp2 = model.addVar(vtype=GRB.BINARY, name='new_good_slice2')
    model.addConstr(new_temp <= 1 - final_state[z][3].ul + final_state[z][3].r + final_state[z][3].b)
    model.addConstr(new_temp <= 1 - final_state[z][4].ul + final_state[z][4].r + final_state[z][4].b)
    for x in [0, 3, 4]:
        model.addConstr(new_temp2 <= 1 - final_state[z][x].ul + final_state[z][x].r + final_state[z][x].b)
    model.addConstr(new_temp + temp <= 1)
    for x in range(5):
        model.addConstr(temp <= 1 - final_state[z][x].ul + final_state[z][x].r + final_state[z][x].b)
    model.addConstr(temp <= 2 - final_state[z][1].r - final_state[z][4].b)
    model.addConstr(temp <= 2 - final_state[z][1].b - final_state[z][4].r)
    model.addConstr(temp <= 2 - final_state[z][1].r - final_state[z][2].b)
    model.addConstr(temp <= 2 - final_state[z][1].b - final_state[z][2].r)
    model.addConstr(temp <= 2 - final_state[z][1].r - final_state[z][0].b)
    model.addConstr(temp <= 2 - final_state[z][1].b - final_state[z][0].r)
    model.addConstr(new_temp + temp + new_temp2 <= 1)
    hash_output_bits.append(temp)

    hash_output_bits.append(0.58 * new_temp)
    cut_bit.append(0.42 * new_temp)

    hash_output_bits.append(new_temp2)
    cut_bit.append(new_temp2)

print("Equation calculation completed")

# 4. Set optimization constraints and objective function
print("Setting constraints and objective function...")

# Add attack complexity variable
temp_degree = model.addVar(vtype=GRB.CONTINUOUS, name='complexity')

# Attack complexity constraints
# Complexity limited by red variables, blue variables and total equations
model.addConstr(blue_vars_count - delta_total_b - gp.quicksum(cut_bit) <= 7)
model.addConstr(temp_degree <= red_vars_count - delta_total_r - gp.quicksum(cut_bit) + 2)
model.addConstr(temp_degree <= blue_vars_count - delta_total_b - gp.quicksum(cut_bit) + 2)
model.addConstr(temp_degree <= gp.quicksum(hash_output_bits))
model.addConstr(gp.quicksum(hash_output_bits) >= red_vars_count - delta_total_r - gp.quicksum(cut_bit) + 2)
model.addConstr(gp.quicksum(hash_output_bits) >= blue_vars_count - delta_total_b - gp.quicksum(cut_bit) + 2)

pre_initial_state = [[Bit(model, f"init_z{__}_x{_}", (0, 0, 0, 0)) for _ in range(5)] for __ in range(slice_number)]

# Initialize state bits
for z in range(slice_number):
    x = 0  # Rate part corresponds to x=0
    pre_initial_state[z][x] = Bit(model, f"init_z{z}_x{x}", (0, '*', '*', 0))
    model.addConstr(pre_initial_state[z][x].r + pre_initial_state[z][x].b <= 1,
                    f"rate_r_b_exclusive_z{z}_x{x}")

print("State initialization completed")

# 2. Apply Ascon round functions
print("Applying round functions...")

# Save intermediate states for analysis and output
pre_intermediate_states = []
pre_current_state = pre_initial_state

# Apply multiple rounds
for round_num in range(num_rounds):
    print(f"Applying round {round_num + 1}")

    # P_S operation
    print(f"  Round {round_num + 1}: P_S operation")

    # Execute P_S operation
    # First round uses special initialization function
    if round_num == 0:
        ps_state, ps_vars = create_first_P_S_operation_first_one_constant_cond(
            model, pre_current_state, f"round{round_num}_PS"
        )
        temp_state_1 = None
        temp_state_2 = None
    elif round_num == 1:
        temp_state_1, temp_state_2, ps_state, ps_vars = create_second_P_S_operation(
            model, pre_current_state, f"round{round_num}_PS"
        )
    else:
        # Subsequent rounds use standard P_S operation function
        temp_state_1, temp_state_2, ps_state, ps_vars = create_P_S_operation(
            model, pre_current_state, f"round{round_num}_PS"
        )

    # P_L operation
    print(f"  Round {round_num + 1}: P_L operation")

    # Choose different P_L operation implementation based on round number
    if round_num == 0:
        pl_state, pl_vars = create_first_P_L_operation(model, ps_state, f"round{round_num}_PL")
    else:
        pl_state, pl_vars = create_P_L_operation(model, ps_state, f"round{round_num}_PL")

    # Save all states and variables of current round
    pre_intermediate_states.append({
        'temp_state_1': temp_state_1,  # Temporary state 1
        'temp_state_2': temp_state_2,  # Temporary state 2
        'ps_state': ps_state,          # State after P_S operation
        'ps_vars': ps_vars,            # Variables for P_S operation
        'pl_state': pl_state,          # State after P_L operation
        'pl_vars': pl_vars,            # Variables for P_L operation
        'round_num': round_num         # Round number index
    })

    # Update current state to state after P_L operation
    pre_current_state = pl_state

# Final state is the state after last P_L operation
pre_final_state = pre_current_state
print(f"Completed {num_rounds} rounds application")

# 3. Calculate equation count and variable statistics
print("Calculating equation count...")

# Count red and blue variables in initial state
pre_red_vars_count = gp.quicksum(pre_initial_state[z][0].r for z in range(slice_number))
pre_blue_vars_count = gp.quicksum(pre_initial_state[z][0].b for z in range(slice_number))
# model.addConstr(13>=second_blue_vars_count)  # Optional blue variable upper bound constraint

# Count intervention variables in round functions
pre_delta_total_r = 0  # Total reduction in red variables
pre_delta_total_b = 0  # Total reduction in blue variables
pre_sum_const_cond = 0  # Total conditional constraints
pre_capacity_cond = 0   # Total capacity conditions
pre_sum_CT = 0        # Total CTratic constraints

for round_state in pre_intermediate_states:
    ps_vars = round_state['ps_vars']

    if round_state['round_num'] == 0:
        # Variable statistics for first round
        for z in range(slice_number):
            pre_capacity_cond += ps_vars[f'{z}_vars'][0]
            pre_capacity_cond += ps_vars[f'{z}_vars'][1]
            for x in range(5):
                pre_capacity_cond += ps_vars[f'{z}_constant_cond_{x}']
    else:
        # Variable statistics for subsequent rounds
        for z in range(slice_number):
            for x in range(5):
                # Count XOR operation variables
                if f"temp1_z{z}_x{x}" in ps_vars:
                    pre_delta_total_r += ps_vars[f"temp1_z{z}_x{x}"]['delta_r']
                    pre_delta_total_b += ps_vars[f"temp1_z{z}_x{x}"]['delta_b']
                    pre_sum_const_cond += ps_vars[f"temp1_z{z}_x{x}"]['new_cond']

                if f"temp2_z{z}_x{x}" in ps_vars:
                    pre_delta_total_r += ps_vars[f"temp2_z{z}_x{x}"]['delta_r']
                    pre_delta_total_b += ps_vars[f"temp2_z{z}_x{x}"]['delta_b']
                    pre_sum_const_cond += ps_vars[f"temp2_z{z}_x{x}"]['new_cond']

                if f"new_z{z}_x{x}" in ps_vars:
                    pre_delta_total_r += ps_vars[f"new_z{z}_x{x}"]['delta_r']
                    pre_delta_total_b += ps_vars[f"new_z{z}_x{x}"]['delta_b']
                    pre_sum_const_cond += ps_vars[f"new_z{z}_x{x}"]['new_cond']

                # Count AND operation variables
                if f"and_z{z}_x{x}" in ps_vars:
                    pre_sum_CT += ps_vars[f"and_z{z}_x{x}"]['CT']

    # Count variables in P_L operation
    pl_vars = round_state['pl_vars']
    for z in range(slice_number):
        for x in range(5):
            if f"new_z{z}_x{x}" in pl_vars:
                pre_delta_total_r += pl_vars[f"new_z{z}_x{x}"]['delta_r']
                pre_delta_total_b += pl_vars[f"new_z{z}_x{x}"]['delta_b']
                pre_sum_const_cond += pl_vars[f"new_z{z}_x{x}"]['new_cond']

# Add upper bound for total CTratic constraints
model.addConstr(pre_sum_CT <= 3)

# Calculate equation count for hash output bits
pre_hash_output_bits = []
pre_cut_bits = []
# Conditions to be specified here

for z in range(slice_number):
    no_ul0 = model.addVar(vtype=GRB.BINARY, name=f"no_ul0")
    no_ul1 = model.addVar(vtype=GRB.BINARY, name=f"no_ul1")
    no_ul2 = model.addVar(vtype=GRB.BINARY, name=f"no_ul2")
    no_ul3 = model.addVar(vtype=GRB.BINARY, name=f"no_ul3")
    no_ul4 = model.addVar(vtype=GRB.BINARY, name=f"no_ul4")
    no_ul = [no_ul0, no_ul1, no_ul2, no_ul3, no_ul4]
    for i in range(5):
        model.addConstr(no_ul[i] <= 1 - pre_final_state[z][i].ul + pre_final_state[z][i].r + pre_final_state[z][i].b)

    condition = [0, 0, 0, 0, 0]
    for i in range(5):
        condition[i] = model.addVar(vtype=GRB.BINARY, name=f"condition_{i}")
    less_cost = model.addVar(vtype=GRB.BINARY, name=f"less_cost")

    model.addConstr(condition[0] >= initial_p_s[f'{z}_vars'][0] - initial_p_s[f'{z}_vars'][2])
    model.addConstr(condition[0] <= initial_p_s[f'{z}_vars'][0])
    model.addConstr(condition[0] <= 1 - initial_p_s[f'{z}_vars'][2])

    model.addConstr(condition[1] >= initial_p_s[f'{z}_vars'][1] - initial_p_s[f'{z}_vars'][2])
    model.addConstr(condition[1] <= initial_p_s[f'{z}_vars'][1])
    model.addConstr(condition[1] <= 1 - initial_p_s[f'{z}_vars'][2])

    model.addConstr(condition[2] >= initial_p_s[f'{z}_vars'][0] + initial_p_s[f'{z}_vars'][2] - 1)
    model.addConstr(condition[2] <= initial_p_s[f'{z}_vars'][0])
    model.addConstr(condition[2] <= initial_p_s[f'{z}_vars'][2])

    model.addConstr(condition[3] >= initial_p_s[f'{z}_vars'][1] + initial_p_s[f'{z}_vars'][2] - 1)
    model.addConstr(condition[3] <= initial_p_s[f'{z}_vars'][1])
    model.addConstr(condition[3] <= initial_p_s[f'{z}_vars'][2])

    model.addConstr(condition[4] >= - initial_p_s[f'{z}_vars'][0] - initial_p_s[f'{z}_vars'][1] + initial_p_s[f'{z}_vars'][2])
    model.addConstr(condition[4] <= 1 - initial_p_s[f'{z}_vars'][0])
    model.addConstr(condition[4] <= 1 - initial_p_s[f'{z}_vars'][1])
    model.addConstr(condition[4] <= initial_p_s[f'{z}_vars'][2])

    model.addConstr((1 - condition[3 - 1]) + (1 - condition[4 - 1]) >= 1)
    model.addConstr((1 - no_ul3) + (1 - less_cost) >= 1)
    model.addConstr((1 - condition[2 - 1]) + (1 - condition[4 - 1]) >= 1)
    model.addConstr((1 - condition[1 - 1]) + (1 - condition[4 - 1]) >= 1)
    model.addConstr((1 - condition[2 - 1]) + (1 - condition[3 - 1]) >= 1)
    model.addConstr((1 - condition[1 - 1]) + (1 - condition[3 - 1]) >= 1)
    model.addConstr((1 - condition[4 - 1]) + (1 - condition[5 - 1]) >= 1)
    model.addConstr((1 - condition[3 - 1]) + (1 - condition[5 - 1]) >= 1)
    model.addConstr((1 - no_ul3) + no_ul4 >= 1)
    model.addConstr((1 - condition[1 - 1]) + (1 - condition[2 - 1]) >= 1)
    model.addConstr((1 - condition[2 - 1]) + (1 - condition[5 - 1]) >= 1)
    model.addConstr((1 - condition[1 - 1]) + (1 - condition[5 - 1]) >= 1)
    model.addConstr(no_ul0 + (1 - no_ul4) + condition[5 - 1] >= 1)
    model.addConstr(condition[1 - 1] + condition[2 - 1] + (1 - less_cost) >= 1)
    model.addConstr(no_ul2 + (1 - no_ul4) + condition[1 - 1] + condition[2 - 1] >= 1)
    model.addConstr((1 - no_ul1) + no_ul4 + condition[5 - 1] >= 1)
    model.addConstr(no_ul2 + (1 - less_cost) >= 1)
    model.addConstr((1 - no_ul0) + condition[1 - 1] + condition[2 - 1] + condition[3 - 1] + condition[4 - 1] + condition[5 - 1] >= 1)
    model.addConstr(no_ul3 + (1 - condition[2 - 1]) + less_cost >= 1)
    model.addConstr(no_ul3 + (1 - condition[1 - 1]) + less_cost >= 1)
    model.addConstr(no_ul1 + (1 - no_ul2) + no_ul4 >= 1)
    model.addConstr(no_ul3 + (1 - condition[3 - 1]) >= 1)
    model.addConstr(no_ul1 + (1 - condition[4 - 1]) >= 1)
    model.addConstr(no_ul0 + no_ul3 + (1 - condition[5 - 1]) >= 1)
    model.addConstr(no_ul1 + (1 - no_ul2) + no_ul3 + condition[5 - 1] >= 1)
    model.addConstr(no_ul1 + no_ul2 + (1 - no_ul4) >= 1)
    model.addConstr((1 - no_ul0) + no_ul2 + condition[1 - 1] + condition[2 - 1] >= 1)
    model.addConstr(no_ul1 + (1 - no_ul3) + (1 - condition[5 - 1]) >= 1)

    pre_hash_output_bits.append(condition[0])
    pre_hash_output_bits.append(condition[1])
    pre_hash_output_bits.append(2 * condition[2])
    pre_hash_output_bits.append(2 * condition[3])
    pre_hash_output_bits.append(condition[4])

    pre_cut_bits.append(2 * condition[0])
    pre_cut_bits.append(2 * condition[1])
    pre_cut_bits.append(condition[2])
    pre_cut_bits.append(condition[3])
    pre_cut_bits.append(2 * condition[4])

    pre_cut_bits.append(-1 * less_cost)

print("Equation calculation completed")

# 4. Set optimization constraints and objective function
print("Setting constraints and objective function...")

# Add attack complexity variable
free_capacity = model.addVar(vtype=GRB.CONTINUOUS, name='free_capacity')
degree_from_first_c = model.addVar(vtype=GRB.CONTINUOUS, name='degree_from_first_c')

# Attack complexity constraints
model.addConstr(free_capacity <= pre_red_vars_count - pre_delta_total_r - gp.quicksum(pre_cut_bits) + 2)
model.addConstr(free_capacity <= pre_blue_vars_count - pre_delta_total_b - gp.quicksum(pre_cut_bits) + 2)
model.addConstr(free_capacity <= gp.quicksum(pre_hash_output_bits))

# Capacity and conditional constraints
degree_from_c = model.addVar(vtype=GRB.INTEGER, name='degree_from_c')

# Capacity and conditional constraints
model.addConstr(pre_capacity_cond + degree_from_first_c <= 128 * slice_number / 64 - temp_degree)
model.addConstr(degree_from_c <= 64 * slice_number / 64 - pre_sum_const_cond + degree_from_first_c)

model.addConstr(capacity_cond - free_capacity + degree_from_c <= 128 * slice_number / 64 - temp_degree)
model.addConstr((128) * slice_number / 64 <= (64 - 1) * slice_number / 64 - sum_const_cond + degree_from_c)

# Set objective
model.setObjective(temp_degree, GRB.MAXIMIZE)

print("Constraints and objective function set")

# 5. Solve MILP model
print("Starting model solution...")


model.optimize()

# 6. Output results to file
output_file = open(f"./search_result/Ascon_XOF_round_{num_rounds + 1}_preimage.py", 'w')

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

output_file = open(f"./search_result/Ascon_precompute_for_XOF_round_{num_rounds + 1}_preimage.py", 'w')

# Output statistical results
output_file.write(f"Red_variables={pre_red_vars_count.getValue() - pre_delta_total_r.getValue()}\n")
output_file.write(f"Blue_variables={pre_blue_vars_count.getValue() - pre_delta_total_b.getValue()}\n")

print("Ascon MILP automation modeling completed")

# 7. Generate state information for LaTeX documentation
row_num = 0
initial_state_latex = write_Ascon_initial(pre_initial_state, slice_number, row_num, dict(), '$A$')
output_file.write(f"pre_initial_state_output = {initial_state_latex}\n")

intermediate_states_output = []
state_index = 1

for round_state in pre_intermediate_states:
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
output_file.write(f"pre_intermediate_states_output={intermediate_states_output}")

output_file.close()
print("Results saved to file")