# ========== File 2: Ascon_XOF_3_pre_constant_cond_3_stage_Sbox.py (English comments only) ==========
import gurobipy as gp
from gurobipy import GRB
from base_MILP.Ascon_re_search_MILP import *
from output.re_search_write_in_file_slice_32 import *
from attack.Ascon.AsconXOF.search_result.Ascon_XOF_round_3_preimage import *
from attack.Ascon.AsconXOF.search_result.Ascon_precompute_for_XOF_round_3_preimage import *
import os

# Create Gurobi model
model = gp.Model("Ascon_MILP_Automation")
model.setParam('MIPFocus', 2)
model.setParam('MIPGap', 0.0)  # Set optimality gap to 0

# 1. Initialize Ascon hash state
print("Initializing Ascon state...")

# Create 32x5 initial state matrix
# Each element is a Bit object
initial_state = [[Bit(model, f"init_z{_}_x{__}", (0, 0, 0, 0)) for _ in range(5)] for __ in range(slice_number)]

num_rounds = 2  # Number of rounds - 1
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
        ps_state, ps_vars = create_first_P_S_operation_first_one_constant_cond_padding_three_stage(
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

    # P_L operation
    def set_type(var, type):
        if type == 'lr':
            model.addConstr(var.ul == 0)
            model.addConstr(var.r <= 1)
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

    if round_num <= 0:
        inter_state = intermediate_states_output[round_num]
        for z in range(32):
            for x in range(5):
                set_type(ps_state[z][x], inter_state['ps_state'][0][x][z])
                set_type(pl_state[z][x], inter_state['pl_state'][0][x][z])

    # Save all states and variables of current round
    intermediate_states.append({
        'temp_state_1': temp_state_1,  # Temporary state 1
        'temp_state_2': temp_state_2,  # Temporary state 2
        'ps_state': ps_state,          # State after P_S operation
        'ps_vars': ps_vars,            # Variables for P_S operation
        'pl_state': pl_state,          # State after P_L operation
        'pl_vars': pl_vars,            # Variables for P_L operation
        'round_num': round_num,        # Round number index
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
capacity_cond = 0   # Total capacity conditions
sum_CT = 0       
const_cond_sum = 0
sum_without_bits = 0
sum_linear_cancel = 0
for round_state in intermediate_states:
    ps_vars = round_state['ps_vars']
    linear_cancel_chi = round_state['linear_cancel_chi']
    if round_state['round_num'] == 0:
        # Variable statistics for first round
        for z in range(slice_number):
            initial_p_s = ps_vars
            # sum_const_cond += ps_vars[f'{z}_vars'][0]
            # sum_const_cond += ps_vars[f'{z}_vars'][1]
            # sum_const_cond += ps_vars[f'{z}_vars'][2]
            capacity_cond += ps_vars[f'{z}_vars'][0]
            capacity_cond += ps_vars[f'{z}_vars'][1]
            capacity_cond += ps_vars[f'{z}_vars'][2]
            for x in range(5):
                # sum_const_cond += ps_vars[f'{z}_constant_cond_{x}']
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

# Calculate quality indicator variables for hash output bits
hash_output_bits = []
cut_bit = []
for z in range(slice_number):
    temp = model.addVar(vtype=GRB.BINARY, name='good_slice')
    new_temp = model.addVar(vtype=GRB.BINARY, name='new_good_slice')
    new_temp2 = model.addVar(vtype=GRB.BINARY, name='new_good_slice2')
    model.addConstr(new_temp <= 1 - final_state[z][3].ul + final_state[z][3].r + final_state[z][3].b)
    model.addConstr(new_temp <= 1 - final_state[z][4].ul + final_state[z][4].r + final_state[z][4].b)
    for x in [0,3,4]:
        model.addConstr(new_temp2 <= 1 - final_state[z][x].ul + final_state[z][x].r + final_state[z][x].b)
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
# model.addConstr(blue_vars_count - delta_total_b - gp.quicksum(cut_bit) <= 8)
model.addConstr(temp_degree <= red_vars_count - delta_total_r - gp.quicksum(cut_bit) + 1)
model.addConstr(temp_degree <= blue_vars_count - delta_total_b - gp.quicksum(cut_bit) + 2)
model.addConstr(temp_degree <= gp.quicksum(hash_output_bits))

pre_initial_state = [[Bit(model, f"init_z{_}_x{__}", (0, 0, 0, 0)) for _ in range(5)] for __ in range(slice_number)]

# Initialize state bits
for z in range(slice_number):
    x = 0
    if pre_initial_state_output[0][x][z] == 'lb':
        pre_initial_state[z][x].b = 1
    elif pre_initial_state_output[0][x][z] == 'lr':
        pre_initial_state[z][x].r = 1

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
    without_place, linear_cancel_chi = None, None
    # Execute P_S operation
    # First round uses special initialization function
    if round_num == 0:
        ps_state, ps_vars = create_first_P_S_operation_first_one_constant_cond(
            model, pre_current_state, f"round{round_num}_PS"
        )
        temp_state_1 = None
        temp_state_2 = None
    elif round_num == 1:
        temp_state_1, temp_state_2, ps_state, ps_vars, without_place, linear_cancel_chi = create_second_P_S_operation(
            model, pre_current_state, f"round{round_num}_PS"
        )
    else:
        # Subsequent rounds use standard P_S operation function
        temp_state_1, temp_state_2, ps_state, ps_vars, without_place, linear_cancel_chi = create_P_S_operation(
            model, pre_current_state, f"round{round_num}_PS"
        )

    # P_L operation
    print(f"  Round {round_num + 1}: P_L operation")

    # Choose different P_L operation implementation based on round number
    if round_num == 0:
        pl_state, pl_vars, linear_cancel = create_first_P_L_operation(model, ps_state, f"round{round_num}_PL")
    else:
        pl_state, pl_vars, linear_cancel = create_P_L_operation(model, ps_state, f"round{round_num}_PL")

    # Save all states and variables of current round
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

    if round_num <= 0:
        inter_state = pre_intermediate_states_output[round_num]
        for z in range(32):
            for x in range(5):
                set_type(ps_state[z][x], inter_state['ps_state'][0][x][z])
                set_type(pl_state[z][x], inter_state['pl_state'][0][x][z])

    # Save all states and variables of current round
    pre_intermediate_states.append({
        'temp_state_1': temp_state_1,  # Temporary state 1
        'temp_state_2': temp_state_2,  # Temporary state 2
        'ps_state': ps_state,          # State after P_S operation
        'ps_vars': ps_vars,            # Variables for P_S operation
        'pl_state': pl_state,          # State after P_L operation
        'pl_vars': pl_vars,            # Variables for P_L operation
        'round_num': round_num,        # Round number index
        "linear_cancel": linear_cancel,
        "linear_cancel_chi": linear_cancel_chi,
        "without_place": without_place
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
pre_const_cond_sum = 0
pre_sum_without_bits = 0
pre_sum_linear_cancel = 0
for round_state in pre_intermediate_states:
    ps_vars = round_state['ps_vars']
    linear_cancel_chi = round_state['linear_cancel_chi']
    if round_state['round_num'] == 0:
        # Variable statistics for first round
        for z in range(slice_number):
            # second_sum_const_cond += ps_vars[f'{z}_vars'][0]
            # second_sum_const_cond += ps_vars[f'{z}_vars'][1]
            pre_capacity_cond += ps_vars[f'{z}_vars'][0]
            pre_capacity_cond += ps_vars[f'{z}_vars'][1]
            for x in range(5):
                # pre_sum_const_cond += ps_vars[f'{z}_constant_cond_{x}']
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
                    pre_sum_linear_cancel += linear_cancel_chi[f"temp1_z{z}_x{x}"]

                if f"temp2_z{z}_x{x}" in ps_vars:
                    pre_delta_total_r += ps_vars[f"temp2_z{z}_x{x}"]['delta_r']
                    pre_delta_total_b += ps_vars[f"temp2_z{z}_x{x}"]['delta_b']
                    pre_sum_const_cond += ps_vars[f"temp2_z{z}_x{x}"]['new_cond']
                    pre_sum_linear_cancel += linear_cancel_chi[f"temp2_z{z}_x{x}"]

                if f"new_z{z}_x{x}" in ps_vars:
                    pre_delta_total_r += ps_vars[f"new_z{z}_x{x}"]['delta_r']
                    pre_delta_total_b += ps_vars[f"new_z{z}_x{x}"]['delta_b']
                    pre_sum_const_cond += ps_vars[f"new_z{z}_x{x}"]['new_cond']
                    pre_sum_linear_cancel += linear_cancel_chi[f"new_z{z}_x{x}"]

                # Count AND operation variables
                if f"and_z{z}_x{x}" in ps_vars:
                    pre_sum_CT += ps_vars[f"and_z{z}_x{x}"]['CT']
                    pre_const_cond_sum += ps_vars[f"and_z{z}_x{x}"]['const_cond']

    # Count variables in P_L operation
    pl_vars = round_state['pl_vars']
    linear_cancel = round_state['linear_cancel']
    without_place = round_state['without_place']
    for z in range(slice_number):
        for x in range(5):
            if f"new_z{z}_x{x}" in pl_vars:
                pre_delta_total_r += pl_vars[f"new_z{z}_x{x}"]['delta_r']
                pre_delta_total_b += pl_vars[f"new_z{z}_x{x}"]['delta_b']
                pre_sum_const_cond += pl_vars[f"new_z{z}_x{x}"]['new_cond']
                pre_sum_linear_cancel += linear_cancel[f"new_z{z}_x{x}"]
            if round_state['round_num'] > 0:
                pre_sum_without_bits += without_place[z][x]

# Add upper bound for total CTratic constraints
model.addConstr(pre_sum_CT <= 3)

# Calculate equation count for hash output bits
pre_hash_output_bits = []

pre_cut_bits = []
# Conditions to be added

for z in range(slice_number):
    no_ul0 = model.addVar(vtype=GRB.BINARY, name=f"no_ul0")
    no_ul1 = model.addVar(vtype=GRB.BINARY, name=f"no_ul1")
    no_ul2 = model.addVar(vtype=GRB.BINARY, name=f"no_ul2")
    no_ul3 = model.addVar(vtype=GRB.BINARY, name=f"no_ul3")
    no_ul4 = model.addVar(vtype=GRB.BINARY, name=f"no_ul4")
    no_ul = [no_ul0, no_ul1, no_ul2, no_ul3, no_ul4]
    for i in range(5):
        model.addConstr(no_ul[i] <= 1 - pre_final_state[z][i].ul + pre_final_state[z][i].r + pre_final_state[z][i].b)

    condition = [0,0,0,0,0]
    for i in range(5):
        condition[i] = model.addVar(vtype=GRB.BINARY, name=f"condition_{i}")
    less_cost = model.addVar(vtype=GRB.BINARY, name=f"less_cost")

    need_condition = [0,0,0,0,0]
    for i in range(5):
        need_condition[i] = model.addVar(vtype=GRB.BINARY, name=f"need_condition_{i}")

    model.addConstr(need_condition[0] >= initial_p_s[f'{z}_vars'][0] - initial_p_s[f'{z}_vars'][2])
    model.addConstr(need_condition[0] <= initial_p_s[f'{z}_vars'][0])
    model.addConstr(need_condition[0] <= 1 - initial_p_s[f'{z}_vars'][2])

    model.addConstr(need_condition[1] >= initial_p_s[f'{z}_vars'][1] - initial_p_s[f'{z}_vars'][2])
    model.addConstr(need_condition[1] <= initial_p_s[f'{z}_vars'][1])
    model.addConstr(need_condition[1] <= 1 - initial_p_s[f'{z}_vars'][2])

    model.addConstr(need_condition[2] >= initial_p_s[f'{z}_vars'][0] + initial_p_s[f'{z}_vars'][2] - 1)
    model.addConstr(need_condition[2] <= initial_p_s[f'{z}_vars'][0])
    model.addConstr(need_condition[2] <= initial_p_s[f'{z}_vars'][2])

    model.addConstr(need_condition[3] >= initial_p_s[f'{z}_vars'][1] + initial_p_s[f'{z}_vars'][2] - 1)
    model.addConstr(need_condition[3] <= initial_p_s[f'{z}_vars'][1])
    model.addConstr(need_condition[3] <= initial_p_s[f'{z}_vars'][2])

    model.addConstr(need_condition[4] >= - initial_p_s[f'{z}_vars'][0] - initial_p_s[f'{z}_vars'][1] + initial_p_s[f'{z}_vars'][2])
    model.addConstr(need_condition[4] <= 1 - initial_p_s[f'{z}_vars'][0])
    model.addConstr(need_condition[4] <= 1 - initial_p_s[f'{z}_vars'][1])
    model.addConstr(need_condition[4] <= initial_p_s[f'{z}_vars'][2])

    degree_result = [0, 0, 0, 0, 0]
    less_result = model.addVar(vtype=GRB.BINARY, name=f"less_result")
    for i in range(5):
        degree_result[i] = model.addVar(vtype=GRB.BINARY, name=f"need_condition_{i}")

    for i in range(5):
        model.addConstr(degree_result[i] <= need_condition[i])
        model.addConstr(degree_result[i] <= condition[i])
    model.addConstr(less_result <= degree_result[0] + degree_result[1])
    model.addConstr(less_result <= less_cost)

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

    pre_hash_output_bits.append(degree_result[0])
    pre_hash_output_bits.append(degree_result[1])
    pre_hash_output_bits.append(2 * degree_result[2])
    pre_hash_output_bits.append(2 * degree_result[3])
    pre_hash_output_bits.append(degree_result[4])

    pre_cut_bits.append(2 * degree_result[0])
    pre_cut_bits.append(2 * degree_result[1])
    pre_cut_bits.append(degree_result[2])
    pre_cut_bits.append(degree_result[3])
    pre_cut_bits.append(2 * degree_result[4])

    pre_cut_bits.append(-1 * less_result)

print("Equation calculation completed")

# 4. Set optimization constraints and objective function
print("Setting constraints and objective function...")

# Add attack complexity variable
free_capacity = model.addVar(vtype=GRB.CONTINUOUS, name='free_capacity')
degree_from_first_c = model.addVar(vtype=GRB.CONTINUOUS, name='degree_from_first_c')
# Attack complexity constraints
model.addConstr(free_capacity <= pre_red_vars_count - pre_delta_total_r - gp.quicksum(pre_cut_bits))
model.addConstr(free_capacity <= pre_blue_vars_count - pre_delta_total_b - gp.quicksum(pre_cut_bits))
model.addConstr(free_capacity <= gp.quicksum(pre_hash_output_bits))

# Capacity and conditional constraints
degree_from_c = model.addVar(vtype=GRB.INTEGER, name='degree_from_first_c')

# Capacity and conditional constraints
model.addConstr(pre_capacity_cond + degree_from_first_c <= 128 * slice_number / 64 - temp_degree)
model.addConstr(degree_from_c <= 64 * slice_number / 64 - pre_sum_const_cond + degree_from_first_c)

model.addConstr(capacity_cond - free_capacity + degree_from_c <= 128 * slice_number / 64 - temp_degree)
model.addConstr((128) * slice_number / 64 <= 64 * slice_number / 64 - sum_const_cond + degree_from_c)

# Set objective
model.setObjectiveN(-1 * temp_degree + 0.01 * sum_const_cond + 0.01 * pre_sum_const_cond, index=0, priority=2, name="PrimaryObjective")
model.setObjectiveN(-1 * sum_without_bits - 1 * pre_sum_without_bits, index=1, priority=1, name="SecondaryObjective")
model.setObjectiveN(-1 * sum_linear_cancel - 1 * pre_sum_linear_cancel, index=2, priority=0, name="ThirdObjective")

model.optimize()

output_file = open(f"./final_result/Ascon_XOF_round_{num_rounds + 1}_preimage_for_painting.py", 'w')

# Output statistical results
output_file.write(f"Red_variables={red_vars_count.getValue() - delta_total_r.getValue()}\n")
output_file.write(f"Blue_variables={blue_vars_count.getValue() - delta_total_b.getValue()}\n")
output_file.write(f"capacity_cond={capacity_cond.getValue()}\n")
output_file.write(f"degree_from_first_c={degree_from_c.x}\n")

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
        temp1_latex = write_Ascon_temp_s1(temp_state_1, slice_number, linear_cancel_chi, row_num, ps_vars, f'$1/3{{p_S}}^{{({state_index})}}$')
        round_state_output['temp_state_1'] = temp1_latex

        # Process temporary state 2
        row_num += 0.4
        temp_state_2 = round_state['temp_state_2']
        temp2_latex = write_Ascon_temp_s2(temp_state_2, slice_number, linear_cancel_chi, row_num, ps_vars, f'$2/3{{p_S}}^{{({state_index})}}$')
        round_state_output['temp_state_2'] = temp2_latex

        # Process P_S operation state
        row_num += 0.4
        ps_state = round_state['ps_state']
        ps_latex = write_Ascon_P(ps_state, slice_number, linear_cancel_chi, row_num, ps_vars, f'$3/3{{p_S}}^{{({state_index})}}$')
        round_state_output['ps_state'] = ps_latex
    else:
        # Special handling for first round
        row_num += 0.4
        ps_state = round_state['ps_state']
        ps_latex = write_Ascon_initial(ps_state, slice_number, row_num, ps_vars, f'${{p_S}}^{{({state_index})}}$')
        round_state_output['ps_state'] = ps_latex

    # Process P_L operation state
    row_num += 0.4
    pl_state = round_state['pl_state']
    pl_latex = write_Ascon_P(pl_state, slice_number, linear_cancel, row_num, pl_vars, f'${{p_L}}^{{({state_index})}}$')
    round_state_output['pl_state'] = pl_latex
    without_place = round_state['without_place']
    temp = [[0 for x in range(5)] for z in range(32)]
    if without_place != None:
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
output_file = open(f"./final_result/Ascon_pre_for_XOF_round_{num_rounds + 1}_preimage_for_painting.py", 'w')

# Output statistical results
output_file.write(f"Red_variables={pre_red_vars_count.getValue() - pre_delta_total_r.getValue()}\n")
output_file.write(f"Blue_variables={pre_blue_vars_count.getValue() - pre_delta_total_b.getValue()}\n")
output_file.write(f"free_capacity={free_capacity.x}\n")
output_file.write(f"capacity_cond={pre_capacity_cond.getValue()}\n")
output_file.write(f"degree_from_first_c={degree_from_first_c.x}\n")

print("Ascon MILP automation modeling completed")

# 7. Generate state information for LaTeX documentation
row_num = 0
initial_state_latex = write_Ascon_initial(pre_initial_state, slice_number, row_num, dict(), '$A^{(0)}$')
output_file.write(f"pre_initial_state_output = {initial_state_latex}\n")

intermediate_states_output = []
state_index = 0

for round_state in pre_intermediate_states:
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
        temp1_latex = write_Ascon_temp_s1(temp_state_1, slice_number, linear_cancel_chi, row_num, ps_vars, f'$1/3{{p_S}}^{{({state_index})}}$')
        round_state_output['temp_state_1'] = temp1_latex

        # Process temporary state 2
        row_num += 0.4
        temp_state_2 = round_state['temp_state_2']
        temp2_latex = write_Ascon_temp_s2(temp_state_2, slice_number, linear_cancel_chi, row_num, ps_vars, f'$2/3{{p_S}}^{{({state_index})}}$')
        round_state_output['temp_state_2'] = temp2_latex

        # Process P_S operation state
        row_num += 0.4
        ps_state = round_state['ps_state']
        ps_latex = write_Ascon_P(ps_state, slice_number, linear_cancel_chi, row_num, ps_vars, f'$3/3{{p_S}}^{{({state_index})}}$')
        round_state_output['ps_state'] = ps_latex
    else:
        # Special handling for first round
        row_num += 0.4
        ps_state = round_state['ps_state']
        ps_latex = write_Ascon_initial(ps_state, slice_number, row_num, ps_vars, f'${{p_S}}^{{({state_index})}}$')
        round_state_output['ps_state'] = ps_latex

    # Process P_L operation state
    row_num += 0.4
    pl_state = round_state['pl_state']
    pl_latex = write_Ascon_P(pl_state, slice_number, linear_cancel, row_num, pl_vars, f'${{p_L}}^{{({state_index})}}$')
    round_state_output['pl_state'] = pl_latex
    without_place = round_state['without_place']
    temp = [[0 for x in range(5)] for z in range(32)]
    if without_place != None:
        for z in range(32):
            for x in range(5):
                if type(without_place[z][x]) != int and without_place[z][x].x > 0.5:
                    temp[z][x] = 1
    round_state_output['without_place'] = temp

    intermediate_states_output.append(round_state_output)
    state_index += 1

# Write intermediate states output
output_file.write(f"pre_intermediate_states_output={intermediate_states_output}")

output_file.close()