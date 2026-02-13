from new_code.latex.draw_latex_Xoodyak_X import *
from Xoodyak_round_3_preimage_for_painting import initial_state_output,intermediate_states_output

def rho_west_f(state):

    new_state = [[[None for _ in range(4)] for _ in range(3)] for _ in range(32)]

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


def rho_east_f(state):

    new_state = [[[None for _ in range(4)] for _ in range(3)] for _ in range(32)]

    shifts = [
        [0, 0],   # y=0: (x_shift, z_shift)
        [0, -1],  # y=1: (x_shift, z_shift)
        [-2, -8], # y=2: (x_shift, z_shift)
    ]

    for x in range(4):
        for y in range(3):
            for z in range(32):
                new_state[z][y][x] = state[(z + shifts[y][1]) % 32][y][(x + shifts[y][0]) % 4]

    return new_state

def line_delta(first_slice,last_slice,state):
    new_delta_r = []
    new_delta_b = []
    for z in range(first_slice, last_slice):
        for x in range(4):
            if state[1][x][z] == 'delta_r':
                new_delta_r.append((x,  z, state[3]))
            if state[1][x][z] == 'cond+delta_r':
                new_delta_r.append((x,  z, state[3]))
            if state[1][x][z] == 'cond+delta_r_linear':
                new_delta_r.append((x,  z, state[3]))
            if state[1][x][z] == 'delta_r_linear':
                new_delta_r.append((x,  z, state[3]))
            if state[1][x][z] == 'delta_b':
                new_delta_b.append((x,  z, state[3]))
            if state[1][x][z] == 'delta_r+b':
                new_delta_r.append((x,  z, state[3]))
                new_delta_b.append((x,  z, state[3]))
            if state[1][x][z] == 'cond+delta_r+b':
                new_delta_r.append((x, z, state[3]))
                new_delta_b.append((x,  z, state[3]))
            if state[1][x][z] == 'cond+delta_b':
                new_delta_b.append((x,  z, state[3]))
    return new_delta_r,new_delta_b
def state_delta(first_slice,last_slice,state):
    new_delta_r = []
    new_delta_b = []
    for z in range(first_slice, last_slice):
        for y in range(3):
            for x in range(4):
                if state[1][x][y][z] == 'delta_r':
                    new_delta_r.append((x, y, z, state[3]))
                if state[1][x][y][z] == 'cond+delta_r':
                    new_delta_r.append((x, y, z, state[3]))
                if state[1][x][y][z] == 'cond+delta_r_linear':
                    new_delta_r.append((x, y, z, state[3]))
                if state[1][x][y][z] == 'delta_r_linear':
                    new_delta_r.append((x, y, z, state[3]))
                if state[1][x][y][z] == 'delta_b':
                    new_delta_b.append((x, y, z, state[3]))
                if state[1][x][y][z] == 'delta_r+b':
                    new_delta_r.append((x, y, z, state[3]))
                    new_delta_b.append((x, y, z, state[3]))
                if state[1][x][y][z] == 'cond+delta_r+b':
                    new_delta_r.append((x, y, z, state[3]))
                    new_delta_b.append((x, y, z, state[3]))
                if state[1][x][y][z] == 'cond+delta_b':
                    new_delta_b.append((x, y, z, state[3]))
    return new_delta_r,new_delta_b
latex_code = ''
row_num = 0
delta_r = []
delta_b = []
first_slice= 0
last_slice = 32
r = []
b = []
c = []
for z in range(first_slice,last_slice):
    for y in range(3):
        for x in range(4):
            if initial_state_output[0][x][y][z] == 'lr':
                r.append(z)
            elif initial_state_output[0][x][y][z] == 'lb':
                b.append(z)
            else:
                c.append(z)
