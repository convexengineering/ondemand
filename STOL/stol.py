" short take off and landing aircraft model "
from numpy import pi
from gpkit import Variable, Model
from takeoff import TakeOff
from flightstate import FlightState
# pylint: disable=too-many-locals, invalid-name, unused-variable

class Aircraft(Model):
    " thing that we want to build "
    def setup(self):

        W = Variable("W", "lbf", "aircraft weight")
        Wpay = Variable("W_{pay}", 800, "lbf", "payload weight")
        hbatt = Variable("h_{batt}", 210, "W*hr/kg", "battery specific energy")
        etae = Variable("\\eta_{e}", 0.9, "-", "total electrical efficiency")
        Wbatt = Variable("W_{batt}", "lbf", "battery weight")
        AR = Variable("AR", 10, "-", "wing aspect ratio")
        S = Variable("S", "ft**2", "wing planform area")
        WS = Variable("(W/S)", 2.5, "lbf/ft**2",
                      "wing weight scaling factor")
        Wwing = Variable("W_{wing}", "lbf", "wing weight")
        Pshaftmax = Variable("P_{shaft-max}", "W", "max shaft power")
        sp_motor = Variable("sp_{motor}", 7./9.81, "kW/N",
                            'Motor specific power')
        Wmotor = Variable("W_{motor}", "lbf", "motor weight")
        fstruct = Variable("f_{struct}", 0.2, "-",
                           "structural weight fraction")
        Wstruct = Variable("W_{struct}", "lbf", "structural weight")
        b = Variable("b", "ft", "Wing span")

        constraints = [W >= Wbatt + Wpay + Wwing + Wmotor + Wstruct,
                       Wstruct >= fstruct*W,
                       Wwing >= WS*S,
                       Wmotor >= Pshaftmax/sp_motor,
                       AR == b**2/S]

        return constraints

    def flight_model(self):
        " what happens during flight "
        return AircraftPerf(self)

class AircraftPerf(Model):
    " simple drag model "
    def setup(self, aircraft):

        CL = Variable("C_L", "-", "lift coefficient")
        CD = Variable("C_D", "-", "drag coefficient")
        cda = Variable("CDA", 0.024, "-", "non-lifting drag coefficient")
        e = Variable("e", 0.8, "-", "span efficiency")

        constraints = [CD >= cda + CL**2/pi/e/aircraft["AR"]]

        return constraints

class Cruise(Model):
    " calculates aircraft range "
    def setup(self, aircraft):

        fs = FlightState()
        aircraftperf = aircraft.flight_model()

        R = Variable("R", 200, "nmi", "aircraft range")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        T = Variable("T", "lbf", "thrust")
        Pshaft = Variable("P_{shaft}", "W", "shaft power")
        etaprop = Variable("\\eta_{prop}", 0.8, "-", "propellor efficiency")

        constraints = [
            aircraft["W"] == (0.5*aircraftperf["C_L"]*fs["\\rho"]
                              * aircraft["S"]*fs["V"]**2),
            T >= 0.5*aircraftperf["C_D"]*fs["\\rho"]*aircraft["S"]*fs["V"]**2,
            Pshaft >= T*fs["V"]/etaprop,
            R <= (aircraft["h_{batt}"]*aircraft["W_{batt}"]/g
                  * aircraft["\\eta_{e}"]*fs["V"]/Pshaft)]

        return constraints, aircraftperf, fs

class Mission(Model):
    " creates aircraft and flies it around "
    def setup(self):

        aircraft = Aircraft()

        takeoff = TakeOff(aircraft)
        cruise = Cruise(aircraft)

        constraints = [aircraft["P_{shaft-max}"] >= cruise["P_{shaft}"]]

        return constraints, aircraft, takeoff, cruise

if __name__ == "__main__":
    M = Mission()
    M.cost = M["W"]
    sol = M.solve("mosek")
    print sol.table()
