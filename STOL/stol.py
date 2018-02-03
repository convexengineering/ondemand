" short take off and landing aircraft model "
import os
import pandas as pd
from numpy import pi
from gpkit import Variable, Model, SignomialsEnabled, units, parse_variables
from gpkitmodels.GP.aircraft.wing.wing import Wing
from gpkitmodels.GP.aircraft.wing.wing_test import FlightState
from gpfit.fit_constraintset import FitCS
from flightstate import FlightState
from landing import Landing
from gpkit.constraints.tight import Tight as TCS
from gpkit.constraints.relax import ConstantsRelaxed
from cost import Cost

# pylint: disable=too-many-locals, invalid-name, unused-variable

class Aircraft(Model):
    """ thing that we want to build

    Variables
    ---------
    W                           [lbf]           aircraft weight
    WS                          [lbf/ft^2]      Aircraft wing loading
    PW                          [hp/lbf]        Aircraft shaft hp/weight ratio
    Npax            2           [-]             number of seats
    Wpax            195         [lbf]           passenger weight
    hbatt           210         [W*hr/kg]       battery specific energy
    etae            0.9         [-]             total electrical efficiency
    Wbatt                       [lbf]           battery weight
    Wwing                       [lbf]           wing weight
    Pshaftmax                   [W]             max shaft power
    sp_motor        7./9.81     [kW/N]          Motor specific power
    Wmotor                      [lbf]           motor weight
    Wcent                       [lbf]           aircraft center weight
    fstruct         0.2         [-]             structural weight fraction
    Wstruct                     [lbf]           structural weight
    e               0.8         [-]             span efficiency factor
    CL_max_clean    1.6         [-]             Clean CL max
    CL_max_to       2.0         [-]             Clean CL max
    CL_max_aprch    2.4         [-]             Clean CL max
    fbattmax        1.0         [-]             max battery fraction
    """
    def setup(self):
        exec parse_variables(Aircraft.__doc__)

        Wing.fillModel = None
        self.wing = Wing()

        loading = self.wing.spar.loading(self.wing, FlightState())
        loading.substitutions.update({loading.kappa: 0.05,
                                      self.wing.spar.material.sigma: 1.5e9,
                                      loading.Nmax: 6,
                                      self.wing.planform.lam: 0.7,
                                      self.wing.skin.material.tmin: 0.012*4,
                                      self.wing.planform.tau: 0.115,
                                      self.wing.mfac: 1.4,
                                      self.wing.spar.mfac: 0.8})

        S = self.S = self.wing.planform.S

        constraints = [
            Wcent == loading.W,
            WS == W/S,
            PW == Pshaftmax/W,
            TCS([W >= Wbatt + Wpax*Npax+ self.wing.W + Wmotor + Wstruct]),
            Wcent >= Wbatt + Wpax*Npax + Wmotor + Wstruct,
            Wstruct >= fstruct*W,
            Wmotor >= Pshaftmax/sp_motor,
            Wbatt/W <= fbattmax,
            ]


        return constraints, self.wing, loading

    def flight_model(self):
        " what happens during flight "
        return AircraftPerf(self)

class AircraftPerf(Model):
    """ Simple Drag model

    Variables
    ---------
    CD              [-]         drag coefficient
    cda     0.015   [-]         non-lifting drag coefficient

    """
    def setup(self, aircraft):
        exec parse_variables(AircraftPerf.__doc__)

        self.fs = FlightState()
        self.wing = aircraft.wing.flight_model(aircraft.wing, self.fs)
        self.wing.substitutions[self.wing.CLstall] = 5

        cdw = self.wing.Cd

        constraints = [CD >= cda + cdw]

        return constraints, self.wing, self.fs

