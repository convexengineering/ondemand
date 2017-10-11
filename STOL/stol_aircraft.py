" short take off and landing aircraft model "
from numpy import pi
from gpkit import Variable, Model
from takeoff import TakeOff
from flightstate import FlightState

# pylint: disable=too-many-locals, invalid-name, unused-variable

class simpleAircraft(Model):
    " thing that we want to build "
    def setup(self):

        W = Variable("W", "lbf", "aircraft weight")
        Wpay = Variable("W_{pay}", 500, "lbf", "payload weight")
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
