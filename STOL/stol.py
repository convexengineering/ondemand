" short take off and landing aircraft model "
import os
import pandas as pd
from numpy import pi
from gpkit import Variable, Model, SignomialsEnabled,units
from gpkitmodels.GP.aircraft.wing.wing import Wing
from gpfit.fit_constraintset import FitCS
from flightstate import FlightState
from landing import Landing
from gpkit.constraints.tight import Tight as TCS
from gpkit.constraints.relax import ConstantsRelaxed
from cost import Cost

# pylint: disable=too-many-locals, invalid-name, unused-variable

class Aircraft(Model):
    " thing that we want to build "
    def setup(self):

        Wing.fillModel = None
        self.wing = Wing()

        W = Variable("W", "lbf", "aircraft weight")
        WS = Variable("W/S", "lbf/ft^2", "Aircraft wing loading")
        PW = Variable("P/W", "hp/lbf", "Aircraft shaft hp/weight ratio")
        Wpay = Variable("W_{pay}", 2*195, "lbf", "payload weight")
        hbatt = Variable("h_{batt}", 210, "W*hr/kg", "battery specific energy")
        etae = Variable("\\eta_{e}", 0.9, "-", "total electrical efficiency")
        Wbatt = Variable("W_{batt}", "lbf", "battery weight")
        Wwing = Variable("W_{wing}", "lbf", "wing weight")
        Pshaftmax = Variable("P_{shaft-max}", "W", "max shaft power")
        sp_motor = Variable("sp_{motor}", 7./9.81, "kW/N",
                            'Motor specific power')
        Wmotor = Variable("W_{motor}", "lbf", "motor weight")
        Wcent = Variable("W_{cent}", "lbf", "aircraft center weight")
        fstruct = Variable("f_{struct}", 0.2, "-",
                           "structural weight fraction")
        Wstruct = Variable("W_{struct}", "lbf", "structural weight")
        e = Variable("e", 0.8, "-", "span efficiency factor")
        CL_max_clean = Variable("CL_{max_{clean}}", 1.6, "-", "Clean CL max")
        CL_max_to = Variable("CL_{max_{to}}", 2.0, "-", "Clean CL max")
        CL_max_aprch = Variable("CL_{max_{aprch}}", 2.4, "-", "Clean CL max")
        fbattmax = Variable("f_{batt,max}", 1.0, "-", "max battery fraction")

        loading = self.wing.spar.loading(self.wing)
        loading.substitutions.update({loading.kappa: 0.05,
                                      loading.sigmacfrp: 1.5e9,
                                      loading.Nmax: 6,
                                      self.wing.skin.tmin: 0.012*4,
                                      self.wing.mfac: 1.4,
                                      self.wing.spar.mfac: 0.8})
        constraints = [
            Wcent == loading.W,
            WS == W/self.wing.planform.S,
            PW == Pshaftmax/W,
            TCS([W >= Wbatt + Wpay + self.wing.W + Wmotor + Wstruct]),
            Wcent >= Wbatt + Wpay + Wmotor + Wstruct,
            Wstruct >= fstruct*W,
            Wmotor >= Pshaftmax/sp_motor,
            Wbatt/W <= fbattmax,
            ]


        return constraints, self.wing, loading

    def flight_model(self):
        " what happens during flight "
        return AircraftPerf(self)

class AircraftPerf(Model):
    " simple drag model "
    def setup(self, aircraft):

        self.fs = FlightState()
        self.wing = aircraft.wing.flight_model(aircraft.wing, self.fs)
        self.wing.substitutions[self.wing.CLstall] = 5

        CD = Variable("C_D", "-", "drag coefficient")
        cda = Variable("CDA", 0.015, "-", "non-lifting drag coefficient")

        constraints = [CD >= cda + self.wing.Cd]

        return constraints, self.wing, self.fs

