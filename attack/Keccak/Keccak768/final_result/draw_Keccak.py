from output.write_in_latex_Keccak import *
from SHA3_384_round_5_preimage_for_painting  import initial_state_output,intermediate_states_output


def line_delta(first_slice,last_slice,state):
    new_delta_r = []
    new_delta_b = []
    for z in range(first_slice, last_slice):
        for x in range(5):
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
        for y in range(5):
            for x in range(5):
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
                if state[1][x][y][z] == 'cond+delta_r':
                    new_delta_r.append((x, y, z, state[3]))
                if state[1][x][y][z] == 'cond+delta_b':
                    new_delta_b.append((x, y, z, state[3]))
    return new_delta_r,new_delta_b

latex_code = ''
row_num = 0
delta_r = []
delta_b = []
first_slice= 32
last_slice = 48
full_slice = 64

rho_box = [
    [0, 1, 62, 28, 27],
    [36, 44, 6, 55, 20],
    [3, 10, 43, 25, 39],
    [41, 45, 15, 21, 8],
    [18, 2, 61, 56, 14]
]

def rho_f(old_state):
    new_state = [[[0 for _ in range(5)] for _ in range(5)] for _ in range(full_slice)]
    for z in range(full_slice):
        for y in range(5):
            for x in range(5):
                new_state[z][y][x] = old_state[(z - rho_box[y][x]) % full_slice][y][x]
    return new_state


def pi_f(old_state):
    new_state = [[[0 for _ in range(5)] for _ in range(5)] for _ in range(full_slice)]
    for z in range(full_slice):
        for y in range(5):
            for x in range(5):
                new_state[z][y][x] = old_state[z][x][(x + 3 * y) % 5]
    return new_state
r = []
b = []
c = []
for z in range(first_slice,last_slice):
    for y in range(5):
        for x in range(5):
            if initial_state_output[0][x][y][z] == 'lr':
                r.append(z)
            elif initial_state_output[0][x][y][z] == 'lb':
                b.append(z)
            else:
                c.append(z)
latex_code += generate_tikz_code(initial_state_output[0], initial_state_output[1],if_index=True,add_bit=[len(r),len(b)], index_row=initial_state_output[2], name=initial_state_output[3],first_slice=first_slice, last_slice=last_slice)
#######
without_place = [[0 for y in range(5)] for z in range(full_slice)]
#######
for round_state_output in intermediate_states_output:
    C = round_state_output['C']
    new_delta_r, new_delta_b = line_delta(first_slice,last_slice,C)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b
    latex_code += generate_line_tikz_code(C[0], C[1],add_bit=add_bit, index_row=C[2], name=C[3],first_slice=first_slice, last_slice=last_slice)

    #######
    C_without_place = [0 for z in range(full_slice)]
    for z in range(full_slice):
        for y in range(5):
            if without_place[z][y] > 0.5:
                C_without_place[z] = 1
    latex_code += generate_line_zero_Sbox_tikz_code(C_without_place,index_row=C[2], first_slice=first_slice, last_slice=last_slice)
    #######

    D = round_state_output['D']
    new_delta_r, new_delta_b = line_delta(first_slice,last_slice,D)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b
    latex_code += generate_line_tikz_code(D[0], D[1],add_bit=add_bit,index_row=D[2], name=D[3],first_slice=first_slice, last_slice=last_slice)

    #######
    D_without_place = [0 for z in range(full_slice)]
    for z in range(full_slice):
        if C_without_place[z] > 0.5 or C_without_place[(z-1)%full_slice] > 0.5:
            D_without_place[z] = 1
    latex_code += generate_line_zero_Sbox_tikz_code(D_without_place, index_row=D[2], first_slice=first_slice, last_slice=last_slice)
    #######

    theta = round_state_output['theta']
    new_delta_r, new_delta_b = state_delta(first_slice,last_slice,theta)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b
    latex_code += generate_tikz_code(theta[0], theta[1],add_bit=add_bit, index_row=theta[2], name=theta[3],first_slice=first_slice, last_slice=last_slice)

    theta_without_place = [[0 for y in range(5)] for z in range(full_slice)]
    for z in range(full_slice):
        for y in range(5):
            if D_without_place[z] > 0.5 or without_place[z][y]>0.5:
                theta_without_place[z][y] = 1
    latex_code += generate_zero_Sbox_tikz_code(theta_without_place, index_row=theta[2], first_slice=first_slice, last_slice=last_slice)


    rho = round_state_output['rho']
    if rho==None:
        continue
    new_delta_r, new_delta_b = state_delta(first_slice,last_slice,rho)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b


    full_theta_without_place = [[[0 for x in range(5)] for y in range(5)] for z in range(full_slice)]
    for z in range(full_slice):
        for y in range(5):
            if theta_without_place[z][y] > 0.5:
                for x in range(5):
                    full_theta_without_place[z][y][x] = 1

    rho_without_place = rho_f(full_theta_without_place)
    latex_code += generate_tikz_code_without(rho[0], rho[1],rho_without_place,add_bit=add_bit, index_row=rho[2], name=rho[3],first_slice=first_slice, last_slice=last_slice)


    pi = round_state_output['pi']
    new_delta_r, new_delta_b = state_delta(first_slice,last_slice,pi)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b
    pi_without_place = pi_f(rho_without_place)
    latex_code += generate_tikz_code_without(pi[0], pi[1],pi_without_place,add_bit=add_bit, index_row=pi[2], name=pi[3],first_slice=first_slice, last_slice=last_slice)



    chi = round_state_output['chi']
    if chi==None:
        continue
    new_delta_r, new_delta_b = state_delta(first_slice,last_slice,chi)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b
    latex_code += generate_tikz_code(chi[0], chi[1],if_index=True,add_bit=add_bit, index_row=chi[2], name=chi[3],first_slice=first_slice, last_slice=last_slice)
    without_place = round_state_output['without_place']
    latex_code += generate_zero_Sbox_tikz_code(without_place, index_row=chi[2], first_slice=first_slice, last_slice=last_slice)
latex_code += last_generate_tikz_code(chi[0],chi[1],if_index=True,add_bit=add_bit, index_row=chi[2], name=chi[3],first_slice=first_slice, last_slice=last_slice)

with open(f"../tex/SHA3-384_round_5_preimage_{first_slice}-{last_slice}.tex", "w", encoding="utf-8") as f:
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