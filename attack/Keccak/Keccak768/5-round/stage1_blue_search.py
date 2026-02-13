from base_MILP.Keccak_MILP import *
from output.write_in_file_slice_64 import *

# Store all initial state solutions for each least_number
all_solutions = {}

for least_number in range(2,4):
    add_constr = []
    solutions_list = []
    for search_number in range(3):
        print(f"\n=== Searching for blue bits >= {least_number} ===")

        model = gp.Model("Keccak_MILP_Automation")
        model.setParam('MIPGap', 0.30)
        # model.setParam('MIPFocus', 1)

        # Initial state
        initial_state = [[[Bit(model, 'constant', 'uc') for x in range(5)] for y in range(5)] for z in range(64)]

        blue_bits = []

        for z in range(64):
            for x in range(5):
                initial_state[z][0][x] = Bit(model, f'initial_state[{z}][0][{x}]', (0, 0, '*', 0))
                initial_state[z][1][x].b = initial_state[z][0][x].b
                blue_bits.append(initial_state[z][0][x].b)
                if x<=2:
                    if x == 2 and z >= 60:
                        continue
                    else:
                        initial_state[z][2][x].b = initial_state[z][0][x].b
                        blue_bits.append(initial_state[z][2][x].b)

        for one_place,zero_place in add_constr:
            one_place_vars = []
            zero_place_vars = []
            for z,x in one_place:
                one_place_vars.append(initial_state[z][0][x].b)
            for z,x in zero_place:
                zero_place_vars.append(initial_state[z][0][x].b)
            model.addConstr(gp.quicksum(one_place_vars)<=len(one_place_vars)-1)
        model.addConstr(gp.quicksum(blue_bits)<=10)



        # First round theta (skip propagation)
        theta_state_1, C_1, D_1, theta_vars1 = create_first_theta_operation(model, initial_state, 'theta_1')


        # First round rho and chi

        rho_state_1 = rho(theta_state_1)

        pi_state_1 = pi(rho_state_1)

        # Constraints
        for z in range(64):
            for y in range(5):
                for x in range(5):
                    model.addConstr(pi_state_1[z][y][x].b + pi_state_1[z][y][(x+1)%5].b <= 1)

        # First round chi (skip propagation)
        C_2 = [[None for _ in range(5)] for _ in range(64)]

        for x in range(5):
            for z in range(64):
                # Create C[z][x] bit with ul=0
                C_bit = Bit(model, f"C_x{x}_z{z}", (0, 0, '*', 0))
                # Constraint: cannot have both red and blue flags

                model.addConstr(C_bit.b<=pi_state_1[z][0][x].b+pi_state_1[z][1][x].b+pi_state_1[z][2][x].b+pi_state_1[z][3][x].b+pi_state_1[z][4][x].b)
                model.addConstr(5*C_bit.b >= pi_state_1[z][0][x].b + pi_state_1[z][1][x].b + pi_state_1[z][2][x].b + pi_state_1[z][3][x].b + pi_state_1[z][4][x].b)
                C_2[z][x] = C_bit

        # Count diffusion bits
        diffusion_bit = []
        good_place = []
        # sum_C = []

        # model.addConstr(gp.quicksum(sum_C)<=4)
        # model.addConstr(gp.quicksum(blue_bits)- gp.quicksum(sum_C) >= least_number)
        model.addConstr(gp.quicksum(blue_bits) >= least_number)
        adjacent_place = []
        for x in range(5):
            for z in range(64):
                diffusion_bit.append(C_2[z][x].b)
                    # adjacent_bit = model.addVar(vtype=GRB.BINARY)
                    # model.addConstr(adjacent_bit >= pi_state_2[z][y][x].b + pi_state_2[z][y][(x + 1) % 5].b - 1)
                    # model.addConstr(2 * adjacent_bit <= pi_state_2[z][y][x].b + pi_state_2[z][y][(x + 1) % 5].b)
                    # adjacent_place.append(adjacent_bit)

        # Multi-objective setting
        model.setObjective(gp.quicksum(diffusion_bit), GRB.MINIMIZE)
        model.addConstr(gp.quicksum(blue_bits) >= least_number)
        # model.setObjective(gp.quicksum(diffusion_bit) - 0.01 * gp.quicksum(adjacent_place), GRB.MINIMIZE)

        model.optimize()

        # Collect all found solutions


        if model.status == GRB.OPTIMAL:

            # Create a 64x5x5 matrix representing the initial state
            state_matrix = [[[0 for x in range(5)] for y in range(5)] for z in range(64)]

            # Fill the matrix
            for z in range(64):
                for x in range(5):
                    for y in range(5):
                        if isinstance(initial_state[z][y][x].b, gp.Var):
                            state_matrix[z][y][x] = int(initial_state[z][y][x].b.X)
                        else:
                            state_matrix[z][y][x] = int(initial_state[z][y][x].b)
            temp_one = []
            temp_zero = []
            for z in range(64):
                for x in range(5):
                    b_value = 0
                    if isinstance(initial_state[z][0][x].b, gp.Var):
                        b_value = int(initial_state[z][0][x].b.X)
                    else:
                        b_value = int(initial_state[z][0][x].b)
                    if b_value>0.5:
                        temp_one.append((z,x))
                    else:
                        temp_zero.append((z, x))

            add_constr.append((temp_one,temp_zero))
            # Add the matrix to the solutions list
            solutions_list.append(state_matrix)

    # Store all solutions for the current least_number
    all_solutions[least_number] = solutions_list

f = open(f"../blue_result/blue_scheme.py", 'w')
f.write(f"all_solutions = {all_solutions}\n")