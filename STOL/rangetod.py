import numpy as np
from stol import Mission
from gpkit.tools.autosweep import autosweep_1d
import matplotlib.pyplot as plt

M = Mission()
M.cost = M["S_{TO}"]*M["W"]

Rmin = 25
Rmax = 100
R = np.linspace(Rmin, Rmax, 100)

bst = autosweep_1d(M, 0.01, M["R"], [Rmin, Rmax], solver="mosek")
S = bst.sample_at(R)("S_{TO}")

fig, ax = plt.subplots()
ax.plot(R, S)
ax.set_xlabel("Aircraft Range [nmi]")
ax.set_ylabel("Take-off Distance [ft]")
ax.set_ylim([0, 800])
ax.grid()
fig.savefig("rangetod.pdf")
