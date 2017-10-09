from gpkit import Variable, Model

class Aircraft(Model):
    def setup(self):

        W = Variable("W", "lbf", "aircraft weight")
        Wpay = Variable("W_{pay}", 500, "lbf", "payload weight")
        hbatt = Variable("h_{batt}", 300, "W*hr/kg", "battery specific energy")
        LoD = Variable("(L/D)", 10, "-", "lift to drag ratio")
        etatotal = Variable("\\eta_{total}", 0.8, "-",
                            "total propulsive efficiency")
        Wbatt = Variable("W_{batt}", "lbf", "battery weight")

        constraints = [W >= Wbatt + Wpay]

        return constraints

class Cruise(Model):
    def setup(self, aircraft):

        R = Variable("R", 50, "nmi", "aircraft range")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")

        constraints = [R <= (
            aircraft["h_{batt}"]*aircraft["W_{batt}"]/aircraft["W"]/g
            * aircraft["(L/D)"]*aircraft["\\eta_{total}"])]

        return constraints

class Mission(Model):
    def setup(self):

        aircraft = Aircraft()

        cruise = Cruise(aircraft)

        return aircraft, cruise

if __name__ == "__main__":
    M = Mission()
    M.cost = M["W"]
    sol = M.solve("mosek")
