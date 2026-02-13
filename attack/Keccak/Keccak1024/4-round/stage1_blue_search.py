from base_MILP.Keccak_MILP import *
from output.write_in_file_slice_64 import *

# 用于存储所有least_number对应的初始状态列表
all_solutions = {}

for least_number in range(16, 20):
    print(f"\n=== 搜索蓝色比特数 >= {least_number} 的情况 ===")

    model = gp.Model("Keccak_MILP_Automation")
    model.setParam('MIPGap', 0.0)
    model.setParam('MIPFocus', 2)

    # 设置参数以获取多个解
    model.setParam('PoolSearchMode', 2)  # 探索解空间
    model.setParam('PoolSolutions', 30)  # 最多存储100个解
    model.setParam('PoolGap', 0.0)  # 只收集最优解

    # 初始状态

    initial_state = [[[Bit(model,'constant','uc') for x in range(5)] for y in range(5)] for z in range(64)]

    blue_bits = []
    # 赋值
    for z in range(64):
        for x in range(4):
            if x==3 and z>=60:
                continue
            initial_state[z][0][x] = Bit(model, f'initial_state[{z}][0][{x}]', (0, 0, '*', 0))
            initial_state[z][1][x] = Bit(model,f'initial_state[{z}][1][{x}]',(0,0,0,0))
            initial_state[z][1][x].b = initial_state[z][0][x].b
            blue_bits.append(initial_state[z][0][x].b)

    model.addConstr(initial_state[16][0][1].b==1)

    # 初始状态要求蓝色个数大于等于least_number

    model.addConstr(gp.quicksum(blue_bits)>=least_number)

    # 第一轮的theta空过
    theta_state_1, C_1, D_1, theta_vars1 = create_first_theta_operation(model, initial_state, 'theta_1')
    # 第一轮不扩散
    for x in range(5):
        for z in range(64):
            model.addConstr(theta_vars1[f"C_x{x}_z{z}"]['delta_r'] == 0)
            model.addConstr(theta_vars1[f"C_x{x}_z{z}"]['delta_b'] == initial_state[z][0][x].b)
            model.addConstr(theta_vars1[f"D_x{x}_z{z}"]['delta_r'] == 0)
            model.addConstr(theta_vars1[f"D_x{x}_z{z}"]['delta_b'] == 0)

    for x in range(5):
        for y in range(5):
            for z in range(64):
                model.addConstr(theta_vars1[f"new_z{z}_y{y}_x{x}"]['delta_r'] == 0)
                model.addConstr(theta_vars1[f"new_z{z}_y{y}_x{x}"]['delta_b'] == 0)

    # 第一轮的rho、chi

    rho_state_1 = rho(theta_state_1)

    pi_state_1 = pi(rho_state_1)

    # 限制条件
    for z in range(64):
            for y in range(5):
                model.addConstr(pi_state_1[z][y][0].b+pi_state_1[z][y][1].b<=1)

    # 第一轮的chi空过

    theta_state_2, C_2, D_2, theta_vars2 = create_theta_operation(model, pi_state_1, 'theta_2')
    rho_state_2 = rho(theta_state_2)
    pi_state_2 = pi(rho_state_2)
    # 统计扩散个数
    diffusion_bit = []
    good_place = []
    # 限制比特抵消操作
    for x in range(5):
        for z in range(64):
            model.addConstr(theta_vars2[f"C_x{x}_z{z}"]['delta_r'] == 0)
            model.addConstr(theta_vars2[f"C_x{x}_z{z}"]['delta_b'] == 0)
            model.addConstr(theta_vars2[f"D_x{x}_z{z}"]['delta_r'] == 0)
            model.addConstr(theta_vars2[f"D_x{x}_z{z}"]['delta_b'] == 0)

    adjacent_place = []
    for x in range(5):
        for y in range(5):
            for z in range(64):
                model.addConstr(theta_vars2[f"new_z{z}_y{y}_x{x}"]['delta_r'] == 0)
                model.addConstr(theta_vars2[f"new_z{z}_y{y}_x{x}"]['delta_b'] == 0)
                diffusion_bit.append(theta_state_2[z][y][x].b)
                adjacent_bit = model.addVar(vtype=GRB.BINARY)
                model.addConstr(adjacent_bit>=pi_state_2[z][y][x].b+pi_state_2[z][y][(x+1)%5].b-1)
                model.addConstr(2*adjacent_bit <= pi_state_2[z][y][x].b + pi_state_2[z][y][(x + 1) % 5].b)
                adjacent_place.append(adjacent_bit)
                if (x,y) in [(0,1),(1,3)]:
                    good_place.append(pi_state_1[z][y][x].b)


    # 设置多目标
    model.setObjective(gp.quicksum(diffusion_bit)-0.1*gp.quicksum(good_place)-0.001*gp.quicksum(adjacent_place), GRB.MINIMIZE)

    model.optimize()

    # 收集所有找到的解
    solutions_list = []

    if model.status == GRB.OPTIMAL:
        # 获取解的数量
        num_solutions = model.SolCount
        print(f"找到 {num_solutions} 个解")

        # 遍历所有解
        for sol_idx in range(num_solutions):
            model.setParam('SolutionNumber', sol_idx)

            # 创建一个64x5x5的矩阵表示初始状态
            state_matrix = [[[0  for x in range(5)] for y in range(5)] for z in range(64)]

            # 填充矩阵
            for z in range(64):
                for x in range(4):  # x=0-3
                    # y=0, x=0-3
                    if isinstance(initial_state[z][0][x].b, gp.Var):
                        state_matrix[z][0][x] = int(initial_state[z][0][x].b.Xn)
                    else:
                        state_matrix[z][0][x] = int(initial_state[z][0][x].b)

                    # y=1, x=0-3 (与y=0相同)
                    state_matrix[z][1][x] = state_matrix[z][0][x]

            # 计算该解的蓝色比特数

            # 将矩阵添加到列表中
            solutions_list.append(state_matrix)

    # 存储当前least_number的所有解
    all_solutions[least_number] = solutions_list

f = open(f"../blue_result/SHA3_512_all_blue.py", 'w')
f.write(f"all_solutions = {all_solutions}\n")
