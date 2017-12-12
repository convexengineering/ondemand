import numpy as np
from scipy.interpolate import interp1d
from plotting import labelLines
from stol import Mission, baseline, advanced
from gpkit.tools import autosweep_1d
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':19})

clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
clrs2 = ["#4F090C", "#9D1317", "#EC1C23", "#F2686C", "#F9B3B6"]*5

def plot_trade(model, minx, xvar, xex, yvar, ymax, zvar, zrange, xlabel,
               ylabel, xllabel, fsl=12, svar=None, senslabel=None):

    del model.substitutions[xvar]
    fig, ax = plt.subplots()
    if svar:
        fis, axs = plt.subplots()
        fig = [fig, fis]
    i = 0
    Nsweep = 100
    xplot = 0

    for z in zrange:
        model.substitutions.update({zvar: z})
        model.cost = xvar if minx else 1/xvar
        sol = model.solve("mosek", verbosity=0)
        model.cost = yvar
        xmin = sol(xvar).magnitude*1.01 if minx else xex
        xmax = xex if minx else sol(xvar).magnitude*0.99
        xplot = xmax if xmax > xplot else xplot
        bst = autosweep_1d(model, 0.1, model[xvar], [xmin, xmax], verbosity=0)
        _x = np.linspace(xmin, xmax, Nsweep)
        if svar:
            for sv, cls in zip(svar, [clrs, clrs2]):
                sensland = bst.solarray["sensitivities"]["constants"][sv]
                xp = bst.solarray(xvar).magnitude
                f = interp1d(xp, sensland)
                sensland = f(_x)
                axs.plot(_x, np.abs(sensland), c=cls[i])
        y = bst.sample_at(_x)(yvar)
        lstr = "%d" if isinstance(z, int) else "%.1f"
        ax.plot(_x, y, c=clrs[i], lw=2, label=lstr % z)
        i += 1

    ax.grid()
    ax.set_ylim([0, ymax])
    ax.set_xlim([0, xplot])
    labelLines(ax.lines, align=False, xvals=xllabel, fontsize=fsl)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if svar:
        axs.set_ylabel(senslabel)
        axs.grid()
        axs.set_xlim([0, xmax])
        axs.set_xlabel(xlabel)
        ax = [ax, axs]

    return fig, ax

if __name__ == "__main__":
    path = "../docs/"
    M = Mission(sp=False)
    baseline(M)
    fig, ax = plot_trade(M, minx=True, xvar=M.Srunway, xex=800,
                        yvar=M.aircraft.W,
                        ymax=8000, zvar=M.aircraft.Npax, zrange=range(2, 9),
                        xlabel="Runway Length [ft]",
                        ylabel="Max Takeoff Weight [lbf]", xllabel=[450]*7,
                        fsl=14, svar=[M.landing.CLland, M.takeoff.CLto],
                        senslabel="Sensitivity to Constraints")
    ax[1].set_ylim([-2, 10])
    ax[1].text(125, -0.75, "Takeoff", ha="center")
    ax[1].text(210, 8, "Landing")
    fig[0].savefig(path + "sw_mtow.pdf", bbox_inches="tight")
    fig[1].savefig(path + "sw_mtowsens.pdf", bbox_inches="tight")
    advanced(M)
    fig, ax = plot_trade(M, minx=True, xvar=M.Srunway, xex=800,
                        yvar=M.aircraft.W,
                        ymax=8000, zvar=M.aircraft.Npax, zrange=range(2, 9),
                        xlabel="Runway Length [ft]",
                        ylabel="Max Takeoff Weight [lbf]", xllabel=[450]*7,
                        fsl=14, svar=[M.landing.CLland, M.takeoff.CLto],
                        senslabel="Sensitivity to Constraints")
    ax[1].set_ylim([-2, 10])
    ax[1].text(25, -0.75, "Takeoff")
    ax[1].text(65, 8, "Landing")
    fig[0].savefig(path + "sw_mtowt.pdf", bbox_inches="tight")
    fig[1].savefig(path + "sw_mtowtsens.pdf", bbox_inches="tight")
    baseline(M)
    fig, ax = plot_trade(M, minx=False, xvar=M.cruise.Vmin, xex=1,
                         yvar=M.aircraft.W, ymax=8000, zvar=M.cruise.R,
                         zrange=[100, 125, 150],
                         xlabel="Minimum Cruise Speed ($V_{\mathrm{min}}$) [kts]",
                         ylabel="Max Takeoff Weight [lbf]",
                         xllabel=[130, 120, 110],
                         fsl=14)
    ax.set_xlim([20, 160])
    ax.fill_between([20, 90], 0, 8000, facecolor="None", edgecolor="k",
                    hatch="/", lw=1)
    ax.text(40, 1300, "$V_{\mathrm{cruise}} \geq V_{\mathrm{min}}$\n inactive", ha="center")
    ax.text(110, 1300, "$V_{\mathrm{cruise}} \geq V_{\mathrm{min}}$\n active", ha="center")
    fig.savefig(path + "vweightR.pdf", bbox_inches="tight")
    baseline(M)
    fig, ax = plot_trade(M, minx=False, xvar=M.cruise.Vmin, xex=1,
                         yvar=M.aircraft.W, ymax=8000, zvar=M.Srunway,
                         zrange=[200, 400, 600],
                         xlabel="Minimum Cruise Speed ($V_{\mathrm{min}}$) [kts]",
                         ylabel="Max Takeoff Weight [lbf]",
                         xllabel=[81, 117, 138],
                         fsl=14)
    ax.set_xlim([20, 180])
    ax.fill_between([20, 60], 0, 8000, facecolor="None", edgecolor="k",
                    hatch="/", lw=1)
    ax.text(40, 1300, "$V_{\mathrm{cruise}} \geq V_{\mathrm{min}}$\n inactive", ha="center")
    ax.text(80, 1300, "$V_{\mathrm{cruise}} \geq V_{\mathrm{min}}$\n active", ha="center")
    fig.savefig(path + "vweightS.pdf", bbox_inches="tight")
    baseline(M)
    fig, _ = plot_trade(M, minx=True, xvar=M.Srunway, xex=800,
                        yvar=M.aircraft.W,
                        ymax=8000, zvar=M.landing.CLland,
                        zrange=[3.5, 4.0, 4.5],
                        xlabel="Runway Length [ft]",
                        ylabel="Max Takeoff Weight [lbf]",
                        xllabel=[245, 225, 212],
                        fsl=14)
    fig.savefig(path + "smtow_clmax.pdf", bbox_inches="tight")
    baseline(M)
    fig, _ = plot_trade(M, minx=True, xvar=M.Srunway, xex=800,
                        yvar=M.aircraft.W,
                        ymax=8000, zvar=M.landing.gload,
                        zrange=[0.4, 0.6, 0.7],
                        xlabel="Runway Length [ft]",
                        ylabel="Max Takeoff Weight [lbf]",
                        xllabel=[235, 180, 200],
                        fsl=14)
    fig.savefig(path + "smtow_gl.pdf", bbox_inches="tight")
    baseline(M)
    fig, _ = plot_trade(M, minx=True, xvar=M.Srunway, xex=800,
                        yvar=M.aircraft.W,
                        ymax=8000, zvar=M.aircraft.hbatt,
                        zrange=[210, 250, 300],
                        xlabel="Runway Length [ft]",
                        ylabel="Max Takeoff Weight [lbf]",
                        xllabel=[225, 210, 210],
                        fsl=14)
    fig.savefig(path + "smtow_hbatt.pdf", bbox_inches="tight")

