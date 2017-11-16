from gpkit import Variable, Model

class FlightState(Model):
    def setup(self):

        rho = self.rho = Variable("\\rho", 1.225, "kg/m**3", "air density")
        mu = self.mu = Variable("\\mu", 1.789e-5, "kg/m/s", "air viscosity")
        V = self.V = Variable("V", "knots", "speed")

        constraints = [rho == rho, V == V, mu == mu]

        return constraints
