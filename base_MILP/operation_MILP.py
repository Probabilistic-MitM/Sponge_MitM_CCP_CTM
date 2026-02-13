import gurobipy as gp
from gurobipy import GRB


def get_value(X):
    """Get integer value from variable or constant."""
    if type(X) == int:
        return X
    if type(X) == gp.LinExpr:
        return int(X.getValue())
    else:
        return int(X.x)


class Bit:
    """
    Bit class representing one bit in the hash function.
    Contains four flags:
    - ul: nonlinear flag
    - r:  contains red flag
    - b:  contains blue flag
    - cond: condition constant flag
    """

    def __init__(self, model: gp.Model, name_prefix="", bit_type=''):
        """
        Initialize bit variables.

        Parameters:
        - model: Gurobi model object
        - name_prefix: variable name prefix
        - bit_type: bit type, supports 'lr','ur','lb','ub','lg','ug','uc','c','cc','u' or tuple
        """
        if bit_type == '':
            self.model = model

            # Nonlinear flag
            self.ul = model.addVar(vtype=GRB.BINARY, name=f"{name_prefix}_ul")

            # Contains red flag
            self.r = model.addVar(vtype=GRB.BINARY, name=f"{name_prefix}_r")

            # Contains blue flag
            self.b = model.addVar(vtype=GRB.BINARY, name=f"{name_prefix}_b")

            # Condition constant flag
            self.cond = model.addVar(vtype=GRB.BINARY, name=f"{name_prefix}_cond")

            # Add bit type constraints
            self._add_bit_constraints()
        else:
            self.init_type(model, bit_type, name_prefix)

    def init_type(self, model, bit_type, name_prefix):
        """Initialize flags based on bit type."""
        self.model = model
        if type(bit_type) == str:
            if bit_type == 'lr':      # linear red bit
                self.ul = 0
                self.r = 1
                self.b = 0
                self.cond = 0
            elif bit_type == 'ur':    # nonlinear red bit
                self.ul = 1
                self.r = 1
                self.b = 0
                self.cond = 0
            elif bit_type == 'lb':    # linear blue bit
                self.ul = 0
                self.r = 0
                self.b = 1
                self.cond = 0
            elif bit_type == 'ub':    # nonlinear blue bit
                self.ul = 1
                self.r = 0
                self.b = 1
                self.cond = 0
            elif bit_type == 'lg':    # linear red-blue combination
                self.ul = 0
                self.r = 1
                self.b = 1
                self.cond = 0
            elif bit_type == 'uc':    # unconditional constant
                self.ul = 0
                self.r = 0
                self.b = 0
                self.cond = 0
            elif bit_type == 'c':     # constant
                self.ul = 0
                self.r = 0
                self.b = 0
                self.cond = 0
            elif bit_type == 'cc':    # conditional constant
                self.ul = 0
                self.r = 0
                self.b = 0
                self.cond = 1
            elif bit_type == 'u':     # pure nonlinear bit
                self.ul = 1
                self.r = 0
                self.b = 0
                self.cond = 0
            elif bit_type == 'ug':    # nonlinear red-blue combination
                self.ul = 1
                self.r = 1
                self.b = 1
                self.cond = 0
            else:
                raise ValueError(f"Unsupported bit type: {bit_type} (only 'lr','ur','lb','ub','lg','ug','uc','c','cc','u')")
        elif type(bit_type) == tuple:
            # Use tuple to flexibly specify each flag value
            if bit_type[0] == '*':
                self.ul = model.addVar(vtype=GRB.BINARY, name=f"{name_prefix}_ul")
            elif bit_type[0] == 0:
                self.ul = 0
            elif bit_type[0] == 1:
                self.ul = 1

            if bit_type[1] == '*':
                self.r = model.addVar(vtype=GRB.BINARY, name=f"{name_prefix}_r")
            elif bit_type[1] == 0:
                self.r = 0
            elif bit_type[1] == 1:
                self.r = 1

            if bit_type[2] == '*':
                self.b = model.addVar(vtype=GRB.BINARY, name=f"{name_prefix}_b")
            elif bit_type[2] == 0:
                self.b = 0
            elif bit_type[2] == 1:
                self.b = 1

            if bit_type[3] == '*':
                self.cond = model.addVar(vtype=GRB.BINARY, name=f"{name_prefix}_cond")
            elif bit_type[3] == 0:
                self.cond = 0
            elif bit_type[3] == 1:
                self.cond = 1

            # Add bit type constraints
            self._add_bit_constraints()

    def _add_bit_constraints(self):
        """
        Add basic constraints for bit types.
        Ensure the combination of flags conforms to bit type definitions.
        """
        self.model.addConstr(self.cond + self.ul <= 1)  # cond and ul cannot both be 1
        self.model.addConstr(self.cond + self.r <= 1)  # cond and r cannot both be 1
        self.model.addConstr(self.b + self.cond <= 1)  # b and cond cannot both be 1

    def _get_type(self) -> str:
        """Return bit type based on flag variable values."""
        ul = get_value(self.ul)
        r = get_value(self.r)
        b = get_value(self.b)

        if ul == 1 and r == 0 and b == 0:
            return 'u'
        elif ul == 0 and r == 1 and b == 0:
            return 'lr'
        elif ul == 1 and r == 1 and b == 0:
            return 'ur'
        elif ul == 0 and r == 0 and b == 1:
            return 'lb'
        elif ul == 1 and r == 0 and b == 1:
            return 'ub'
        elif ul == 0 and r == 1 and b == 1:
            return 'lg'
        elif ul == 1 and r == 1 and b == 1:
            return 'ug'
        else:
            return 'c'


