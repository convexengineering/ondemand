from gpkit      import Model, Variable, units
from rangetod   import run_cost_trade_point

def print_summary(sol):
    print "\n\n----Output Summary----\n"
    print "----Weights Summary----"
    MTOW = sol["freevariables"]["W_Mission/Aircraft"].magnitude
    trip_cost = sol["freevariables"]["Cost_per_trip"]
    vehicle_cost = sol["freevariables"]["Cost_Vehicle"]
    print "MTO: %5.0f lb" % (MTOW)
    WBat = sol["freevariables"]["W_{batt}"].magnitude
    WPay = sol["constants"]["W_{pay}"].magnitude
    print "Battery: %5.0f lbs \t\t %2.1f %%MTOW"%(WBat, WBat/MTOW*100.)
    print "Payload: %5.0f lbs \t\t %2.1f %%MTOW"%(WPay, WPay/MTOW*100.)
    WStruct= sol["freevariables"]["W_{struct}"].magnitude
    Wmotor= sol["freevariables"]["W_{motor}"].magnitude
    Wwing = sol["freevariables"]["W_Mission/Aircraft/Wing"].magnitude
    OEW   = WStruct+Wmotor+Wwing
    print "OEW    : %5.0f lbs \t\t %2.1f %%MTOW"%(OEW, OEW/MTOW*100.)
    print "Struct : %5.0f lbs \t\t %2.1f %%MTOW"%(WStruct, WStruct/MTOW*100.)
    print "Motor  : %5.0f lbs \t\t %2.1f %%MTOW"%(Wmotor, Wmotor/MTOW*100.)
    print "Wing   : %5.0f lbs \t\t %2.1f %%MTOW"%(Wwing, Wwing/MTOW*100.)
    print "Useful load: %5.0f" % (WBat+WPay)

    print"_______________________\n"
    print "W/S: %3.1f lbs/ft^2" % (sol["freevariables"]["W/S_Mission/Aircraft"].magnitude)
    print "P/W: %3.3f hp/lb" % (sol["freevariables"]["P/W"].magnitude)
    print "PFEI: %3.2f "%(sol["freevariables"]["PFEI"].magnitude)
    print "b: %3.1f ft"%(sol["freevariables"]["b"].magnitude)
    print "L/D: %3.1f"%(sol["freevariables"]["C_L"]/sol["freevariables"]["C_D"])
    print "AR: %3.1f"%(sol["freevariables"]["AR"])
    print "Cruise CL: %3.3f"%(sol["freevariables"]["C_L"])
    print "V_REF: %4.1f kts"%(sol["freevariables"]["V_{ref}"].magnitude)
    print "V_cruise: %4.1f kts"%sol["freevariables"]["V_Mission/Cruise/AircraftPerf/FlightState"].magnitude
    print "______"
    print "S_land: %4.0f ft"%(sol["freevariables"]["S_{land}"].magnitude)
    print "S_gr, l: %4.0f ft"%(sol["freevariables"]["S_{gr}"].magnitude)
    print "S_TO: %4.0f ft"%(sol["freevariables"]["S_{TO}"].magnitude)
    print "\n----Cost Summary----\n"
    print "Trip_Cost: %4.0f USD" % (trip_cost)
    print "Vehicle_Cost: %4.0f USD" % (vehicle_cost)
    print "Energy Cost (one trip): %4.0f USD" % (sol["freevariables"]["Cost_Energy_per_trip"])
    print "Battery Cost (one trip): %4.0f USD" % (sol["freevariables"]["Cost_battery_per_trip"])
if __name__ == "__main__":
    import sys
    RNWYs = [250, 500]
    RNGs  = [150]
    PAYs  = [p*195 for p in [4, 6, 8, 10, 20]]
    VCRs  = [120]  #Becomes prim. infeasible for 250ft runway, 160 kts, 200nmi range, 3900lbs payload
    gLNDs  = [.5]

    for RNWY in RNWYs:
        for RNG in RNGs:
            for PAY in PAYs:
                for VCR in VCRs: 
                    for gLND in gLNDs:

                        filename = "Analysis/Cost/RNWY_%4.0f_RNG_%4.0f_PAY_%4.0f_V_%3.0f_GLND_%3.0f" % \
                            (RNWY, RNG, PAY, VCR, gLND*10)
                        sys.stdout = open(filename+'.sum', 'w+')
                        try:
                            sol = run_cost_trade_point(filename,RNWY, RNG, PAY, VCR, gLND)
                            print_summary(sol) 
                        except:
                            print "---Error---"