" trade off between aircraft range and take off distance "
import numpy as np
import matplotlib.pyplot as plt
from stol import Mission
from gpkit.tools.autosweep import autosweep_1d
from scipy.interpolate import interp1d

M = Mission()
M.cost = M["W"]

sto = np.linspace(100, 700, 5)
Rmin = 25

Fig, Ax = plt.subplots()
Figrw, Axrw = plt.subplots()

st = [":", "-.", "--", "-"]*5
i = 0
Rknee = []
del M.substitutions["R"]

for s in sto:
    M.substitutions.update({"S_{TO}": s})
    M.cost = 1/M["R"]
    sol = M.solve("mosek")
    Rmax = sol("R").magnitude
    M.cost = M["W"]
    R = np.linspace(Rmin, Rmax-10, 100)
    Bst = autosweep_1d(M, 0.01, M["R"], [Rmin, Rmax-10], solver="mosek")

    if len(sto) < 6:
        W = Bst.sample_at(R)("W")
        Axrw.plot(R, W, color="k", linestyle=st[i],
                  label="$S_{} = %d [ft]$" % s)
        i += 1

    stosens = Bst.solarray["sensitivities"]["constants"]["S_{TO}"]
    f = interp1d(stosens, Bst.solarray("R"), "cubic")
    Rknee.extend([f(-0.8)])


Ax.plot(sto, Rknee)
Ax.set_xlabel("Take off Distance [ft]")
Ax.set_ylabel("Range [nmi]")
Ax.grid()
Fig.savefig("rangetod.pdf")

if len(sto) < 6:
    Axrw.set_ylabel("Max Takeoff Weight [lbf]")
    Axrw.set_xlabel("Range [nmi]")
    Axrw.legend(loc=2)
    Axrw.grid()
    Axrw.set_ylim([0, 10000])
    Figrw.savefig("mtowrange.pdf")