class Cruise(Model):
    """ Aicraft Range model

    Variables
    ---------
    R               100    [nmi]     aircraft range
    g               9.81   [m/s**2]  gravitational constant
    T                      [lbf]     thrust
    t_reserve       30.0   [min]     Reserve flight time
    R_reserve              [nmi]     Reserve range
    Vmin            100    [kts]     min speed
    Pshaft                 [W]       shaft power
    etaprop         0.8    [-]       propellor efficiency
    f_useable       0.8    [-]       Fraction of usable battery energy
    """
    def setup(self, aircraft):
        exec parse_variables(Cruise.__doc__)

        perf = aircraft.flight_model()

        CL = self.CL = perf.wing.CL
        S = self.S = aircraft.S
        CD = self.CD = perf.CD
        W = self.W = aircraft.W
        CL_max_clean = aircraft.CL_max_clean
        hbatt = aircraft.hbatt
        Wbatt = aircraft.Wbatt
        etae = aircraft.etae

        constraints = [
            W == (0.5*CL*perf["\\rho"]*S*perf["V"]**2),
            T >= 0.5*CD*perf["\\rho"]*S*perf["V"]**2,
            Pshaft >= T*perf["V"]/etaprop,
            perf.fs["V"] >= Vmin,
            CL <= CL_max_clean,

            (R+(t_reserve*perf["V"])) <= (f_useable*(hbatt*Wbatt)/g
                  * etae*perf["V"]/Pshaft)]

        return constraints, perf
class Climb(Model):
    """ Climb model

    Variables
    ---------
    ROC         1000        [ft/min]        Target rate of climb
    V_s                     [kts]           Stall speed in takeoff config
    T_max                   [lbf]           Maximum thrust
    T_req                   [lbf]           Required thrust
    V2                      [kts]           V2
    Pshaft                  [W]             shaft power
    etaprop     0.8         [-]             propellor efficiency
    """
    def setup(self, aircraft):
        exec parse_variables(Climb.__doc__)

        perf = aircraft.flight_model()

        CL = self.CL = perf.wing.CL
        S = self.S = aircraft.S
        CD = self.CD = perf.CD
        W = self.W = aircraft.W
        Pshaftmax = aircraft.Pshaftmax

        constraints = [
            W == (0.5*CL*perf["\\rho"]*S*perf["V"]**2),
            perf["V"] == V2,
            T_req == 0.5*CD*perf["\\rho"]*S*perf["V"]**2,
            Pshaftmax >= T_max*V2/etaprop,
            V2 == 1.2*V_s,
            ROC + V2*T_req/W <= T_max*V2/W
            ]
        return constraints, perf

class GLanding(Model):
    """ Glanding model

    Variables
    ---------
    g           9.81        [m/s**2]    gravitational constant
    gload       0.5         [-]         gloading constant
    Vstall                  [knots]     stall velocity
    Sgr                     [ft]        landing ground roll
    Slnd                    [ft]        landing distance
    msafety     1.4         [-]         Landing safety margin
    CLland      3.5         [-]         landing CL
    Vref                    [kts]       Approach reference speed
    fref        1.3         [-]         stall margin
    """
    def setup(self, aircraft):
        exec parse_variables(GLanding.__doc__)

        fs = FlightState()

        S = self.S = aircraft.S
        W = self.W = aircraft.W

        constraints = [
            Sgr >= 0.5*fs["V"]**2/gload/g,
            Vstall == (2.*W/fs["\\rho"]/S/CLland)**0.5,
            Slnd >= Sgr,
            fs["V"] >= fref*Vstall,
            Vref == fs["V"],
            ]

        return constraints, fs

class Mission(Model):
    """ Mission

    Variables
    ---------
    Srunway             [ft]        runway length
    PFEI                [kJ/kg/km]  parameter of interest
    msafety     1.4     [-]         safety margin
    """
    def setup(self, sp=False, costModel=False):
        exec parse_variables(Mission.__doc__)

        self.aircraft = Aircraft()

        self.takeoff = TakeOff(self.aircraft, sp=sp)
        self.cruise  = Cruise(self.aircraft)
        self.climb   = Climb(self.aircraft)
        self.mission = [self.cruise, self.takeoff, self.climb]
        if costModel:
            cost    = Cost(self.aircraft)
            self.mission.extend([cost])

        S = self.S = self.aircraft.S
        W = self.W = self.aircraft.W
        Pshaftmax = self.aircraft.Pshaftmax
        Pshaft = self.cruise.Pshaft
        hbatt = self.aircraft.hbatt
        Wbatt = self.aircraft.Wbatt
        Wpax = self.aircraft.Wpax
        Npax = self.aircraft.Npax
        R = self.cruise.R
        Sto = self.takeoff.Sto

        constraints = [Pshaftmax >= Pshaft,
                       Srunway >= msafety*Sto,
                       PFEI == hbatt*Wbatt/(R*Wpax*Npax)]

        if sp:
            self.landing = Landing(self.aircraft)
            constraints.extend([Srunway >= msafety*self.landing.Slnd])
            self.mission.extend([self.landing])
        else:
            self.landing = GLanding(self.aircraft)
            constraints.extend([Srunway >= msafety*self.landing.Slnd])
            self.mission.extend([self.landing])

        return constraints, self.aircraft, self.mission

