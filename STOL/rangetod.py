" trade off between aircraft range and take off distance "
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from stol import Mission
from gpkit.tools.autosweep import autosweep_1d
import cPickle as pkl
plt.rcParams.update({'font.size':19})

# pylint: disable=invalid-name, too-many-locals
def plot_torange(N, vname, vrange):
    " plot trade studies of weight, range, and TO distance "

    model = Mission(sp=False)
    del model.substitutions["R"]
    model.substitutions["g_{loading}"] = 1.0
    sto = np.linspace(100, 500, N)

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

def run_RNWY_RNG_PAY_V_trade_point(filename, srunway, range_nmi, payload_lbs, min_speed_kts=120):
    """Set up and solve the model for a specified:
        srunway         Runway length, in ft
        range_nmi       Cruise range, in nautical miles
        payload_lbs     Payload weight, in lbs
        min_speed_kts   Minimum cruise speed, in knots.  Defaults to 120

        Output of sol.table() is written to .out file

        solution array is returned for futher processing

    """
    M = Mission(sp=False)
    del M.substitutions["R"]
    del M.substitutions["W_{pay}"]
    M.cost = M.aircraft.topvar("W")
    M.substitutions["V_{min}"] = min_speed_kts
    M.substitutions.update({"S_{runway}": srunway,
                            "R": range_nmi,
                            "W_{pay}": payload_lbs})

    sol = run_single_point(M, filename)

    return sol
def run_RNWY_RNG_PAY_V_g_trade_point(filename, srunway, range_nmi, payload_lbs, min_speed_kts, glnd):
    """Set up and solve the model for a specified:
        srunway         Runway length, in ft
        range_nmi       Cruise range, in nautical miles
        payload_lbs     Payload weight, in lbs
        min_speed_kts   Minimum cruise speed, in knots.  Defaults to 120

        Output of sol.table() is written to .out file

        solution array is returned for futher processing

    """
    M = Mission(sp=False)
    del M.substitutions["R"]
    del M.substitutions["W_{pay}"]
    del M.substitutions["g_{loading}"]
    M.cost = M.aircraft.topvar("W")
    M.substitutions["V_{min}"] = min_speed_kts
    M.substitutions.update({"S_{runway}": srunway,
                            "R": range_nmi,
                            "W_{pay}": payload_lbs,
                            "g_{loading}":glnd})

    sol = run_single_point(M, filename)

    return sol
def run_cost_trade_point(filename, srunway, range_nmi, payload_lbs, min_speed_kts, glnd):
    """Set up and solve the model for a specified:
        srunway         Runway length, in ft
        range_nmi       Cruise range, in nautical miles
        payload_lbs     Payload weight, in lbs
        min_speed_kts   Minimum cruise speed, in knots.  Defaults to 120

        Output of sol.table() is written to .out file

        solution array is returned for futher processing

    """
    M = Mission(sp=False)
    del M.substitutions["R"]
    del M.substitutions["W_{pay}"]
    del M.substitutions["g_{loading}"]
    M.cost = M["Cost_per_trip"]
    M.substitutions["V_{min}"] = min_speed_kts
    M.substitutions.update({"S_{runway}": srunway,
                            "R": range_nmi,
                            "W_{pay}": payload_lbs,
                            "g_{loading}":glnd})

    sol = run_single_point(M, filename)

    return sol
def run_single_point(M, filename):
    """
    Solve a single model, and dump the results of sol.table() into a .out file
    return the solution array for futher processing
    """
    sol = M.solve("mosek")
    fname = filename+".out"
    fid = open(fname, "w+")
    fid.write(sol.table())
    fid.close()
    return sol


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
                    label="$S_{\\mathrm{runwawy}} = %d [ft]$" % s)
            axv.plot(solR, fbatt, color=clrs[i],
                     label="$S_{\\mathrm{runway}} = %d [ft]$" % s)
            # ax.plot(Rknee[-1], wint, marker='o', color="k", markersize=5)
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


