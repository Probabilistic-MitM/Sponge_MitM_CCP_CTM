from base_MILP.operation_MILP import *
from gurobipy import GRB

slice_numebr = 64
def create_theta_operation(model, state, operation_name="theta"):
    """
    MILP modeling for Keccak theta function

    Parameters:
    - model: Gurobi model object
    - state: slice_numebrx5x5 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after theta operation
    - C: Intermediate variable C [z][x]
    - D: Intermediate variable D [z][x]
    - theta_vars: Variables related to theta operation
    """

    new_state = [[[None for _ in range(5)] for _ in range(5)] for _ in range(slice_numebr)]
    theta_vars = {}
    linear_cancel = {}

    # Step 1: Calculate C[z][x] = A[z][0][x] ⊕ A[z][1][x] ⊕ A[z][2][x] ⊕ A[z][3][x] ⊕ A[z][4][x]
    C = [[None for _ in range(5)] for _ in range(slice_numebr)]

    for x in range(5):
        for z in range(slice_numebr):
            C_bit = Bit(model, f"{operation_name}_C_x{x}_z{z}", ('*', '*', '*', 0))

            input_bits = [state[z][y][x] for y in range(5)]

            xor_vars = xor_with_ul_input_no_delta_b(model, input_bits, C_bit, f"{operation_name}_C_x{x}_z{z}")

            theta_vars[f"C_x{x}_z{z}"] = xor_vars
            if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_C_x{x}_z{z}")
            model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
            model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

            linear_cancel[f"C_x{x}_z{z}"] = if_linear_cancel_r
            C[z][x] = C_bit

    # Step 2: Calculate D[z][x] = C[z][(x-1)%5] ⊕ C[(z-1)%slice_numebr][(x+1)%5]
    D = [[None for _ in range(5)] for _ in range(slice_numebr)]

    for x in range(5):
        for z in range(slice_numebr):
            D_bit = Bit(model, f"{operation_name}_D_x{x}_z{z}", ('*', '*', '*', 0))

            input_bit1 = C[z][(x - 1) % 5]
            input_bit2 = C[(z - 1) % slice_numebr][(x + 1) % 5]

            xor_vars = xor_with_ul_input_no_delta_b(model, [input_bit1, input_bit2], D_bit, f"{operation_name}_D_x{x}_z{z}")

            if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_C_x{x}_z{z}")
            model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
            model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

            linear_cancel[f"D_x{x}_z{z}"] = if_linear_cancel_r
            theta_vars[f"D_x{x}_z{z}"] = xor_vars
            D[z][x] = D_bit

    # Step 3: Calculate new state A'[z][y][x] = A[z][y][x] ⊕ D[z][x]
    for z in range(slice_numebr):
        for y in range(5):
            for x in range(5):
                new_bit = Bit(model, f"{operation_name}_new_z{z}_y{y}_x{x}", ('*', '*', '*', 0))

                input_bit1 = state[z][y][x]
                input_bit2 = D[z][x]

                xor_vars = xor_with_ul_input_no_delta_b(model, [input_bit1, input_bit2], new_bit, f"{operation_name}_new_z{z}_y{y}_x{x}")

                new_state[z][y][x] = new_bit
                theta_vars[f"new_z{z}_y{y}_x{x}"] = xor_vars

                if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_C_x{x}_z{z}")
                model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
                model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

                linear_cancel[f"new_z{z}_y{y}_x{x}"] = if_linear_cancel_r

    return new_state, C, D, theta_vars, linear_cancel


