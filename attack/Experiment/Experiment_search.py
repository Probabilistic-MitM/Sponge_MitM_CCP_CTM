import gurobipy as gp
from gurobipy import GRB
from base_MILP.Ascon_re_search_MILP import *
from output.re_search_write_in_file_slice_32 import *


# Create Gurobi model
model = gp.Model("Ascon_MILP_Automation")
# model.setParam('MIPGap', 0.53)  # Set optimality gap to 0

# 1. Initialize Ascon-XOF preimage attack state
print("正在初始化Ascon状态... - Initializing Ascon state...")

# Create 64x5 initial state matrix (but only 32 slices used? Actually slice_number is defined elsewhere)
# Each element is a Bit object
initial_state = [[Bit(model, f"init_z{_}_x{__}", (0, 0, 0, 0)) for _ in range(5)] for __ in range(slice_number)]

num_rounds = 2  # Number of rounds-1

# Initialize state bits
for z in range(slice_number):
    x = 0  #Rate part corresponds to x=0
    if z >= slice_number - 1:  # 填充部分 - Padding part
        # Use undetermined constant for specific positions
        initial_state[z][x] = Bit(model, f"init_z{z}_x{x}", (0, 0, 0, 0))
        continue
    else:
        # Create bit variables for rate part
        # ul=0, cond=0
        initial_state[z][x] = Bit(model, f"init_z{z}_x{x}", (0, '*', '*', 0))

        # Add mutually exclusive constraint for r and b
        # A bit cannot be both red and blue variable
        model.addConstr(initial_state[z][x].r + initial_state[z][x].b <= 1,
                        f"rate_r_b_exclusive_z{z}_x{x}")

print("状态初始化完成 - State initialization completed")

# 2. Apply Ascon round functions
print("正在应用轮函数... - Applying round functions...")

# Save intermediate states for analysis and output
intermediate_states = []
current_state = initial_state

