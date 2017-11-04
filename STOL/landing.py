" Landing distance model "
from numpy import pi
import pandas as pd
import os
from gpkit import Variable, Model, units, SignomialsEnabled
from gpkit.constraints.tight import Tight as TCS
from gpfit.fit_constraintset import FitCS
from gpkit.tools.tools import te_exp_minus1 as em1
from flightstate import FlightState
from stol_aircraft import testAircraft, HelioCourier

class dummy(Model):
    def setup(self):

        W = Variable("W", 5000, "N", "aircraft weight")
        Pshaft = Variable("P_{shaft-max}", 1e6, "W", "max shaft power")
        AR = Variable("AR", 10, "-", "aspect ratio")
        e = Variable("e", 0.8, "-", "span efficiency")
        S = Variable("S", 10, "m**2", "wing area")

        cns = [S == S]

        return cns

class Landing(Model):
    """
    Landing model
    http://www.dept.aoe.vt.edu/~lutze/AOE3104/takeoff&landing.pdf

    Landing_Margin is required additional distance for
    takeoff and landing operations (nominally 20%)
    """
    def setup(self, aircraft):

        fs = FlightState()

        A = Variable("A", "m/s**2", "log fit equation helper 1")
        B = Variable("B", "1/m", "log fit equation helper 2")

        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        mu = Variable("\\mu", 0.5, "-", "Braking coefficient of friction")
        T_rev = Variable("T", "N", "Reverse thrust")
        cda = Variable("CDA", 0.024, "-", "parasite drag coefficient")

        CLg = Variable("C_{L_g}", "-", "ground lift coefficient")
        CDg = Variable("C_{D_g}", "-", "grag ground coefficient")
        Vstall = Variable("V_{stall}", "knots", "stall velocity")
        Sgr = Variable("S_{gr}", "ft", "landing ground roll")
        Slnd = Variable("S_{land}", "ft", "landing distance")
        etaprop = Variable("\\eta_{prop}", 0.05, "-", "propellor efficiency")
        msafety = Variable("m_{fac}", 1.4, "-", "Landing safety margin")
        CLland = Variable("C_{L_{land}}", 3.5, "-", "landing CL")
        cdp = Variable("c_{d_{p_{stall}}}", 0.025, "-",
                       "profile drag at Vstallx1.2")

        path = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(path + os.sep + "logfit.csv")
        fd = df.to_dict(orient="records")[0]

        constraints = [
            T_rev == aircraft["P_{shaft-max}"]*etaprop/fs["V"],
            Vstall == (2.*aircraft.topvar("W")/fs["\\rho"]/aircraft["S"]
                       / CLland)**0.5,
            fs["V"] >= 1.2*Vstall,
            Slnd >= msafety*Sgr,
            FitCS(fd, Sgr*2*B, [A/g, B*fs["V"]**2/g]),
            ]

        with SignomialsEnabled():
            constraints.extend([
                TCS([(B*aircraft.topvar("W")/g + 0.5*fs["\\rho"]*aircraft["S"]
                      * CDg >= 0.5*fs["\\rho"]*aircraft["S"]*mu*CLland)]),
                TCS([A/g <= T_rev/aircraft.topvar("W") + mu]),
                CDg <= cda + cdp + CLland**2/pi/aircraft["AR"]/aircraft["e"],
                ])

        return constraints, fs

if __name__ == "__main__":
    ac = dummy()
    M = Landing(ac)
    M.cost = M["S_{land}"]
    sol = M.localsolve("mosek")
    print sol.table()
    # ac = testAircraft()
    # M = Landing(ac)
    # M.cost = M["S_{land}"]
    # sol = M.localsolve("mosek_cli")
    # #sol = M.debug("mosek")
    # print sol.table()

    #hc = HelioCourier()
    #M  = Landing(hc)
    ##M.cost = 1/M["S_{land}"]
    #sol    = M.solve("mosek")
    #print sol.table()
