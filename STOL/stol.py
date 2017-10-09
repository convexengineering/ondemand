from numpy import pi
from gpkit import Variable, Model

class Aircraft(Model):
    def setup(self):

        W = Variable("W", "lbf", "aircraft weight")
        Wpay = Variable("W_{pay}", 500, "lbf", "payload weight")
        hbatt = Variable("h_{batt}", 300, "W*hr/kg", "battery specific energy")
        etae = Variable("\\eta_{e}", 0.9, "-", "total electrical efficiency")
        Wbatt = Variable("W_{batt}", "lbf", "battery weight")
        AR = Variable("AR", 10, "-", "wing aspect ratio")
        S = Variable("S", "ft**2", "wing planform area")

        constraints = [W >= Wbatt + Wpay]

        return constraints

    def flight_model(self):
        return AircraftPerf(self)

class AircraftPerf(Model):
    def setup(self, aircraft):

        CL = Variable("C_L", "-", "lift coefficient")
        CD = Variable("C_D", "-", "drag coefficient")
        cda = Variable("CDA", 0.024, "-", "non-lifting drag coefficient")
        e = Variable("e", 0.8, "-", "span efficiency")

        constraints = [CD >= cda + CL**2/pi/e/aircraft["AR"]]

        return constraints

class FlightState(Model):
    def setup(self):

        rho = Variable("\\rho", 1.225, "kg/m**3", "air density")
        V = Variable("V", "knots", "speed")

        constraints = [rho == rho, V == V]

        return constraints

class Cruise(Model):
    def setup(self, aircraft):

        fs = FlightState()
        aircraftperf = aircraft.flight_model()

        R = Variable("R", 50, "nmi", "aircraft range")
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

        return constraints, aircraftperf

class Mission(Model):
    def setup(self):

        aircraft = Aircraft()

        cruise = Cruise(aircraft)

        return aircraft, cruise

if __name__ == "__main__":
    M = Mission()
    M.cost = M["W"]
    sol = M.solve("mosek")
