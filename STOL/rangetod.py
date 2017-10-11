" trade off between aircraft range and take off distance "
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from stol import Mission
from gpkit.tools.autosweep import autosweep_1d
plt.rcParams.update({'font.size':19})

# pylint: disable=invalid-name, too-many-locals
def plot_torange(N):
    " plot trade studies of weight, range, and TO distance "
    M = Mission()
    M.cost = M["W"]

    sto = np.linspace(100, 700, N)
    Rmin = 25

    fig, ax = plt.subplots()

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
            ax.plot(R, W, color="k", linestyle=st[i],
                    label="$S_{TO} = %d [ft]$" % s)
            i += 1

        stosens = Bst.solarray["sensitivities"]["constants"]["S_{TO}"]
        f = interp1d(stosens, Bst.solarray("R"), "cubic")
        Rknee.extend([f(-0.8)])

    if len(sto) > 6:
        ax.plot(sto, Rknee)
        ax.set_xlabel("Take off Distance [ft]")
        ax.set_ylabel("Range [nmi]")
        ax.set_ylim([0, 350])
        ax.grid()

    if len(sto) < 6:
        ax.set_ylabel("Max Takeoff Weight [lbf]")
        ax.set_xlabel("Range [nmi]")
        ax.legend(loc=2)
        ax.grid()
        ax.set_ylim([0, 10000])

    return fig, ax

if __name__ == "__main__":
    Fig, _ = plot_torange(5)
    Fig.savefig("mtowrange.pdf", bbox_inches="tight")
    Fig, _ = plot_torange(25)
    Fig.savefig("rangetod.pdf", bbox_inches="tight")
