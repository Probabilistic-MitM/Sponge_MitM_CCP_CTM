from output.write_in_latex_Ascon import generate_line_tikz_code
from attack.Experiment.search_result.Ascon_XOF_round_3_preimage import *

def line_delta(first_slice, last_slice, state):
    new_delta_r = []
    new_delta_b = []
    for z in range(first_slice, last_slice):
        for x in range(5):
            if state[1][x][z] == 'delta_r':
                new_delta_r.append((x, z, state[3]))

            if state[1][x][z] == 'cond+delta_r':
                new_delta_r.append((x, z, state[3]))

            if state[1][x][z] == 'cond+delta_r_linear':
                new_delta_r.append((x, z, state[3]))

            if state[1][x][z] == 'delta_r_linear':
                new_delta_r.append((x, z, state[3]))

            if state[1][x][z] == 'delta_b':
                new_delta_b.append((x, z, state[3]))
            if state[1][x][z] == 'delta_r+b':
                new_delta_r.append((x, z, state[3]))
                new_delta_b.append((x, z, state[3]))
            if state[1][x][z] == 'cond+delta_r+b':
                new_delta_r.append((x, z, state[3]))
                new_delta_b.append((x, z, state[3]))
            if state[1][x][z] == 'cond+delta_b':
                new_delta_b.append((x, z, state[3]))
    return new_delta_r, new_delta_b

delta_r = []
delta_b = []
r = []
b = []
c = []
latex_code = ''
row_num = 0
last_slice = 32
for y in range(32):
    if initial_state_output[0][0][y] == 'lr':
        r.append(y)
    elif initial_state_output[0][0][y] == 'lb':
        b.append(y)
    else:
        c.append(y)
latex_code += generate_line_tikz_code(initial_state_output[0], initial_state_output[1], add_bit=[len(r), len(b)], slice_number=last_slice, index_row=initial_state_output[2], name=initial_state_output[3], first_slice=0, last_slice=last_slice)

for round_state_output in intermediate_states_output:
    if round_state_output['round_num'] > 0:
        temp = round_state_output['temp_state_1']
        one_point = []
        for y in range(32):
            for x in range(5):
                if temp[1][x][y] == 'cond':
                    one_point.append((x, y))
        print("one_point=", one_point)
        new_delta_r, new_delta_b = line_delta(0, 32, temp)
        add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
        delta_r += new_delta_r
        delta_b += new_delta_b
        latex_code += generate_line_tikz_code(temp[0], temp[1], add_bit=add_bit, slice_number=last_slice, index_row=temp[2], name=temp[3], first_slice=0, last_slice=last_slice)

        temp = round_state_output['temp_state_2']
        new_delta_r, new_delta_b = line_delta(0, 32, temp)
        add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
        delta_r += new_delta_r
        delta_b += new_delta_b
        latex_code += generate_line_tikz_code(temp[0], temp[1], add_bit=add_bit, slice_number=last_slice, index_row=temp[2], name=temp[3], first_slice=0, last_slice=last_slice)

        temp = round_state_output['ps_state']
        new_delta_r, new_delta_b = line_delta(0, 32, temp)
        add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
        delta_r += new_delta_r
        delta_b += new_delta_b
        latex_code += generate_line_tikz_code(temp[0], temp[1], add_bit=add_bit, slice_number=last_slice, index_row=temp[2], name=temp[3], first_slice=0, last_slice=last_slice)
    else:
        temp = round_state_output['ps_state']
        new_delta_r, new_delta_b = line_delta(0, 32, temp)
        add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
        delta_r += new_delta_r
        delta_b += new_delta_b
        latex_code += generate_line_tikz_code(temp[0], temp[1], add_bit=add_bit, slice_number=last_slice, index_row=temp[2], name=temp[3], first_slice=0, last_slice=last_slice)
        condition_in_capacity = [[] for i in range(32)]
        for y in range(32):
            if (temp[0][0][y], temp[0][1][y], temp[0][2][y], temp[0][3][y], temp[0][4][y]) == ('c', 'lr', 'c', 'c', 'lr'):
                condition_in_capacity[y] += [(1, 1), (3, 4, 1)]
            elif (temp[0][0][y], temp[0][1][y], temp[0][2][y], temp[0][3][y], temp[0][4][y]) == ('lr', 'lr', 'c', 'c', 'c'):
                condition_in_capacity[y] += [(1, 0), (3, 4, 1)]
            elif (temp[0][0][y], temp[0][1][y], temp[0][2][y], temp[0][3][y], temp[0][4][y]) == ('c', 'lr', 'c', 'lr', 'lr'):
                condition_in_capacity[y] += [(1, 1)]
            elif (temp[0][0][y], temp[0][1][y], temp[0][2][y], temp[0][3][y], temp[0][4][y]) == ('lr', 'lr', 'c', 'lr', 'c'):
                condition_in_capacity[y] += [(1, 0)]
            elif (temp[0][0][y], temp[0][1][y], temp[0][2][y], temp[0][3][y], temp[0][4][y]) == ('lr', 'lr', 'c', 'c', 'lr'):
                condition_in_capacity[y] += [(3, 4, 1)]
            elif (temp[0][0][y], temp[0][1][y], temp[0][2][y], temp[0][3][y], temp[0][4][y]) == ('lb', 'lb', 'c', 'c', 'c'):
                condition_in_capacity[y] += [(1, 0), (3, 4, 1)]
            elif (temp[0][0][y], temp[0][1][y], temp[0][2][y], temp[0][3][y], temp[0][4][y]) == ('c', 'lb', 'c', 'c', 'lb'):
                condition_in_capacity[y] += [(1, 1), (3, 4, 1)]
        print("pre_condition_to_MILP=", condition_in_capacity)

    temp = round_state_output['pl_state']
    new_delta_r, new_delta_b = line_delta(0, 32, temp)
    add_bit = [-1 * len(new_delta_r), -1 * len(new_delta_b)]
    delta_r += new_delta_r
    delta_b += new_delta_b
    latex_code += generate_line_tikz_code(temp[0], temp[1], add_bit=add_bit, slice_number=last_slice, index_row=temp[2], name=temp[3], first_slice=0, last_slice=last_slice)

