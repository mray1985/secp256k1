D = {1:1,2:3,3:7,4:8,5:21,6:49,7:76,8:224,9:467,10:514,11:1155,12:2683,13:5216,14:10544,15:26867,16:51510,17:95823,18:198669,19:357535,22:3007503}
TARGET = 3007503
block = [("A",19),("D",19),("A",19),("D",19),("A",19)]
rem = TARGET - sum(D[n] if o == "A" else 2*D[n] for o, n in block)
print("After ADADA remainder:", rem)

def search(rem, op, path, max_depth=20):
    if rem == 0:
        return path
    if rem < 0 or len(path) > max_depth:
        return None
    for n in range(18, 0, -1):
        sub = 2 * D[n] if op == "D" else D[n]
        if sub <= rem:
            r = search(rem - sub, "A" if op == "D" else "D", path + [(op, n)])
            if r:
                return r
    return None

tail = search(rem, "D", [])
print("Tail:", tail)
if tail:
    full = block + tail
    s = sum(D[n] if o == "A" else 2 * D[n] for o, n in full)
    print("Sum", s)
    print("AD:", "".join(f"{o}({n})" for o, n in full))
    print("Ends", full[-1][0])
