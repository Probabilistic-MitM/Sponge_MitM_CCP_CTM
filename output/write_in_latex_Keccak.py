slice_number = 64

def generate_zero_Sbox_tikz_code(A, block_size=0.2, h_spacing=0.2, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0):
    line_width = "0.6pt"
    frame_width = "1.0pt"

    latex_code = []
    # Begin TikZ environment

    # Iterate over each z value (0..31, total 32 slices)
    for z in range(last_slice - first_slice):
        row = index_row          # row index of current subfigure (starting from 0)
        col = z                 # column index of current subfigure

        # Compute shift offset for this subfigure
        x_offset = (col) * (5 * block_size + h_spacing)   # horizontal shift
        y_offset = -(row) * (5 * block_size + v_spacing)  # vertical shift (negative because TikZ y-axis points up)

        # Begin scope for the subfigure
        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        # Loop over x (0..4) and y (0..4)
        for y in range(5):
            # Compute rectangle coordinates (TikZ y increases downward)
            start_x = 0
            start_y = -y * block_size     # y=0 at top, y=4 at bottom
            end_x = 5 * block_size
            end_y = -(y + 1) * block_size

            if A[(z + first_slice) % slice_number][y] > 0.5:
                fill_color = "mygray"
                fill_cmd = f"    \\filldraw[fill={fill_color}, draw={fill_color}, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
                latex_code.append(fill_cmd)
                # Draw frame around neighboring empty cells
                for y0 in [(y - 1) % 5, (y + 1) % 5]:
                    if A[(z + first_slice) % slice_number][y0] < 0.5:
                        start_x = 0
                        start_y = -y0 * block_size
                        end_x = 5 * block_size
                        end_y = -(y0 + 1) * block_size
                        Xframe = f"\\draw[black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {start_y:.2f});\\draw[black, line width={line_width}] ({start_x:.2f}, {end_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\\draw[black, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) -- ({start_x:.2f}, {end_y:.2f});\\draw[black, line width={line_width}] ({end_x:.2f}, {start_y:.2f}) -- ({end_x:.2f}, {end_y:.2f});\n"
                        latex_code.append(Xframe)

        # End scope for the subfigure
        latex_code.append("  \\end{scope}")

    # Return concatenated LaTeX code
    return "\n".join(latex_code)


