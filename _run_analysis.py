p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
delta = p - N

A = 80184233617433755134183875136831551618578922487806929476230322368028862899169
x2 = A - 7

A_inv_N = pow(A, -1, N)
print(f'A^-1 mod N = {A_inv_N}')
print(f'A^-1 mod N == true71 value? {A_inv_N == 97746773493746747058920733380537359447728098653318259670155670018669113547958}')

A_inv_p = pow(A, -1, p)
print(f'A^-1 mod p = {A_inv_p}')
print(f'A^-1 mod p == true71 value? {A_inv_p == 113815319824136702418055618210753784886129610589155325388531398708410984741688}')

A_inv_delta = pow(A, -1, delta)
print(f'A^-1 mod delta = {A_inv_delta}')
print(f'A^-1 mod delta == true71 value? {A_inv_delta == 295764655099084523609236324240371899233}')

print()
print('Mod 9 analysis:')
print(f'A^-1 mod N     mod 9 = {A_inv_N % 9}')
print(f'A^-1 mod p     mod 9 = {A_inv_p % 9}')
print(f'A^-1 mod delta mod 9 = {A_inv_delta % 9}')
diff = (A_inv_N - A_inv_p) % 9
print(f'(A^-1 mod N - A^-1 mod p) mod 9 = {diff}')

print()
target = {1, 4, 7}
print(f'A^-1 mod N     in target? {A_inv_N % 9 in target}')
print(f'A^-1 mod p     in target? {A_inv_p % 9 in target}')
print(f'A^-1 mod delta in target? {A_inv_delta % 9 in target}')

print()
print('x2 = A-7 analysis:')
x2_inv_N = pow(x2, -1, N)
x2_inv_p = pow(x2, -1, p)
x2_inv_delta = pow(x2, -1, delta)
print(f'x2^-1 mod N     % 9 = {x2_inv_N % 9}')
print(f'x2^-1 mod p     % 9 = {x2_inv_p % 9}')
print(f'x2^-1 mod delta % 9 = {x2_inv_delta % 9}')
print(f'x2 inverses in target? N: {x2_inv_N % 9 in target}, p: {x2_inv_p % 9 in target}, d: {x2_inv_delta % 9 in target}')

print()
print('Inverse gap:')
print(f'A_inv_N - A_inv_p mod 9 = {(A_inv_N - A_inv_p) % 9}')
print(f'A_inv_N - A_inv_delta mod 9 = {(A_inv_N - A_inv_delta) % 9}')
print(f'abs diff A_inv_N - A_inv_p mod 9 = {abs(A_inv_N - A_inv_p) % 9}')