condition_number = 0

condition_list10 = []
condition_list11 = []
condition_list20 = []
condition_list21 = []
for i in range(len(condition_in_capacity)):
    for condition in condition_in_capacity[i]:
        if len(condition) == 2:
            if condition[1] == 0:
                condition_list10.append(i)
            else:
                condition_list11.append(i)
        elif len(condition) == 3:
            if condition[2] == 0:
                condition_list20.append(i)
            else:
                condition_list21.append(i)
print(condition_list10)
print(condition_list11)
print(condition_list20)
print(condition_list21)
print("condition_number=", condition_number)

probability = []
determine = []

CT = []
for y in range(32):
    determine_flag = 1
    probability_flag = 1
    for x in range(5):
        if round_state_output['temp_state_2'][1][x][y] == 'CT':
            CT.append((x, y))
        if temp[0][x][y] == 'u':
            determine_flag = 0
        if (temp[0][1][y], temp[0][2][y]) in [('ug', 'ug'), ('ug', 'lg'), ('lg', 'ug')]:
            determine_flag = 0

    for x in [3, 4]:
        if temp[0][x][y] == 'u':
            probability_flag = 0
    if determine_flag == 1:
        determine.append(y)
        print(f"{{P_S}}^{(2)}_{{\\{{4,{y}\\}}}}{{P_S}}^{(2)}_{{\\{{1,{y}\\}}}} \\oplus {{P_S}}^{(2)}_{{\\{{3,{y}\\}}}} \\oplus {{P_S}}^{(2)}_{{\\{{2,{y}\\}}}}{{P_S}}^{(2)}_{{\\{{1,{y}\\}}}} \\oplus {{P_S}}^{(2)}_{{\\{{2,{y}\\}}}} \\oplus {{P_S}}^{(2)}_{{\\{{1,{y}\\}}}}{{P_S}}^{(2)}_{{\\{{0,{y}\\}}}} \\oplus {{P_S}}^{(2)}_{{\\{{1,{y}\\}}}} \\oplus {{P_S}}^{(2)}_{{\\{{0,{y}\\}}}} = {{P_L}}^{(2)}_{{\\{{0,{y}\\}}}}\\\\[2mm]")
    if probability_flag == 1 and determine_flag == 0:
        probability.append(y)
        print(f"{{P_S}}^{(2)}_{{\\{{3,{y}\\}}}} \\oplus {{P_S}}^{(2)}_{{\\{{4,{y}\\}}}} \\oplus 1 = {{P_L}}^{(2)}_{{\\{{0,{y}\\}}}}\\\\[2mm]")

print("r_place=", r)
print("b_place=", b)
print("c_place=", c)
print("determine=", determine)
print("probability=", probability)
print("delta_r=", delta_r)
print("CT=", CT)

Ascon_state = [[[] for x in range(5)] for y in range(32)]
for x, y in CT:
    Ascon_state[y][x].append(f"{x},{y}")
Ascon_state_new = [[[] for x in range(5)] for y in range(32)]
for y in range(32):
    Ascon_state_new[y][0] = Ascon_state[y][0] + Ascon_state[y][4]
    Ascon_state_new[y][1] = Ascon_state[y][0] + Ascon_state[y][1]
    Ascon_state_new[y][2] = Ascon_state[y][2]
    Ascon_state_new[y][3] = Ascon_state[y][2] + Ascon_state[y][3]
    Ascon_state_new[y][4] = Ascon_state[y][4]

def P_L_list(old_state):
    new_state = [[0 for _ in range(5)] for _ in range(32)]

    for k in range(32):
        new_state[k][0] = old_state[k][0] + old_state[(k + 19) % 32][0] + old_state[(k + 28) % 32][0]
        new_state[k][1] = old_state[k][1] + old_state[(k + 61) % 32][1] + old_state[(k + 39) % 32][1]
        new_state[k][2] = old_state[k][2] + old_state[(k + 1) % 32][2] + old_state[(k + 6) % 32][2]
        new_state[k][3] = old_state[k][3] + old_state[(k + 10) % 32][3] + old_state[(k + 17) % 32][3]
        new_state[k][4] = old_state[k][4] + old_state[(k + 7) % 32][4] + old_state[(k + 41) % 32][4]

    return new_state

Ascon_state = P_L_list(Ascon_state_new)
print("Cross terms in deterministic matching")
for y in range(32):
    for x in range(5):
        if Ascon_state[y][x] != [] and (y in determine):
            print([x, y, Ascon_state[y][x]])
print("Cross terms in probabilistic matching")
for y in probability:
    if Ascon_state[y][3] + Ascon_state[y][4] != []:
        print([y, Ascon_state[y][3] + Ascon_state[y][4]])

with open("Experiment-Ascon_XOF-round-3-pic.tex", "w", encoding="utf-8") as f:
    f.write("""\\documentclass{standalone}\n
    \\usepackage{tikz}  % must import tikz package\n
    \\usepackage{color}\n
    \\definecolor{myblue}{HTML}{5555FF}
    \\begin{document}\n""")
    f.write("\\begin{tikzpicture}")
    f.write(latex_code)
    f.write("\\end{tikzpicture}")
    f.write("\n\\end{document}")