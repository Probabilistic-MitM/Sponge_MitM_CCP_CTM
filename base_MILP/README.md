# Base MILP Modeling Modules

This folder provides reusable MILP modeling components shared by multiple attacks.

## Files

- **`operation_MILP.py`**  
  Models bit-oriented variables and provides MILP constraints for basic operations such as **XOR** and **AND**.

- **`Keccak_MILP.py`**  
  Uses `operation_MILP.py` to model the **Keccak round function**.

- **`Keccak_re_search_MILP.py`**  
  MILP model of the **Keccak round function** used in the **re-search** phase.

- **`Ascon_MILP.py`**  
  Uses `operation_MILP.py` to model the **Ascon round function**.

- **`Ascon_re_search_MILP.py`**  
  MILP model of the **Ascon round function** used in the **re-search** phase.

- **`Xoodyak_MILP.py`**  
  Uses `operation_MILP.py` to model the **Xoodyak round function**.

- **`Xoodyak_re_search_MILP.py`**  
  MILP model of the **Xoodyak round function** used in the **re-search** phase.
