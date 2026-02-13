import random
import time

# -----------------------------
# Original parameters / settings
# -----------------------------
condition_in_capacity = [[(1, 1), (3, 4, 1)], [(1, 1), (3, 4, 1)], [(1, 1), (3, 4, 1)], [(1, 1), (3, 4, 1)], [], [(1, 0), (3, 4, 1)],
 [(1, 0), (3, 4, 1)], [(1, 0), (3, 4, 1)], [(1, 0), (3, 4, 1)], [(1, 0), (3, 4, 1)], [(1, 0)], [(1, 0), (3, 4, 1)],
 [(1, 0), (3, 4, 1)], [(1, 0), (3, 4, 1)], [], [(1, 0), (3, 4, 1)], [(1, 1)], [(1, 0), (3, 4, 1)], [(1, 0), (3, 4, 1)],
 [(1, 0), (3, 4, 1)], [(1, 0), (3, 4, 1)], [(1, 1), (3, 4, 1)], [(1, 0), (3, 4, 1)], [(1, 1), (3, 4, 1)],
 [(1, 1), (3, 4, 1)], [(1, 0), (3, 4, 1)], [(1, 0), (3, 4, 1)], [(1, 1), (3, 4, 1)], [(1, 0), (3, 4, 1)],
 [(1, 1), (3, 4, 1)], [(1, 1), (3, 4, 1)], []]

r_place = [0, 3, 5, 6, 7, 9, 10, 12, 15, 16, 18, 19, 22, 25, 26, 27, 28, 29]
b_place = [1, 8, 11, 13, 17, 20, 21, 23, 24, 30]
c_place = [4, 14, 31]

determine = [0, 22, 25, 28]
probability = [8, 12, 15, 18, 24, 27]

# Scale knobs
Red_size = 2**18
Blue_size = 2**10

# Outer constant loop
N_iter = 2**12

# For speed in experiments: stop immediately after finding a valid preimage.
# Set to False if you want to keep searching and print all solutions.
STOP_AFTER_FIRST = False


# -----------------------------
# Bit-sliced core (32 columns packed into one 32-bit integer per row)
# -----------------------------
MASK32 = (1 << 32) - 1

def P_L(s0: int, s1: int, s2: int, s3: int, s4: int):
    """Linear layer P_L in bit-sliced form. Input/Output are 5 packed 32-bit rows."""
    m = MASK32

    # rotr(x,n) = (x>>n) | (x<<(32-n))
    s0r19 = (s0 >> 19) | ((s0 << 13) & m)
    s0r28 = (s0 >> 28) | ((s0 << 4) & m)
    n0 = (s0 ^ s0r19 ^ s0r28) & m

    s1r29 = (s1 >> 29) | ((s1 << 3) & m)   # 61 % 32 = 29
    s1r7  = (s1 >> 7)  | ((s1 << 25) & m)  # 39 % 32 = 7
    n1 = (s1 ^ s1r29 ^ s1r7) & m

    s2r1 = (s2 >> 1) | ((s2 << 31) & m)
    s2r6 = (s2 >> 6) | ((s2 << 26) & m)
    n2 = (s2 ^ s2r1 ^ s2r6) & m

    s3r10 = (s3 >> 10) | ((s3 << 22) & m)
    s3r17 = (s3 >> 17) | ((s3 << 15) & m)
    n3 = (s3 ^ s3r10 ^ s3r17) & m

    s4r7 = (s4 >> 7) | ((s4 << 25) & m)
    s4r9 = (s4 >> 9) | ((s4 << 23) & m)   # 41 % 32 = 9
    n4 = (s4 ^ s4r7 ^ s4r9) & m

    return n0, n1, n2, n3, n4


