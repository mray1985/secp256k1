"""Find AD paths with no repeated puzzle index (except early P1-8 self-references)."""
import re
from pathlib import Path

D = {1:1,2:3,3:7,4:8,5:21,6:49,7:76,8:224,9:467,10:514,11:1155,12:2683,13:5216,14:10544,15:26867,16:51510,17:95823,18:198669,19:357535,20:863317,21:1811764,22:3007503,23:5598802,24:14428676,25:33185509,26:54538862,27:111949941,28:227634408,29:400708894,30:1033162084,31:2102388551,32:3093472814,33:7137437912,34:14133072157,35:20112871792,36:42387769980,37:100251560595,38:146971536592,39:323724968937,40:1003651412950,41:1458252205147,42:2895374552463,43:7409811047825,44:15404761757071,45:19996463086597,46:51408670348612,47:119666659114170,48:191206974700443,49:409118905032525,50:611140496167764,51:2058769515153876,52:4216495639600700,53:6763683971478124,54:9974455244496707,55:30045390491869460,56:44218742292676575,57:138245758910846492,58:199976667976342049,59:525070384258266191,60:1135041350219496382,61:1425787542618654982,62:3908372542507822062,63:8993229949524469768,64:17799667357578236628,65:30568377312064202855,66:46346217550346335726,67:132656943602386256302,68:219898266213316039825,69:297274491920375905804,70:970436974005023690481}
D_TO_N = {v:n for n,v in D.items()}


def ad_sum(tokens):
    return sum(2*D[n] if o=='D' else D[n] for o,n in tokens)


def find_path(target, start_op, max_n, used=frozenset(), end_op=None, max_depth=50):
    def go(rem, op, used, path):
        if rem == 0:
            if end_op is None or (path and path[-1][0] == end_op):
                return path
            return None
        if rem < 0 or len(path) >= max_depth:
            return None
        best = None
        for n in range(min(max_n, 70), 0, -1):
            if n in used:
                continue
            sub = 2*D[n] if op == 'D' else D[n]
            if sub > rem:
                continue
            r = go(rem - sub, 'A' if op == 'D' else 'D', used | {n}, path + [(op, n)])
            if r is not None and (best is None or len(r) < len(best)):
                best = r
        return best
    return go(target, start_op, used, [])


def find_with_anchor_prefix(prefix, target, end_op):
    """prefix is list of (op,n) already applied; find suffix to target."""
    used = {n for _, n in prefix}
    s = ad_sum(prefix)
    if s > target:
        return None
    rem = target - s
    if not prefix:
        start = None
    else:
        start = 'A' if prefix[-1][0] == 'D' else 'D'
    if rem == 0:
        return prefix if prefix[-1][0] == end_op else None
    tail = find_path(rem, start, 70, frozenset(used), end_op=end_op)
    return prefix + tail if tail else None


def fmt(tokens):
    return ''.join(f'{o}({n})' for o,n in tokens)


# P22: keep ADADA anchor on 19, fix tail - no repeat puzzle index
p22_prefix = [('A',19),('D',19),('A',19),('D',19),('A',19)]
p22 = find_with_anchor_prefix(p22_prefix, D[22], 'A')
print('P22', fmt(p22) if p22 else 'FAIL', 'sum', ad_sum(p22) if p22 else 0)

# Load boundaries from file
text = Path(r'F:\New folder\secp256k1\DOUBLE_AND_ADD+BREAKDOWN_P1_P70.txt').read_text()
puzzles = {}
n = 0
for line in text.splitlines():
    if re.match(r'^[AD]\(', line.strip()):
        n += 1
        puzzles[n] = line.strip()

for pn in [52, 56, 57, 63]:
    prev_end = puzzles[pn-1][-2]  # last char before )
    # parse last token
    m = re.findall(r'([AD])\((\d+)\)', puzzles[pn-1])
    prev_end = m[-1][0]
    start = 'D' if prev_end == 'A' else 'A'
    m2 = re.findall(r'([AD])\((\d+)\)', puzzles[pn])
    end = m2[-1][0]
    path = find_path(D[pn], start, pn-1, frozenset(), end_op=end)
    if not path:
        path = find_path(D[pn], start, pn-1, frozenset(), end_op=None)
    reps = [n for n in [x[1] for x in path] if [x[1] for x in path].count(n)>1]
    print(f'P{pn} start={start} end={end} len={len(path) if path else 0}', fmt(path) if path else 'FAIL')
