# Ascon-XOF128 Attacks

This folder contains implementations and data for MitM trail search and attacks on **Ascon-XOF128**, including re-search and visualization.

## Subfolders

- **`search_result/`**  
  Stores results from the **red and blue bits** search stage and the **long-running** search stage.

- **`final_result/`**  
  Stores results after the **re-search** phase and includes code for plotting/visualization.

- **`tex/`**  
  LaTeX figure code used for drawing the results.

## files

- **`Ascon_XOF_3_collision.py`**  
  Search code for collision attack on 3-round Ascon-XOF128

- **`Ascon_XOF_re_search.py`**  
  Re-search stage code for collision attack on 3-round Ascon-XOF128


## Notes

- The attack code is typically split into multiple Python files corresponding to different stages of the overall workflow.
