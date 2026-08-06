from decimal import Decimal, getcontext

# Set precision to 200 to ensure 156 digits are accurate
getcontext().prec = 200

# Constants for secp256k1
p = Decimal("115792089237316195423570985008687907853269984665640564039457584007908834671663")
p2 = p * p

def get_phi(x, y):
    # Phi = (x * p + y) / p^2
    # We use Decimals to handle the 156+ digit requirement
    dx = Decimal(x)
    dy = Decimal(y)
    numerator = dx * p + dy
    return numerator / p2

# You can iterate your EC point generation loop here
# For each n, compute the (x, y) and then:
# phi_n = get_phi(x, y)
# print(f"{n}G: {phi_n:.156f}")