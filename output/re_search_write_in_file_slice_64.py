import gurobipy as gp

def get_value(X):
    if type(X) == int:
        return X
    elif type(X) == gp.LinExpr:
        return int(X.getValue())
    elif type(X) == gp.QuadExpr:
        return int(X.getValue())
    else:
        return int(X.x)

def write_row(state, row, name):
    A = [[[0 for z in range(64)] for y in range(5)] for x in range(5)]  # Color values: 0-2
    B = [[[0 for z in range(64)] for y in range(5)] for x in range(5)]
    for x in range(5):
        for y in range(5):
            for z in range(64):
                A[x][y][z] = state[z][y][x]._get_type()
                cond = get_value(state[z][y][x].cond)
                if cond == 1:
                    B[x][y][z] = 'cond'
                else:
                    B[x][y][z] = None
    return A, B, row, name


def write_row_chi(state, row, chi_vars, linear_cancel_chi, name):
    A = [[[0 for z in range(64)] for y in range(5)] for x in range(5)]  # Color values: 0-2
    B = [[[0 for z in range(64)] for y in range(5)] for x in range(5)]
    for x in range(5):
        for y in range(5):
            for z in range(64):
                A[x][y][z] = state[z][y][x]._get_type()

                temp_cond = get_value(state[z][y][x].cond)
                temp_delta_r = get_value(chi_vars[f"new_z{z}_y{y}_x{x}"]['delta_r'])
                temp_delta_b = get_value(chi_vars[f"new_z{z}_y{y}_x{x}"]['delta_b'])
                temp_CT = get_value(chi_vars[f"and_z{z}_y{y}_x{x}"]['CT'])
                temp_const_cond = get_value(chi_vars[f"and_z{z}_y{y}_x{x}"]['const_cond'])
                if_linear_delta = get_value(linear_cancel_chi[f"new_z{z}_y{y}_x{x}"])

                if temp_cond == 1 and temp_delta_r > 0.5 and temp_delta_b > 0.5:
                    B[x][y][z] = 'cond+delta_r+b'
                elif temp_cond == 1 and temp_delta_r > 0.5 and if_linear_delta > 0.5:
                    B[x][y][z] = 'cond+delta_r_linear'
                elif temp_delta_r > 0.5 and if_linear_delta > 0.5:
                    B[x][y][z] = 'delta_r_linear'
                elif temp_cond == 1 and temp_delta_r > 0.5:
                    B[x][y][z] = 'cond+delta_r'
                elif temp_cond == 1 and temp_delta_b > 0.5:
                    B[x][y][z] = 'cond+delta_b'
                elif temp_cond == 1:
                    B[x][y][z] = 'cond'
                elif temp_delta_r > 0.5 and temp_delta_b > 0.5:
                    B[x][y][z] = 'delta_r+b'
                elif temp_delta_r > 0.5:
                    B[x][y][z] = 'delta_r'
                elif temp_delta_b > 0.5:
                    B[x][y][z] = 'delta_b'
                elif temp_CT > 0.5:
                    B[x][y][z] = 'CT'
                elif temp_const_cond > 0.5:
                    B[x][y][z] = 'delta_AND'
                else:
                    B[x][y][z] = None
    return A, B, row, name