def generate_line_zero_Sbox_tikz_code(A, block_size=0.2, h_spacing=0.2, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0):
    line_width = "0.6pt"
    frame_width = "1.0pt"

    latex_code = []
    # Begin TikZ environment

    # Iterate over each z value
    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (5 * block_size + h_spacing)
        y_offset = -(row) * (5 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        # Only row y=0 is drawn
        start_x = 0
        start_y = 0
        end_x = (4 + 1) * block_size
        end_y = -(0 + 1) * block_size

        if A[(z + first_slice)] > 0.5:
            fill_color = "mygray"
            fill_cmd = f"\\filldraw[fill={fill_color}, draw={fill_color}, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
            latex_code.append(fill_cmd)

        latex_code.append("  \\end{scope}")

    return "\n".join(latex_code)


def generate_tikz_code(A, B, add_bit, block_size=0.2, h_spacing=0.2, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0, if_index=False, name=''):
    """
    Generate TikZ code for LaTeX, drawing 32 5×5 grids (z from 0 to 31).

    Parameters:
        A: 3D list of shape (5,5,64), storing color codes (e.g., 'r','b','g','u', etc.)
        B: 3D list of shape (5,5,64), storing frame types (e.g., 'delta_r', 'cond', etc.)
        add_bit: tuple/list of two ints, showing the number of added red/blue bits (positive/negative)
        block_size: side length of each square (cm)
        h_spacing: horizontal gap between subfigures (cm)
        v_spacing: vertical gap between subfigures (cm)
        first_slice, last_slice: range of slices to draw (inclusive of first, exclusive of last)
        index_row: row number of this group in the overall figure
        if_index: whether to print z label below each subfigure
        name: label placed to the left of the group
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
        'delta_r': 'red',               # red cancellation
        'delta_b': 'myblue',            # blue cancellation
        'delta_r+b': 'green',           # both red and blue cancellation
        'CT': 'orange',              # CTratic term
        'delta_r_linear': 'pink',
        'cond': 'black',               # conditional constant
        'delta_AND': 'zero',           # forced zero via conditional constant
        'cond+delta_r+b': 'green',
        'cond+delta_r': 'red',
        'cond+delta_r_linear': 'pink',
        'cond+delta_b': 'myblue',
        None: None
    }

    line_width = "0.6pt"
    frame_width = "1.0pt"

    latex_code = []
    # Begin TikZ environment

    # Group label
    label_cmd = f"  \\node at ({- 1.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{{name}}};"
    latex_code.append(label_cmd)

    # Legend: red added bit
    if add_bit[0] > 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny $+{add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(red_add)
    elif add_bit[0] < 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny${add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(red_add)
    # Legend: blue added bit
    if add_bit[1] > 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5.5 * block_size :.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny$+{add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(blue_add)
    elif add_bit[1] < 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny ${add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(blue_add)

    # Iterate over slices
    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (5 * block_size + h_spacing)
        y_offset = -(row) * (5 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        # Draw each 5x5 cell
        for x in range(5):
            for y in range(5):
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

        # Draw frames on top of cells
        for x in range(5):
            for y in range(5):
                start_x = x * block_size
                start_y = -y * block_size
                end_x = (x + 1) * block_size
                end_y = -(y + 1) * block_size

                frame_key = B[x][y][(z + first_slice) % slice_number]
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
        if if_index:
            label_x = x_offset + 2.5 * block_size
            label_y = y_offset - 5 * block_size - 0.2
            label_cmd = f"  \\node at ({label_x:.2f}, {label_y:.2f}) {{$z={z + first_slice}$}};"
            latex_code.append(label_cmd)

    return "\n".join(latex_code)


def generate_tikz_code_without(A, B, without, add_bit, block_size=0.2, h_spacing=0.2, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0, if_index=False, name=''):
    """
    Generate TikZ code for LaTeX, similar to generate_tikz_code, but cells marked in 'without' are skipped (left grayed out).

    Parameters:
        without: 3D list of shape (slice_count,5,5) indicating cells to skip (1 = skip, 0 = draw)
        All other parameters are the same as in generate_tikz_code.
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

    label_cmd = f"  \\node at ({- 1.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{{name}}};"
    latex_code.append(label_cmd)

    if add_bit[0] > 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny $+{add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(red_add)
    elif add_bit[0] < 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny${add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(red_add)
    if add_bit[1] > 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5.5 * block_size :.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny$+{add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(blue_add)
    elif add_bit[1] < 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny ${add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(blue_add)

    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (5 * block_size + h_spacing)
        y_offset = -(row) * (5 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        # Draw gray background for the whole 5x5 block
        start_x = 0
        start_y = 0
        end_x = 5 * block_size
        end_y = -5 * block_size
        fill_cmd = f"    \\filldraw[fill=mygray, draw=mygray, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
        latex_code.append(fill_cmd)

        # Draw cells that are NOT skipped
        for x in range(5):
            for y in range(5):
                if without[z][y][x] == 1:
                    continue
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

        # Draw frames for drawn cells
        for x in range(5):
            for y in range(5):
                if without[z][y][x] == 1:
                    continue
                start_x = x * block_size
                start_y = -y * block_size
                end_x = (x + 1) * block_size
                end_y = -(y + 1) * block_size

                frame_key = B[x][y][(z + first_slice) % slice_number]
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
        if if_index:
            label_x = x_offset + 2.5 * block_size
            label_y = y_offset - 5 * block_size - 0.2
            label_cmd = f"  \\node at ({label_x:.2f}, {label_y:.2f}) {{$z={z + first_slice}$}};"
            latex_code.append(label_cmd)

    return "\n".join(latex_code)


def last_generate_tikz_code(A, B, add_bit, block_size=0.2, h_spacing=0.2, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0, if_index=False, name=''):
    """
    Generate TikZ code for LaTeX, drawing only non-'u' cells on a gray background.
    Similar to generate_tikz_code, but the background is gray and only cells with value != 'u' are drawn.
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

    label_cmd = f"  \\node at ({- 1.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{{name}}};"
    latex_code.append(label_cmd)

    if add_bit[0] > 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny $+{add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(red_add)
    elif add_bit[0] < 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny${add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(red_add)
    if add_bit[1] > 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5.5 * block_size :.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny$+{add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(blue_add)
    elif add_bit[1] < 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2.5 * block_size:.2f}) {{\\tiny ${add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 2 * block_size:.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 3 * block_size:.2f});"
        latex_code.append(blue_add)

    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (5 * block_size + h_spacing)
        y_offset = -(row) * (5 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        # Gray background for the whole 5x5 area
        start_x = 0
        start_y = 0
        end_x = 5 * block_size
        end_y = -5 * block_size
        fill_cmd = f"    \\filldraw[fill=mygray, draw=mygray, line width={line_width}] ({start_x:.2f}, {start_y:.2f}) rectangle ({end_x:.2f}, {end_y:.2f});"
        latex_code.append(fill_cmd)

        # Draw only cells that are not 'u'
        for x in range(5):
            for y in range(5):
                if A[x][y][(z + first_slice) % slice_number] == 'u':
                    continue
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

        # Draw frames for drawn cells
        for x in range(5):
            for y in range(5):
                if A[x][y][(z + first_slice) % slice_number] == 'u':
                    continue
                start_x = x * block_size
                start_y = -y * block_size
                end_x = (x + 1) * block_size
                end_y = -(y + 1) * block_size

                frame_key = B[x][y][(z + first_slice) % slice_number]
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
        if if_index:
            label_x = x_offset + 2.5 * block_size
            label_y = y_offset - 5 * block_size - 0.2
            label_cmd = f"  \\node at ({label_x:.2f}, {label_y:.2f}) {{$z={z + first_slice}$}};"
            latex_code.append(label_cmd)

    return "\n".join(latex_code)


def generate_line_tikz_code(A, B, add_bit, block_size=0.2, h_spacing=0.2, v_spacing=0.5, first_slice=0, last_slice=31, index_row=0, name=''):
    """
    Generate TikZ code for LaTeX, drawing only row y=0 (a single row of 5 squares) for each slice.
    Used for linear layer visualisation.
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

    label_cmd = f"  \\node at ({- 1.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 0.5 * block_size:.2f}) {{{name}}};"
    latex_code.append(label_cmd)

    if add_bit[0] > 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 0.5 * block_size:.2f}) {{\\tiny $+{add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing):.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - block_size:.2f});"
        latex_code.append(red_add)
    elif add_bit[0] < 0:
        red_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2.5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 0.5 * block_size:.2f}) {{\\tiny${add_bit[0]}$}};\\filldraw[fill=red, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 2 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing):.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 3 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - block_size:.2f});"
        latex_code.append(red_add)
    if add_bit[1] > 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5.5 * block_size :.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 0.5 * block_size:.2f}) {{\\tiny$+{add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing):.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - block_size:.2f});"
        latex_code.append(blue_add)
    elif add_bit[1] < 0:
        blue_add = f"  \\node[anchor=east] at ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5.5 * block_size :.2f}, {-1 * index_row * (5 * block_size + v_spacing) - 0.5 * block_size:.2f}) {{\\tiny ${add_bit[1]}$}};\\filldraw[fill=myblue, draw=black, line width={line_width}] ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 5 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing):.2f}) rectangle ({(last_slice - first_slice) * (5 * block_size + h_spacing) + 6 * block_size:.2f}, {-1 * index_row * (5 * block_size + v_spacing) - block_size:.2f});"
        latex_code.append(blue_add)

    for z in range(last_slice - first_slice):
        row = index_row
        col = z

        x_offset = (col) * (5 * block_size + h_spacing)
        y_offset = -(row) * (5 * block_size + v_spacing)

        latex_code.append(f"  \\begin{{scope}}[shift={{({x_offset:.2f}, {y_offset:.2f})}}]")

        for x in range(5):
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

        for x in range(5):
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