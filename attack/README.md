# Attacks and Experiments

This folder contains code for meet-in-the-middle (MitM) attacks, including trail search and visualization, as well as verification experiments.

## Subfolders

- **`Keccak/`**  
  Trail search and drawing code for:
  - 4-/5-round Keccak[1024] preimage attacks
  - 5-round Keccak[768] preimage attack

- **`Ascon/`**  
  Trail search and drawing code for:
  - 4-round Ascon-Hash256 collision attack
  - 3-round Ascon-XOF128 preimage attack

- **`Xoodyak/`**  
  Trail search and drawing code for:
  - 3–/4-round Xoodyak-XOF collision and preimage attacks

- **`Experiment/`**  
  Verification experiment code including trail search, implementation of the preimage attack search process, and drawing utilities.
