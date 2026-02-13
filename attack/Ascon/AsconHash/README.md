# Ascon-Hash256 Attacks

This folder contains implementations and data for MitM trail search and attacks on **Ascon-Hash256**, including re-search and visualization.

## Subfolders

- **`search_result/`**  
  Stores results from the **red and blue bits** search stage and the **long-running** search stage.

- **`final_result/`**  
  Stores results after the **re-search** phase and includes code for plotting/visualization.

- **`tex/`**  
  LaTeX figure code used for drawing the results.

## files

- **`Ascon_Hash_4_collision.py`**  
  Search code for collision attack on 4-round Ascon-Hash256

- **`Ascon_Hash_re_search.py`**  
  Re-search stage code for collision attack on 4-round Ascon-Hash256




## Notes

- The attack code is typically split into multiple Python files corresponding to different stages of the overall workflow.