def P_S(s0: int, s1: int, s2: int, s3: int, s4: int):
    """
    Substitution layer P_S in bit-sliced form.
    Returns (t10,t11,t12,t13,t14, n0,n1,n2,n3,n4):
      - t1*  are temp_1 rows (packed)
      - n*   are new_state rows (packed)
    """
    m = MASK32

    # temp_1
    t10 = (s0 ^ s4) & m
    t11 = s1 & m
    t12 = (s1 ^ s2) & m
    t13 = s3 & m
    t14 = (s3 ^ s4) & m

    # temp_2
    nt10 = (~t10) & m
    nt11 = (~t11) & m
    nt12 = (~t12) & m
    nt13 = (~t13) & m
    nt14 = (~t14) & m

    t20 = (t10 ^ (nt11 & t12)) & m
    t21 = (t11 ^ (nt12 & t13)) & m
    t22 = (t12 ^ (nt13 & t14)) & m
    t23 = (t13 ^ (nt14 & t10)) & m
    t24 = (t14 ^ (nt10 & t11)) & m

    # new_state
    n0 = (t20 ^ t24) & m
    n1 = (t21 ^ t20) & m
    n2 = (t22 ^ m) & m  # +1 in GF(2) toggles every bit => xor with all-ones mask
    n3 = (t22 ^ t23) & m
    n4 = t24 & m

    return t10, t11, t12, t13, t14, n0, n1, n2, n3, n4


RBIT_MASKS = [1 << p for p in r_place]
BBIT_MASKS = [1 << p for p in b_place]
# r_place index where column==27 (needed for column2 computation)
R_INDEX_column27 = r_place.index(27)

# Determine indices for the 4 determine equations.
# Probabilistic indices for the 6 probabilistic equations.
DET0, DET1, DET2, DET3 = determine  # columns
PROB0,PROB1,PROB2,PROB3,PROB4,PROB5 = probability

def build_mask_from_value(value: int, bit_masks):
    """Map low bits of 'value' onto the given column positions (given as precomputed bit masks)."""
    mask = 0
    i = 0
    while value:
        if value & 1:
            mask |= bit_masks[i]
        value >>= 1
        i += 1
    return mask


def unpack_state(row0: int, row1: int, row2: int, row3: int, row4: int):
    """Only used when a solution is found (printing)."""
    st = [[0] * 5 for _ in range(32)]
    for k in range(32):
        st[k][0] = (row0 >> k) & 1
        st[k][1] = (row1 >> k) & 1
        st[k][2] = (row2 >> k) & 1
        st[k][3] = (row3 >> k) & 1
        st[k][4] = (row4 >> k) & 1
    return st


