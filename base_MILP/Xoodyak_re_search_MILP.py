from new_code.base.simple_base import *
from gurobipy import GRB


def create_theta_operation(model, state, operation_name="xoodyak_theta"):
    """
    MILP modeling for Xoodyak theta function

    Parameters:
    - model: Gurobi model object
    - state: 32x3x4 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after theta operation
    - C: Intermediate variable C [z][x]
    - D: Intermediate variable D [z][x]
    - theta_vars: Variables related to theta operation
    - linear_cancel: Linear cancellation flags
    """

    # Initialize new state
    new_state = [[[None for _ in range(4)] for _ in range(3)] for _ in range(32)]
    theta_vars = {}
    linear_cancel = {}

    # Step 1: Calculate C[z][x] = state[z][0][x] ⊕ state[z][1][x] ⊕ state[z][2][x]
    C = [[None for _ in range(4)] for _ in range(32)]

    for x in range(4):
        for z in range(32):
            # Create C[z][x] bit
            C_bit = Bit(model, f"{operation_name}_C_x{x}_z{z}", ('*', '*', '*', 0))

            # Get input bits list
            input_bits = [state[z][y][x] for y in range(3)]

            # Create XOR operation
            xor_vars = xor_with_ul_input_no_delta_b(model, input_bits, C_bit, f"{operation_name}_C_x{x}_z{z}")

            # Add linear cancellation variable
            if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_C_x{x}_z{z}")
            model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
            model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

            # Store variables
            theta_vars[f"C_x{x}_z{z}"] = xor_vars
            linear_cancel[f"C_x{x}_z{z}"] = if_linear_cancel_r
            C[z][x] = C_bit

    # Step 2: Calculate D[z][x] = C[(z-5)%32][(x-1)%4] ⊕ C[(z-14)%32][(x-1)%4]
    D = [[None for _ in range(4)] for _ in range(32)]

    for x in range(4):
        for z in range(32):
            # Create D[z][x] bit
            D_bit = Bit(model, f"{operation_name}_D_x{x}_z{z}", ('*', '*', '*', 0))

            # Get input bits
            input_bit1 = C[(z - 5) % 32][(x - 1) % 4]
            input_bit2 = C[(z - 14) % 32][(x - 1) % 4]

            # Create XOR operation
            xor_vars = xor_with_ul_input_no_delta_b(model, [input_bit1, input_bit2], D_bit, f"{operation_name}_D_x{x}_z{z}")

            # Add linear cancellation variable
            if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_D_x{x}_z{z}")
            model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
            model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

            # Store variables
            theta_vars[f"D_x{x}_z{z}"] = xor_vars
            linear_cancel[f"D_x{x}_z{z}"] = if_linear_cancel_r
            D[z][x] = D_bit

    # Step 3: Calculate new state state'[z][y][x] = state[z][y][x] ⊕ D[z][x]
    for z in range(32):
        for y in range(3):
            for x in range(4):
                # Create new state bit
                new_bit = Bit(model, f"{operation_name}_new_z{z}_y{y}_x{x}", ('*', '*', '*', 0))

                # Get input bits
                input_bit1 = state[z][y][x]
                input_bit2 = D[z][x]

                # Create XOR operation
                xor_vars = xor_with_ul_input_no_delta_b(model, [input_bit1, input_bit2], new_bit, f"{operation_name}_new_z{z}_y{y}_x{x}")

                # Add linear cancellation variable
                if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_new_z{z}_y{y}_x{x}")
                model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
                model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

                # Store new state and variables
                new_state[z][y][x] = new_bit
                theta_vars[f"new_z{z}_y{y}_x{x}"] = xor_vars
                linear_cancel[f"new_z{z}_y{y}_x{x}"] = if_linear_cancel_r

    return new_state, C, D, theta_vars, linear_cancel


