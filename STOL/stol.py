" short take off and landing aircraft model "
import os
import pandas as pd
from gpkit import Variable, Model, SignomialsEnabled
from gpkitmodels.GP.aircraft.wing.wing import Wing
from gpfit.fit_constraintset import FitCS
from flightstate import FlightState
# pylint: disable=too-many-locals, invalid-name, unused-variable

class Aircraft(Model):
    " thing that we want to build "
    def setup(self):

        Wing.fillModel = None
        self.wing = Wing()

        W = Variable("W", "lbf", "aircraft weight")
        Wpay = Variable("W_{pay}", 800, "lbf", "payload weight")
        hbatt = Variable("h_{batt}", 210, "W*hr/kg", "battery specific energy")
        etae = Variable("\\eta_{e}", 0.9, "-", "total electrical efficiency")
        Wbatt = Variable("W_{batt}", "lbf", "battery weight")
        WS = Variable("(W/S)", 2.5, "lbf/ft**2",
                      "wing weight scaling factor")
        Wwing = Variable("W_{wing}", "lbf", "wing weight")
        Pshaftmax = Variable("P_{shaft-max}", "W", "max shaft power")
        sp_motor = Variable("sp_{motor}", 7./9.81, "kW/N",
                            'Motor specific power')
        Wmotor = Variable("W_{motor}", "lbf", "motor weight")
        Wcent = Variable("W_{cent}", "lbf", "aircraft center weight")
        fstruct = Variable("f_{struct}", 0.2, "-",
                           "structural weight fraction")
        Wstruct = Variable("W_{struct}", "lbf", "structural weight")
        b = Variable("b", "ft", "Wing span")


        constraints = [
            W >= Wbatt + Wpay + self.wing.topvar("W") + Wmotor + Wstruct,
            Wcent >= Wbatt + Wpay + Wmotor + Wstruct,
            Wstruct >= fstruct*W,
            Wmotor >= Pshaftmax/sp_motor]

        loading = self.wing.loading(self.wing, Wcent)
        loading.substitutions.update({"\\kappa": 0.05,
                                      "\\sigma_{CFRP}": 1.5e9})

        return constraints, self.wing, loading

    def flight_model(self):
        " what happens during flight "
        return AircraftPerf(self)

class AircraftPerf(Model):
    " simple drag model "
    def setup(self, aircraft):

        self.fs = FlightState()
        self.wing = aircraft.wing.flight_model(aircraft.wing, self.fs)
        self.wing.substitutions["C_{L_{stall}}"] = 5

        CD = Variable("C_D", "-", "drag coefficient")
        cda = Variable("CDA", 0.024, "-", "non-lifting drag coefficient")

        constraints = [CD >= cda + self.wing["C_d"]]

        return constraints, self.wing, self.fs

class Cruise(Model):
    " calculates aircraft range "
    def setup(self, aircraft):

        perf = aircraft.flight_model()
        perf.fs.substitutions["V"] = 150

        R = Variable("R", 200, "nmi", "aircraft range")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        T = Variable("T", "lbf", "thrust")
        Pshaft = Variable("P_{shaft}", "W", "shaft power")
        etaprop = Variable("\\eta_{prop}", 0.8, "-", "propellor efficiency")

        constraints = [
            aircraft.topvar("W") == (0.5*perf["C_L"]*perf["\\rho"]
                                     * aircraft["S"]*perf["V"]**2),
            T >= 0.5*perf["C_D"]*perf["\\rho"]*aircraft.wing["S"]*perf["V"]**2,
            Pshaft >= T*perf["V"]/etaprop,
            R <= (aircraft["h_{batt}"]*aircraft["W_{batt}"]/g
                  * aircraft["\\eta_{e}"]*perf["V"]/Pshaft)]

        return constraints, perf

class Mission(Model):
    " creates aircraft and flies it around "
    def setup(self):

        self.aircraft = Aircraft()

        takeoff = TakeOff(self.aircraft)
        cruise = Cruise(self.aircraft)

        constraints = [self.aircraft["P_{shaft-max}"] >= cruise["P_{shaft}"]]

        return constraints, self.aircraft, takeoff, cruise

class TakeOff(Model):
    """
    take off model
    http://www.dept.aoe.vt.edu/~lutze/AOE3104/takeoff&landing.pdf

    """
    def setup(self, aircraft, sp=False):

        perf = aircraft.flight_model()

        A = Variable("A", "m/s**2", "log fit equation helper 1")
        B = Variable("B", "1/m", "log fit equation helper 2")

        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        mu = Variable("\\mu", 0.025, "-", "coefficient of friction")
        T = Variable("T", "lbf", "take off thrust")
        cda = Variable("CDA", 0.024, "-", "parasite drag coefficient")

        CLg = Variable("C_{L_g}", "-", "ground lift coefficient")
        CDg = Variable("C_{D_g}", "-", "grag ground coefficient")
        Kg = Variable("K_g", 0.04, "-", "ground-effect induced drag parameter")
        CLmax = Variable("C_{L_{max}}", 3.4, "-", "max lift coefficient")
        Vstall = Variable("V_{stall}", "m/s", "stall velocity")

        zsto = Variable("z_{S_{TO}}", "-", "take off distance helper variable")
        Sto = Variable("S_{TO}", 300, "ft", "take off distance")
        etaprop = Variable("\\eta_{prop}", 0.8, "-", "propellor efficiency")

        path = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(path + os.sep + "logfit.csv")
        fd = df.to_dict(orient="records")[0]

        constraints = [
            T/aircraft.topvar("W") >= A/g + mu,
            T <= aircraft["P_{shaft-max}"]*etaprop/perf["V"],
            CLmax >= perf["C_L"],
            Vstall == (2*aircraft.topvar("W")/perf["\\rho"]/aircraft.wing["S"]
                       / perf["C_L"])**0.5,
            perf["V"] == 1.2*Vstall,
            FitCS(fd, zsto, [A/g, B*perf["V"]**2/g]),
            Sto >= 1.0/2.0/B*zsto]

        if sp:
            with SignomialsEnabled():
                constraints.extend([
                    (B*aircraft.topvar("W")/g + 0.5*perf["\\rho"]
                     * aircraft.wing["S"]*mu*CLg >= 0.5*perf["\\rho"]
                     * aircraft.wing["S"]*CDg)])
        else:
            constraints.extend([
                B >= (g/aircraft.topvar("W")*0.5*perf["\\rho"]
                      * aircraft.wing["S"]*perf["C_D"])])

        return constraints, perf

if __name__ == "__main__":
    M = Mission()
    M.cost = M.aircraft.topvar("W")
    sol = M.solve("mosek")
    print sol.table()