def main():

    randbit = lambda: random.randint(0, 1)

    # Precompute all b masks once.
    b_masks = [0] * Blue_size
    for b in range(Blue_size):
        b_masks[b] = build_mask_from_value(b, BBIT_MASKS)

    for _N in range(N_iter):
        print(f"{_N / N_iter * 100:.2f}",'%')
        # -----------------------------
        # Build constants (rows 1..4) and constant row-0 bits (c bits)
        # -----------------------------
        row1 = row2 = row3 = row4 = 0

        # Fill rows 1..4.
        for y in range(32):
            vals = [None, None, None, None, None]  # vals[x] for x in 0..4
            for cond in condition_in_capacity[y]:
                if len(cond) == 2:
                    vals[cond[0]] = cond[1]
                else:
                    vals[cond[0]] = 0
                    vals[cond[1]] = cond[2]

            # randomize for y<10, else set to 0, only for x=1..4
            # Supplement additional degrees of freedom
            for x in range(1, 5):
                if x==2 and y<8:
                    if vals[x] is None:
                        vals[x] = randbit()
                else:
                    if vals[x] is None:
                        vals[x] = 0

            if vals[1]:
                row1 |= (1 << y)
            if vals[2]:
                row2 |= (1 << y)
            if vals[3]:
                row3 |= (1 << y)
            if vals[4]:
                row4 |= (1 << y)

        # row0 constants: only c_place random, b_place forced 0, r_place set later, column2 computed later
        row0_const = 0
        for y in c_place:
            if randbit():
                row0_const |= (1 << y)

        # Compute the conditional constant part for column2:
        #   A[2][0] = 1 + A[27][4] + A[27][0] + A[2][4] + t1 + t2   (mod 2)
        # where only A[27][0] depends on r, everything else constant for this N.
        # So: A[2][0] = base_const XOR A[27][0]
        a14_0 = (row0_const >> 14) & 1
        a14_1 = (row1 >> 14) & 1
        a14_2 = (row2 >> 14) & 1
        a14_3 = (row3 >> 14) & 1
        a14_4 = (row4 >> 14) & 1

        a4_0 = (row0_const >> 4) & 1
        a4_1 = (row1 >> 4) & 1
        a4_3 = (row3 >> 4) & 1
        a4_4 = (row4 >> 4) & 1

        t1 = (a14_4 & a14_1) ^ a14_3 ^ (a14_2 & a14_1) ^ a14_2 ^ (a14_1 & a14_0) ^ a14_1 ^ a14_0
        t2 = (a4_4 & a4_1) ^ a4_4 ^ a4_3 ^ (a4_1 & a4_0) ^ a4_1

        base_const = 1 ^ ((row4 >> 27) & 1) ^ ((row4 >> 2) & 1) ^ t1 ^ t2

        # -----------------------------
        # Build the meet-in-the-middle table U
        #   U[delta_key][match_key] -> list of row0_r (b=0), stored as 32-bit packed row-0 state
        # -----------------------------
        U = {}

        for r in range(Red_size):
            # Build packed row0 for this r (b=0)
            r_mask = build_mask_from_value(r, RBIT_MASKS)
            row0_r = row0_const | r_mask

            # Set column2 based on r's bit at column27:
            r_bit27 = (r >> R_INDEX_column27) & 1
            if base_const ^ r_bit27:
                row0_r |= (1 << 2)
            # else: column2 is 0 already

            # ----- forward to get delta_key, base match bits, and P(r) (r_quad bits) -----
            # Round 1: P_S then P_L
            _t10, _t11, _t12, _t13, _t14, ps1_0, ps1_1, ps1_2, ps1_3, ps1_4 = P_S(row0_r, row1, row2, row3, row4)
            pl1_0, pl1_1, pl1_2, pl1_3, pl1_4 = P_L(ps1_0, ps1_1, ps1_2, ps1_3, ps1_4)

            # delta bits (from P_L_1)
            d0 = (pl1_1 >> 8) & 1
            d1 = (pl1_1 >> 21) & 1

            # Round 2: P_S then P_L
            t10, t11, t12, t13, t14, ps2_0, ps2_1, ps2_2, ps2_3, ps2_4 = P_S(pl1_0, pl1_1, pl1_2, pl1_3, pl1_4)

            # b_quad_value_0 == Q(b0) (two bits)
            q0 = (t10 >> 12) & 1
            q1 = (t10 >> 15) & 1

            # r_quad_value == P(r) (two bits)
            p0 = (t11 >> 12) & 1
            p1 = (t11 >> 15) & 1

            pl2_0, pl2_1, pl2_2, pl2_3, pl2_4 = P_L(ps2_0, ps2_1, ps2_2, ps2_3, ps2_4)

            # remaining delta bits (from P_L_2)
            d4 = (pl2_1 >> 0) & 1
            d5 = (pl2_1 >> 22) & 1
            d6 = (pl2_1 >> 25) & 1
            d7 = (pl2_1 >> 28) & 1

            # pack 8 delta bits into one small int (faster dict key than tuples)
            delta_key = d0 | (d1 << 1) | (q0 << 2) | (q1 << 3) | (d4 << 4) | (d5 << 5) | (d6 << 6) | (d7 << 7)

            # compute the 32-bit vector of determine-equation outputs for all columns at once
            expr_all = (pl2_1 & (pl2_0 ^ pl2_2 ^ pl2_4)) ^ pl2_0 ^ pl2_1 ^ pl2_2 ^ pl2_3

            m0 = (expr_all >> DET0) & 1
            m1 = (expr_all >> DET1) & 1
            m2 = (expr_all >> DET2) & 1
            m3 = (expr_all >> DET3) & 1

            expr_xor = pl2_3 ^ pl2_4
            m4 = (expr_xor >> PROB0) & 1
            m5 = (expr_xor >> PROB1) & 1
            m6 = (expr_xor >> PROB2) & 1
            m7 = (expr_xor >> PROB3) & 1
            m8 = (expr_xor >> PROB4) & 1
            m9 = (expr_xor >> PROB5) & 1

            # subtract P(r)Q(b0) to get F(r)+G(b0)
            a1_25 = (pl2_1 >> 25) & 1
            a1_28 = (pl2_1 >> 28) & 1
            m2 ^= (1 - a1_25) & q0 & p0
            m3 ^= (1 - a1_28) & q1 & p1

            m4 ^= q1 & p1
            m5 ^= q0 & p0
            m6 ^= q1 & p1

            match_dict = U.setdefault(delta_key, {})

            # enumerate all possible Q(b) values (2 bits) and add P(r)Q(b)
            # key packs: [m0,m1,m2,m3,m4,m5,m6,m7,m8,m9,qb0,qb1] into a 12-bit integer
            for qb in range(4):
                qb0 = qb & 1
                qb1 = (qb >> 1) & 1
                mm2 = m2 ^ ((1 - a1_25) & p0 & qb0)
                mm3 = m3 ^ ((1 - a1_28) & p1 & qb1)
                mm4 = m4 ^ (p1 & qb1)
                mm5 = m5 ^ (p0 & qb0)
                mm6 = m6 ^ (p1 & qb1)
                match_key = m0 | (m1 << 1) | (mm2 << 2) | (mm3 << 3) | (mm4 << 4) | (mm5 << 5) | (mm6 << 6) | (m7 << 7) | (m8 << 8) | (m9 << 9) | (qb0 << 10) | (qb1 << 11)
                match_dict.setdefault(match_key, []).append(row0_r)

        # -----------------------------
        # Search phase for each delta_key group
        # -----------------------------
        for _delta_key, match_dict in U.items():
            # pick any r_0 in this delta group
            r0_row0 = None
            for lst in match_dict.values():
                if lst:
                    r0_row0 = lst[0]
                    break
            if r0_row0 is None:
                continue

            # Compute d_match_value = F(r0)+G(b0) and P(r0) (r_quad) once.
            _t10, _t11, _t12, _t13, _t14, ps1_0, ps1_1, ps1_2, ps1_3, ps1_4 = P_S(r0_row0, row1, row2, row3, row4)
            pl1_0, pl1_1, pl1_2, pl1_3, pl1_4 = P_L(ps1_0, ps1_1, ps1_2, ps1_3, ps1_4)

            t10, t11, t12, t13, t14, ps2_0, ps2_1, ps2_2, ps2_3, ps2_4 = P_S(pl1_0, pl1_1, pl1_2, pl1_3, pl1_4)
            q0_0 = (t10 >> 12) & 1
            q1_0 = (t10 >> 15) & 1
            p0_0 = (t11 >> 12) & 1
            p1_0 = (t11 >> 15) & 1

            pl2_0, pl2_1, pl2_2, pl2_3, pl2_4 = P_L(ps2_0, ps2_1, ps2_2, ps2_3, ps2_4)

            expr_all = (pl2_1 & (pl2_0 ^ pl2_2 ^ pl2_4)) ^ pl2_0 ^ pl2_1 ^ pl2_2 ^ pl2_3
            d0 = (expr_all >> DET0) & 1
            d1 = (expr_all >> DET1) & 1
            d2 = (expr_all >> DET2) & 1
            d3 = (expr_all >> DET3) & 1

            expr_xor = pl2_3 ^ pl2_4
            d4 = (expr_xor >> PROB0) & 1
            d5 = (expr_xor >> PROB1) & 1
            d6 = (expr_xor >> PROB2) & 1
            d7 = (expr_xor >> PROB3) & 1
            d8 = (expr_xor >> PROB4) & 1
            d9 = (expr_xor >> PROB5) & 1

            a1_25 = (pl2_1 >> 25) & 1
            a1_28 = (pl2_1 >> 28) & 1
            d2 ^= (1 - a1_25) & q0_0 & p0_0
            d3 ^= (1 - a1_28) & q1_0 & p1_0

            d4 ^= q1_0 & p1_0
            d5 ^= q0_0 & p0_0
            d6 ^= q1_0 & p1_0

            # Iterate all b values
            for b in range(Blue_size):
                bmask = b_masks[b]
                row0_rb = r0_row0 | bmask

                # compute b_match and Q(b)
                _t10, _t11, _t12, _t13, _t14, ps1_0, ps1_1, ps1_2, ps1_3, ps1_4 = P_S(row0_rb, row1, row2, row3, row4)
                pl1_0, pl1_1, pl1_2, pl1_3, pl1_4 = P_L(ps1_0, ps1_1, ps1_2, ps1_3, ps1_4)

                t10, _t11, _t12, _t13, _t14, ps2_0, ps2_1, ps2_2, ps2_3, ps2_4 = P_S(pl1_0, pl1_1, pl1_2, pl1_3, pl1_4)
                qb0 = (t10 >> 12) & 1
                qb1 = (t10 >> 15) & 1

                pl2_0, pl2_1, pl2_2, pl2_3, pl2_4 = P_L(ps2_0, ps2_1, ps2_2, ps2_3, ps2_4)

                expr_all = (pl2_1 & (pl2_0 ^ pl2_2 ^ pl2_4)) ^ pl2_0 ^ pl2_1 ^ pl2_2 ^ pl2_3
                m0 = (expr_all >> DET0) & 1
                m1 = (expr_all >> DET1) & 1
                m2 = (expr_all >> DET2) & 1
                m3 = (expr_all >> DET3) & 1

                expr_xor = pl2_3 ^ pl2_4
                m4 = (expr_xor >> PROB0) & 1
                m5 = (expr_xor >> PROB1) & 1
                m6 = (expr_xor >> PROB2) & 1
                m7 = (expr_xor >> PROB3) & 1
                m8 = (expr_xor >> PROB4) & 1
                m9 = (expr_xor >> PROB5) & 1

                a1_25 = (pl2_1 >> 25) & 1
                a1_28 = (pl2_1 >> 28) & 1

                # subtract P(r0)Q(b) to get F(r0)+G(b)
                m2 ^= (1 - a1_25) & p0_0 & qb0
                m3 ^= (1 - a1_28) & p1_0 & qb1

                m4 ^= p1_0 & qb1
                m5 ^= p0_0 & qb0
                m6 ^= p1_0 & qb1

                # cancel with d_match to get G(b)+G(b0)
                m0 ^= d0
                m1 ^= d1
                m2 ^= d2
                m3 ^= d3
                m4 ^= d4 ^ 1
                m5 ^= d5 ^ 1
                m6 ^= d6 ^ 1
                m7 ^= d7 ^ 1
                m8 ^= d8 ^ 1
                m9 ^= d9 ^ 1

                match_key = m0 | (m1 << 1) | (m2 << 2) | (m3 << 3) | (m4 << 4) | (m5 << 5) | (m6 << 6) | (m7 << 7) | (m8 << 8) | (m9 << 9) | (qb0 << 10) | (qb1 << 11)
                cand_list = match_dict.get(match_key)
                if not cand_list:
                    continue

                # Verify candidates with the full forward computation and final 32-bit all-zero check
                for row0_r in cand_list:
                    row0_cand = row0_r | bmask

                    # Full check: P_S -> P_L -> P_S -> P_L -> P_S ; require final row0 == 0
                    _t10, _t11, _t12, _t13, _t14, ps1_0, ps1_1, ps1_2, ps1_3, ps1_4 = P_S(row0_cand, row1, row2, row3, row4)
                    pl1_0, pl1_1, pl1_2, pl1_3, pl1_4 = P_L(ps1_0, ps1_1, ps1_2, ps1_3, ps1_4)
                    _t10, _t11, _t12, _t13, _t14, ps2_0, ps2_1, ps2_2, ps2_3, ps2_4 = P_S(pl1_0, pl1_1, pl1_2, pl1_3, pl1_4)
                    pl2_0, pl2_1, pl2_2, pl2_3, pl2_4 = P_L(ps2_0, ps2_1, ps2_2, ps2_3, ps2_4)
                    _t10, _t11, _t12, _t13, _t14, ps3_0, ps3_1, ps3_2, ps3_3, ps3_4 = P_S(pl2_0, pl2_1, pl2_2, pl2_3, pl2_4)

                    if ps3_0 == 0:
                        print(unpack_state(row0_cand, row1, row2, row3, row4))
                        with open("result.txt",'a') as f:
                            f.write(f"{unpack_state(row0_cand, row1, row2, row3, row4)}\n")
                            values = (row0_cand, row1, row2, row3, row4)
                            f.write("(" + ", ".join(hex(x) for x in values) + ")\n")
                        if STOP_AFTER_FIRST:
                            return

if __name__ == "__main__":
    # Optional: set a seed for reproducibility during debugging.
    # random.seed(0)
    start = time.time()
    main()
    end = time.time()
    print(f"spend {end-start}s")