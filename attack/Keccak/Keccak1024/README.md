# Keccak[1024] Attacks

This folder contains implementations and data for MitM preimage attacks on Keccak[1024], including trail search, re-search, and visualization.

## Subfolders

- **`4-round/`**  
  Code for the **4-round Keccak[1024]** attack.  
  Different stages of the attack are implemented in multiple Python scripts.

- **`5-round/`**  
  Code for the **5-round Keccak[1024]** attack.  
  Different stages of the attack are implemented in multiple Python scripts.

- **`blue_result/`**  
  Stores results from the **blue-bit** search stage.

- **`red_result/`**  
  Stores results from the **red-bit** search stage and the **long-time** search stage.

- **`final_result/`**  
  Stores results after the **re-search** phase (e.g., best linear bit cancellations and activated S-boxes), and includes code for plotting/visualization.

- **`tex/`**  
  LaTeX figure code used for drawing the results.