def create_second_theta_operation(model, state, operation_name="theta"):
    """
    MILP modeling for Keccak second theta function

    Parameters:
    - model: Gurobi model object
    - state: slice_numebrx5x5 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after theta operation
    - C: Intermediate variable C [z][x]
    - D: Intermediate variable D [z][x]
    - theta_vars: Variables related to theta operation
    """

    new_state = [[[None for _ in range(5)] for _ in range(5)] for _ in range(slice_numebr)]
    theta_vars = {}
    linear_cancel = {}

    # Step 1: Calculate C[z][x] = A[z][0][x] ⊕ A[z][1][x] ⊕ A[z][2][x] ⊕ A[z][3][x] ⊕ A[z][4][x]
    C = [[None for _ in range(5)] for _ in range(slice_numebr)]

    for x in range(5):
        for z in range(slice_numebr):
            C_bit = Bit(model, f"{operation_name}_C_x{x}_z{z}")

            input_bits = [state[z][y][x] for y in range(5)]

            xor_vars = xor_with_ul_input(model, input_bits, C_bit, f"{operation_name}_C_x{x}_z{z}")

            if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_C_x{x}_z{z}")
            model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
            model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

            linear_cancel[f"C_x{x}_z{z}"] = if_linear_cancel_r
            theta_vars[f"C_x{x}_z{z}"] = xor_vars
            C[z][x] = C_bit

    # Step 2: Calculate D[z][x] = C[z][(x-1)%5] ⊕ C[(z-1)%slice_numebr][(x+1)%5]
    D = [[None for _ in range(5)] for _ in range(slice_numebr)]

    for x in range(5):
        for z in range(slice_numebr):
            D_bit = Bit(model, f"{operation_name}_D_x{x}_z{z}")

            input_bit1 = C[z][(x - 1) % 5]
            input_bit2 = C[(z - 1) % slice_numebr][(x + 1) % 5]

            xor_vars = xor_with_ul_input(model, [input_bit1, input_bit2], D_bit, f"{operation_name}_D_x{x}_z{z}")

            if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_C_x{x}_z{z}")
            model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
            model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

            linear_cancel[f"D_x{x}_z{z}"] = if_linear_cancel_r
            theta_vars[f"D_x{x}_z{z}"] = xor_vars
            D[z][x] = D_bit

    # Step 3: Calculate new state A'[z][y][x] = A[z][y][x] ⊕ D[z][x]
    for z in range(slice_numebr):
        for y in range(5):
            for x in range(5):
                new_bit = Bit(model, f"{operation_name}_new_z{z}_y{y}_x{x}")

                input_bit1 = state[z][y][x]
                input_bit2 = D[z][x]

                xor_vars = xor_with_ul_input(model, [input_bit1, input_bit2], new_bit, f"{operation_name}_new_z{z}_y{y}_x{x}")

                if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_C_x{x}_z{z}")
                model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
                model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

                linear_cancel[f"new_z{z}_y{y}_x{x}"] = if_linear_cancel_r
                new_state[z][y][x] = new_bit
                theta_vars[f"new_z{z}_y{y}_x{x}"] = xor_vars

    for x in range(5):
        for z in range(slice_numebr):
            from_ul_to_c = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_C_x{x}_z{z}_from_ul_to_c")
            model.addConstr(theta_vars[f"C_x{x}_z{z}"]['has_ul'] == C[z][x].ul + from_ul_to_c)
            model.addConstr(1 - from_ul_to_c >= D[z][(x + 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= D[(z + 1) % slice_numebr][(x - 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[z][0][(x + 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[z][1][(x + 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[z][2][(x + 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[z][3][(x + 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[z][4][(x + 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[(z + 1) % slice_numebr][0][(x - 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[(z + 1) % slice_numebr][1][(x - 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[(z + 1) % slice_numebr][2][(x - 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[(z + 1) % slice_numebr][3][(x - 1) % 5].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[(z + 1) % slice_numebr][4][(x - 1) % 5].cond)

    for x in range(5):
        for z in range(slice_numebr):
            from_ul_to_c = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_D_x{x}_z{z}_from_ul_to_c")
            model.addConstr(theta_vars[f"D_x{x}_z{z}"]['has_ul'] == D[z][x].ul + from_ul_to_c)
            model.addConstr(1 - from_ul_to_c >= new_state[z][0][x].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[z][1][x].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[z][2][x].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[z][3][x].cond)
            model.addConstr(1 - from_ul_to_c >= new_state[z][4][x].cond)

    _add_theta_condition_constraints(model, theta_vars, state, C, D, new_state, operation_name)

    return new_state, C, D, theta_vars, linear_cancel


def create_first_theta_operation(model, state, operation_name="theta"):
    """
    MILP modeling for Keccak theta function in the first round, no ul=1 variables and no red/blue propagation in C

    Parameters:
    - model: Gurobi model object
    - state: slice_numebrx5x5 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after theta operation
    - C: Intermediate variable C [z][x]
    - D: Intermediate variable D [z][x]
    - theta_vars: Variables related to theta operation
    """

    theta_vars = {}
    linear_cancel = {}

    C = [[Bit(model, f"{operation_name}_C_x{x}_z{z}", 'uc') for x in range(5)] for z in range(slice_numebr)]
    D = [[Bit(model, f"{operation_name}_D_x{x}_z{z}", 'uc') for x in range(5)] for z in range(slice_numebr)]
    for z in range(slice_numebr):
        for x in range(5):
            theta_vars[f"C_x{x}_z{z}"] = {'delta_r': state[z][0][x].r, 'delta_b': state[z][0][x].b, 'delta_r_ul': 0, 'new_cond': 0}
            theta_vars[f"D_x{x}_z{z}"] = {'delta_r': 0, 'delta_b': 0, 'delta_r_ul': 0, 'new_cond': 0}
            linear_cancel[f"C_x{x}_z{z}"] = 1
            linear_cancel[f"D_x{x}_z{z}"] = 1
            for y in range(5):
                theta_vars[f"new_z{z}_y{y}_x{x}"] = {'delta_r': 0, 'delta_b': 0, 'delta_r_ul': 0, 'new_cond': 0}
                linear_cancel[f"new_z{z}_y{y}_x{x}"] = 1

    return state, C, D, theta_vars, linear_cancel


def _add_theta_condition_constraints(model, theta_vars, old_state, C, D, new_state, operation_name):
    """
    Add condition constant propagation constraints in theta function

    Parameters:
    - model: Gurobi model object
    - theta_vars: Variables related to theta operation
    - old_state: Old state [z][y][x]
    - C: Intermediate variable C [z][x]
    - D: Intermediate variable D [z][x]
    - new_state: New state [z][y][x]
    - operation_name: Operation name
    """
    x_old_state2C = [[[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_old_state({z},{y},{x})2C({z},{x})")
                       for x in range(5)] for y in range(5)] for z in range(slice_numebr)]

    x_old_state2new_state = [[[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_old_state({z},{y},{x})2new_state({z},{y},{x})")
                               for x in range(5)] for y in range(5)] for z in range(slice_numebr)]

    x_C2D_1 = [[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_C({z},{x})2D({z},{(x + 1) % 5})")
                for x in range(5)] for z in range(slice_numebr)]
    x_C2D_2 = [[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_C({z},{x})2D({(z + 1) % slice_numebr},{(x - 1) % 5})")
                for x in range(5)] for z in range(slice_numebr)]

    x_D2new_state = [[[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_D({z},{x})2new_state({z},{y},{x})")
                       for x in range(5)] for y in range(5)] for z in range(slice_numebr)]

    for z in range(slice_numebr):
        for y in range(5):
            for x in range(5):
                model.addConstr(old_state[z][y][x].cond == x_old_state2C[z][y][x] + x_old_state2new_state[z][y][x])

    for z in range(slice_numebr):
        for x in range(5):
            model.addConstr(C[z][x].cond == x_C2D_1[z][x] + x_C2D_2[z][x])

    for z in range(slice_numebr):
        for x in range(5):
            model.addConstr(D[z][x].cond == (x_D2new_state[z][0][x] + x_D2new_state[z][1][x] +
                                             x_D2new_state[z][2][x] + x_D2new_state[z][3][x] +
                                             x_D2new_state[z][4][x]))

    for z in range(slice_numebr):
        for x in range(5):
            delta_r = theta_vars[f"C_x{x}_z{z}"]['delta_r']
            delta_b = theta_vars[f"C_x{x}_z{z}"]['delta_b']
            has_ul = theta_vars[f"C_x{x}_z{z}"]['has_ul']
            theta_vars[f"C_x{x}_z{z}"]['new_cond'] = model.addVar(vtype=GRB.BINARY, name=f'C_x{x}_z{z}_new_cond')
            model.addConstr(theta_vars[f"C_x{x}_z{z}"]['new_cond'] <= delta_r + delta_b)
            model.addConstr(theta_vars[f"C_x{x}_z{z}"]['new_cond'] <= 1 - has_ul)
            model.addConstr(C[z][x].cond == (x_old_state2C[z][0][x] + x_old_state2C[z][1][x] +
                                             x_old_state2C[z][2][x] + x_old_state2C[z][3][x] +
                                             x_old_state2C[z][4][x] + theta_vars[f"C_x{x}_z{z}"]['new_cond']))

    for z in range(slice_numebr):
        for x in range(5):
            delta_r = theta_vars[f"D_x{x}_z{z}"]['delta_r']
            delta_b = theta_vars[f"D_x{x}_z{z}"]['delta_b']
            has_ul = theta_vars[f"D_x{x}_z{z}"]['has_ul']
            theta_vars[f"D_x{x}_z{z}"]['new_cond'] = model.addVar(vtype=GRB.BINARY, name=f'D_x{x}_z{z}_new_cond')
            model.addConstr(theta_vars[f"D_x{x}_z{z}"]['new_cond'] <= delta_r + delta_b)
            model.addConstr(theta_vars[f"D_x{x}_z{z}"]['new_cond'] <= 1 - has_ul)
            model.addConstr(D[z][x].cond == x_C2D_1[z][(x - 1) % 5] + x_C2D_2[(z - 1) % slice_numebr][(x + 1) % 5] + theta_vars[f"D_x{x}_z{z}"]['new_cond'])

    for z in range(slice_numebr):
        for y in range(5):
            for x in range(5):
                delta_r = theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_r']
                delta_b = theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_b']
                has_ul = theta_vars[f"new_z{z}_y{y}_x{x}"]['has_ul']
                theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'] = model.addVar(vtype=GRB.BINARY, name=f'new_z{z}_y{y}_x{x}_new_cond')
                model.addConstr(theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'] <= delta_r + delta_b)
                model.addConstr(theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'] <= 1 - has_ul)
                model.addConstr(new_state[z][y][x].cond == x_D2new_state[z][y][x] + x_old_state2new_state[z][y][x] + theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'])


def create_chi_operation(model, state, operation_name="chi"):
    """
    MILP modeling for Keccak chi function

    Parameters:
    - model: Gurobi model object
    - state: slice_numebrx5x5 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after chi operation
    - chi_vars: Variables related to chi operation
    - without_place: Binary variables indicating inactive S-boxes
    - linear_cancel: Binary variables indicating linear cancellations
    """
    new_state = [[[None for _ in range(5)] for _ in range(5)] for _ in range(slice_numebr)]
    and_bits = [[[None for _ in range(5)] for _ in range(5)] for _ in range(slice_numebr)]
    chi_vars = {}
    linear_cancel = {}

    # Step 1: Calculate all AND terms A[z][y][(x+1)%5] AND A[z][y][(x+2)%5]
    for z in range(slice_numebr):
        for y in range(5):
            for x in range(5):
                x1 = (x + 1) % 5
                x2 = (x + 2) % 5
                bit1 = state[z][y][x1]
                bit2 = state[z][y][x2]

                and_bit_name = f"{operation_name}_and_z{z}_y{y}_x{x}"
                and_bit = Bit(model, and_bit_name, ('*', '*', '*', 0))

                and_vars = and_operation_no_cond(model, bit1, bit2, and_bit, operation_name=and_bit_name)

                and_bits[z][y][x] = and_bit
                chi_vars[f"and_z{z}_y{y}_x{x}"] = and_vars

    # Step 2: Calculate new state A'[z][y][x] = A[z][y][x] ⊕ (A[z][y][(x+1)%5] AND A[z][y][(x+2)%5])
    without_place = [[0 for y in range(5)] for z in range(slice_numebr)]
    for z in range(slice_numebr):
        for y in range(5):
            without_compute_this = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_{y}_{z}")

            for x in range(5):
                original_bit = state[z][y][x]
                and_bit = and_bits[z][y][x]

                new_bit_name = f"{operation_name}_new_z{z}_y{y}_x{x}"
                new_bit = Bit(model, new_bit_name, ('*', '*', '*', 0))

                xor_vars = xor_with_ul_input(model, [original_bit, and_bit], new_bit, operation_name=new_bit_name)

                renew_bit = Bit(model, new_bit_name, ('*', '*', '*', 0))
                model.addConstr(renew_bit.r <= new_bit.r)
                model.addConstr(renew_bit.r <= 1 - without_compute_this)
                model.addConstr(renew_bit.r >= new_bit.r - without_compute_this)

                model.addConstr(renew_bit.b <= new_bit.b)
                model.addConstr(renew_bit.b <= 1 - without_compute_this)
                model.addConstr(renew_bit.b >= new_bit.b - without_compute_this)

                model.addConstr(renew_bit.ul >= new_bit.ul)
                model.addConstr(renew_bit.ul >= without_compute_this)
                model.addConstr(renew_bit.ul <= without_compute_this + new_bit.ul)

                if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_C_x{x}_z{z}")
                model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
                model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

                linear_cancel[f"new_z{z}_y{y}_x{x}"] = if_linear_cancel_r
                new_state[z][y][x] = renew_bit
                chi_vars[f"new_z{z}_y{y}_x{x}"] = xor_vars

            without_place[z][y] = without_compute_this

    return new_state, chi_vars, without_place, linear_cancel


def create_second_chi_operation(model, state, operation_name="chi"):
    """
    MILP modeling for Keccak second chi function

    Parameters:
    - model: Gurobi model object
    - state: slice_numebrx5x5 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after chi operation
    - chi_vars: Variables related to chi operation
    - without_place: Binary variables indicating inactive S-boxes
    - linear_cancel: Binary variables indicating linear cancellations
    """
    new_state = [[[None for _ in range(5)] for _ in range(5)] for _ in range(slice_numebr)]
    and_bits = [[[None for _ in range(5)] for _ in range(5)] for _ in range(slice_numebr)]
    chi_vars = {}
    linear_cancel = {}

    # Step 1: Calculate all AND terms A[z][y][(x+1)%5] AND A[z][y][(x+2)%5]
    for z in range(slice_numebr):
        for y in range(5):
            for x in range(5):
                x1 = (x + 1) % 5
                x2 = (x + 2) % 5
                bit1 = state[z][y][x1]
                bit2 = state[z][y][x2]

                and_bit_name = f"{operation_name}_and_z{z}_y{y}_x{x}"
                and_bit = Bit(model, and_bit_name, ('*', '*', '*', 0))

                and_vars = and_operation(model, bit1, bit2, and_bit, operation_name=and_bit_name)

                and_bits[z][y][x] = and_bit
                chi_vars[f"and_z{z}_y{y}_x{x}"] = and_vars

    # Step 2: Calculate new state A'[z][y][x] = A[z][y][x] ⊕ (A[z][y][(x+1)%5] AND A[z][y][(x+2)%5])
    without_place = [[0 for y in range(5)] for z in range(slice_numebr)]
    for z in range(slice_numebr):
        for y in range(5):
            without_compute_this = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_{y}_{z}")
            without_place[z][y] = without_compute_this
            for x in range(5):
                original_bit = state[z][y][x]
                and_bit = and_bits[z][y][x]

                new_bit_name = f"{operation_name}_new_z{z}_y{y}_x{x}"
                new_bit = Bit(model, new_bit_name, ('*', '*', '*', 0))

                xor_vars = xor_with_ul_input_no_delta_b(model, [original_bit, and_bit], new_bit, operation_name=new_bit_name)

                if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_C_x{x}_z{z}")
                model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
                model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

                linear_cancel[f"new_z{z}_y{y}_x{x}"] = if_linear_cancel_r

                renew_bit = Bit(model, new_bit_name, ('*', '*', '*', 0))
                model.addConstr(renew_bit.r <= new_bit.r)
                model.addConstr(renew_bit.r <= 1 - without_compute_this)
                model.addConstr(renew_bit.r >= new_bit.r - without_compute_this)

                model.addConstr(renew_bit.b <= new_bit.b)
                model.addConstr(renew_bit.b <= 1 - without_compute_this)
                model.addConstr(renew_bit.b >= new_bit.b - without_compute_this)

                model.addConstr(renew_bit.ul >= new_bit.ul)
                model.addConstr(renew_bit.ul >= without_compute_this)
                model.addConstr(renew_bit.ul <= without_compute_this + new_bit.ul)
                new_state[z][y][x] = renew_bit
                chi_vars[f"new_z{z}_y{y}_x{x}"] = xor_vars

    _add_chi_condition_constraints(model, state, new_state, chi_vars, operation_name)

    return new_state, chi_vars, without_place, linear_cancel


def create_first_chi_operation_512(model, state, operation_name="chi"):
    """
    MILP modeling for Keccak chi function in the first round (Keccak-512),
    no ul=1 inputs/outputs and no bits with both r=1 and b=1

    Parameters:
    - model: Gurobi model object
    - state: slice_numebrx5x5 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after chi operation
    - chi_vars: Variables related to chi operation
    - without_place: Binary variables indicating inactive S-boxes
    - linear_cancel: Binary variables indicating linear cancellations
    """
    for z in range(slice_numebr):
        for y in [0, 2, 4]:
            model.addConstr(state[z][y][0].r + state[z][y][1].b <= 1)
            model.addConstr(state[z][y][0].b + state[z][y][1].r <= 1)

    chi_vars = dict()
    new_state = [[[None for _ in range(5)] for _ in range(5)] for _ in range(slice_numebr)]
    linear_cancel = {}

    for z in range(slice_numebr):
        r_col_0 = model.addVar(vtype=GRB.BINARY, name=f'r_col_0{z}')
        r_col_4 = model.addVar(vtype=GRB.BINARY, name=f'r_col_4{z}')

        for y in [0, 2, 4]:
            new_state[z][y][0] = Bit(model, f'new_z{z}_y{y}_x{0}', (0, '*', 0, 0))
            new_state[z][y][1] = Bit(model, f'new_z{z}_y{y}_x{1}', (0, 0, 0, 0))
            new_state[z][y][2] = Bit(model, f'new_z{z}_y{y}_x{2}', (0, 0, 0, 0))
            new_state[z][y][3] = Bit(model, f'new_z{z}_y{y}_x{3}', (0, 0, 0, 0))
            new_state[z][y][4] = Bit(model, f'new_z{z}_y{y}_x{4}', ('*', '*', 0, 0))

            new_state[z][y][1].b = state[z][y][1].b
            new_state[z][y][0].b = state[z][y][0].b
            new_state[z][y][1].r = state[z][y][1].r

            model.addConstr(new_state[z][y][4].ul >= state[z][y][0].r + state[z][y][1].r - 1)
            model.addConstr(2 * new_state[z][y][4].ul <= state[z][y][0].r + state[z][y][1].r)

            model.addConstr(r_col_4 + (1 - new_state[z][y][4].r) >= 1)
            model.addConstr(state[z][y][0].r + (1 - new_state[z][y][4].r) >= 1)
            model.addConstr(r_col_0 + (1 - new_state[z][y][0].r) >= 1)
            model.addConstr((1 - state[z][y][0].r) + new_state[z][y][0].r >= 1)
            model.addConstr(state[z][y][0].r + state[z][y][1].r + (1 - new_state[z][y][0].r) >= 1)
            model.addConstr((1 - state[z][y][1].r) + (1 - r_col_0) + new_state[z][y][0].r >= 1)
            model.addConstr((1 - state[z][y][0].r) + (1 - r_col_4) + new_state[z][y][4].r >= 1)
            model.addConstr((1 - state[z][y][0].r) + (1 - state[z][y][1].r) + new_state[z][y][4].r >= 1)

            chi_vars[f"and_z{z}_y{y}_x{0}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{1}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{2}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{3}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{4}"] = {'const_cond': 0, 'CT': 0}

            for x in range(5):
                chi_vars[f"new_z{z}_y{y}_x{x}"] = {'any_u': 0, 'delta_r': 0, 'delta_b': 0, 'delta_r_ul': 0, 'new_cond': 0}
                linear_cancel[f"new_z{z}_y{y}_x{x}"] = 0

        model.addConstr(r_col_4 <= new_state[z][0][4].r + new_state[z][2][4].r + new_state[z][4][4].r)
        model.addConstr(3 * r_col_4 >= new_state[z][0][4].r + new_state[z][2][4].r + new_state[z][4][4].r)

        model.addConstr(r_col_0 <= state[z][0][0].r + state[z][1][0].r + state[z][2][0].r + state[z][4][0].r)
        model.addConstr(4 * r_col_0 >= state[z][0][0].r + state[z][1][0].r + state[z][2][0].r + state[z][4][0].r)

        y = 1
        new_state[z][y][0] = Bit(model, f'new_z{z}_y{y}_x{0}', (0, 0, 0, 0))
        new_state[z][y][1] = Bit(model, f'new_z{z}_y{y}_x{1}', (0, 0, 0, 0))
        new_state[z][y][2] = Bit(model, f'new_z{z}_y{y}_x{2}', (0, 0, 0, 0))
        new_state[z][y][3] = Bit(model, f'new_z{z}_y{y}_x{3}', (0, 0, 0, 0))
        new_state[z][y][4] = Bit(model, f'new_z{z}_y{y}_x{4}', (0, '*', 0, 0))

        new_state[z][y][0].r = state[z][y][0].r
        new_state[z][y][0].b = state[z][y][0].b

        model.addConstr(new_state[z][y][4].r >= state[z][y][0].r + r_col_4 - 1)
        model.addConstr(new_state[z][y][4].r <= state[z][y][0].r)
        model.addConstr(new_state[z][y][4].r <= r_col_4)

        chi_vars[f"and_z{z}_y{y}_x{0}"] = {'const_cond': 0, 'CT': 0}
        chi_vars[f"and_z{z}_y{y}_x{1}"] = {'const_cond': 0, 'CT': 0}
        chi_vars[f"and_z{z}_y{y}_x{2}"] = {'const_cond': 0, 'CT': 0}
        chi_vars[f"and_z{z}_y{y}_x{3}"] = {'const_cond': 0, 'CT': 0}
        chi_vars[f"and_z{z}_y{y}_x{4}"] = {'const_cond': 0, 'CT': 0}

        for x in range(5):
            chi_vars[f"new_z{z}_y{y}_x{x}"] = {'any_u': 0, 'delta_r': 0, 'delta_b': 0, 'delta_r_ul': 0, 'new_cond': 0}
            linear_cancel[f"new_z{z}_y{y}_x{x}"] = 0

        y = 3
        new_state[z][y][0] = Bit(model, f'new_z{z}_y{y}_x{0}', (0, '*', 0, 0))
        new_state[z][y][1] = Bit(model, f'new_z{z}_y{y}_x{1}', (0, 0, 0, 0))
        new_state[z][y][2] = Bit(model, f'new_z{z}_y{y}_x{2}', (0, 0, 0, 0))
        new_state[z][y][3] = Bit(model, f'new_z{z}_y{y}_x{3}', (0, 0, 0, 0))
        new_state[z][y][4] = Bit(model, f'new_z{z}_y{y}_x{4}', (0, 0, 0, 0))

        new_state[z][y][1].r = state[z][y][1].r
        new_state[z][y][1].b = state[z][y][1].b

        model.addConstr(new_state[z][y][0].r >= state[z][y][1].r + r_col_0 - 1)
        model.addConstr(new_state[z][y][0].r <= state[z][y][1].r)
        model.addConstr(new_state[z][y][0].r <= r_col_0)

        chi_vars[f"and_z{z}_y{y}_x{0}"] = {'const_cond': 0, 'CT': 0}
        chi_vars[f"and_z{z}_y{y}_x{1}"] = {'const_cond': 0, 'CT': 0}
        chi_vars[f"and_z{z}_y{y}_x{2}"] = {'const_cond': 0, 'CT': 0}
        chi_vars[f"and_z{z}_y{y}_x{3}"] = {'const_cond': 0, 'CT': 0}
        chi_vars[f"and_z{z}_y{y}_x{4}"] = {'const_cond': 0, 'CT': 0}

        for x in range(5):
            chi_vars[f"new_z{z}_y{y}_x{x}"] = {'any_u': 0, 'delta_r': 0, 'delta_b': 0, 'delta_r_ul': 0, 'new_cond': 0}
            linear_cancel[f"new_z{z}_y{y}_x{x}"] = 0

    without_place = [[0 for _ in range(5)] for _ in range(slice_numebr)]

    return new_state, chi_vars, without_place, linear_cancel


def create_first_chi_operation_384(model, state, operation_name="chi"):
    """
    MILP modeling for Keccak chi function in the first round (Keccak-384),
    no ul=1 inputs/outputs and no bits with both r=1 and b=1

    Parameters:
    - model: Gurobi model object
    - state: slice_numebrx5x5 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after chi operation
    - chi_vars: Variables related to chi operation
    - without_place: Binary variables indicating inactive S-boxes
    - linear_cancel: Binary variables indicating linear cancellations
    """
    for z in range(slice_numebr):
        for y in [0, 1, 3]:
            model.addConstr(state[z][y][0].r + state[z][y][1].b <= 1)
            model.addConstr(state[z][y][0].b + state[z][y][1].r <= 1)

            model.addConstr(state[z][y][0].r + state[z][y][2].b <= 1)
            model.addConstr(state[z][y][0].b + state[z][y][2].r <= 1)

            model.addConstr(state[z][y][2].r + state[z][y][1].b <= 1)
            model.addConstr(state[z][y][2].b + state[z][y][1].r <= 1)
        for y in [2, 4]:
            model.addConstr(state[z][y][0].r + state[z][y][1].b <= 1)
            model.addConstr(state[z][y][0].b + state[z][y][1].r <= 1)

    chi_vars = dict()
    linear_cancel = {}
    new_state = [[[None for _ in range(5)] for _ in range(5)] for _ in range(slice_numebr)]

    for z in range(slice_numebr):
        r_col_0 = model.addVar(vtype=GRB.BINARY, name=f'r_col_0{z}')
        r_col_1 = model.addVar(vtype=GRB.BINARY, name=f'r_col_1{z}')
        r_col_4 = model.addVar(vtype=GRB.BINARY, name=f'r_col_4{z}')

        for y in [0, 1, 3]:
            new_state[z][y][0] = Bit(model, f'new_z{z}_y{y}_x{0}', ('*', '*', 0, 0))
            new_state[z][y][1] = Bit(model, f'new_z{z}_y{y}_x{1}', (0, '*', 0, 0))
            new_state[z][y][2] = Bit(model, f'new_z{z}_y{y}_x{2}', (0, 0, 0, 0))
            new_state[z][y][3] = Bit(model, f'new_z{z}_y{y}_x{3}', (0, 0, 0, 0))
            new_state[z][y][4] = Bit(model, f'new_z{z}_y{y}_x{4}', ('*', '*', 0, 0))

            new_state[z][y][2].b = state[z][y][2].b
            new_state[z][y][1].b = state[z][y][1].b
            new_state[z][y][0].b = state[z][y][0].b
            new_state[z][y][2].r = state[z][y][2].r

            model.addConstr(new_state[z][y][0].ul >= state[z][y][2].r + state[z][y][1].r - 1)
            model.addConstr(2 * new_state[z][y][0].ul <= state[z][y][2].r + state[z][y][1].r)

            model.addConstr(new_state[z][y][4].ul >= state[z][y][0].r + state[z][y][1].r - 1)
            model.addConstr(2 * new_state[z][y][4].ul <= state[z][y][0].r + state[z][y][1].r)

            model.addConstr(r_col_4 + (1 - new_state[z][y][4].r) >= 1)
            model.addConstr(state[z][y][0].r + state[z][y][1].r + (1 - new_state[z][y][4].r) >= 1)
            model.addConstr((1 - state[z][y][1].r) + (1 - r_col_4) + new_state[z][y][4].r >= 1)
            model.addConstr((1 - state[z][y][1].r) + new_state[z][y][1].r >= 1)
            model.addConstr(r_col_0 + (1 - new_state[z][y][0].r) >= 1)
            model.addConstr((1 - state[z][y][0].r) + new_state[z][y][0].r >= 1)
            model.addConstr(r_col_1 + (1 - new_state[z][y][1].r) >= 1)
            model.addConstr((1 - state[z][y][0].r) + (1 - r_col_4) + new_state[z][y][4].r >= 1)
            model.addConstr((1 - state[z][y][2].r) + (1 - r_col_0) + new_state[z][y][0].r >= 1)
            model.addConstr(state[z][y][1].r + state[z][y][2].r + (1 - new_state[z][y][1].r) >= 1)
            model.addConstr((1 - state[z][y][2].r) + (1 - r_col_1) + new_state[z][y][1].r >= 1)
            model.addConstr((1 - r_col_0) + new_state[z][y][0].r + (1 - new_state[z][y][1].r) >= 1)
            model.addConstr((1 - state[z][y][1].r) + (1 - state[z][y][2].r) + new_state[z][y][0].r >= 1)
            model.addConstr((1 - state[z][y][0].r) + (1 - state[z][y][1].r) + new_state[z][y][4].r >= 1)
            model.addConstr(state[z][y][0].r + state[z][y][2].r + (1 - new_state[z][y][0].r) + new_state[z][y][1].r >= 1)

            chi_vars[f"and_z{z}_y{y}_x{0}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{1}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{2}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{3}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{4}"] = {'const_cond': 0, 'CT': 0}

            for x in range(5):
                chi_vars[f"new_z{z}_y{y}_x{x}"] = {'any_u': 0, 'delta_r': 0, 'delta_b': 0, 'delta_r_ul': 0, 'new_cond': 0}
                linear_cancel[f"new_z{z}_y{y}_x{x}"] = 0

        for y in [2, 4]:
            new_state[z][y][0] = Bit(model, f'new_z{z}_y{y}_x{0}', (0, '*', 0, 0))
            new_state[z][y][1] = Bit(model, f'new_z{z}_y{y}_x{1}', (0, 0, 0, 0))
            new_state[z][y][2] = Bit(model, f'new_z{z}_y{y}_x{2}', (0, 0, 0, 0))
            new_state[z][y][3] = Bit(model, f'new_z{z}_y{y}_x{3}', (0, 0, 0, 0))
            new_state[z][y][4] = Bit(model, f'new_z{z}_y{y}_x{4}', (0, '*', 0, 0))

            new_state[z][y][1].b = state[z][y][1].b
            new_state[z][y][0].b = state[z][y][0].b
            new_state[z][y][1].r = state[z][y][1].r

            model.addConstr(new_state[z][y][4].ul >= state[z][y][0].r + state[z][y][1].r - 1)
            model.addConstr(2 * new_state[z][y][4].ul <= state[z][y][0].r + state[z][y][1].r)

            model.addConstr(r_col_4 + (1 - new_state[z][y][4].r) >= 1)
            model.addConstr(state[z][y][0].r + (1 - new_state[z][y][4].r) >= 1)
            model.addConstr(r_col_0 + (1 - new_state[z][y][0].r) >= 1)
            model.addConstr((1 - state[z][y][0].r) + new_state[z][y][0].r >= 1)
            model.addConstr(state[z][y][0].r + state[z][y][1].r + (1 - new_state[z][y][0].r) >= 1)
            model.addConstr((1 - state[z][y][1].r) + (1 - r_col_0) + new_state[z][y][0].r >= 1)
            model.addConstr((1 - state[z][y][0].r) + (1 - r_col_4) + new_state[z][y][4].r >= 1)
            model.addConstr((1 - state[z][y][0].r) + (1 - state[z][y][1].r) + new_state[z][y][4].r >= 1)

            chi_vars[f"and_z{z}_y{y}_x{0}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{1}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{2}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{3}"] = {'const_cond': 0, 'CT': 0}
            chi_vars[f"and_z{z}_y{y}_x{4}"] = {'const_cond': 0, 'CT': 0}

            for x in range(5):
                chi_vars[f"new_z{z}_y{y}_x{x}"] = {'any_u': 0, 'delta_r': 0, 'delta_b': 0, 'delta_r_ul': 0, 'new_cond': 0}
                linear_cancel[f"new_z{z}_y{y}_x{x}"] = 0

        model.addConstr(r_col_1 <= state[z][0][1].r + state[z][1][1].r + state[z][2][1].r + state[z][3][1].r + state[z][4][1].r)
        model.addConstr(5 * r_col_1 >= state[z][0][1].r + state[z][1][1].r + state[z][2][1].r + state[z][3][1].r + state[z][4][1].r)

        model.addConstr(r_col_0 <= state[z][0][0].r + state[z][1][0].r + state[z][2][0].r + state[z][3][0].r + state[z][4][0].r + new_state[z][0][0].r + new_state[z][1][0].r + new_state[z][3][0].r)
        model.addConstr(
            7 * r_col_0 >= state[z][0][0].r + state[z][1][0].r + state[z][2][0].r + state[z][3][0].r + state[z][4][0].r + new_state[z][0][0].r + new_state[z][1][0].r + new_state[z][3][0].r)

        model.addConstr(r_col_4 <= new_state[z][0][4].r + new_state[z][1][4].r + new_state[z][3][4].r)
        model.addConstr(3 * r_col_4 >= new_state[z][0][4].r + new_state[z][1][4].r + new_state[z][3][4].r)

    without_place = [[0 for _ in range(5)] for _ in range(slice_numebr)]

    return new_state, chi_vars, without_place, linear_cancel


def _add_chi_condition_constraints(model, old_state, new_state, chi_vars, operation_name):
    """
    Add condition constant propagation constraints in chi function

    Parameters:
    - model: Gurobi model object
    - old_state: Old state [z][y][x]
    - new_state: New state [z][y][x]
    - chi_vars: Variables related to Chi operation
    - operation_name: Operation name
    """
    x_old_state2and_1 = [[[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_old_state2and_1_z{z}_y{y}_x{(x - 1) % 5}")
                           for x in range(5)] for y in range(5)] for z in range(slice_numebr)]

    x_old_state2and_2 = [[[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_old_state2and_2_z{z}_y{y}_x{(x - 2) % 5}")
                           for x in range(5)] for y in range(5)] for z in range(slice_numebr)]

    for z in range(slice_numebr):
        for y in range(5):
            for x in range(5):
                model.addConstr(old_state[z][y][x].cond == (x_old_state2and_1[z][y][x] + x_old_state2and_2[z][y][x]))

    for z in range(slice_numebr):
        for y in range(5):
            for x in range(5):
                const_cond = chi_vars[f"and_z{z}_y{y}_x{x}"]["const_cond"]
                model.addConstr(const_cond == x_old_state2and_1[z][y][(x + 1) % 5] + x_old_state2and_2[z][y][(x + 2) % 5])


rho_box = [
    [0, 1, 62, 28, 27],
    [36, 44, 6, 55, 20],
    [3, 10, 43, 25, 39],
    [41, 45, 15, 21, 8],
    [18, 2, 61, 56, 14]
]


def rho(old_state):
    """
    Keccak Rho function: performs cyclic shift operation in z-direction on the state

    Parameters:
    - old_state: slice_numebrx5x5 3D input state array [z][y][x]

    Returns:
    - new_state: New state array after Rho operation
    """
    new_state = [[[0 for _ in range(5)] for _ in range(5)] for _ in range(slice_numebr)]

    for z in range(slice_numebr):
        for y in range(5):
            for x in range(5):
                new_state[z][y][x] = old_state[(z - rho_box[y][x]) % slice_numebr][y][x]

    return new_state


def pi(old_state):
    """
    Keccak Pi function: performs lane position permutation on the state

    Parameters:
    - old_state: slice_numebrx5x5 3D input state array [z][y][x]

    Returns:
    - new_state: New state array after Pi operation
    """
    new_state = [[[0 for _ in range(5)] for _ in range(5)] for _ in range(slice_numebr)]

    for z in range(slice_numebr):
        for y in range(5):
            for x in range(5):
                new_state[z][y][x] = old_state[z][x][(x + 3 * y) % 5]

    return new_state