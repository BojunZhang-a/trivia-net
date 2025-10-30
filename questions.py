# =============================
# FILE: questions.py
# =============================
# English comments only as requested.

import random

# --- 1) Mathematics ---
def generate_mathematics_question() -> str:
    # 2..5 operands, at most 4 operators. + and - are frequent; * and / are rarer.
    ops_pool = ["+"] * 3 + ["-"] * 3 + ["*"] + ["/"]
    n_operands = random.randint(2, 5)
    parts = []
    for i in range(n_operands):
        parts.append(str(random.randint(1, 100)))
        if i < n_operands - 1:
            parts.append(random.choice(ops_pool))
    # space-delimited infix expression
    return " ".join(parts)

# --- 2) Roman numerals (1..3999) ---
def generate_roman_numerals_question() -> str:
    number = random.randint(1, 3999)
    numerals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    out = []
    x = number
    for v, sym in numerals:
        while x >= v:
            out.append(sym)
            x -= v
    return "".join(out)

# --- 3) Usable IPv4 addresses of a subnet ---
def generate_usable_ip_question() -> str:
    # Return CIDR like "A.B.C.D/prefix"
    prefix = random.choice([8, 16, 24, 25, 26, 27, 28, 29])
    a = random.randint(1, 223)  # avoid special ranges
    b = random.randint(0, 255)
    c = random.randint(0, 255)
    d = random.choice([0, 128]) if prefix >= 25 else 0
    return f"{a}.{b}.{c}.{d}/{prefix}"

# --- 4) Network and Broadcast addresses of a subnet ---
def generate_network_broadcast_question() -> str:
    prefix = random.choice([16, 24, 25, 26, 27, 28])
    a = random.randint(1, 223)
    b = random.randint(0, 255)
    c = random.randint(0, 255)
    d = random.randint(1, 254)
    return f"{a}.{b}.{c}.{d}/{prefix}"