# Apply multiple rounds
for round_num in range(num_rounds):
    print(f"应用第{round_num + 1}轮 - Applying round {round_num + 1}")

    # P_S operation
    print(f"  第{round_num + 1}轮: P_S操作 - Round {round_num + 1}: P_S operation")

    # Execute P_S operation
    without_place, linear_cancel_chi = None, None
    if round_num == 0:
        ps_state, ps_vars = create_first_P_S_operation_first_one(
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
    print(f"  第{round_num + 1}轮: P_L操作 - Round {round_num + 1}: P_L operation")

    # Choose different P_L operation implementation based on round number
    if round_num == 0:
        pl_state, pl_vars, linear_cancel = create_first_P_L_operation(model, ps_state, f"round{round_num}_PL")
    else:
        pl_state, pl_vars, linear_cancel = create_P_L_operation(model, ps_state, f"round{round_num}_PL")

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

    if round_num <= 1:
        inter_state = intermediate_states_output[round_num]
        for z in range(32):
            for x in range(5):
                set_type(ps_state[z][x], inter_state['ps_state'][0][x][z])
                set_type(pl_state[z][x], inter_state['pl_state'][0][x][z])
    if round_num == 2:
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
print(f"完成{num_rounds}轮函数应用 - Completed {num_rounds} rounds application")

# 3. Calculate equation count and variable statistics
print("正在计算方程个数... - Calculating equation count...")

# Count red and blue variables in initial state
red_vars_count = gp.quicksum(initial_state[z][0].r for z in range(slice_number))
blue_vars_count = gp.quicksum(initial_state[z][0].b for z in range(slice_number))

# Add blue variable count constraint (upper bound 11)
# model.addConstr(11 >= second_blue_vars_count)

# Count intervention variables in round functions
delta_total_r = 0  # Total reduction in red variables
delta_total_b = 0  # Total reduction in blue variables
sum_constraints = 0  # Total conditional constraints
capacity_cond = 0  # Total capacity conditions
sum_quad = 0  # Total quadratic constraints
sum_cond_const = 0
const_cond_sum = 0
sum_linear_cancel = 0
for round_state in intermediate_states:
    ps_vars = round_state['ps_vars']
    linear_cancel_chi = round_state['linear_cancel_chi']

    if round_state['round_num'] == 0:
        # Variable statistics for first round
        for z in range(slice_number):
            sum_constraints += ps_vars[f'{z}_vars'][0]
            sum_constraints += ps_vars[f'{z}_vars'][1]
            capacity_cond += ps_vars[f'{z}_vars'][0]
            capacity_cond += ps_vars[f'{z}_vars'][1]
    else:
        # Variable statistics for subsequent rounds
        for z in range(slice_number):
            for x in range(5):
                # Count XOR operation variables
                if f"temp1_z{z}_x{x}" in ps_vars:
                    delta_total_r += ps_vars[f"temp1_z{z}_x{x}"]['delta_r']
                    delta_total_b += ps_vars[f"temp1_z{z}_x{x}"]['delta_b']
                    sum_constraints += ps_vars[f"temp1_z{z}_x{x}"]['new_cond']
                    sum_linear_cancel += linear_cancel_chi[f"temp1_z{z}_x{x}"]

                if f"temp2_z{z}_x{x}" in ps_vars:
                    delta_total_r += ps_vars[f"temp2_z{z}_x{x}"]['delta_r']
                    delta_total_b += ps_vars[f"temp2_z{z}_x{x}"]['delta_b']
                    sum_constraints += ps_vars[f"temp2_z{z}_x{x}"]['new_cond']
                    sum_linear_cancel += linear_cancel_chi[f"temp2_z{z}_x{x}"]

                if f"new_z{z}_x{x}" in ps_vars:
                    delta_total_r += ps_vars[f"new_z{z}_x{x}"]['delta_r']
                    delta_total_b += ps_vars[f"new_z{z}_x{x}"]['delta_b']
                    sum_constraints += ps_vars[f"new_z{z}_x{x}"]['new_cond']
                    sum_linear_cancel += linear_cancel_chi[f"new_z{z}_x{x}"]

                # Count AND operation variables
                if f"and_z{z}_x{x}" in ps_vars:
                    sum_quad += ps_vars[f"and_z{z}_x{x}"]['quad']
                    const_cond_sum += ps_vars[f"and_z{z}_x{x}"]['const_cond']

    # Count variables in P_L operation
    pl_vars = round_state['pl_vars']
    linear_cancel = round_state['linear_cancel']
    for z in range(slice_number):
        for x in range(5):
            if f"new_z{z}_x{x}" in pl_vars:
                delta_total_r += pl_vars[f"new_z{z}_x{x}"]['delta_r']
                delta_total_b += pl_vars[f"new_z{z}_x{x}"]['delta_b']
                sum_constraints += pl_vars[f"new_z{z}_x{x}"]['new_cond']
                sum_cond_const += pl_vars[f"new_z{z}_x{x}"]['new_cond']
                sum_linear_cancel += linear_cancel[f"new_z{z}_x{x}"]

# Add upper bound for total quadratic constraints
model.addConstr(sum_quad >= 1)
model.addConstr(sum_quad <= 4)
model.addConstr(const_cond_sum >= 1)

# Calculate quality indicator variables for hash output bits
hash_output_bits = []
cut_bit = []
new_temp_list = []
for z in range(slice_number):
    temp = model.addVar(vtype=GRB.BINARY, name='good_slice')
    new_temp = model.addVar(vtype=GRB.BINARY, name='new_good_slice')
    model.addConstr(new_temp <= 1 - final_state[z][3].ul + final_state[z][3].r + final_state[z][3].b)
    model.addConstr(new_temp <= 1 - final_state[z][4].ul + final_state[z][4].r + final_state[z][4].b)
    for x in range(5):
        model.addConstr(temp <= 1 - final_state[z][x].ul + final_state[z][x].r + final_state[z][x].b)
    model.addConstr(temp <= 2 - final_state[z][1].r - final_state[z][4].b)
    model.addConstr(temp <= 2 - final_state[z][1].b - final_state[z][4].r)
    model.addConstr(temp <= 2 - final_state[z][1].r - final_state[z][2].b)
    model.addConstr(temp <= 2 - final_state[z][1].b - final_state[z][2].r)
    model.addConstr(temp <= 2 - final_state[z][1].r - final_state[z][0].b)
    model.addConstr(temp <= 2 - final_state[z][1].b - final_state[z][0].r)
    hash_output_bits.append(temp)
    model.addConstr(new_temp + temp <= 1)
    hash_output_bits.append(0.58 * new_temp)
    new_temp_list.append(new_temp)
    cut_bit.append(0.42 * new_temp)

model.addConstr(gp.quicksum(new_temp_list) >= 1)

print("方程计算完成 - Equation calculation completed")

# 4. Set optimization constraints and objective function
print("正在设置约束和目标函数... - Setting constraints and objective function...")

# Add attack complexity variable
temp_degree = model.addVar(vtype=GRB.CONTINUOUS, name='complexity')

# Attack complexity constraints
# Complexity limited by red variables, blue variables and total equations
model.addConstr(temp_degree <= red_vars_count - delta_total_r - gp.quicksum(cut_bit))
model.addConstr(temp_degree <= blue_vars_count - delta_total_b - gp.quicksum(cut_bit))
model.addConstr(temp_degree <= gp.quicksum(hash_output_bits))

# Capacity and conditional constraints
degree_from_c = model.addVar(vtype=GRB.INTEGER, name='degree_from_first_c')
model.addConstr(capacity_cond + degree_from_c <= 128)
model.addConstr(32 <= 31 - sum_constraints + degree_from_c)

# Set objective
model.setObjective(temp_degree + 0.1 * sum_linear_cancel, GRB.MAXIMIZE)

print("约束和目标函数设置完成 - Constraints and objective function set")

# 5. Solve MILP model
print("开始求解模型... - Starting model solution...")
model.optimize()

# 6. Output results to file
output_file = open(f"Ascon_XOF_round_{num_rounds + 1}_preimage.py", 'w')

# Output statistical results
output_file.write(f"Red_variables={red_vars_count.getValue() - delta_total_r.getValue()}\n")
output_file.write(f"Blue_variables={blue_vars_count.getValue() - delta_total_b.getValue()}\n")
output_file.write(f"temp_degree={temp_degree.x}\n")

print("Ascon MILP自动化建模完成 - Ascon MILP automation modeling completed")

# 7. Generate state information for LaTeX documentation
row_num = 0
initial_state_latex = write_Ascon_initial(initial_state, slice_number, row_num, dict(), '$A$')
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
        ps_latex = write_Ascon_P(ps_state, slice_number, linear_cancel_chi, row_num, ps_vars, f'${{p_S}}^{{({state_index})}}$')
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

    intermediate_states_output.append(round_state_output)
    state_index += 1

# Write intermediate states output
output_file.write(f"intermediate_states_output={intermediate_states_output}")

output_file.close()
print("结果已保存到文件 - Results saved to file")