class Cruise(Model):
    " calculates aircraft range "
    def setup(self, aircraft):

        perf = aircraft.flight_model()

        R = Variable("R", 100, "nmi", "aircraft range")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        T = Variable("T", "lbf", "thrust")
        t_reserve = Variable("t_{reserve}", 30.,"min", "Reserve flight time")
        R_reserve = Variable("R_{reserve}", "nmi", "Reserve range")
        Vmin = Variable("V_{min}", 100, "kts", "min speed")
        Pshaft = Variable("P_{shaft}", "W", "shaft power")
        etaprop = Variable("\\eta_{prop}", 0.8, "-", "propellor efficiency")
        f_useable = Variable("f_useable", .8, "-", "Fraction of battery energy that can be used")

        constraints = [
            aircraft.topvar("W") == (0.5*perf.wing.CL*perf["\\rho"]
                                     * aircraft["S"]*perf["V"]**2),
            T >= 0.5*perf["C_D"]*perf["\\rho"]*aircraft.wing["S"]*perf["V"]**2,
            Pshaft >= T*perf["V"]/etaprop,
            perf.fs["V"] >= Vmin,
            perf["CL"] <= aircraft["CL_{max_{clean}}"],

            (R+(t_reserve*perf["V"])) <= (f_useable*(aircraft["h_{batt}"]*aircraft["W_{batt}"])/g
                  * aircraft["\\eta_{e}"]*perf["V"]/Pshaft)]

        return constraints, perf
class Climb(Model):
    " calculates aircraft range "
    def setup(self, aircraft):

        perf = aircraft.flight_model()

        ROC = Variable("ROC", 1000, "ft/min", "Target rate of climb")
        V_s = Variable("V_s",  "kts", "Stall speed in takeoff configuration")
        T_max = Variable("T_max", "lbf", "Maximum thrust")
        T_req = Variable("T_req", "lbf", "Required thrust")
        V2 = Variable("V2",  "kts", "V2")
        Pshaft = Variable("P_{shaft}", "W", "shaft power")
        etaprop = Variable("\\eta_{prop}", 0.8, "-", "propellor efficiency")

        constraints = [
            aircraft.topvar("W") == (0.5*perf["CL"]*perf["\\rho"]
                                     * aircraft["S"]*perf["V"]**2),
            perf["V"] == V2,
            T_req == 0.5*perf["C_D"]*perf["\\rho"]*aircraft.wing["S"]*perf["V"]**2,
            aircraft["P_{shaft-max}"] >= T_max*V2/etaprop,
            V2 == 1.2*V_s,
            ROC + V2*T_req/aircraft.topvar("W") <= T_max*V2/aircraft.topvar("W")
            ]
        return constraints, perf

class GLanding(Model):
    def setup(self, aircraft):

        fs = FlightState()

        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        gload = Variable("g_{loading}", 0.5, "-", "gloading constant")
        Vstall = Variable("V_{stall}", "knots", "stall velocity")
        Sgr = Variable("S_{gr}", "ft", "landing ground roll")
        Slnd = Variable("S_{land}", "ft", "landing distance")
        msafety = Variable("m_{fac}", 1.4, "-", "Landing safety margin")
        CLland = Variable("C_{L_{land}}", 3.5, "-", "landing CL")
        V_ref = Variable("V_{ref}", "kts", "Approach reference speed")
        f_ref = Variable("f_{ref}", 1.3, "-", "Approach reference speed margin above stall")

        constraints = [
            Sgr >= 0.5*fs["V"]**2/gload/g,
            Vstall == (2.*aircraft.topvar("W")/fs["\\rho"]/aircraft["S"]
                       / CLland)**0.5,
            Slnd >= msafety*Sgr,
            fs["V"] >= f_ref*Vstall,
            V_ref == fs["V"],
            ]

        return constraints, fs

