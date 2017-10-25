" trade off between aircraft range and take off distance "
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from stol import Mission
from gpkit.tools.autosweep import autosweep_1d
plt.rcParams.update({'font.size':19})

# pylint: disable=invalid-name, too-many-locals
def plot_torange(N, clmax, to=True):
    " plot trade studies of weight, range, and TO distance "

    model = Mission(sp=True)
    sto = np.linspace(50, 450, N)

    st = [":", "-.", "--", "-"]
    i = 0
    fig, ax = plt.subplots()
    for cl in clmax:
        if to:
            model.substitutions.update({"C_{L_{TO}}": cl})
        else:
            model.substitutions.update({"C_{L_{land}}": cl})
        Rknee = plot_wrange(model, sto, 10, plot=False)
        ax.plot(sto, Rknee, color="k", linestyle=st[i],
                label="$C_{L_{max}} = %.1f$" % cl)
        i += 1

    ax.set_xlabel("Runway Distance [ft]")
    ax.set_ylabel("Range [nmi]")
    ax.set_ylim([0, 350])
    ax.grid()
    ax.legend(loc=4, fontsize=15)

    return fig, ax

def plot_wrange(model, sto, Nr, plot=True):
    model.cost = model.aircraft.topvar("W")

    Rmin = 25

    if plot:
        fig, ax = plt.subplots()
        figs, axs = plt.subplots()

    st = [":", "-.", "--", "-"]*5
    i = 0
    Rknee = []

    for s in sto:
        model.substitutions.update({"S_{runway}": s})
        del model.substitutions["R"]
        model.cost = 1/model["R"]
        sol = model.localsolve("mosek")
        Rmax = sol("R").magnitude
        model.cost = model.aircraft.topvar("W")
        R = np.linspace(Rmin, Rmax-10, Nr)
        model.substitutions.update({"R": ("sweep", R)})
        sol = model.localsolve("mosek", skipsweepfailures=True)

        if plot:
            W = sol(model.aircraft.topvar("W"))
            ax.plot(R, W, color="k", linestyle=st[i],
                    label="$S_{runwawy} = %d [ft]$" % s)
            lands = sol["sensitivities"]["constants"]["m_{fac}_Mission/Landing"]
            axs.plot(R, lands, color="k", linestyle=st[i],
                     label="$S_{runway} = %d [ft]$" % s)
            i += 1
        else:
            stosens = sol["sensitivities"]["constants"]["S_{runway}"]
            f = interp1d(stosens, sol("R"), "cubic")
            if -0.8 < min(stosens):
                Rknee.extend([np.nan])
            else:
                Rknee.extend([f(-0.8)])

    if plot:
        ax.set_ylabel("Max Takeoff Weight [lbf]")
        ax.set_xlabel("Range [nmi]")
        ax.legend(loc=4, fontsize=12)
        ax.grid()
        ax.set_ylim([0, 10000])
        axs.set_ylabel("Landing Sensitivity")
        axs.set_xlabel("Range [nmi]")
        axs.legend(loc=2, fontsize=12)
        axs.grid()
        axs.set_ylim([-0.1, 1])

    if plot:
        ret = [fig, figs]
    else:
        ret = Rknee

    return ret

if __name__ == "__main__":
    M = Mission(sp=True)
    Figs = plot_wrange(M, [100, 200, 300, 400, 500], 20, plot=True)
    Figs[0].savefig("mtowrange.pdf", bbox_inches="tight")
    Figs[1].savefig("landingsens.pdf", bbox_inches="tight")
    Fig, _ = plot_torange(20, [3.5, 4.5, 5.5])
    Fig.savefig("rangetod.pdf", bbox_inches="tight")
    Fig, _ = plot_torange(20, [3.5, 4.5, 5.5], to=False)
    Fig.savefig("rangelandd.pdf", bbox_inches="tight")
