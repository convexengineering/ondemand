from gpkit import Variable, Model

class FlightState(Model):
    def setup(self):

        rho = Variable("\\rho", 1.225, "kg/m**3", "air density")
        V = Variable("V", "knots", "speed")

        constraints = [rho == rho, V == V]

        return constraints