def create_first_theta_operation(model, state, operation_name="theta"):
    """
    MILP modeling for Xoodyak theta function (first round, with constraints on ul flag)

    Parameters:
    - model: Gurobi model object
    - state: 32x3x4 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after theta operation
    - C: Intermediate variable C [z][x]
    - D: Intermediate variable D [z][x]
    - theta_vars: Variables related to theta operation
    - linear_cancel: Linear cancellation flags
    """

    # Initialize new state
    new_state = [[[None for _ in range(4)] for _ in range(3)] for _ in range(32)]
    theta_vars = {}
    linear_cancel = {}

    # Step 1: Calculate C[z][x] = state[z][0][x] ⊕ state[z][1][x] ⊕ state[z][2][x]
    C = [[None for _ in range(4)] for _ in range(32)]

    for x in range(4):
        for z in range(32):
            # Create C[z][x] bit with ul=0
            C_bit = Bit(model, f"{operation_name}_C_x{x}_z{z}", (0, '*', '*', '*'))
            # Constraint: cannot have both red and blue flags
            model.addConstr(C_bit.r + C_bit.b <= 1)

            # Get input bits list
            input_bits = [state[z][y][x] for y in range(3)]

            # Create XOR operation
            xor_vars = xor_without_ul_input(model, input_bits, C_bit, f"{operation_name}_C_x{x}_z{z}")

            # Add linear cancellation variable
            if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_C_x{x}_z{z}")
            model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
            model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

            # Store variables
            theta_vars[f"C_x{x}_z{z}"] = xor_vars
            linear_cancel[f"C_x{x}_z{z}"] = if_linear_cancel_r
            C[z][x] = C_bit

    # Step 2: Calculate D[z][x] = C[(z-5)%32][(x-1)%4] ⊕ C[(z-14)%32][(x-1)%4]
    D = [[None for _ in range(4)] for _ in range(32)]

    for x in range(4):
        for z in range(32):
            # Create D[z][x] bit with ul=0
            D_bit = Bit(model, f"{operation_name}_D_x{x}_z{z}", (0, '*', '*', '*'))
            # Constraint: cannot have both red and blue flags
            model.addConstr(D_bit.r + D_bit.b <= 1)

            # Get input bits
            input_bit1 = C[(z - 5) % 32][(x - 1) % 4]
            input_bit2 = C[(z - 14) % 32][(x - 1) % 4]

            # Create XOR operation
            xor_vars = xor_without_ul_input(model, [input_bit1, input_bit2], D_bit, f"{operation_name}_D_x{x}_z{z}")

            # Add linear cancellation variable
            if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_D_x{x}_z{z}")
            model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
            model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

            # Store variables
            theta_vars[f"D_x{x}_z{z}"] = xor_vars
            linear_cancel[f"D_x{x}_z{z}"] = if_linear_cancel_r
            D[z][x] = D_bit

    # Step 3: Calculate new state A'[z][y][x] = A[z][y][x] ⊕ D[z][x]
    for z in range(32):
        for y in range(3):
            for x in range(4):
                # Create new state bit with ul=0
                new_bit = Bit(model, f"{operation_name}_new_z{z}_y{y}_x{x}", (0, '*', '*', '*'))

                # Get input bits
                input_bit1 = state[z][y][x]
                input_bit2 = D[z][x]

                # Create XOR operation
                xor_vars = xor_without_ul_input(model, [input_bit1, input_bit2], new_bit, f"{operation_name}_new_z{z}_y{y}_x{x}")

                # Add linear cancellation variable
                if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_new_z{z}_y{y}_x{x}")
                model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
                model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])

                # Store new state and variables
                new_state[z][y][x] = new_bit
                theta_vars[f"new_z{z}_y{y}_x{x}"] = xor_vars
                linear_cancel[f"new_z{z}_y{y}_x{x}"] = if_linear_cancel_r

    # Step 4: Add condition constant propagation constraints
    _add_theta_condition_constraints(model, theta_vars, state, C, D, new_state, operation_name)

    return new_state, C, D, theta_vars, linear_cancel


