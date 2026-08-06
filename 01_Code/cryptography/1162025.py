import numpy as np
import matplotlib

# Number of steps around the cycle
N = 255
n = np.arange(N+1)
theta = 2 * np.pi * n / N

# Three harmonic components
f3  = np.exp(1j * (3*theta + 0.0))          # starting phase 0
f5  = np.exp(1j * (5*theta + np.pi/6))      # example offset
f17 = np.exp(1j * (17*theta + np.pi/3))     # example offset

# Composite vector sum (the "echo path")
composite = f3 + f5 + f17

(composite.real, composite, '-')
(([composite.real[0]], [composite.imag[0]], ##'red', label="Start"]))
axis('equal')
title("3×5×17 Spin-Cycle Overlay (255-step composite)")
legend()
show()