latex_code += generate_tikz_code(initial_state_output[0], initial_state_output[1],add_bit=[len(r),len(b)], index_row=initial_state_output[2], name=initial_state_output[3],first_slice=first_slice, last_slice=last_slice)
#######
rho_east_without = [[[0 for x in range(4)] for y in range(3)] for z in range(32)]
#######
for round_state_output in intermediate_states_output:
    C = round_state_output['C']
    new_delta_r, new_delta_b = line_delta(first_slice, last_slice, C)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b

    C_without_place = [[0 for x in range(4)] for z in range(32)]
    for z in range(32):
        for x in range(4):
            for y in range(3):
                if rho_east_without[z][y][x] > 0.5:
                    C_without_place[z][x] = 1
    latex_code += generate_line_tikz_code(C[0], C[1],C_without_place,add_bit=add_bit, index_row=C[2], name=C[3],first_slice=first_slice, last_slice=last_slice)


    D = round_state_output['D']
    new_delta_r, new_delta_b = line_delta(first_slice, last_slice, D)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b

    D_without_place = [[0 for x in range(4)] for z in range(32)]
    for z in range(32):
        for x in range(4):
            if C_without_place[(z - 5) % 32][(x - 1) % 4] > 0.5 or C_without_place[(z - 14) % 32][(x - 1) % 4] > 0.5:
                D_without_place[z][x] = 1
    latex_code += generate_line_tikz_code(D[0], D[1],D_without_place,add_bit=add_bit,index_row=D[2], name=D[3],first_slice=first_slice, last_slice=last_slice)


    theta = round_state_output['theta_state']
    new_delta_r, new_delta_b = state_delta(first_slice, last_slice, theta)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b

    theta_without_place = [[[0 for x in range(4)] for y in range(3)] for z in range(32)]
    for z in range(32):
        for x in range(4):
            for y in range(3):
                if D_without_place[z][x] > 0.5 or rho_east_without[z][y][x]>0.5:
                    theta_without_place[z][y][x] = 1
    latex_code += generate_tikz_code_without(theta[0], theta[1],theta_without_place,add_bit=add_bit, index_row=theta[2], name=theta[3],first_slice=first_slice, last_slice=last_slice)

    if 'rho_west_state' not in round_state_output:
        continue
    rho_west = round_state_output['rho_west_state']
    new_delta_r, new_delta_b = state_delta(first_slice, last_slice, rho_west)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b


    rho_west_without = rho_west_f(theta_without_place)
    latex_code += generate_tikz_code_without(rho_west[0], rho_west[1],rho_west_without,add_bit=add_bit, index_row=rho_west[2], name=rho_west[3],first_slice=first_slice, last_slice=last_slice)


    chi = round_state_output['chi_state']
    new_delta_r, new_delta_b = state_delta(first_slice, last_slice, chi)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b
    latex_code += generate_tikz_code(chi[0], chi[1], add_bit=add_bit, index_row=chi[2], name=chi[3], first_slice=first_slice, last_slice=last_slice)
    without_place = round_state_output['without_place']
    latex_code += generate_zero_Sbox_tikz_code(without_place, index_row=chi[2], first_slice=first_slice, last_slice=last_slice)

    full_chi_without_place = [[[0 for x in range(4)] for y in range(3)] for z in range(32)]
    for z in range(32):
        for x in range(4):
            if without_place[z][x] > 0.5:
                for y in range(3):
                    full_chi_without_place[z][y][x] = 1

    rho_east_without = rho_east_f(full_chi_without_place)
    rho_east = round_state_output['rho_east_state']
    new_delta_r, new_delta_b = state_delta(first_slice, last_slice, rho_east)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b
    latex_code += generate_tikz_code_without(rho_east[0], rho_east[1],rho_east_without, add_bit=add_bit, index_row=rho_east[2], name=rho_east[3], first_slice=first_slice, last_slice=last_slice)


with open(f"../tex/Xoodyak_round_3_preimage_{first_slice}-{last_slice}.tex", "w", encoding="utf-8") as f:
    f.write("""\\documentclass{standalone}\n 
    \\usepackage{tikz}  % Must import tikz package\n
    \\usepackage{color}\n
    \\definecolor{myblue}{HTML}{5555FF}
    \\definecolor{mygray}{HTML}{E0E0E0}
    \\begin{document}\n""")
    f.write("\\begin{tikzpicture}")
    f.write(latex_code)
    f.write("\\end{tikzpicture}")
    f.write("\n\\end{document}")