" Landing distance model "
from numpy import pi
from gpkit import Variable, Model, units, SignomialsEnabled
from gpkit.constraints.tight import Tight as TCS
from gpkit.tools.tools import te_exp_minus1 as em1
from flightstate import FlightState
from stol_aircraft import testAircraft, HelioCourier

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
        mu = Variable("\\mu", 0.024, "-", "coefficient of friction")
        mu_b = Variable("\\mu_b", 0.5, "-", "Braking coefficient of friction")
        T_rev = Variable("T", "lbf", "Reverse thrust")
        cda = Variable("CDA", 0.024, "-", "parasite drag coefficient")

        CLg = Variable("C_{L_g}", "-", "ground lift coefficient")
        CDg = Variable("C_{D_g}", "-", "grag ground coefficient")
        #CLmax   = Variable("C_{L_{max}}", 2.5, "-", "max lift coefficient")
        Vstall = Variable("V_{stall}", "knots", "stall velocity")
        Sgr = Variable("S_{gr}", "ft", "landing ground roll")
        Slnd = Variable("S_{land}", "ft", "landing distance")
        etaprop = Variable("\\eta_{prop}", 0.05, "-", "propellor efficiency")
        lnd_mrg = Variable("m_{fac}", 1.2, "-", "Landing safety margin")
        CLland = Variable("C_{L_{land}}", 3.5, "-", "landing CL")
        cdp = Variable("c_{d_{p_{stall}}}", 0.025, "-",
                       "profile drag at Vstallx1.2")

        constraints = [
            T_rev == aircraft["P_{shaft-max}"]*etaprop/fs["V"],
            CLg == CLland/1.2**.5,
            Vstall == (2.*aircraft.topvar("W")/fs["\\rho"]/aircraft["S"]
                       / CLland)**0.5,
            fs["V"] >= 1.2*Vstall,
            Slnd >= lnd_mrg * Sgr,
            TCS([(B*aircraft.topvar("W")/g + 0.5*fs["\\rho"]*aircraft["S"]*mu*CLland<=
                  0.5*fs["\\rho"]*aircraft["S"]*CDg)]),
            ]

        with SignomialsEnabled():
            constraints.extend([
                TCS([em1(Sgr*2*B, 3) >= B*fs["V"]**2./A]),
                CDg <= cda + cdp + CLland**2/pi/aircraft["AR"]/aircraft["e"],
                TCS([A/g <= T_rev/aircraft.topvar("W") + mu + mu_b]),
                ])

        return constraints, fs

if __name__ == "__main__":
    ac = testAircraft()
    M = Landing(ac, sp=True)
    M.cost = M["S_{land}"]
    sol = M.localsolve("mosek")
    #sol = M.debug("mosek")
    print sol.table()

    #hc = HelioCourier()
    #M  = Landing(hc)
    ##M.cost = 1/M["S_{land}"]
    #sol    = M.solve("mosek")
    #print sol.table()