def add_or(model, z, xs, name=""):
    # z, xs are {0,1} variables or constants
    for i, x in enumerate(xs):
        model.addConstr(z >= x, name=f"{name}_or_lb_{i}")
    model.addConstr(z <= gp.quicksum(xs), name=f"{name}_or_ub")


def xor_with_ul_input(model, inputs, output, operation_name=''):
    """
    XOR operation with nonlinear inputs.
    Returns delta_r and delta_b variables.
    """
    # delta_r, delta_b: whether red/blue bits cancel in XOR
    delta_r = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_delta_r")
    delta_b = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_delta_b")

    # Check if inputs contain red bits
    has_r = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_has_r")
    add_or(model, has_r, [i.r for i in inputs])

    # Check if inputs contain blue bits
    has_b = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_has_b")
    add_or(model, has_b, [i.b for i in inputs])

    # Check if inputs contain nonlinear bits
    has_ul = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_has_ul")
    add_or(model, has_ul, [i.ul for i in inputs])

    # Check if inputs contain pure nonlinear bits (type u)
    sum_temp_u = []
    for i in inputs:
        temp = model.addVar(vtype=GRB.BINARY)
        model.addConstr(temp >= i.ul - i.r - i.b)
        model.addConstr(temp <= i.ul)
        model.addConstr(temp <= 1 - i.r)
        model.addConstr(temp <= 1 - i.b)
        sum_temp_u.append(temp)

    # Check if inputs contain nonlinear blue bits (type ub) or nonlinear red-blue bits
    input_ub = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_input_ub")
    sum_temp_ub = []
    for i in inputs:
        temp = model.addVar(vtype=GRB.BINARY)
        model.addConstr(temp >= i.ul + i.b - 1)
        model.addConstr(temp <= i.ul)
        model.addConstr(temp <= i.b)
        sum_temp_ub.append(temp)
    add_or(model, input_ub, sum_temp_ub)

    # Constraints for output nonlinear flag
    model.addConstr(output.ul >= has_ul - delta_r)
    model.addConstr(output.ul <= has_ul)
    model.addConstr(output.ul <= 1 - delta_r + input_ub)
    model.addConstr(output.ul >= input_ub)

    # Constraints for delta_r
    model.addConstr(delta_r <= has_r)

    # Constraints for delta_b
    model.addConstr(delta_b <= 1 - has_ul)
    model.addConstr(delta_b <= has_b)

    # Constraints for output condition constant flag
    model.addConstr(output.cond <= 1 - has_ul)

    # Constraints for output red flag
    model.addConstr(output.r <= has_r)
    model.addConstr(output.r >= has_r - delta_r - gp.quicksum(sum_temp_u))
    for if_u in sum_temp_u:
        model.addConstr(output.r + if_u + delta_r <= 1)

    # Constraints for output blue flag
    model.addConstr(output.b <= has_b)
    model.addConstr(output.b >= has_b - gp.quicksum(sum_temp_u) - delta_b)
    for if_u in sum_temp_u:
        model.addConstr(output.b + if_u + delta_b <= 1)

    return {
        "delta_r": delta_r,
        "delta_b": delta_b,
        'has_ul': has_ul,
        'new_cond': 0,
    }


