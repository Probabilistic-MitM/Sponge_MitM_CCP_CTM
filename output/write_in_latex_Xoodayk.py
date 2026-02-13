slice_number = 32

def generate_zero_Sbox_tikz_code(A, block_size=0.2, h_spacing=0.2, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0):
    line_width = "0.6pt"
    frame_width = "1.0pt"

    latex_code = []

    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (4 * block_size + h_spacing)
        y_offset = -(row) * (3 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        for x in range(4):
            start_x = x * block_size
            start_y = 0
            end_x = (x + 1) * block_size
            end_y = -3 * block_size

            if A[z][x] > 0.5:
                fill_color = 'mygray'
                fill_cmd = f"    \\filldraw[fill={fill_color}, draw=black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(fill_cmd)

        latex_code.append("  \\end{scope}")

        # Label z value below the subfigure
        label_x = x_offset + 2 * block_size
        label_y = y_offset - 3 * block_size - 0.2
        label_cmd = f"  \\node at ({label_x:.2f}, {label_y:.2f}) {{\\small$z={z + first_slice}$}};"
        latex_code.append(label_cmd)

    return "\n".join(latex_code)


def generate_tikz_code(A, B, add_bit, block_size=0.2, h_spacing=0.2, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0, if_index=False, name=''):
    """
    Generate TikZ code for LaTeX, drawing 32 Xoodyak state slices (4 columns, 3 rows).
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

    label_cmd = f"  \\node[anchor=east] at ({- 0.5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 1.5 * block_size:.2f}) {{{name}}};"
    latex_code.append(label_cmd)

    if add_bit[0] > 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 1.5 * block_size:.2f}) {{\\tiny $+{add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 1 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 2 * block_size:.2f});"
        latex_code.append(red_add)
    elif add_bit[0] < 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 1.5 * block_size:.2f}) {{\\tiny${add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 1 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 2 * block_size:.2f});"
        latex_code.append(red_add)
    if add_bit[1] > 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 5.5 * block_size :.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 1.5 * block_size:.2f}) {{\\tiny$+{add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 1 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 2 * block_size:.2f});"
        latex_code.append(blue_add)
    elif add_bit[1] < 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 5.5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 1.5 * block_size:.2f}) {{\\tiny ${add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 1 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 2 * block_size:.2f});"
        latex_code.append(blue_add)

    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (4 * block_size + h_spacing)
        y_offset = -(row) * (3 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        for x in range(4):
            for y in range(3):
                start_x = x * block_size
                start_y = -y * block_size
                end_x = (x + 1) * block_size
                end_y = -(y + 1) * block_size

                color_val = A[x][y][(z + first_slice) % slice_number]
                fill_color = color_map.get(color_val, 'white')
                fill_cmd = f"    \\filldraw[fill={fill_color}, draw=black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(fill_cmd)
                if color_val in ['ub', 'ur', 'ug']:
                    Xframe = f"\\draw[black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n\\draw[black, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});"
                    latex_code.append(Xframe)

        for x in range(4):
            for y in range(3):
                start_x = x * block_size
                start_y = -y * block_size
                end_x = (x + 1) * block_size
                end_y = -(y + 1) * block_size

                frame_key = B[x][y][(z + first_slice) % slice_number]
                if frame_key is not None and frame_key[-6:] == 'linear':
                    frame_cmd = f"    \\draw[pink, line width={frame_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                    latex_code.append(frame_cmd)
                    if frame_key[:4] == 'cond':
                        Xframe = f"\\draw[yellow, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n\\draw[yellow, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});"
                        latex_code.append(Xframe)
                elif frame_key is not None and frame_key != 'delta_AND' and frame_key[:4] != 'cond':
                    frame_cmd = f"    \\draw[{frame[frame_key]}, line width={frame_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                    latex_code.append(frame_cmd)
                elif frame_key == 'delta_AND' and frame_key[:4] != 'cond':
                    zero = f'\\draw ({start_x:.2f}-0.03, {start_y:.2f}+0.01) node [anchor=north west][inner sep=0.7pt][font=\\scriptsize] {{$Z$}};\n'
                    latex_code.append(zero)
                elif frame_key is not None and frame_key[:4] == 'cond':
                    if frame[frame_key] == 'black':
                        frame_width = "0.6pt"
                    frame_cmd = f"    \\draw[{frame[frame_key]}, line width={frame_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                    latex_code.append(frame_cmd)
                    Xframe = f"\\draw[yellow, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n\\draw[yellow, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});"
                    latex_code.append(Xframe)
                    frame_width = "1.0pt"

        latex_code.append("  \\end{scope}")
        if if_index:
            label_x = x_offset + 2 * block_size
            label_y = y_offset - 3 * block_size - 0.2
            label_cmd = f"  \\node at ({label_x:.2f}, {label_y:.2f}) {{\\tiny$z={z + first_slice}$}};"
            latex_code.append(label_cmd)

    return "\n".join(latex_code)


def generate_line_tikz_code(A, B, add_bit, block_size=0.2, h_spacing=0.2, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0, name=''):
    """
    Generate TikZ code for LaTeX, drawing only row y=0 (4 squares) for each slice.
    Used for linear layer visualisation of Xoodyak.
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
        'q': 'green'
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

    label_cmd = f"  \\node[anchor=east] at ({- 0.5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 0.5 * block_size:.2f}) {{{name}}};"
    latex_code.append(label_cmd)

    if add_bit[0] > 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 0.5 * block_size:.2f}) {{\\tiny $+{add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing):.2f}) rectangle ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - block_size:.2f});"
        latex_code.append(red_add)
    elif add_bit[0] < 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 0.5 * block_size:.2f}) {{\\tiny${add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing):.2f}) rectangle ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - block_size:.2f});"
        latex_code.append(red_add)
    if add_bit[1] > 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 5.5 * block_size :.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 0.5 * block_size:.2f}) {{\\tiny$+{add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing):.2f}) rectangle ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - block_size:.2f});"
        latex_code.append(blue_add)
    elif add_bit[1] < 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 5.5 * block_size :.2f}, {-1 * index_row * (3 * block_size + v_spacing) - 0.5 * block_size:.2f}) {{\\tiny ${add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing):.2f}) rectangle ({(last_slice - first_slice) * (4 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (3 * block_size + v_spacing) - block_size:.2f});"
        latex_code.append(blue_add)

    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (4 * block_size + h_spacing)
        y_offset = -(row) * (3 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        for x in range(4):
            start_x = x * block_size
            start_y = 0
            end_x = (x + 1) * block_size
            end_y = -(0 + 1) * block_size

            color_val = A[x][(z + first_slice) % slice_number]
            fill_color = color_map.get(color_val, 'white')
            fill_cmd = f"    \\filldraw[fill={fill_color}, draw=black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
            latex_code.append(fill_cmd)
            if color_val in ['ub', 'ur', 'ug']:
                Xframe = f"\\draw[black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n\\draw[black, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});"
                latex_code.append(Xframe)

        for x in range(4):
            start_x = x * block_size
            start_y = 0
            end_x = (x + 1) * block_size
            end_y = -(0 + 1) * block_size

            frame_key = B[x][(z + first_slice) % slice_number]
            if frame_key is not None and frame_key[-6:] == 'linear':
                frame_cmd = f"    \\draw[pink, line width={frame_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(frame_cmd)
                if frame_key[:4] == 'cond':
                    Xframe = f"\\draw[yellow, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n\\draw[yellow, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});"
                    latex_code.append(Xframe)
            elif frame_key is not None and frame[frame_key] != 'zero' and frame_key[:4] != 'cond':
                frame_cmd = f"    \\draw[{frame[frame_key]}, line width={frame_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(frame_cmd)
            elif frame_key == 'delta_AND' and frame_key[:4] != 'cond':
                zero = f'\\draw ({start_x:.2f}-0.03, {start_y:.2f}+0.01) node [anchor=north west][inner sep=0.7pt][font=\\scriptsize] {{$Z$}};\n'
                latex_code.append(zero)
            elif frame_key is not None and frame_key[:4] == 'cond':
                if frame[frame_key] == 'black':
                    frame_width = "0.6pt"
                frame_cmd = f"    \\draw[{frame[frame_key]}, line width={frame_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(frame_cmd)
                Xframe = f"\\draw[yellow, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n\\draw[yellow, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});"
                latex_code.append(Xframe)
                frame_width = "1.0pt"

        latex_code.append("  \\end{scope}")

    return "\n".join(latex_code)