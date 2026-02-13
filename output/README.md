# Output Utilities

This folder provides utilities for exporting internal states and generating LaTeX plotting code.

## Dump Internal States to Files

- **`write_in_file_slice_32.py`**  
  Dumps internal states in re-search stage to files when using **slice = 32**.  
  Used by **Ascon** and part of the **Keccak** attacks.

- **`write_in_file_slice_64.py`**  
  Dumps internal states in re-search stage to files when using **slice = 64**.  
  Used by part of the **Keccak** attacks.


- **`write_in_file_slice_32.py`**  
  Dumps internal states to files when using **slice = 32**.  
  Used by **Ascon** and part of the **Keccak** attacks.

- **`write_in_file_slice_64.py`**  
  Dumps internal states to files when using **slice = 64**.  
  Used by part of the **Keccak** attacks.

- **`write_in_file_Xoodyak.py`**  
  Dumps internal states of **Xoodyak** to files.

## Convert Trails to LaTeX Plotting Code

- **`write_in_latex_Ascon.py`**  
  Converts **Ascon** trails into LaTeX drawing code.

- **`write_in_latex_Keccak.py`**  
  Converts **Keccak** trails into LaTeX drawing code.

- **`write_in_latex_Xoodyak.py`**  
  Converts **Xoodyak** trails into LaTeX drawing code.
