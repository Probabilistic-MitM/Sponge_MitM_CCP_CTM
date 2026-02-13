def generate_line_tikz_code(A, B, add_bit, slice_number, block_size=0.2, h_spacing=0.5, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0, name=''):
    """
    Generate TikZ code for LaTeX, drawing a single column (x=0) of 5 squares for each slice.
    Used for visualising the linear layer of Ascon.
    """
    color_map = {
        'lr': 'red',
        'r': 'red',
        'ur': 'red',
        'b': 'myblue',
        'lb': 'myblue',
        'ub': 'myblue',
        'lg': 'green',
        'ug': 'green',
        'c': 'gray',
        'u': 'white',
        'q': 'green',
        'eq': 'myyellow'
    }
    frame = {
        'delta_r': 'red',
        'delta_b': 'myblue',
        'delta_r+b': 'green',
        'CT': 'orange',
        'delta_r_linear': 'pink',
        'cond': 'black',
        'delta_AND': 'zero',
        'cond+delta_r+b': 'green',
        'cond+delta_r': 'red',
        'cond+delta_r_linear': 'pink',
        'cond+delta_b': 'myblue',
        None: None
    }

    line_width = "0.6pt"
    frame_width = "1.0pt"
    latex_code = []

    label_cmd = f"  \\node[anchor=east] at ({- 1 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{{name}}};"
    latex_code.append(label_cmd)

    if add_bit[0] > 0:
        red_add = f"  \\node at ({(last_slice - first_slice) * (h_spacing * 0.6) + block_size - 0.3 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny +{add_bit[0]}}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (h_spacing * 0.6) + 2 * block_size - 0.2 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (h_spacing * 0.6) + 3 * block_size - 0.2 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(red_add)
    elif add_bit[0] < 0:
        red_add = f"  \\node at ({(last_slice - first_slice) * (h_spacing * 0.6) + block_size - 0.3 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny{add_bit[0]}}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (h_spacing * 0.6) + 2 * block_size - 0.2 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (h_spacing * 0.6) + 3 * block_size - 0.2 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(red_add)
    if add_bit[1] > 0:
        blue_add = f"  \\node at ({(last_slice - first_slice) * (h_spacing * 0.6) + 4 * block_size - 0.1 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny+{add_bit[1]}}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (h_spacing * 0.6) + 5 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (h_spacing * 0.6) + 6 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(blue_add)
    elif add_bit[1] < 0:
        blue_add = f"  \\node at ({(last_slice - first_slice) * (h_spacing * 0.6) + 4 * block_size - 0.1 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny {add_bit[1]}}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (h_spacing * 0.6) + 5 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (h_spacing * 0.6) + 6 * block_size:.2f}, {-1 * index_row * (16 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(blue_add)

    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (h_spacing * 0.6)
        y_offset = -(row) * (16 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        for x in range(5):
            start_x = 0
            start_y = -x * block_size
            end_x = (0 + 1) * block_size
            end_y = -(x + 1) * block_size

            color_val = A[x][z]
            fill_color = color_map.get(color_val, 'white')
            fill_cmd = f"    \\filldraw[fill={fill_color}, draw=black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
            latex_code.append(fill_cmd)
            if color_val in ['ub', 'ur', 'ug']:
                Xframe = f"\\draw[black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n\\draw[black, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});"
                latex_code.append(Xframe)

        for x in range(5):
            start_x = 0
            start_y = -x * block_size
            end_x = (0 + 1) * block_size
            end_y = -(x + 1) * block_size

            frame_key = B[x][(z + first_slice) % slice_number]
            if frame_key is None:
                continue
            elif frame_key[-6:] == 'linear':
                frame_cmd = f"    \\draw[pink, line width={frame_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(frame_cmd)
                if frame_key[:4] == 'cond':
                    Xframe = f"\\draw[yellow, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n\\draw[yellow, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});"
                    latex_code.append(Xframe)
            elif frame_key != 'delta_AND' and frame_key[:4] != 'cond':
                frame_cmd = f"    \\draw[{frame[frame_key]}, line width={frame_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(frame_cmd)
            elif frame_key == 'delta_AND' and frame_key[:4] != 'cond':
                zero = f'\\draw ({start_x:.2f}-0.03, {start_y:.2f}+0.01) node [anchor=north west][inner sep=0.7pt][font=\\scriptsize] {{$Z$}};\n'
                latex_code.append(zero)
            elif frame_key[:4] == 'cond':
                if frame[frame_key] == 'black':
                    frame_width = "0.6pt"
                frame_cmd = f"    \\draw[{frame[frame_key]}, line width={frame_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(frame_cmd)
                Xframe = f"\\draw[yellow, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n\\draw[yellow, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});"
                latex_code.append(Xframe)
                frame_width = "1.0pt"

        latex_code.append("  \\end{scope}")

    return "\n".join(latex_code)


def generate_zero_Sbox_line_tikz_code(A, block_size=0.2, h_spacing=0.5, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0, name=''):
    """
    Generate TikZ code for the zero‑difference S‑box pattern (Ascon).
    Fills cells where A[z][x] > 0.5 with gray, and draws black frames around neighbours that are zero.
    """
    line_width = "0.6pt"
    latex_code = []

    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (h_spacing * 0.6)
        y_offset = -(row) * (16 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        for x in range(5):
            start_x = 0
            start_y = -x * block_size
            end_x = (0 + 1) * block_size
            end_y = -(x + 1) * block_size

            if A[z][x] > 0.5:
                fill_color = "mygray"
                fill_cmd = f"    \\filldraw[fill={fill_color}, draw={fill_color}, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(fill_cmd)
                for x0 in [(x - 1) % 5, (x + 1) % 5]:
                    if A[z][x0] < 0.5:
                        start_x = 0
                        start_y = -x0 * block_size
                        end_x = (0 + 1) * block_size
                        end_y = -(x0 + 1) * block_size
                        Xframe = f"\\draw[black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});\\draw[black, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\\draw[black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({start_x:.2f}, {end_y:.2f});\\draw[black, line width={line_width}] ({end_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n"
                        latex_code.append(Xframe)

        latex_code.append("  \\end{scope}")

    return "\n".join(latex_code)


def last_generate_zero_Sbox_line_tikz_code(A, block_size=0.2, h_spacing=0.5, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0, name=''):
    """
    Generate TikZ code for the final zero‑difference S‑box pattern (Ascon).
    Similar to generate_zero_Sbox_line_tikz_code, but uses 'u' as the condition for gray fill.
    """
    line_width = "0.6pt"
    latex_code = []

    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (h_spacing * 0.6)
        y_offset = -(row) * (16 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        for x in range(5):
            start_x = 0
            start_y = -x * block_size
            end_x = (0 + 1) * block_size
            end_y = -(x + 1) * block_size

            if A[x][z] == 'u':
                fill_color = "mygray"
                fill_cmd = f"    \\filldraw[fill={fill_color}, draw={fill_color}, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(fill_cmd)
                for x0 in [(x - 1) % 5, (x + 1) % 5]:
                    if A[x0][z] != 'u':
                        start_x = 0
                        start_y = -x0 * block_size
                        end_x = (0 + 1) * block_size
                        end_y = -(x0 + 1) * block_size
                        Xframe = f"\\draw[black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});\\draw[black, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\\draw[black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({start_x:.2f}, {end_y:.2f});\\draw[black, line width={line_width}] ({end_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n"
                        latex_code.append(Xframe)

        latex_code.append("  \\end{scope}")

    return "\n".join(latex_code)