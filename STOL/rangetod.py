" trade off between aircraft range and take off distance "
import numpy as np
import matplotlib.pyplot as plt
from stol import Mission
from gpkit.tools.autosweep import autosweep_1d

M = Mission()
M.cost = M["S_{TO}"]*M["W"]

Rmin = 25
Rmax = 100
R = np.linspace(Rmin, Rmax, 100)

Bst = autosweep_1d(M, 0.01, M["R"], [Rmin, Rmax], solver="mosek")
S = Bst.sample_at(R)("S_{TO}")

Fig, Ax = plt.subplots()
Ax.plot(R, S)
Ax.set_xlabel("Aircraft Range [nmi]")
Ax.set_ylabel("Take-off Distance [ft]")
Ax.set_ylim([0, 800])
Ax.grid()
Fig.savefig("rangetod.pdf")
