import numpy as np
from scipy.interpolate import interp1d
from stol import Mission
from gpkit.tools import autosweep_1d
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':19})

def plot_range():
    M = Mission(sp=False)
    M.substitutions.update({"V_{min}": 100, "W_{pay}": 195*4,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 4.0})

    del M.substitutions["R"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for srun in [300, 500, 5000]:
        M.substitutions.update({"S_{runway}": srun})
        M.cost = 1/M["R"]
        sol = M.solve("mosek")
        M.cost = M[M.aircraft.topvar("W")]
        Rmax = sol("R").magnitude-5
        Rmin = 5
        bst = autosweep_1d(M, 0.1, M["R"], [Rmin, Rmax])
        _x = np.linspace(Rmin, Rmax, 100)
        mtow = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, mtow, c=clrs[i], lw=2,
                label="$S_{\\mathrm{runway}} = %d$" % srun)
        i += 1

    ax.grid()
    ax.set_ylim([0, 10000])
    ax.set_xlabel("Range [nmi]")
    ax.set_ylabel("Max Takeoff Weight [lbf]")
    fig.savefig("range.pdf", bbox_inches="tight")

def plot_runway():
    M = Mission(sp=False)
    M.substitutions.update({"V_{min}": 100, "W_{pay}": 195*4,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 4.0})

    del M.substitutions["R"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for wtot in [2000, 3000, 4000]:
        M.substitutions.update({M.aircraft.topvar("W"): wtot})
        M.cost = 1./M["R"]
        Smin = 200
        Smax = 800
        bst = autosweep_1d(M, 0.1, M["S_{runway}"], [Smin, Smax])
        _x = np.linspace(Smin, Smax, 100)
        rng = bst.sample_at(_x)("R")
        ax.plot(_x, rng, c=clrs[i], lw=2,
                label="$W_{\\mathrm{MTO}} = %d$ [lbs]" % wtot)
        i += 1

    ax.grid()
    ax.set_ylim([0, 8000])
    ax.set_xlabel("Runway Length [ft]")
    ax.set_ylabel("Range [nmi]")
    fig.savefig("runway.pdf", bbox_inches="tight")

def plot_vminS():
    M = Mission(sp=False)
    M.substitutions.update({"R": 100, "W_{pay}": 195*5,
                            "g_{loading}": 0.4, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 3.5})

    del M.substitutions["V_{min}"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for srun in [200, 400, 600]:
        M.substitutions.update({"S_{runway}": srun})
        M.cost = 1/M["V_{min}"]
        sol = M.solve("mosek")
        M.cost = M[M.aircraft.topvar("W")]
        Vmin = 50
        Vmax = sol("V_{min}").magnitude-1
        bst = autosweep_1d(M, 0.01, M["V_{min}"], [Vmin, Vmax])
        _x = np.linspace(Vmin, Vmax, 100)
        mtow = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, mtow, c=clrs[i], lw=2,
                label="$S_{\\mathrm{runway}} = %d$ [ft]" % srun)
        i += 1

    ax.grid()
    ax.set_ylim([0, 8000])
    ax.set_xlabel("Minimum Cruise Speed [kts]")
    ax.set_ylabel("Max Takeoff Weight [lbf]")
    fig.savefig("vweightS.pdf", bbox_inches="tight")

def plot_vminR():
    M = Mission(sp=False)
    M.substitutions.update({"S_{runway}": 400, "W_{pay}": 195*5,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 3.5})

    del M.substitutions["V_{min}"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for rng in [100, 125, 150]:
        M.substitutions.update({"R": rng})
        M.cost = 1/M["V_{min}"]
        sol = M.solve("mosek")
        M.cost = M[M.aircraft.topvar("W")]
        Vmin = 50
        Vmax = sol("V_{min}").magnitude-1
        bst = autosweep_1d(M, 0.01, M["V_{min}"], [Vmin, Vmax])
        _x = np.linspace(Vmin, Vmax, 100)
        mtow = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, mtow, c=clrs[i], lw=2,
                label="$R = %d$ [nmi]" % rng)
        i += 1

    ax.grid()
    ax.set_ylim([0, 8000])
    ax.set_xlabel("Minimum Cruise Speed [kts]")
    ax.set_ylabel("Max Takeoff Weight [lbf]")
    fig.savefig("vweightR.pdf", bbox_inches="tight")

def plot_pass():
    M = Mission(sp=False)
    M.substitutions.update({"S_{runway}": 400, "V_{min}": 100,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 4.0})

    del M.substitutions["W_{pay}"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for rng in [100, 120, 150]:
        M.substitutions.update({"R": rng})
        M.cost = M[M.aircraft.topvar("W")]
        Pmin = 1.*195
        Pmax = 8.*195
        bst = autosweep_1d(M, 0.1, M["W_{pay}"], [Pmin, Pmax])
        _x = np.linspace(Pmin, Pmax, 100)
        mtow = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x/195., mtow, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_ylim([0, 10000])
    ax.set_xlabel("Number of Passengers")
    ax.set_ylabel("Max Takeoff Weight [lbf]")
    fig.savefig("passweight.pdf", bbox_inches="tight")

def plot_cost():
    M = Mission(sp=False, costModel=True)
    M.substitutions.update({"S_{runway}": 400, "V_{min}": 100,
                            "g_{loading}": 0.4, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 3.5})

    del M.substitutions["W_{pay}"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for rng in [100, 150]:
        M.substitutions.update({"R": rng})
        M.cost = M["Cost_per_trip"]
        Pmin = 1.*195
        Pmax = 8.*195
        bst = autosweep_1d(M, 0.05, M["W_{pay}"], [Pmin, Pmax])
        _x = np.linspace(Pmin, Pmax, 100)
        cst = bst.sample_at(_x)("Cost_per_trip")
        ax.plot(_x/195., cst*195./_x, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_ylim([0, 150])
    ax.set_xlabel("Number of Passengers")
    ax.set_ylabel("Cost Per Passenger [\\$]")
    fig.savefig("passcost.pdf", bbox_inches="tight")

def plot_costS():
    M = Mission(sp=False, costModel=True)
    M.substitutions.update({"R": 100, "V_{min}": 100,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 4.0})

    del M.substitutions["W_{pay}"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for srun in [250, 500]:
        M.substitutions.update({"S_{runway}": srun})
        M.cost = M["Cost_per_trip"]
        Pmin = 1.*195
        Pmax = 8.*195
        bst = autosweep_1d(M, 0.1, M["W_{pay}"], [Pmin, Pmax])
        _x = np.linspace(Pmin, Pmax, 100)
        cst = bst.sample_at(_x)("Cost_per_trip")
        ax.plot(_x/195., cst*195./_x, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_xlabel("Number of Passengers")
    ax.set_ylabel("Cost Per Passenger")
    fig.savefig("passcostS.pdf", bbox_inches="tight")

def plot_CLmax():
    M = Mission(sp=False)
    M.substitutions.update({"R": 100, "V_{min}": 100,
                            "g_{loading}": 0.3, "W_{pay}": 195*4,
                            "C_{L_{land}}": 4.0})

    del M.substitutions["C_{L_{TO}}"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for mtow in [3000, 4000]:
        M.substitutions.update({M.aircraft.topvar("W"): mtow})
        M.cost = M["S_{runway}"]
        CLmin = 3
        CLmax = 6
        bst = autosweep_1d(M, 0.1, M["C_{L_{TO}}"], [CLmin, CLmax])
        _x = np.linspace(CLmin, CLmax, 100)
        srun = bst.sample_at(_x)("S_{runway}")
        ax.plot(_x, srun, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_xlabel("$C_{L_{TO}}$")
    ax.set_ylabel("Runway Length [ft]")
    fig.savefig("clto.pdf", bbox_inches="tight")

def plot_vminWp():
    M = Mission(sp=False)
    M.substitutions.update({"S_{runway}": 600, "R": 100,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 4.0})

    del M.substitutions["V_{min}"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for wpay in [2, 4, 6, 8]:
        M.substitutions.update({"W_{pay}": 195.*wpay})
        M.cost = 1/M["V_{min}"]
        sol = M.solve("mosek")
        M.cost = M[M.aircraft.topvar("W")]
        Vmin = 50
        Vmax = sol("V_{min}").magnitude-1
        bst = autosweep_1d(M, 0.1, M["V_{min}"], [Vmin, Vmax])
        _x = np.linspace(Vmin, Vmax, 100)
        mtow = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, mtow, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_ylim([0, 10000])
    ax.set_xlabel("Minimum Cruise Speed [kts]")
    ax.set_ylabel("Max Takeoff Weight [lbf]")
    fig.savefig("vweightWp.pdf", bbox_inches="tight")

def plot_srunwpay():
    M = Mission(sp=False)
    M.substitutions.update({"R": 100, "V_{min}": 100,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 4.5})

    del M.substitutions["W_{pay}"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    M.cost = 1./M["W_{pay}"]
    Smin = 400
    Smax = 800
    bst = autosweep_1d(M, 0.1, M["S_{runway}"], [Smin, Smax])
    _x = np.linspace(Smin, Smax, 100)
    pay = bst.sample_at(_x)("W_{pay}")
    ax.plot(_x, pay, c=clrs[i], lw=2)
    i += 1

    ax.grid()
    ax.set_xlabel("Runway Length [ft]")
    ax.set_ylabel("Payload Weight [lbs]")
    fig.savefig("srunwpay.pdf", bbox_inches="tight")

def plot_sw_pay():
    M = Mission(sp=False)
    M.substitutions.update({"R": 100, "V_{min}": 100,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 3.5})

    del M.substitutions["W_{pay}"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for mtow in [2000, 3000, 4000, 5000, 6000]:
        M.substitutions.update({M.aircraft.topvar("W"): mtow})
        M.cost = 1./M["W_{pay}"]
        Smin = 250
        Smax = 800
        bst = autosweep_1d(M, 0.01, M["S_{runway}"], [Smin, Smax])
        _x = np.linspace(Smin, Smax, 100)
        pay = bst.sample_at(_x)("W_{pay}")/195.
        ax.plot(_x, pay, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_xlabel("Runway Length [ft]")
    ax.set_ylabel("Number of Passengers")
    fig.savefig("srunwpay.pdf", bbox_inches="tight")

def plot_sw_mtow():
    M = Mission(sp=False)
    M.substitutions.update({"R": 100, "V_{min}": 100,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 3.5})

    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    fig2, ax2 = plt.subplots()
    i = 0
    for npax in range(2, 9):
        M.substitutions.update({"W_{pay}": npax*195.})
        M.cost = M["S_{runway}"]
        sol = M.solve("mosek")
        M.cost = M.aircraft.topvar("W")
        Smin = sol("S_{runway}").magnitude + 5
        Smax = 800
        bst = autosweep_1d(M, 0.1, M["S_{runway}"], [Smin, Smax])
        _x = np.linspace(Smin, Smax, 100)
        sensland = bst.solarray["sensitivities"]["constants"]["C_{L_{land}}"]
        xp = bst.solarray("S_{runway}").magnitude
        f = interp1d(xp, sensland)
        sensland = f(_x)
        ax2.plot(_x, sensland, c=clrs[i])
        pay = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, pay, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_ylim([0, 8000])
    ax.set_xlim([0, 800])
    ax.set_xlabel("Runway Length [ft]")
    ax.set_ylabel("Max Take Off Weight [lbs]")
    fig.savefig("sw_mtow.pdf", bbox_inches="tight")

    ax2.set_ylabel("Sensitivity to CLmax")
    ax2.grid()
    ax2.set_xlim([0, 800])
    ax2.set_xlabel("Runway Length [ft]")
    fig2.savefig("sw_mtowsens.pdf", bbox_inches="tight")

def plot_rangev():
    M = Mission(sp=False)
    M.substitutions.update({"S_{runway}": 400, "W_{pay}": 195*6,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 3.5})

    del M.substitutions["R"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for vmin in [100, 125, 150]:
        M.substitutions.update({"V_{min}": vmin})
        M.cost = 1/M["R"]
        sol = M.solve("mosek")
        M.cost = M[M.aircraft.topvar("W")]
        Rmax = sol("R").magnitude-5
        Rmin = 5
        bst = autosweep_1d(M, 0.01, M["R"], [Rmin, Rmax])
        _x = np.linspace(Rmin, Rmax, 100)
        mtow = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, mtow, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_ylim([0, 10000])
    ax.set_xlabel("Range [nmi]")
    ax.set_ylabel("Max Takeoff Weight [lbf]")
    fig.savefig("rangev.pdf", bbox_inches="tight")

def plot_runwayv():
    M = Mission(sp=False)
    M.substitutions.update({"R": 400, "W_{pay}": 195*6,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "C_{L_{land}}": 3.5})

    del M.substitutions["R"]
    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    i = 0
    for vmin in [100, 125, 150]:
        M.substitutions.update({"V_{min}": vmin})
        M.cost = 1/M["R"]
        sol = M.solve("mosek")
        M.cost = M[M.aircraft.topvar("W")]
        Rmax = sol("R").magnitude-5
        Rmin = 5
        bst = autosweep_1d(M, 0.01, M["R"], [Rmin, Rmax])
        _x = np.linspace(Rmin, Rmax, 100)
        mtow = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, mtow, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_ylim([0, 10000])
    ax.set_xlabel("Range [nmi]")
    ax.set_ylabel("Max Takeoff Weight [lbf]")
    fig.savefig("rangev.pdf", bbox_inches="tight")

def plot_smtow_clmax():
    M = Mission(sp=False)
    M.substitutions.update({"R": 100, "V_{min}": 100,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "W_{pay}": 5.*195})

    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    fig2, ax2 = plt.subplots()
    i = 0
    for clland in [3.5, 4.0, 4.5]:
        M.substitutions.update({"C_{L_{land}}": clland})
        M.cost = M["S_{runway}"]
        sol = M.solve("mosek")
        M.cost = M.aircraft.topvar("W")
        Smin = sol("S_{runway}").magnitude + 5
        Smax = 800
        bst = autosweep_1d(M, 0.01, M["S_{runway}"], [Smin, Smax])
        _x = np.linspace(Smin, Smax, 100)
        pay = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, pay, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_ylim([0, 8000])
    ax.set_xlim([0, 800])
    ax.set_xlabel("Runway Length [ft]")
    ax.set_ylabel("Max Take Off Weight [lbs]")
    fig.savefig("smtow_clmax.pdf", bbox_inches="tight")

def plot_hbatt():
    M = Mission(sp=False)
    M.substitutions.update({"R": 100, "V_{min}": 100, "C_{L_{land}}": 3.5,
                            "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
                            "W_{pay}": 5.*195})

    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    fig2, ax2 = plt.subplots()
    i = 0
    for hbatt in [210, 250, 300]:
        M.substitutions.update({"h_{batt}": hbatt})
        M.cost = M["S_{runway}"]
        sol = M.solve("mosek")
        M.cost = M.aircraft.topvar("W")
        Smin = sol("S_{runway}").magnitude + 5
        Smax = 800
        bst = autosweep_1d(M, 0.01, M["S_{runway}"], [Smin, Smax])
        _x = np.linspace(Smin, Smax, 100)
        pay = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, pay, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_ylim([0, 8000])
    ax.set_xlim([0, 800])
    ax.set_xlabel("Runway Length [ft]")
    ax.set_ylabel("Max Take Off Weight [lbs]")
    fig.savefig("smtow_hbatt.pdf", bbox_inches="tight")

def plot_gl():
    M = Mission(sp=False)
    M.substitutions.update({"R": 100, "V_{min}": 100, "C_{L_{land}}": 3.5,
                            "C_{L_{TO}}": 4.0,
                            "W_{pay}": 5.*195})

    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    fig2, ax2 = plt.subplots()
    i = 0
    for gl in [0.3, 0.4, 0.5]:
        M.substitutions.update({"g_{loading}": gl})
        M.cost = M["S_{runway}"]
        sol = M.solve("mosek")
        M.cost = M.aircraft.topvar("W")
        Smin = sol("S_{runway}").magnitude + 5
        Smax = 800
        bst = autosweep_1d(M, 0.01, M["S_{runway}"], [Smin, Smax])
        _x = np.linspace(Smin, Smax, 100)
        pay = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, pay, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_ylim([0, 8000])
    ax.set_xlim([0, 800])
    ax.set_xlabel("Runway Length [ft]")
    ax.set_ylabel("Max Take Off Weight [lbs]")
    fig.savefig("smtow_gl.pdf", bbox_inches="tight")

def plot_sw_mtowtech():
    M = Mission(sp=False)
    M.substitutions.update({"R": 100, "V_{min}": 100, "h_{batt}": 300,
                            "m_{fac}_Mission/GLanding": 1.2,
                            "m_{fac}_Mission/TakeOff": 1.2,
                            "sp_{motor}": 7./9.81*0.8,
                            "f_{ref}": 1.1,
                            "g_{loading}": 0.5, "C_{L_{TO}}": 5.0,
                            "C_{L_{land}}": 4.5})

    clrs = ["#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#7bccc4"]*5
    fig, ax = plt.subplots()
    fig2, ax2 = plt.subplots()
    i = 0
    for npax in range(2, 9):
        M.substitutions.update({"W_{pay}": npax*195.})
        M.cost = M["S_{runway}"]
        sol = M.solve("mosek")
        M.cost = M.aircraft.topvar("W")
        Smin = sol("S_{runway}").magnitude + 5
        Smax = 800
        bst = autosweep_1d(M, 0.1, M["S_{runway}"], [Smin, Smax])
        _x = np.linspace(Smin, Smax, 100)
        sensland = bst.solarray["sensitivities"]["constants"]["C_{L_{land}}"]
        xp = bst.solarray("S_{runway}").magnitude
        f = interp1d(xp, sensland)
        sensland = f(_x)
        ax2.plot(_x, sensland, c=clrs[i])
        pay = bst.sample_at(_x)(M.aircraft.topvar("W"))
        ax.plot(_x, pay, c=clrs[i], lw=2)
        i += 1

    ax.grid()
    ax.set_ylim([0, 8000])
    ax.set_xlim([0, 800])
    ax.set_xlabel("Runway Length [ft]")
    ax.set_ylabel("Max Take Off Weight [lbs]")
    fig.savefig("sw_mtowt.pdf", bbox_inches="tight")

    ax2.set_ylabel("Sensitivity to landing constraints")
    ax2.grid()
    ax2.set_xlabel("Runway Length [ft]")
    fig2.savefig("sw_mtowtsens.pdf", bbox_inches="tight")

if __name__ == "__main__":
    # plot_runway()
    plot_vminS()
    # plot_vminR()
    # plot_cost()
    # plot_costS()
    # plot_CLmax()
    # plot_vminWp()
    # plot_sw_mtow()
    # plot_rangev()
    # plot_smtow_clmax()
    # plot_hbatt()
    # plot_gl()
    # plot_sw_mtowtech()

