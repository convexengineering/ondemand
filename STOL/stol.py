from gpkit import Variable, Model

class Aicraft(Model):
    def setup(self):

        W = Variable("W", "lbf", "aircraft weight")
        Wpay = Variable("W_{pay}", 500, "lbf", "payload weight")
        hbatt = Variable("h_{batt}", 300, "W*hr/kg", "battery specific energy")
        LoD = Variable("(L/D)", 10, "-", "lift to drag ratio")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        R = Variable("R", 50, "nmi", "aircraft range")
        etatotal = Variable("\\eta_{total}", 0.8, "-",
                            "total propulsive efficiency")
        Wbatt = Variable("W_{batt}", "lbf", "battery weight")

        constraints = [R <= hbatt*Wbatt/W/g*LoD*etatotal,
                       W >= Wbatt + Wpay]

        return constraints

if __name__ == "__main__":
    M = Aicraft()
    M.cost = M["W"]
    sol = M.solve("mosek")