def xor_without_ul_input(model, inputs, output, operation_name=''):
    """
    XOR operation without nonlinear inputs.
    Returns delta_r and delta_b variables.
    """
    # delta_r, delta_b: whether red/blue bits cancel in XOR
    delta_r = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_delta_r")
    delta_b = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_delta_b")

    # Sums of red/blue components in inputs
    sum_r = gp.quicksum([i.r for i in inputs])
    sum_b = gp.quicksum([i.b for i in inputs])
    n = len(inputs)

    # Constraints for output nonlinear flag (no nonlinear output)
    model.addConstr(output.ul == 0)

    # === Red Component Logic ===
    # Logic: has_r = output.r + delta_r
    # has_r is OR over inputs' red flags
    # 1. If sum_r == 0, then output.r + delta_r must be 0
    model.addConstr(output.r + delta_r <= sum_r)
    # 2. If sum_r >= 1, then output.r + delta_r must be 1
    for i in inputs:
        model.addConstr((output.r + delta_r) >= i.r)
    # 3. Mutual exclusivity: output.r and delta_r cannot both be 1
    model.addConstr(output.r + delta_r <= 1)

    # === Blue Component Logic ===
    # Same as above
    model.addConstr(output.b + delta_b <= sum_b)
    for i in inputs:
        model.addConstr((output.b + delta_b) >= i.b)
    model.addConstr(output.b + delta_b <= 1)

    return {
        "delta_r": delta_r,
        "delta_b": delta_b,
        'new_cond': 0,
        'has_ul': 0
    }


def xor_with_ul_input_no_delta_b(model, inputs, output, operation_name=''):
    """
    XOR operation with nonlinear inputs (blue cancellation not allowed).
    Returns delta_r variable.
    """
    # delta_r: whether red bits cancel in XOR
    delta_r = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_delta_r")

    # Check if inputs contain red bits
    has_r = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_has_r")
    add_or(model, has_r, [i.r for i in inputs])

    # Check if inputs contain blue bits
    has_b = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_has_b")
    add_or(model, has_b, [i.b for i in inputs])

    # Check if inputs contain nonlinear bits
    has_ul = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_has_ul")
    add_or(model, has_ul, [i.ul for i in inputs])

    # Check if inputs contain pure nonlinear bits (type u)
    sum_temp_u = []
    for i in inputs:
        temp = model.addVar(vtype=GRB.BINARY)
        model.addConstr(temp >= i.ul - i.r - i.b)
        model.addConstr(temp <= i.ul)
        model.addConstr(temp <= 1 - i.r)
        model.addConstr(temp <= 1 - i.b)
        sum_temp_u.append(temp)

    # Check if inputs contain nonlinear blue bits (type ub)
    sum_temp_ub = []
    for i in inputs:
        temp = model.addVar(vtype=GRB.BINARY)
        model.addConstr(temp >= i.ul + i.b - 1)
        model.addConstr(temp <= i.ul)
        model.addConstr(temp <= i.b)
        sum_temp_ub.append(temp)

    # Constraints for output nonlinear flag
    for i in inputs:
        model.addConstr(output.ul >= i.ul - delta_r)
    model.addConstr(output.ul <= gp.quicksum([i.ul for i in inputs]))
    model.addConstr(output.ul <= 1 - delta_r + gp.quicksum(sum_temp_ub))
    for ub in sum_temp_ub:
        model.addConstr(output.ul >= ub)

    # Constraints for delta_r
    model.addConstr(delta_r <= has_r)

    # Constraints for output condition constant flag
    for i in inputs:
        model.addConstr(output.cond <= 1 - i.ul)

    # Constraints for output red flag
    model.addConstr(output.r <= has_r)
    model.addConstr(output.r >= has_r - delta_r - gp.quicksum(sum_temp_u))
    for if_u in sum_temp_u:
        model.addConstr(output.r + if_u + delta_r <= 1)

    # Constraints for output blue flag
    model.addConstr(output.b <= has_b)
    model.addConstr(output.b >= has_b - gp.quicksum(sum_temp_u))
    for t_u in sum_temp_u:
        model.addConstr(output.b <= 1 - t_u)

    return {
        "delta_r": delta_r,
        "delta_b": 0,
        'new_cond': 0,
        'has_ul': has_ul
    }


