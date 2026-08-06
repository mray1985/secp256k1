from decimal import Decimal, getcontext

# Set precision high enough to capture 156 decimal places
getcontext().prec = 200

# secp256k1 Constants
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424

def modinv(a, m):
    return pow(a, -1, m)

def point_add(x1, y1, x2, y2):
    if x1 == x2 and y1 == y2:
        # Point Doubling
        lam = ((3 * x1 * x1) * modinv(2 * y1, P)) % P
    else:
        # Point Addition
        lam = ((y2 - y1) * modinv(x2 - x1, P)) % P
    
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return x3, y3

def get_phi_string(x, y):
    # Phi = (x*p + y) / p^2
    p_dec = Decimal(P)
    x_dec = Decimal(x)
    y_dec = Decimal(y)
    numerator = x_dec * p_dec + y_dec
    phi = numerator / (p_dec * p_dec)
    return f"{phi:.156f}"

# Generate sequence
curr_x, curr_y = Gx, Gy
results = []

# Sequence 101 to 1100
for i in range(1, 1101):
    if i >= 101:
        results.append(f"{i}G: 0.{get_phi_string(curr_x, curr_y)[2:]}")
    
    # Add G to current point
    curr_x, curr_y = point_add(curr_x, curr_y, Gx, Gy)

# Write to file
with open("secp256k1_sequence_101_1100.txt", "w") as f:
    f.write("\n".join(results))