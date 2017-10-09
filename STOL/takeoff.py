from gpkit import Variable, Model, SignomialsEnabled
import os
import pandas as pd
from gpfit.fit_constraintset import FitCS

class TakeOff(Model):
    def setup(self, sp=False):
        """
        take off model
        http://www.dept.aoe.vt.edu/~lutze/AOE3104/takeoff&landing.pdf

        """

        A = Variable("A", "m/s**2", "log fit equation helper 1")
        B = Variable("B", "1/m", "log fit equation helper 2")

        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        mu = Variable("\\mu", 0.025, "-", "coefficient of friction")
        T0 = Variable("T_0", 13000, "lbf", "total static thrust")
        W = Variable("W", 56000, "lbf", "aircraft weight")

        rho = Variable("\\rho", 1.225, "kg/m**3", "air density")
        S = Variable("S", 1000, "ft**2", "wing area")
        cda = Variable("CDA", 0.024, "-", "parasite drag coefficient")

        CLg = Variable("C_{L_g}", "-", "ground lift coefficient")
        CDg = Variable("C_{D_g}", "-", "grag ground coefficient")
        Vto = Variable("V_{TO}", "m/s", "speed at take off")
        Kg = Variable("K_g", 0.04, "-", "ground-effect induced drag parameter")
        CLmax = Variable("C_{L_{max}}", 2.4, "-", "max lift coefficient")
        Vstall = Variable("V_{stall}", "m/s", "stall velocity")

        zsto = Variable("z_{S_{TO}}", "-", "take off distance helper variable")
        Sto = Variable("S_{TO}", "ft", "take off distance")

        path = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(path + os.sep + "logfit.csv")
        fd = df.to_dict(orient="records")[0]

        constraints = [T0/W >= A/g + mu,
                       CDg >= cda + Kg*CLg**2,
                       CLg == mu/2/Kg,
                       Vstall == (2*W/rho/S/CLmax)**0.5,
                       Vto == 1.2*Vstall,
                       FitCS(fd, zsto, [A/g, B*Vto**2/g]),
                       Sto >= 1.0/2.0/B*zsto]

        if sp:
            with SignomialsEnabled():
                constraints.extend([B*W/g + 0.5*rho*S*mu*CLg >= (
                    0.5*rho*S*CDg)])
        else:
            constraints.extend([B >= g/W*(0.5*rho*S*CDg)])

        return constraints

if __name__ == "__main__":
    M = TakeOff()
    M.cost = M["S_{TO}"]
    sol = M.solve("mosek")