def and_operation(model, input1, input2, output, operation_name=''):
    """
    AND operation.
    Returns CT and const_cond variables.
    """
    # CT: whether special CT term is used
    CT = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_CT')
    # const_cond: whether condition constant is generated
    const_cond = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_const_cond')

    # Determine if each input has color (Red OR Blue)
    has_c1 = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_has_c1')
    has_c2 = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_has_c2')

    # Linearization of OR: z >= x, z >= y, z <= x+y
    model.addConstr(has_c1 >= input1.r)
    model.addConstr(has_c1 >= input1.b)
    model.addConstr(has_c1 <= input1.r + input1.b)
    model.addConstr(has_c2 >= input2.r)
    model.addConstr(has_c2 >= input2.b)
    model.addConstr(has_c2 <= input2.r + input2.b)

    # new_ul = (input1 has color) AND (input2 has color)
    new_ul = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_input_color_geq_2')
    # Linearization of AND: z >= x+y-1, z <= x, z <= y
    model.addConstr(new_ul >= has_c1 + has_c2 - 1)
    model.addConstr(new_ul <= has_c1)
    model.addConstr(new_ul <= has_c2)

    # Constraints for output nonlinear flag
    model.addConstr(output.ul >= CT)
    model.addConstr(output.ul <= 1 - const_cond)
    model.addConstr(output.ul >= new_ul - const_cond)
    model.addConstr(2 * output.ul >= input1.ul + input2.ul - const_cond)
    model.addConstr(output.ul <= input1.ul + input2.ul + new_ul)

    # Check if inputs contain pure nonlinear bits (type u)
    input_u = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_input_u")
    sum_temp = []
    for i in [input1, input2]:
        temp = model.addVar(vtype=GRB.BINARY)
        model.addConstr(temp >= i.ul - i.r - i.b)
        model.addConstr(temp <= i.ul)
        model.addConstr(temp <= 1 - i.r)
        model.addConstr(temp <= 2 - i.b)
        sum_temp.append(temp)
    add_or(model, input_u, sum_temp)

    # Check if inputs contain red-blue combination (type g)
    has_g = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_has_g')
    sum_temp_g = []
    for i in [input1, input2]:
        temp = model.addVar(vtype=GRB.BINARY)
        model.addConstr(temp >= i.r + i.b - 1)
        model.addConstr(temp <= i.r)
        model.addConstr(temp <= i.b)
        sum_temp_g.append(temp)
    add_or(model, has_g, sum_temp_g)

    # Check if new pure nonlinear bit (type u) is generated
    create_u = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_create_u')
    # create_u >= (input1.r AND input2.b)
    model.addConstr(create_u >= input1.r + input2.b - 1)
    # create_u >= (input2.r AND input1.b)
    model.addConstr(create_u >= input2.r + input1.b - 1)

    model.addConstr(create_u <= input1.r + input2.r)
    model.addConstr(create_u <= input1.b + input2.b)
    model.addConstr(create_u <= has_c1)
    model.addConstr(create_u <= has_c2)

    # Constraints for CT
    model.addConstr(CT <= 1 - has_g)
    model.addConstr(CT <= create_u)

    # Constraints for const_cond
    model.addConstr(const_cond <= input1.r + input2.r + input1.b + input2.b + input1.ul + input2.ul)

    # Check if inputs contain red/blue flags
    has_r = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_has_r')
    has_b = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_has_b')

    model.addConstr(has_r >= input1.r)
    model.addConstr(has_r >= input2.r)
    model.addConstr(has_r <= input1.r + input2.r)

    model.addConstr(has_b >= input1.b)
    model.addConstr(has_b >= input2.b)
    model.addConstr(has_b <= input1.b + input2.b)

    # Constraints for output red flag
    model.addConstr(output.r <= has_r)
    model.addConstr(3 * output.r >= has_r + 2 * CT - const_cond - input_u - create_u)
    model.addConstr(output.r >= CT)
    model.addConstr(output.r <= 1 - input_u)
    model.addConstr(output.r <= 1 - create_u + CT)
    model.addConstr(output.r <= 1 - const_cond)

    # Constraints for output blue flag
    model.addConstr(output.b <= has_b)
    model.addConstr(3 * output.b >= has_b + 2 * CT - const_cond - input_u - create_u)
    model.addConstr(output.b >= CT)
    model.addConstr(output.b <= 1 - input_u)
    model.addConstr(output.b <= 1 - create_u + CT)
    model.addConstr(output.b <= 1 - const_cond)

    return {
        "const_cond": const_cond,
        "CT": CT,
    }


