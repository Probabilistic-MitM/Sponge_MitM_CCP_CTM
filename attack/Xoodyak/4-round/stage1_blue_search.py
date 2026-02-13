from base_MILP.Xoodyak_MILP import *
from output.write_in_file_Xoodayk import *

# Dictionary to store all initial state lists for each least_number
all_solutions = {}

for least_number in range(11,20):
    add_constr = []
    solutions_list = []
    for search_number in range(5):
        print(f"\n=== Searching for blue bits >= {least_number} ===")

        model = gp.Model("Keccak_MILP_Automation")
        # Stop when 25% gap is reached
        model.setParam('MIPGap', 0.25)
        # Focus on improving bound to reach gap faster
        # model.setParam('MIPFocus', 2)

        # Initial state
        initial_state = [[[Bit(model, f"init_z{___}_y{__}_x{_}", (0, 0, 0, '*')) for _ in range(4)] for __ in range(3)] for ___ in range(32)]

        blue_bits = []

        for z in range(32):
            y = 2
            for x in range(4):
                if z >= 30 and x == 3:  # Padding part
                    # Specific position uses undetermined constant
                    initial_state[z][y][x] = Bit(model, f"init_z{z}_x{x}", (0, 0, 0, 0))
                else:
                    # Create bit with ul=0, cond=0
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
        # If chi is not bypassed and blues can be adjacent?
        chi_state_1, chi_vars = create_first_chi_operation(model,rho_west_1)
        for z in range(32):
            for y in range(3):
                for x in range(4):
                    model.addConstr(chi_vars[f"and_z{z}_y{y}_x{x}"]["const_cond"] >= rho_west_1[z][(y + 1)%3][x].b - rho_west_1[z][y][x].b)
                    model.addConstr(chi_vars[f"and_z{z}_y{y}_x{x}"]["const_cond"] >= rho_west_1[z][(y + 2) % 3][x].b - rho_west_1[z][y][x].b)
        rho_east_state_1 = rho_east(chi_state_1)
        # Constraints

        theta_state_2, C_2, D_2, theta_vars2 = create_theta_operation(model, rho_east_state_1, 'theta_2')
        rho_west_2 = rho_west(theta_state_2)
        # Count diffusion
        diffusion_bit = []
        good_place = []
        sum_C = []
        # Restrict cancellation
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

        # Set multi-objective
        # model.setObjective(gp.quicksum(diffusion_bit), GRB.MINIMIZE)
        model.setObjective(gp.quicksum(diffusion_bit) - 0.01 * gp.quicksum(adjacent_place), GRB.MINIMIZE)

        # model.setObjective(gp.quicksum(diffusion_bit) - 0.01 * gp.quicksum(adjacent_place), GRB.MINIMIZE)

        model.optimize()

        if model.status == GRB.INFEASIBLE:
            print("Model is infeasible")

            # Compute IIS
            model.computeIIS()

            print("\nThe following constraints are in the IIS (minimal conflict set):")
            for c in model.getConstrs():
                if c.IISConstr:  # Check if constraint is in IIS
                    print(f"Constraint {c.constrname}: {model.getRow(c)} {c.sense} {c.rhs}")
        else:
            print("Model is feasible")

        if model.status == GRB.OPTIMAL:

            # Create a 32x3x4 matrix representing the initial state
            state_matrix = [[[0 for x in range(4)] for y in range(3)] for z in range(32)]

            # Fill the matrix
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
            # Add the matrix to the list
            solutions_list.append(state_matrix)

    # Store all solutions for the current least_number
    all_solutions[least_number] = solutions_list

f = open(f"../blue_result/all_best_Xoodyak_blue_bits.py", 'w')
f.write(f"all_solutions = {all_solutions}\n")