import hashlib
import time

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)

def point_add(P1, P2):
if P1 is None: return P2
if P2 is None: return P1
x1, y1 = P1
x2, y2 = P2
if x1 == x2:
if y1 != y2: return None
m = (3 * x1 * x1) * pow(2 * y1, P - 2, P) % P
else:
m = (y2 - y1) * pow(x2 - x1, P - 2, P) % P
x3 = (m * m - x1 - x2) % P
y3 = (m * (x1 - x3) - y1) % P
return (x3, y3)

def scalar_mult(k, point):
result = None
addend = point
while k:
if k & 1:
result = point_add(result, addend)
addend = point_add(addend, addend)
k >>= 1
return result

def privkey_to_address(k):
pub = scalar_mult(k, G)
x, y = pub
prefix = b”\x02” if y % 2 == 0 else b”\x03”
pubkey = prefix + x.to_bytes(32, “big”)
s1 = hashlib.sha256(pubkey).digest()
r = hashlib.new(“ripemd160”, s1).digest()
vh = b”\x00” + r
chk = hashlib.sha256(hashlib.sha256(vh).digest()).digest()[:4]
payload = vh + chk
alphabet = “123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz”
n = int.from_bytes(payload, “big”)
result = “”
while n:
n, r2 = divmod(n, 58)
result = alphabet[r2] + result
for byte in payload:
if byte == 0: result = “1” + result
else: break
return result

TARGET = “1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU”

TOP_CLUSTER = [
1936492198895840244483,
1930550710048680267915,
1929421851610687679281,
]

CENTER = sum(TOP_CLUSTER) // len(TOP_CLUSTER)
RADIUS = 5000000

scan_ranges = [
(“TOP_CLUSTER_CENTER”, CENTER, RADIUS),
(“RMD160_TOP”, 1936492198895840244483, RADIUS),
(“SHA256_1_TOP”, 1930550710048680267915, RADIUS),
(“SHA256_2_TOP”, 1929421851610687679281, RADIUS),
(“CLUSTER2_RMD”, 2198895840244483013614, RADIUS),
(“CLUSTER2_S1”, 2196111411241235534079, RADIUS),
(“CLUSTER2_S2”, 2185161068767928179375, RADIUS),
]

assert privkey_to_address(1) == “1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH”, “Address function error!”
print(“Address derivation verified”)
print(“Target: “ + TARGET)
print(“Convergence center: “ + str(CENTER))
print(””)

found = False

for label, center, radius in scan_ranges:
start = center - radius
end = center + radius
total = radius * 2
t0 = time.time()
print(“Scanning: “ + label)
print(“Center: “ + str(center))
print(“Range: “ + str(start) + “ to “ + str(end))
for i in range(total):
k = start + i
if k < 1180591620717411303424 or k > 2361183241434822606848:
continue
addr = privkey_to_address(k)
if addr == TARGET:
elapsed = time.time() - t0
print(””)
print(”*** PUZZLE 71 SOLVED ***”)
print(“Private key dec: “ + str(k))
print(“Private key hex: “ + format(k, “064x”))
print(“Address: “ + addr)
print(“Time: “ + str(round(elapsed, 2)) + “s”)
with open(“PUZZLE71_SOLVED.txt”, “w”) as f:
f.write(“PUZZLE 71 PRIVATE KEY\n”)
f.write(“Decimal: “ + str(k) + “\n”)
f.write(“Hex: “ + format(k, “064x”) + “\n”)
f.write(“Address: “ + addr + “\n”)
print(“Saved to PUZZLE71_SOLVED.txt”)
found = True
break
if i % 10000 == 0 and i > 0:
elapsed = time.time() - t0
rate = i / elapsed
eta = (total - i) / rate
pct = i / total * 100
print(str(round(pct, 1)) + “% | “ + str(i) + “/” + str(total) + “ | “ + str(round(rate)) + “ keys/s | ETA: “ + str(round(eta)) + “s”)
if found:
break

if not found:
print(””)
print(“Not found in any window.”)
print(“Try widening RADIUS to 50000000 and run again.”)