def and_operation_no_cond(model, input1, input2, output, operation_name=''):
    """
    AND operation without conditional constant generation.
    Returns CT variable.
    """
    # CT: whether special CT term is used
    CT = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_CT')

    # Determine if each input has color (Red OR Blue)
    has_c1 = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_has_c1')
    has_c2 = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_has_c2')

    # Linearization of OR: z >= x, z >= y, z <= x+y
    model.addConstr(has_c1 >= input1.r)
    model.addConstr(has_c1 >= input1.b)
    model.addConstr(has_c1 <= input1.r + input1.b)
    model.addConstr(has_c2 >= input2.r)
    model.addConstr(has_c2 >= input2.b)
    model.addConstr(has_c2 <= input2.r + input2.b)

    # new_ul = (input1 has color) AND (input2 has color)
    new_ul = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_input_color_geq_2')
    # Linearization of AND: z >= x+y-1, z <= x, z <= y
    model.addConstr(new_ul >= has_c1 + has_c2 - 1)
    model.addConstr(new_ul <= has_c1)
    model.addConstr(new_ul <= has_c2)

    # Constraints for output nonlinear flag
    model.addConstr(output.ul >= new_ul)
    model.addConstr(output.ul >= input1.ul)
    model.addConstr(output.ul >= input2.ul)
    model.addConstr(output.ul <= input1.ul + input2.ul + new_ul)

    # Check if inputs contain pure nonlinear bits (type u)
    input_u = model.addVar(vtype=GRB.BINARY, name=f"{operation_name}_input_u")
    sum_temp = []
    for i in [input1, input2]:
        temp = model.addVar(vtype=GRB.BINARY)
        model.addConstr(temp >= i.ul - i.r - i.b)
        model.addConstr(temp <= i.ul)
        model.addConstr(temp <= 1 - i.r)
        model.addConstr(temp <= 1 - i.b)
        sum_temp.append(temp)
    add_or(model, input_u, sum_temp)

    # Check if inputs contain red-blue combination (type g)
    has_g = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_has_g')
    sum_temp_g = []
    for i in [input1, input2]:
        temp = model.addVar(vtype=GRB.BINARY)
        model.addConstr(temp >= i.r + i.b - 1)
        model.addConstr(temp <= i.r)
        model.addConstr(temp <= i.b)
        sum_temp_g.append(temp)
    add_or(model, has_g, sum_temp_g)

    # Check if new pure nonlinear bit (type u) is generated
    create_u = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_create_u')
    # create_u >= (input1.r AND input2.b)
    model.addConstr(create_u >= input1.r + input2.b - 1)
    # create_u >= (input2.r AND input1.b)
    model.addConstr(create_u >= input2.r + input1.b - 1)

    model.addConstr(create_u <= input1.r + input2.r)
    model.addConstr(create_u <= input1.b + input2.b)
    model.addConstr(create_u <= has_c1)
    model.addConstr(create_u <= has_c2)

    # Constraints for CT
    model.addConstr(CT <= 1 - has_g)
    model.addConstr(CT <= create_u)

    # Check if inputs contain red/blue flags
    has_r = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_has_r')
    has_b = model.addVar(vtype=GRB.BINARY, name=f'{operation_name}_has_b')

    model.addConstr(has_r >= input1.r)
    model.addConstr(has_r >= input2.r)
    model.addConstr(has_r <= input1.r + input2.r)

    model.addConstr(has_b >= input1.b)
    model.addConstr(has_b >= input2.b)
    model.addConstr(has_b <= input1.b + input2.b)

    # Constraints for output red flag
    model.addConstr(output.r <= has_r)
    model.addConstr(3 * output.r >= has_r + 2 * CT - input_u - create_u)
    model.addConstr(output.r >= CT)
    model.addConstr(output.r <= 1 - input_u)
    model.addConstr(output.r <= 1 - create_u + CT)

    # Constraints for output blue flag
    model.addConstr(output.b <= has_b)
    model.addConstr(3 * output.b >= has_b + 2 * CT - input_u - create_u)
    model.addConstr(output.b >= CT)
    model.addConstr(output.b <= 1 - input_u)
    model.addConstr(output.b <= 1 - create_u + CT)

    return {
        "const_cond": 0,
        "CT": CT,
    }