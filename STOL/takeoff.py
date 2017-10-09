" take off model "
import os
import pandas as pd
from gpkit import Variable, Model, SignomialsEnabled
from gpfit.fit_constraintset import FitCS
from flightstate import FlightState

# pylint: disable=too-many-locals, invalid-name

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
        Kg = Variable("K_g", 0.04, "-", "ground-effect induced drag parameter")
        CLmax = Variable("C_{L_{max}}", 3.4, "-", "max lift coefficient")
        Vstall = Variable("V_{stall}", "m/s", "stall velocity")

        zsto = Variable("z_{S_{TO}}", "-", "take off distance helper variable")
        Sto = Variable("S_{TO}", 200, "ft", "take off distance")
        etaprop = Variable("\\eta_{prop}", 0.8, "-", "propellor efficiency")

        path = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(path + os.sep + "logfit.csv")
        fd = df.to_dict(orient="records")[0]

        constraints = [
            T/aircraft["W"] >= A/g + mu,
            T <= aircraft["P_{shaft-max}"]*etaprop/fs["V"],
            CDg >= cda + Kg*CLg**2,
            CLg == mu/2/Kg,
            Vstall == (2*aircraft["W"]/fs["\\rho"]/aircraft["S"]/CLmax)**0.5,
            fs["V"] == 1.2*Vstall,
            FitCS(fd, zsto, [A/g, B*fs["V"]**2/g]),
            Sto >= 1.0/2.0/B*zsto]

        if sp:
            with SignomialsEnabled():
                constraints.extend([
                    (B*aircraft["W"]/g + 0.5*fs["\\rho"]*aircraft["S"]*mu
                     * CLg >= 0.5*fs["\\rho"]*aircraft["S"]*CDg)])
        else:
            constraints.extend([
                B >= g/aircraft["W"]*0.5*fs["\\rho"]*aircraft["S"]*CDg])

        return constraints, fs

if __name__ == "__main__":
    M = TakeOff()
    M.cost = M["S_{TO}"]
    sol = M.solve("mosek")