def print_summary(sol):
    print "\n\n----Output Summary----\n"
    print "----Weights Summary----"
    MTOW = sol["freevariables"]["W_Mission/Aircraft"].magnitude
    print "MTO: %5.0f lb" % (MTOW)
    WBat = sol["freevariables"]["W_{batt}"].magnitude
    WPay = sol["constants"]["W_{pay}"].magnitude
    print "Battery: %5.0f lbs \t\t %2.1f %%MTOW"%(WBat, WBat/MTOW*100.)
    print "Payload: %5.0f lbs \t\t %2.1f %%MTOW"%(WPay, WPay/MTOW*100.)
    WStruct= sol["freevariables"]["W_{struct}"].magnitude
    Wmotor= sol["freevariables"]["W_{motor}"].magnitude
    Wwing = sol["freevariables"]["W_Mission/Aircraft/Wing"].magnitude
    OEW   = WStruct+Wmotor+Wwing
    print "OEW    : %5.0f lbs \t\t %2.1f %%MTOW"%(OEW, OEW/MTOW*100.)
    print "Struct : %5.0f lbs \t\t %2.1f %%MTOW"%(WStruct, WStruct/MTOW*100.)
    print "Motor  : %5.0f lbs \t\t %2.1f %%MTOW"%(Wmotor, Wmotor/MTOW*100.)
    print "Wing   : %5.0f lbs \t\t %2.1f %%MTOW"%(Wwing, Wwing/MTOW*100.)
    print "Useful load: %5.0f" % (WBat+WPay)

    print"_______________________\n"
    print "W/S: %3.1f lbs/ft^2" % (sol["freevariables"]["W/S_Mission/Aircraft"].magnitude)
    print "P/W: %3.3f hp/lb" % (sol["freevariables"]["P/W"].magnitude)
    print "PFEI: %3.2f "%(sol["freevariables"]["PFEI"].magnitude)
    print "b: %3.1f ft"%(sol["freevariables"]["b"].magnitude)
    print "L/D: %3.1f"%(sol["freevariables"]["C_L"]/sol["freevariables"]["C_D"])
    print "AR: %3.1f"%(sol["freevariables"]["AR"])
    print "Cruise CL: %3.3f"%(sol["freevariables"]["C_L"])
    print "V_REF: %4.1f kts"%(sol["freevariables"]["V_{ref}"].magnitude)
    print "V_cruise: %4.1f kts"%sol["freevariables"]["V_Mission/Cruise/AircraftPerf/FlightState"].magnitude
    print "______"
    print "S_land: %4.0f ft"%(sol["freevariables"]["S_{land}"].magnitude)
    print "S_gr, l: %4.0f ft"%(sol["freevariables"]["S_{gr}"].magnitude)
    print "S_TO: %4.0f ft"%(sol["freevariables"]["S_{TO}"].magnitude)
    print "S_gr, t: %4.0f ft"%(sol["freevariables"]["S_{ground}"].magnitude)

if __name__ == "__main__":
    import sys
    #RNWY = 250
    #RNG  = 150
    #PAY  = 195*20
    #VCR  = 120

    RNWYs = [300]
    RNGs  = [50, 100, 150, 200]
    PAYs  = [p*195 for p in [4,6,8,10,20]]
    VCRs  = [80, 100, 120, 140, 160]  #Becomes prim. infeasible for 250ft runway, 160 kts, 200nmi range, 3900lbs payload
    gLNDs  = [.5, .7, 1]

    for RNWY in RNWYs:
        for RNG in RNGs:
            for PAY in PAYs:
                for VCR in VCRs:
                    for gLND in gLNDs:

                        filename = "Analysis/RNWY_%4.0f_RNG_%4.0f_PAY_%4.0f_V_%3.0f_GLND_%3.0f" % \
                            (RNWY, RNG, PAY, VCR, gLND*10)
                        sys.stdout = open(filename+'.sum', 'w+')
                        try:
                            sol = run_RNWY_RNG_PAY_V_g_trade_point(filename,RNWY, RNG, PAY, VCR, gLND)
                            print_summary(sol)
                        except:
                            print "---Error---"
    """
    M = Mission(sp=False)
    del M.substitutions["R"]
    Figs = plot_wrange(M, [100, 200, 350, 500], 10, plot=True)
    Figs[0].savefig("mtowrangew.pdf", bbox_inches="tight")
    Figs[1].savefig("landingsens.pdf", bbox_inches="tight")
    Figs[2].savefig("vrange.pdf", bbox_inches="tight")
    Fig, _ = plot_torange(20, "W_{pay}", [800])
    Fig.savefig("rangetodwpay.pdf", bbox_inches="tight")
    Fig, _ = plot_torange(20, "g_{loading}", [1, .7, .5])
    Fig.savefig("rangetodgland.pdf", bbox_inches="tight")
    """
    #Fig, _ = plot_torange(20, "C_{L_{land}}", [2.5, 3.5, 4.5])
    #Fig.savefig("rangetodclland.pdf", bbox_inches="tight")
    #Fig, _ = plot_torange(20, "C_{L_{TO}}", [2.5, 3.5, 4.5])
    #Fig.savefig("rangetodclto.pdf", bbox_inches="tight")