class Mission(Model):
    " creates aircraft and flies it around "
    def setup(self, sp=False, costModel=False):

        Srunway = Variable("S_{runway}", "ft", "runway length")
        PFEI = Variable("PFEI", "kJ/(kg*km)", "PFEI")
        "Parameters of interest"

        self.aircraft = Aircraft()

        takeoff = TakeOff(self.aircraft, sp=sp)
        cruise  = Cruise(self.aircraft)
        mission = [cruise,
                    takeoff
                    ]
        climb   = Climb(self.aircraft)
        if costModel:
            cost    = Cost(self.aircraft)
            mission.extend([cost])

        constraints = [self.aircraft["P_{shaft-max}"] >= cruise["P_{shaft}"],
                       Srunway >= takeoff["S_{TO}"],
                       PFEI == self.aircraft["h_{batt}"]*self.aircraft["W_{batt}"]/(cruise["R"]*self.aircraft["W_{pay}"])]

        if sp:
            landing = Landing(self.aircraft)
            constraints.extend([Srunway >= landing["S_{land}"]])
            mission.extend([landing])
        else:
            landing = GLanding(self.aircraft)
            constraints.extend([Srunway >= landing["S_{land}"]])
            mission.extend([landing])

        return constraints, self.aircraft, mission, climb

class TakeOff(Model):
    """
    take off model
    http://www.dept.aoe.vt.edu/~lutze/AOE3104/takeoff&landing.pdf

    """
    def setup(self, aircraft, sp=False):

        fs = FlightState()
        A = Variable("A", "m/s**2", "log fit equation helper 1")
        B = Variable("B", "1/m", "log fit equation helper 2")

        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        mu = Variable("\\mu", 0.025, "-", "coefficient of friction")
        T = Variable("T", "lbf", "take off thrust")
        cda = Variable("CDA", 0.024, "-", "parasite drag coefficient")

        CLg = Variable("C_{L_g}", "-", "ground lift coefficient")
        CDg = Variable("C_{D_g}", "-", "grag ground coefficient")
        cdp = Variable("c_{d_{p_{stall}}}", 0.025, "-",
                       "profile drag at Vstallx1.2")
        Kg = Variable("K_g", 0.04, "-", "ground-effect induced drag parameter")
        CLto = Variable("C_{L_{TO}}", 3.5, "-", "max lift coefficient")
        Vstall = Variable("V_{stall}", "knots", "stall velocity")
        e = Variable("e", 0.8, "-", "span efficiency")

        zsto = Variable("z_{S_{TO}}", "-", "take off distance helper variable")
        Sto = Variable("S_{TO}", "ft", "take off distance")
        Sground = Variable("S_{ground}", "ft", "ground roll")
        etaprop = Variable("\\eta_{prop}", 0.8, "-", "propellor efficiency")
        msafety = Variable("m_{fac}", 1.4, "-", "safety margin")

        path = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(path + os.sep + "logfit.csv")
        fd = df.to_dict(orient="records")[0]

        constraints = [
            T/aircraft.topvar("W") >= A/g + mu,
            T <= aircraft["P_{shaft-max}"]*etaprop/fs["V"],
            CDg >= 0.024 + cdp + CLto**2/pi/aircraft["AR"]/e,
            Vstall == (2*aircraft.topvar("W")/fs["\\rho"]/aircraft.wing["S"]
                       / CLto)**0.5,
            fs["V"] == 1.2*Vstall,
            FitCS(fd, zsto, [A/g, B*fs["V"]**2/g]),
            Sground >= 1.0/2.0/B*zsto,
            Sto/msafety >= Sground]

        if sp:
            with SignomialsEnabled():
                constraints.extend([
                    (B*aircraft.topvar("W")/g + 0.5*fs["\\rho"]
                     * aircraft.wing["S"]*mu*CLto >= 0.5*fs["\\rho"]
                     * aircraft.wing["S"]*CDg)])
        else:
            constraints.extend([
                B >= (g/aircraft.topvar("W")*0.5*fs["\\rho"]
                      * aircraft.wing["S"]*CDg)])

        return constraints, fs

if __name__ == "__main__":
    SP = False
    M = Mission(sp=SP)
    M.substitutions.update({"R": 100, "S_{runway}": 10000})
    M.cost = M[M.aircraft.topvar("W")]
    #M.cost = M["Cost_per_trip"]
    if SP:
        sol = M.localsolve("mosek")
    else:
        sol = M.solve("mosek")
    print sol.table()

    M.substitutions.update({"R": 100, "S_{runway}": 600, "V_{min}": 100,
        "W_{pay}": 2*195, "g_{loading}": 0.3, "C_{L_{TO}}": 4.0,
        "C_{L_{land}}": 3.5})

    sol = M.solve("mosek")

