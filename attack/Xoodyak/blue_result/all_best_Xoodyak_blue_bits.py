from new_code.base.simple_xoodyak import *
from new_code.latex.write_output_xoodyak import *

# 用于存储所有least_number对应的初始状态列表
all_solutions = {}

for least_number in range(11,20):
    add_constr = []
    solutions_list = []
    for search_number in range(5):
        print(f"\n=== 搜索蓝色比特数 >= {least_number} 的情况 ===")

        model = gp.Model("Keccak_MILP_Automation")
        # 当达到30%的gap时停止求解
        model.setParam('MIPGap', 0.25)
        # 专注于提高边界以更快达到gap目标
        # model.setParam('MIPFocus', 2)

        # 初始状态
        initial_state = [[[Bit(model, f"init_z{___}_y{__}_x{_}", (0, 0, 0, '*')) for _ in range(4)] for __ in range(3)] for ___ in range(32)]

        blue_bits = []

        for z in range(32):
            y = 2
            for x in range(4):
                if z >= 30 and x == 3:  # 填充部分 - Padding part
                    # 特定位置使用未定常数 - Use undetermined constant for specific positions
                    initial_state[z][y][x] = Bit(model, f"init_z{z}_x{x}", (0, 0, 0, 0))
                else:
                    # 创建比特，ul=0，cond=0 - Create bit with ul=0, cond=0
                    initial_state[z][y][x] = Bit(model, f"init_z{z}_x{x}", (0, 0, '*', '*'))
                    blue_bits.append(initial_state[z][y][x].b)

        for one_place,zero_place in add_constr:
            one_place_vars = []
            zero_place_vars = []
            for z,x in one_place:
                one_place_vars.append(initial_state[z][2][x].b)
            for z,x in zero_place:
                zero_place_vars.append(initial_state[z][2][x].b)
            model.addConstr(gp.quicksum(one_place_vars)<=len(one_place_vars)-1)
        model.addConstr(gp.quicksum(blue_bits)<=25)

        theta_state_1, C_1, D_1, theta_vars1 = create_first_theta_operation(model, initial_state, 'theta_1')
        for x in range(4):
            for z in range(32):
                # sum_C.append(theta_vars2[f"C_x{x}_z{z}"]['delta_b'])
                model.addConstr(theta_vars1[f"C_x{x}_z{z}"]['delta_b'] == 0)
                model.addConstr(theta_vars1[f"D_x{x}_z{z}"]['delta_b'] == 0)
                for y in range(3):
                    model.addConstr(theta_vars1[f"new_z{z}_y{y}_x{x}"]['delta_b'] == 0)
        rho_west_1 = rho_west(theta_state_1)
        for z in range(32):
            for y in range(3):
                for x in range(4):
                    model.addConstr(rho_west_1[z][y][x].b + rho_west_1[z][(y+1)%3][x].b <= 1)
        # 如果不空过chi，并且蓝色可以相邻呢？
        chi_state_1, chi_vars = create_first_chi_operation(model,rho_west_1)
        for z in range(32):
            for y in range(3):
                for x in range(4):
                    model.addConstr(chi_vars[f"and_z{z}_y{y}_x{x}"]["const_cond"] >= rho_west_1[z][(y + 1)%3][x].b - rho_west_1[z][y][x].b)
                    model.addConstr(chi_vars[f"and_z{z}_y{y}_x{x}"]["const_cond"] >= rho_west_1[z][(y + 2) % 3][x].b - rho_west_1[z][y][x].b)
        rho_east_state_1 = rho_east(chi_state_1)
        # 限制条件

        theta_state_2, C_2, D_2, theta_vars2 = create_theta_operation(model, rho_east_state_1, 'theta_2')
        rho_west_2 = rho_west(theta_state_2)
        # 统计扩散个数
        diffusion_bit = []
        good_place = []
        sum_C = []
        # 限制比特抵消操作
        for x in range(4):
            for z in range(32):
                # sum_C.append(theta_vars2[f"C_x{x}_z{z}"]['delta_b'])
                model.addConstr(theta_vars2[f"C_x{x}_z{z}"]['delta_r'] == 0)
                model.addConstr(theta_vars2[f"C_x{x}_z{z}"]['delta_b'] == 0)
                model.addConstr(theta_vars2[f"D_x{x}_z{z}"]['delta_r'] == 0)
                model.addConstr(theta_vars2[f"D_x{x}_z{z}"]['delta_b'] == 0)
        # model.addConstr(gp.quicksum(sum_C)<=4)

        model.addConstr(sum(blue_bits) >= least_number)
        adjacent_place = []

        for x in range(4):
            for y in range(3):
                for z in range(32):
                    model.addConstr(theta_vars2[f"new_z{z}_y{y}_x{x}"]['delta_r'] == 0)
                    model.addConstr(theta_vars2[f"new_z{z}_y{y}_x{x}"]['delta_b'] == 0)
                    diffusion_bit.append(theta_state_2[z][y][x].b)
                    adjacent_bit = model.addVar(vtype=GRB.BINARY)
                    model.addConstr(adjacent_bit >= rho_west_2[z][y][x].b + rho_west_2[z][(y + 1) % 3][x].b - 1)
                    model.addConstr(2 * adjacent_bit <= rho_west_2[z][y][x].b + rho_west_2[z][(y + 1) % 3][x].b)
                    adjacent_place.append(adjacent_bit)

        # 设置多目标
        # model.setObjective(gp.quicksum(diffusion_bit), GRB.MINIMIZE)
        model.setObjective(gp.quicksum(diffusion_bit) - 0.01 * gp.quicksum(adjacent_place), GRB.MINIMIZE)

        # model.setObjective(gp.quicksum(diffusion_bit) - 0.01 * gp.quicksum(adjacent_place), GRB.MINIMIZE)

        model.optimize()

        if model.status == GRB.INFEASIBLE:
            print("Model is infeasible")

            # 计算IIS
            model.computeIIS()

            print("\n以下约束属于IIS（最小矛盾约束集）:")
            for c in model.getConstrs():
                if c.IISConstr:  # 检查约束是否在IIS中
                    print(f"约束 {c.constrname}: {model.getRow(c)} {c.sense} {c.rhs}")
        else:
            print("Model is feasible")
        #
        # f = open("temp.py", 'w')
        # row_num = 0
        # # 收集所有找到的解
        # temp = write_row(second_initial_state, row_num, '$A$')
        # f.write(f"pre_initial_state_output = {temp}\n")
        # pre_intermediate_states_output = []
        #
        # index = 1
        # round_state_output = dict()
        #
        # row_num += 1
        # temp = write_row_C(C_1, row_num, theta_vars1, f'$C_{index}$')
        # round_state_output['C'] = temp
        # row_num += 0.4
        # temp = write_row_D(D_1, row_num, theta_vars1, f'$D_{index}$')
        # round_state_output['D'] = temp
        # row_num += 0.4
        #
        # temp = write_row_theta(theta_state_1, row_num, theta_vars1, f'$\\theta_{index}$')
        # round_state_output['theta_state'] = temp
        # row_num += 1
        # temp = write_row(rho_west_1, row_num, f'$\\rho_west_state{index}$')
        # round_state_output['rho_west_state'] = temp
        # row_num += 1
        # temp = write_row_chi(chi_state_1, row_num, chi_vars, f'$\\chi_{index}$')
        # round_state_output['chi_state'] = temp
        # row_num += 1
        # temp = write_row(rho_east_state_1, row_num, f'$\\rho_east_state{index}$')
        # round_state_output['rho_east_state'] = temp
        #
        # index += 1
        # pre_intermediate_states_output.append(round_state_output)
        #
        # f.write(f"pre_intermediate_states_output={pre_intermediate_states_output}")

        if model.status == GRB.OPTIMAL:

            # 创建一个64x5x5的矩阵表示初始状态
            state_matrix = [[[0 for x in range(4)] for y in range(3)] for z in range(32)]

            # 填充矩阵
            for z in range(32):
                for x in range(4):
                    for y in range(3):
                        if isinstance(initial_state[z][y][x].b, gp.Var):
                            state_matrix[z][y][x] = int(initial_state[z][y][x].b.X)
                        else:
                            state_matrix[z][y][x] = int(initial_state[z][y][x].b)
            temp_one = []
            temp_zero = []
            for z in range(32):
                for x in range(4):
                    b_value = 0
                    if isinstance(initial_state[z][2][x].b, gp.Var):
                        b_value = int(initial_state[z][2][x].b.X)
                    else:
                        b_value = int(initial_state[z][2][x].b)
                    if b_value>0.5:
                        temp_one.append((z,x))
                    else:
                        temp_zero.append((z, x))

            add_constr.append((temp_one,temp_zero))
            # 将矩阵添加到列表中
            solutions_list.append(state_matrix)

    # 存储当前least_number的所有解
    all_solutions[least_number] = solutions_list

f = open(f"../result/blue/Xoodyak_all_blue_big.py", 'w')
f.write(f"all_solutions = {all_solutions}\n")