class TakeOff(Model):
    """
    take off model
    http://www.dept.aoe.vt.edu/~lutze/AOE3104/takeoff&landing.pdf

    Variables
    ---------
    A                       [m/s**2]    log fit equation helper 1
    B                       [1/m]       log fit equation helper 2
    g           9.81        [m/s**2]    gravitational constant
    mu          0.025       [-]         coefficient of friction
    T                       [lbf]       take off thrust
    cda         0.024       [-]         parasite drag coefficient
    CLg                     [-]         ground lift coefficient
    CDg                     [-]         grag ground coefficient
    cdp         0.025       [-]         profile drag at Vstallx1.2
    Kg          0.04        [-]         ground-effect induced drag parameter
    CLto        3.5         [-]         max lift coefficient
    Vstall                  [knots]     stall velocity
    e           0.8         [-]         span efficiency
    zsto                    [-]         take off distance helper variable
    Sto                     [ft]        take off distance
    Sground                 [ft]        ground roll
    etaprop     0.8         [-]         propellor efficiency
    fref        1.3         [-]         stall margin

    """
    def setup(self, aircraft, sp=False):
        exec parse_variables(TakeOff.__doc__)

        fs = FlightState()

        path = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(path + os.sep + "logfit.csv")
        fd = df.to_dict(orient="records")[0]

        S = self.S = aircraft.S
        W = self.W = aircraft.W
        Pshaftmax = aircraft.Pshaftmax
        AR = aircraft.wing.planform.AR

        constraints = [
            T/W >= A/g + mu,
            T <= Pshaftmax*etaprop/fs["V"],
            CDg >= 0.024 + cdp + CLto**2/pi/AR/e,
            Vstall == (2*W/fs["\\rho"]/S/CLto)**0.5,
            fs["V"] == fref*Vstall,
            FitCS(fd, zsto, [A/g, B*fs["V"]**2/g]),
            Sground >= 1.0/2.0/B*zsto,
            Sto >= Sground]

        if sp:
            with SignomialsEnabled():
                constraints.extend([
                    (B*W/g + 0.5*fs["\\rho"]*S*mu*CLto >= 0.5*fs["\\rho"]
                        * S*CDg)])
        else:
            constraints.extend([
                B >= (g/W*0.5*fs["\\rho"]*S*CDg)])

        return constraints, fs

def baseline(model):
    " sub in baseline parameters "
    model.substitutions.update({
        model.cruise.R: 100, model.cruise.Vmin: 100, model.aircraft.hbatt: 210,
        model.Srunway: 400,
        model.msafety: 1.4,
        model.aircraft.Npax: 5,
        model.aircraft.sp_motor: 7./9.81,
        model.landing.fref: 1.3,
        model.takeoff.fref: 1.3,
        model.landing.gload: 0.4, model.takeoff.CLto: 4.0,
        model.landing.CLland: 3.5})

def advanced(model):
    " sub in advanced tech params "
    model.substitutions.update({
        model.cruise.R: 100, model.cruise.Vmin: 100, model.aircraft.hbatt: 300,
        model.Srunway: 200,
        model.msafety: 1.2,
        model.aircraft.Npax: 5,
        model.aircraft.sp_motor: 7./9.81*1.2,
        model.landing.fref: 1.1,
        model.takeoff.fref: 1.1,
        model.landing.gload: 0.7, model.takeoff.CLto: 5.0,
        model.landing.CLland: 4.5})

if __name__ == "__main__":
    SP = False
    M = Mission(sp=SP)
    M.substitutions.update({M.cruise.R: 100, M.Srunway: 10000})
    M.cost = M[M.aircraft.W]
    #M.cost = M["Cost_per_trip"]
    if SP:
        sol = M.localsolve("mosek")
    else:
        sol = M.solve("mosek")
    print sol.table()

    baseline(M)
    solbase = M.solve("mosek")

    advanced(M)
    soladv = M.solve("mosek")