def write_row_theta(state, row, theta_vars, linear_cancel, name):
    A = [[[0 for z in range(64)] for y in range(5)] for x in range(5)]  # Color values: 0-2
    B = [[[0 for z in range(64)] for y in range(5)] for x in range(5)]
    for x in range(5):
        for y in range(5):
            for z in range(64):
                A[x][y][z] = state[z][y][x]._get_type()

                temp_cond = get_value(state[z][y][x].cond)
                temp_delta_r = get_value(theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_r'])
                temp_delta_b = get_value(theta_vars[f"new_z{z}_y{y}_x{x}"]['delta_b'])
                if_linear_delta = get_value(linear_cancel[f"new_z{z}_y{y}_x{x}"])

                if temp_cond == 1 and temp_delta_r > 0.5 and temp_delta_b > 0.5:
                    B[x][y][z] = 'cond+delta_r+b'
                elif temp_cond == 1 and temp_delta_r > 0.5 and if_linear_delta > 0.5:
                    B[x][y][z] = 'cond+delta_r_linear'
                elif temp_delta_r > 0.5 and if_linear_delta > 0.5:
                    B[x][y][z] = 'delta_r_linear'
                elif temp_cond == 1 and temp_delta_r > 0.5:
                    B[x][y][z] = 'cond+delta_r'
                elif temp_cond == 1 and temp_delta_b > 0.5:
                    B[x][y][z] = 'cond+delta_b'
                elif temp_cond == 1:
                    B[x][y][z] = 'cond'
                elif temp_delta_r > 0.5 and temp_delta_b > 0.5:
                    B[x][y][z] = 'delta_r+b'
                elif temp_delta_r > 0.5:
                    B[x][y][z] = 'delta_r'
                elif temp_delta_b > 0.5:
                    B[x][y][z] = 'delta_b'
                else:
                    B[x][y][z] = None

    return A, B, row, name


def write_row_C(state, row, theta_vars, linear_cancel, name):
    A = [[0 for z in range(64)] for x in range(5)]  # Color values: 0-2
    B = [[0 for z in range(64)] for x in range(5)]
    for x in range(5):
        for z in range(64):
            A[x][z] = state[z][x]._get_type()
            cond = get_value(state[z][x].cond)

            temp_cond = get_value(state[z][x].cond)
            temp_delta_r = get_value(theta_vars[f"C_x{x}_z{z}"]['delta_r'])
            temp_delta_b = get_value(theta_vars[f"C_x{x}_z{z}"]['delta_b'])
            if_linear_delta = get_value(linear_cancel[f"C_x{x}_z{z}"])

            if temp_cond == 1 and temp_delta_r > 0.5 and temp_delta_b > 0.5:
                B[x][z] = 'cond+delta_r+b'
            elif temp_cond == 1 and temp_delta_r > 0.5 and if_linear_delta > 0.5:
                B[x][z] = 'cond+delta_r_linear'
            elif temp_delta_r > 0.5 and if_linear_delta > 0.5:
                B[x][z] = 'delta_r_linear'
            elif temp_cond == 1 and temp_delta_r > 0.5:
                B[x][z] = 'cond+delta_r'
            elif temp_cond == 1 and temp_delta_b > 0.5:
                B[x][z] = 'cond+delta_b'
            elif temp_cond == 1:
                B[x][z] = 'cond'
            elif temp_delta_r > 0.5 and temp_delta_b > 0.5:
                B[x][z] = 'delta_r+b'
            elif temp_delta_r > 0.5:
                B[x][z] = 'delta_r'
            elif temp_delta_b > 0.5:
                B[x][z] = 'delta_b'
            else:
                B[x][z] = None

    return A, B, row, name

def write_row_D(state, row, theta_vars, linear_cancel, name):
    A = [[0 for z in range(64)] for x in range(5)]  # Color values: 0-2
    B = [[0 for z in range(64)] for x in range(5)]
    for x in range(5):
        for z in range(64):
            A[x][z] = state[z][x]._get_type()

            temp_cond = get_value(state[z][x].cond)
            temp_delta_r = get_value(theta_vars[f"D_x{x}_z{z}"]['delta_r'])
            temp_delta_b = get_value(theta_vars[f"D_x{x}_z{z}"]['delta_b'])
            if_linear_delta = get_value(linear_cancel[f"D_x{x}_z{z}"])

            if temp_cond == 1 and temp_delta_r > 0.5 and temp_delta_b > 0.5:
                B[x][z] = 'cond+delta_r+b'
            elif temp_cond == 1 and temp_delta_r > 0.5 and if_linear_delta > 0.5:
                B[x][z] = 'cond+delta_r_linear'
            elif temp_delta_r > 0.5 and if_linear_delta > 0.5:
                B[x][z] = 'delta_r_linear'
            elif temp_cond == 1 and temp_delta_r > 0.5:
                B[x][z] = 'cond+delta_r'
            elif temp_cond == 1 and temp_delta_b > 0.5:
                B[x][z] = 'cond+delta_b'
            elif temp_cond == 1:
                B[x][z] = 'cond'
            elif temp_delta_r > 0.5 and temp_delta_b > 0.5:
                B[x][z] = 'delta_r+b'
            elif temp_delta_r > 0.5:
                B[x][z] = 'delta_r'
            elif temp_delta_b > 0.5:
                B[x][z] = 'delta_b'
            else:
                B[x][z] = None
    return A, B, row, name


def write_Ascon_P(state, slice_number, linear_cancel, row, vars, name):
    A = [[0 for z in range(64)] for x in range(5)]  # Color values: 0-2
    B = [[None for z in range(64)] for x in range(5)]
    for x in range(5):
        for z in range(slice_number):
            A[x][z] = state[z][x]._get_type()

            temp_cond = get_value(state[z][x].cond)
            temp_delta_r = get_value(vars[f"new_z{z}_x{x}"]['delta_r'])
            temp_delta_b = get_value(vars[f"new_z{z}_x{x}"]['delta_b'])
            if_linear_delta = get_value(linear_cancel[f"new_z{z}_x{x}"])

            if temp_cond == 1 and temp_delta_r > 0.5 and temp_delta_b > 0.5:
                B[x][z] = 'cond+delta_r+b'
            elif temp_cond == 1 and temp_delta_r > 0.5 and if_linear_delta > 0.5:
                B[x][z] = 'cond+delta_r_linear'
            elif temp_delta_r > 0.5 and if_linear_delta > 0.5:
                B[x][z] = 'delta_r_linear'
            elif temp_cond == 1 and temp_delta_r > 0.5:
                B[x][z] = 'cond+delta_r'
            elif temp_cond == 1 and temp_delta_b > 0.5:
                B[x][z] = 'cond+delta_b'
            elif temp_cond == 1:
                B[x][z] = 'cond'
            elif temp_delta_r > 0.5 and temp_delta_b > 0.5:
                B[x][z] = 'delta_r+b'
            elif temp_delta_r > 0.5:
                B[x][z] = 'delta_r'
            elif temp_delta_b > 0.5:
                B[x][z] = 'delta_b'
            else:
                B[x][z] = None

    return A, B, row, name

def write_Ascon_initial(state, slice_number, row, vars, name):
    A = [[0 for z in range(64)] for x in range(5)]  # Color values: 0-2
    B = [[None for z in range(64)] for x in range(5)]
    for x in range(5):
        for z in range(slice_number):
            A[x][z] = state[z][x]._get_type()

    return A, B, row, name

def write_Ascon_temp_s1(state, slice_number, linear_cancel, row, vars, name):
    A = [[0 for z in range(64)] for x in range(5)]  # Color values: 0-2
    B = [[0 for z in range(64)] for x in range(5)]
    for x in range(5):
        for z in range(slice_number):
            A[x][z] = state[z][x]._get_type()

            temp_cond = get_value(state[z][x].cond)
            temp_delta_r = get_value(vars[f"temp1_z{z}_x{x}"]['delta_r'])
            temp_delta_b = get_value(vars[f"temp1_z{z}_x{x}"]['delta_b'])
            if_linear_delta = get_value(linear_cancel[f"temp1_z{z}_x{x}"])

            if temp_cond == 1 and temp_delta_r > 0.5 and temp_delta_b > 0.5:
                B[x][z] = 'cond+delta_r+b'
            elif temp_cond == 1 and temp_delta_r > 0.5 and if_linear_delta > 0.5:
                B[x][z] = 'cond+delta_r_linear'
            elif temp_delta_r > 0.5 and if_linear_delta > 0.5:
                B[x][z] = 'delta_r_linear'
            elif temp_cond == 1 and temp_delta_r > 0.5:
                B[x][z] = 'cond+delta_r'
            elif temp_cond == 1 and temp_delta_b > 0.5:
                B[x][z] = 'cond+delta_b'
            elif temp_cond == 1:
                B[x][z] = 'cond'
            elif temp_delta_r > 0.5 and temp_delta_b > 0.5:
                B[x][z] = 'delta_r+b'
            elif temp_delta_r > 0.5:
                B[x][z] = 'delta_r'
            elif temp_delta_b > 0.5:
                B[x][z] = 'delta_b'
            else:
                B[x][z] = None
    return A, B, row, name

def write_Ascon_temp_s2(state, slice_number, linear_cancel_chi, row, vars, name):
    A = [[0 for z in range(64)] for x in range(5)]  # Color values: 0-2
    B = [[0 for z in range(64)] for x in range(5)]
    for x in range(5):
        for z in range(slice_number):
            A[x][z] = state[z][x]._get_type()
            temp_cond = get_value(state[z][x].cond)
            temp_delta_r = get_value(vars[f"temp2_z{z}_x{x}"]['delta_r'])
            temp_delta_b = get_value(vars[f"temp2_z{z}_x{x}"]['delta_b'])
            temp_CT = get_value(vars[f"and_z{z}_x{x}"]['CT'])
            temp_const_cond = get_value(vars[f"and_z{z}_x{x}"]['const_cond'])
            if linear_cancel_chi != None:
                if_linear_delta = get_value(linear_cancel_chi[f"temp2_z{z}_x{x}"])
            else:
                if_linear_delta = 0

            if temp_cond == 1 and temp_delta_r > 0.5 and temp_delta_b > 0.5:
                B[x][z] = 'cond+delta_r+b'
            elif temp_cond == 1 and temp_delta_r > 0.5 and if_linear_delta > 0.5:
                B[x][z] = 'cond+delta_r_linear'
            elif temp_delta_r > 0.5 and if_linear_delta > 0.5:
                B[x][z] = 'delta_r_linear'
            elif temp_cond == 1 and temp_delta_r > 0.5:
                B[x][z] = 'cond+delta_r'
            elif temp_cond == 1 and temp_delta_b > 0.5:
                B[x][z] = 'cond+delta_b'
            elif temp_cond == 1:
                B[x][z] = 'cond'
            elif temp_delta_r > 0.5 and temp_delta_b > 0.5:
                B[x][z] = 'delta_r+b'
            elif temp_delta_r > 0.5:
                B[x][z] = 'delta_r'
            elif temp_delta_b > 0.5:
                B[x][z] = 'delta_b'
            elif temp_CT > 0.5:
                B[x][z] = 'CT'
            elif temp_const_cond > 0.5:
                B[x][z] = 'delta_AND'
            else:
                B[x][z] = None
    return A, B, row, name