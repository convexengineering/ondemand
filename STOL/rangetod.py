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

    model = Mission(sp=False)
    del model.substitutions["R"]
    sto = np.linspace(50, 500, N)

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
    " plot weight vs range "
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
        model.cost = 1/model["R"]
        sol = model.solve("mosek")
        Rmax = sol("R").magnitude - 10
        model.cost = model[model.aircraft.topvar("W")]
        bst = autosweep_1d(model, 0.1, model["R"], [Rmin, Rmax])
        solR = bst.solarray("R")
        stosens = bst.solarray["sensitivities"]["constants"]["R"]
        fbatt = bst.solarray("W_{batt}")/bst.solarray(
            model.aircraft.topvar("W"))
        wair = bst.solarray(model.aircraft.topvar("W"))
        lands = bst.solarray["sensitivities"]["constants"][
            "m_{fac}_Mission/GLanding"]

        f = interp1d(stosens, solR, "cubic")
        fw = interp1d(stosens, wair, "cubic")
        fwf = interp1d(stosens, fbatt, "cubic")
        if 1.0 > max(stosens):
            Rknee.extend([np.nan])
            wint = np.nan
            wbint = np.nan
        else:
            Rknee.extend([f(1.0)])
            wint = fw(1.0)
            wbint = fwf(1.0)

        if plot:
            axs.plot(solR, lands, color=clrs[i],
                     label="$S_{runway} = %d [ft]$" % s)
            x = np.linspace(Rmin, Rmax, 100)
            solR = bst.sample_at(x)["R"]
            fbatt = bst.sample_at(x)["W_{batt}"]/bst.sample_at(x)[
                model.aircraft.topvar("W")]
            wair = bst.sample_at(x)[model.aircraft.topvar("W")]
            ax.plot(solR, wair, color=clrs[i],
                    label="$S_{runwawy} = %d [ft]$" % s)
            axv.plot(solR, fbatt, color=clrs[i],
                     label="$S_{runway} = %d [ft]$" % s)
            ax.plot(Rknee[-1], wint, marker='o', color="k", markersize=5)
            axv.plot(Rknee[-1], wbint, marker='o', color="k", markersize=5)
            i += 1

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
    M = Mission(sp=False)
    del M.substitutions["R"]
    Figs = plot_wrange(M, [50, 100, 200, 350, 500], 10, plot=True)
    Figs[0].savefig("mtowrangew1200.pdf", bbox_inches="tight")
    Figs[1].savefig("landingsens.pdf", bbox_inches="tight")
    Figs[2].savefig("vrange.pdf", bbox_inches="tight")
    Fig, _ = plot_torange(20, "W_{pay}", [800])
    Fig.savefig("rangetodwpay.pdf", bbox_inches="tight")
    Fig, _ = plot_torange(20, "C_{L_{land}}", [3.5, 4.5, 5.5])
    Fig.savefig("rangetodclland.pdf", bbox_inches="tight")
    Fig, _ = plot_torange(20, "C_{L_{TO}}", [3.5, 4.5, 5.5])
    Fig.savefig("rangetodclto.pdf", bbox_inches="tight")
