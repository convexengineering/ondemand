" trade off between aircraft range and take off distance "
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from stol import Mission
from gpkit.tools.autosweep import autosweep_1d
plt.rcParams.update({'font.size':19})

# pylint: disable=invalid-name, too-many-locals
def plot_torange(N, vname, vrange):
    " plot trade studies of weight, range, and TO distance "

    model = Mission(sp=True)
    sto = np.linspace(200, 500, N)

    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    i = 0
    fig, ax = plt.subplots()
    for v in vrange:
        model.substitutions.update({vname: v})
        Rknee = plot_wrange(model, sto, 10, plot=False)
        ax.plot(sto, Rknee, color=clrs[i],
                label="$%s = %.1f$" % (vname, v))
        i += 1

    ax.set_xlabel("Runway Distance [ft]")
    ax.set_ylabel("Range [nmi]")
    ax.set_ylim([0, 350])
    ax.grid()
    ax.legend(loc=4, fontsize=15)

    return fig, ax

def plot_wrange(model, sto, Nr, plot=True):
    model.cost = model.aircraft.topvar("W")
    model.substitutions["V_{min}"] = 100

    Rmin = 25

    if plot:
        fig, ax = plt.subplots()
        figs, axs = plt.subplots()
        figv, axv = plt.subplots()

    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5

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
            ax.plot(sol("R"), W, color=clrs[i],
                    label="$S_{runwawy} = %d [ft]$" % s)
            axv.plot(sol("R"), sol("W_{batt}")/sol(M.aircraft.topvar("W")),
                     color=clrs[i], label="$S_{runway} = %d [ft]$" % s)
            lands = sol["sensitivities"]["constants"]["m_{fac}_Mission/Landing"]
            axs.plot(sol("R"), lands, color=clrs[i],
                     label="$S_{runway} = %d [ft]$" % s)
            i += 1
        # else:
        stosens = sol["sensitivities"]["constants"]["R"]
        f = interp1d(stosens, sol("R"), "cubic")
        fw = interp1d(stosens, sol(model.aircraft.topvar("W")), "cubic")
        fwf = interp1d(stosens, sol("W_{batt}")/sol(model.aircraft.topvar("W")),
                       "cubic")
        if 1.0 > max(stosens):
            Rknee.extend([np.nan])
            wint = np.nan
            wbint = np.nan
        else:
            Rknee.extend([f(1.0)])
            wint = fw(1.0)
            wbint = fwf(1.0)

        if plot:
            ax.plot(Rknee[-1], wint, marker='o', color="k", markersize=5)
            axv.plot(Rknee[-1], wbint, marker='o', color="k", markersize=5)

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
        ret = [fig, figs, figv]
    else:
        ret = Rknee

    return ret

if __name__ == "__main__":
    # M = Mission(sp=True)
    # Figs = plot_wrange(M, [200, 300, 400, 500], 10, plot=True)
    # Figs[0].savefig("mtowrangew1200.pdf", bbox_inches="tight")
    # Figs[1].savefig("landingsens.pdf", bbox_inches="tight")
    # Figs[2].savefig("vrange.pdf", bbox_inches="tight")
    # Fig, _ = plot_torange(10, "W_{pay}", [400, 600, 800, 1000, 1200])
    # Fig.savefig("rangetodwpay.pdf", bbox_inches="tight")
    Fig, _ = plot_torange(10, "\\mu_Mission/Landing", [0.4, 0.5, 0.6, 0.8])
    Fig.savefig("rangetodmu.pdf", bbox_inches="tight")
    Fig, _ = plot_torange(10, "\\eta_{prop}_Mission/Landing", [0.01, 0.1, 0.2])
    Fig.savefig("rangetodt.pdf", bbox_inches="tight")
