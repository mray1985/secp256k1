import math, matplotlib.pyplot as plt

# simplified sample of your data
ratios = {10:1.1966,20:1.294e6,40:1.785e12,60:1.232e18,70:1.253e21,
          89:8.882e26,109:7.309e29,114:3.259e31}

xs, ys = zip(*sorted(ratios.items()))
plt.plot(xs,[math.log10(y) for y in ys],'-o')
plt.xlabel("Puzzle spacing Δn")
plt.ylabel("log10(ratio)")
plt.title("Growth of ratio 125/N vs puzzle spacing")
plt.show()
