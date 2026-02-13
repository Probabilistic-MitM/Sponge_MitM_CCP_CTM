# Project Overview

This repository contains code for meet-in-the-middle (MitM) attacks, verification experiments, and a shared MILP-based modeling framework. It also includes utilities for exporting intermediate states and generating LaTeX/TikZ code for figures.

## Repository Structure

- **`attack/`**  
  Stores search code and plotting code for MitM attacks (trail search) and for verification experiments.

- **`base_MILP/`**  
  Contains the base MILP modeling modules shared by the attack implementations.

- **`output/`**  
  Includes utilities to (1) dump intermediate internal states to files and (2) convert states/results into LaTeX plotting code.
