# --------------------------------------------
# Multiply base private key 1425787542618654982
# by all integers from 828 to 1656
# and print each result.
# --------------------------------------------

base_key = 1135041350219496382


start = 1040
end = 2080

for m in range(start, end + 1):
    result = base_key * m
    print(f"{m} * {base_key} = {result}")