def _add_theta_condition_constraints(model, theta_vars, old_state, C, D, new_state, operation_name):
    """
    Add condition constant propagation constraints in Xoodyak theta function

    Parameters:
    - model: Gurobi model object
    - theta_vars: Variables related to theta operation
    - old_state: Old state [z][y][x]
    - C: Intermediate variable C [z][x]
    - D: Intermediate variable D [z][x]
    - new_state: New state [z][y][x]
    - operation_name: Operation name
    """
    # Construct auxiliary variables x_ij
    # Condition constant propagation from old state to C
    x_old_state2C = [[[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_old_state({z},{y},{x})2C({z},{x})")
                       for x in range(4)] for y in range(3)] for z in range(32)]

    # Condition constant propagation from old state to new state
    x_old_state2new_state = [[[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_old_state({z},{y},{x})2new_state({z},{y},{x})")
                               for x in range(4)] for y in range(3)] for z in range(32)]

    # Condition constant propagation from C to D
    x_C2D_1 = [[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_C({z},{x})2D({(z - 5) % 32},{(x - 1) % 4})")
                for x in range(4)] for z in range(32)]
    x_C2D_2 = [[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_C({z},{x})2D({(z - 14) % 32},{(x - 1) % 4})")
                for x in range(4)] for z in range(32)]

    # Condition constant propagation from D to new state
    x_D2new_state = [[[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_D({z},{x})2new_state({z},{y},{x})")
                       for x in range(4)] for y in range(3)] for z in range(32)]

    # Each condition constant has exactly one output propagation bit

    # Condition output constraints for old state
    for z in range(32):
        for y in range(3):
            for x in range(4):
                model.addConstr(old_state[z][y][x].cond == x_old_state2C[z][y][x] + x_old_state2new_state[z][y][x])

    # Condition output constraints for C
    for z in range(32):
        for x in range(4):
            model.addConstr(C[z][x].cond == x_C2D_1[z][x] + x_C2D_2[z][x])

    # Condition output constraints for D
    for z in range(32):
        for x in range(4):
            model.addConstr(D[z][x].cond == (x_D2new_state[z][0][x] + x_D2new_state[z][1][x] + x_D2new_state[z][2][x]))

    # Each condition constant has exactly one input propagation bit

    # Condition input constraints for C
    for z in range(32):
        for x in range(4):
            delta_r = theta_vars[f"C_x{x}_z{z}"]['delta_r']
            delta_b = theta_vars[f"C_x{x}_z{z}"]['delta_b']
            has_ul = theta_vars[f"C_x{x}_z{z}"]['has_ul']
            theta_vars[f"C_x{x}_z{z}"]['new_cond'] = model.addVar(vtype=GRB.BINARY, name=f'C_x{x}_z{z}_new_cond')
            model.addConstr(theta_vars[f"C_x{x}_z{z}"]['new_cond'] <= delta_r + delta_b)
            model.addConstr(theta_vars[f"C_x{x}_z{z}"]['new_cond'] <= 1 - has_ul)
            model.addConstr(C[z][x].cond == (x_old_state2C[z][0][x] + x_old_state2C[z][1][x] +
                                             x_old_state2C[z][2][x] + theta_vars[f"C_x{x}_z{z}"]['new_cond']))

    # Condition input constraints for D
    for z in range(32):
        for x in range(4):
            delta_r = theta_vars[f"D_x{x}_z{z}"]['delta_r']
            delta_b = theta_vars[f"D_x{x}_z{z}"]['delta_b']
            has_ul = theta_vars[f"D_x{x}_z{z}"]['has_ul']
            theta_vars[f"D_x{x}_z{z}"]['new_cond'] = model.addVar(vtype=GRB.BINARY, name=f'D_x{x}_z{z}_new_cond')
            model.addConstr(theta_vars[f"D_x{x}_z{z}"]['new_cond'] <= delta_r + delta_b)
            model.addConstr(theta_vars[f"D_x{x}_z{z}"]['new_cond'] <= 1 - has_ul)
            model.addConstr(D[z][x].cond == x_C2D_1[(z + 5) % 32][(x + 1) % 4] +
                            x_C2D_2[(z + 14) % 32][(x + 1) % 4] +
                            theta_vars[f"D_x{x}_z{z}"]['new_cond'])

    # Condition input constraints for new state
    for z in range(32):
        for y in range(3):
            for x in range(4):
                delta_r = theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_r']
                delta_b = theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_b']
                has_ul = theta_vars[f"new_z{z}_y{y}_x{x}"]['has_ul']
                theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'] = model.addVar(vtype=GRB.BINARY,
                                                                             name=f'new_z{z}_y{y}_x{x}_new_cond')
                model.addConstr(theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'] <= delta_r + delta_b)
                model.addConstr(theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'] <= 1 - has_ul)
                model.addConstr(new_state[z][y][x].cond == x_D2new_state[z][y][x] +
                                x_old_state2new_state[z][y][x] +
                                theta_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'])


def create_chi_operation(model, state, operation_name="xoodyak_chi"):
    """
    MILP modeling for Xoodyak chi function

    Parameters:
    - model: Gurobi model object
    - state: 32x3x4 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after chi operation
    - chi_vars: Variables related to chi operation
    - without_place: Flags indicating skipped computation (renew_bit adjustment)
    - linear_cancel: Linear cancellation flags
    """
    # Initialize new state
    new_state = [[[None for _ in range(4)] for _ in range(3)] for _ in range(32)]
    # Initialize intermediate AND operation results
    and_bits = [[[None for _ in range(4)] for _ in range(3)] for _ in range(32)]
    chi_vars = {}
    linear_cancel = {}

    # Step 1: Calculate all AND terms state[z][(y+1)%3][x] AND state[z][(y+2)%3][x]
    for z in range(32):
        for y in range(3):
            for x in range(4):
                # Get input bit positions
                y1 = (y + 1) % 3
                y2 = (y + 2) % 3
                bit1 = state[z][y1][x]
                bit2 = state[z][y2][x]

                # Create AND operation bit
                and_bit_name = f"{operation_name}_and_z{z}_y{y}_x{x}"
                and_bit = Bit(model, and_bit_name, ('*', '*', '*', 0))

                # Create AND operation
                and_vars = and_operation_no_cond(model, bit1, bit2, and_bit, operation_name=and_bit_name)

                # Store intermediate results and variables
                and_bits[z][y][x] = and_bit
                chi_vars[f"and_z{z}_y{y}_x{x}"] = and_vars

    # Step 2: Calculate new state state'[z][y][x] = state[z][y][x] ⊕ (state[z][(y+1)%3][x] AND state[z][(y+2)%3][x])
    without_place = [[0 for _ in range(4)] for _ in range(32)]

    for z in range(32):
        for x in range(4):
            without_compute_this = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_without_{x}_{z}")

            for y in range(3):
                # Get input bits
                original_bit = state[z][y][x]
                and_bit = and_bits[z][y][x]

                # Create new state bit
                new_bit_name = f"{operation_name}_new_z{z}_y{y}_x{x}"
                new_bit = Bit(model, new_bit_name, ('*', '*', '*', 0))

                # Create XOR operation
                xor_vars = xor_with_ul_input_no_delta_b(model, [original_bit, and_bit], new_bit, operation_name=new_bit_name)

                # Add linear cancellation variable
                if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_new_z{z}_y{y}_x{x}")
                model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
                model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])
                linear_cancel[f"new_z{z}_y{y}_x{x}"] = if_linear_cancel_r

                # Adjust new state bit according to without_compute_this
                renew_bit = Bit(model, f"{new_bit_name}_renew", ('*', '*', '*', 0))
                model.addConstr(renew_bit.r <= new_bit.r)
                model.addConstr(renew_bit.r <= 1 - without_compute_this)
                model.addConstr(renew_bit.r >= new_bit.r - without_compute_this)

                model.addConstr(renew_bit.b <= new_bit.b)
                model.addConstr(renew_bit.b <= 1 - without_compute_this)
                model.addConstr(renew_bit.b >= new_bit.b - without_compute_this)

                model.addConstr(renew_bit.ul >= new_bit.ul)
                model.addConstr(renew_bit.ul >= without_compute_this)
                model.addConstr(renew_bit.ul <= without_compute_this + new_bit.ul)

                # Store new state and variables
                new_state[z][y][x] = renew_bit
                chi_vars[f"new_z{z}_y{y}_x{x}"] = xor_vars
            without_place[z][x] = without_compute_this

    return new_state, chi_vars, without_place, linear_cancel

def create_first_chi_operation(model, state, operation_name="xoodyak_chi"):
    """
    MILP modeling for Xoodyak chi function (first round, with condition constraints)

    Parameters:
    - model: Gurobi model object
    - state: 32x3x4 3D state array [z][y][x]
    - operation_name: Operation name for variable naming

    Returns:
    - new_state: New state after chi operation
    - chi_vars: Variables related to chi operation
    - without_place: Flags indicating skipped computation (always zero in first round)
    - linear_cancel: Linear cancellation flags
    """
    # Initialize new state
    new_state = [[[None for _ in range(4)] for _ in range(3)] for _ in range(32)]
    # Initialize intermediate AND operation results
    and_bits = [[[None for _ in range(4)] for _ in range(3)] for _ in range(32)]
    chi_vars = {}
    linear_cancel = {}

    # Step 1: Calculate all AND terms state[z][(y+1)%3][x] AND state[z][(y+2)%3][x]
    for z in range(32):
        for y in range(3):
            for x in range(4):
                # Get input bit positions
                y1 = (y + 1) % 3
                y2 = (y + 2) % 3
                bit1 = state[z][y1][x]
                bit2 = state[z][y2][x]

                # Create AND operation bit
                and_bit_name = f"{operation_name}_and_z{z}_y{y}_x{x}"
                and_bit = Bit(model, and_bit_name, ('*', '*', '*', 0))

                # Create AND operation
                and_vars = and_operation(model, bit1, bit2, and_bit, operation_name=and_bit_name)

                # Store intermediate results and variables
                and_bits[z][y][x] = and_bit
                chi_vars[f"and_z{z}_y{y}_x{x}"] = and_vars

    # Step 2: Calculate new state state'[z][y][x] = state[z][y][x] ⊕ (state[z][(y+1)%3][x] AND state[z][(y+2)%3][x])
    without_place = [[0 for _ in range(4)] for _ in range(32)]

    for z in range(32):
        for x in range(4):
            for y in range(3):
                # Get input bits
                original_bit = state[z][y][x]
                and_bit = and_bits[z][y][x]

                # Create new state bit
                new_bit_name = f"{operation_name}_new_z{z}_y{y}_x{x}"
                new_bit = Bit(model, new_bit_name, ('*', '*', '*', 0))

                # Create XOR operation
                xor_vars = xor_with_ul_input_no_delta_b(model, [original_bit, and_bit], new_bit, operation_name=new_bit_name)

                # Add linear cancellation variable
                if_linear_cancel_r = model.addVar(vtype=GRB.BINARY, name=f"if_linear_cancel_r_{operation_name}_new_z{z}_y{y}_x{x}")
                model.addConstr(if_linear_cancel_r <= 1 - xor_vars['has_ul'])
                model.addConstr(if_linear_cancel_r <= xor_vars['delta_r'])
                linear_cancel[f"new_z{z}_y{y}_x{x}"] = if_linear_cancel_r

                # Store new state and variables
                new_state[z][y][x] = new_bit
                chi_vars[f"new_z{z}_y{y}_x{x}"] = xor_vars

    # Step 3: Add condition constant propagation constraints
    _add_xoodyak_chi_condition_constraints(model, state, new_state, chi_vars, operation_name)

    return new_state, chi_vars, without_place, linear_cancel



def _add_xoodyak_chi_condition_constraints(model, old_state, new_state, chi_vars, operation_name):
    """
    Add condition constant propagation constraints in Xoodyak chi function

    Parameters:
    - model: Gurobi model object
    - old_state: Old state [z][y][x]
    - new_state: New state [z][y][x]
    - chi_vars: Variables related to chi operation
    - operation_name: Operation name
    """
    # Construct auxiliary variables

    # Condition constant propagation from old state to first input of AND operation
    x_old_state2and_1 = [[[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_old_state2and_1_z{z}_y{(y - 1) % 3}_x{x}")
                           for x in range(4)] for y in range(3)] for z in range(32)]

    # Condition constant propagation from old state to second input of AND operation
    x_old_state2and_2 = [[[model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_x_old_state2and_2_z{z}_y{(y - 2) % 3}_x{x}")
                           for x in range(4)] for y in range(3)] for z in range(32)]

    # Condition output constraints for old state
    for z in range(32):
        for y in range(3):
            for x in range(4):
                model.addConstr(old_state[z][y][x].cond == (x_old_state2and_1[z][y][x] + x_old_state2and_2[z][y][x]))

    # Condition input constraints for AND operation
    for z in range(32):
        for y in range(3):
            for x in range(4):
                const_cond = chi_vars[f"and_z{z}_y{y}_x{x}"]["const_cond"]
                model.addConstr(const_cond == x_old_state2and_1[z][(y + 1) % 3][x] + x_old_state2and_2[z][(y + 2) % 3][x])

    # Condition input constraints for new state
    for z in range(32):
        for y in range(3):
            for x in range(4):
                delta_r = chi_vars[f"new_z{z}_y{y}_x{x}"]['delta_r']
                delta_b = chi_vars[f"new_z{z}_y{y}_x{x}"]['delta_b']
                has_ul = chi_vars[f"new_z{z}_y{y}_x{x}"]['has_ul']
                chi_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'] = model.addVar(vtype=GRB.BINARY,
                                                                           name=f'new_z{z}_y{y}_x{x}_new_cond')
                model.addConstr(chi_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'] <= (delta_r + delta_b))
                model.addConstr(chi_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'] <= (1 - has_ul))
                model.addConstr(new_state[z][y][x].cond == chi_vars[f"new_z{z}_y{y}_x{x}"]['new_cond'])


def rho_west(state):
    """
    MILP modeling for Xoodyak rho_west function (shift operation)

    Parameters:
    - state: 32x3x4 3D state array [z][y][x]

    Returns:
    - new_state: New state after rho_west operation
    """
    # Initialize new state
    new_state = [[[None for _ in range(4)] for _ in range(3)] for _ in range(32)]

    # Shift parameters
    shifts = [
        [0, 0],   # y=0: (x_shift, z_shift)
        [-1, 0],  # y=1: (x_shift, z_shift)
        [0, -11], # y=2: (x_shift, z_shift)
    ]

    # Perform shift operation
    for x in range(4):
        for y in range(3):
            for z in range(32):
                new_state[z][y][x] = state[(z + shifts[y][1]) % 32][y][(x + shifts[y][0]) % 4]

    return new_state


def rho_east(state):
    """
    MILP modeling for Xoodyak rho_east function (shift operation)

    Parameters:
    - state: 32x3x4 3D state array [z][y][x]

    Returns:
    - new_state: New state after rho_east operation
    """
    # Initialize new state
    new_state = [[[None for _ in range(4)] for _ in range(3)] for _ in range(32)]

    # Shift parameters
    shifts = [
        [0, 0],   # y=0: (x_shift, z_shift)
        [0, -1],  # y=1: (x_shift, z_shift)
        [-2, -8], # y=2: (x_shift, z_shift)
    ]

    # Perform shift operation
    for x in range(4):
        for y in range(3):
            for z in range(32):
                new_state[z][y][x] = state[(z + shifts[y][1]) % 32][y][(x + shifts[y][0]) % 4]

    return new_state