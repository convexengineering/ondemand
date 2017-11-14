from gpkit import Model, Variable, units
"""Vehicle cost model"""
class Cost(Model):
    def setup(self, aircraft):
        struct_Sp_Cost  = Variable('struct_Sp_Cost', 150., '1/kg', 'Cost per kilo of structure')
        motor_Sp_Cost   = Variable('motor_Sp_Cost',  360., '1/kg', 'Cost per kilo of motor')
        battery_Sp_Cost = Variable('batt_Sp_Cost', 150., '1/(kW*hr)', 'Cost per kw_hr of battery')
        Cost_Addl       = Variable('Cost_Addl',50000, '-', 'Additional cost per vehicle')
        Cost_Motors     = Variable('Cost_Motors', '-', 'Motor cost per vehicle')
        Cost_Structures = Variable('Cost_Structures', '-', 'Structure cost per vehicle')
        Cost_Battery    = Variable('Cost_Battery', '-', 'Battery cost per vehicle')
        Cost_Vehicle    = Variable('Cost_Vehicle', '-', 'Cost Vehicle ')
        Cost_Vehicle_Spares     = Variable('Cost_Vehicle_Spares', '-', 'Cost Vehicle + Spares')
        Cost_Battery_Spares     = Variable('Cost_Battery_Spares', '-', 'Cost Battery + Spares')
        Cost_Energy_per_trip    = Variable('Cost_Energy_per_trip', '-', 'Cost energy per trip')
        Cost_vehicle_per_trip   = Variable('Cost_vehicle_per_trip', '-', 'Cost vehicle per trip')
        Cost_battery_per_trip   = Variable('Cost_battery_per_trip', '-', 'Cost battery per trip')
        Cost_per_trip           = Variable('Cost_per_trip', '-', 'Total Cost per trip')

        trips_per_year  = Variable('trips_per_year', 1000., '-', '# Trips/year')
        cycles_per_trip = Variable('battery_cycles_per_trip', 1, '-', "# cycles per trip")
        cycles_per_year = Variable('cycles_per_year', 1000., '-', '# battery cycles/year')

        spares_factor_vehicle   = Variable('spares_vehicle', 1.1, '-', 'Vehicle spares factor')
        spares_factor_battery   = Variable('spares_battery', 1.1, '-', 'Battery spares factor')
        cycle_life_battery      = Variable('cycle_life_battery', 2000, '-', 'Useful battery lift (cycles)')
        useful_life_vehicle     = Variable('useful_life_vehicle', 10., '-', 'useful_life_vehicle (yrs)')
        useful_life_trips       = Variable('useful_life_trip', '-', 'useful life in trips')
        energy_cost             = Variable('energy cost',.1,  '1/(kW*hr)', 'Energy cost per trip')
        maintenance_cost_per_trip           = Variable('cost_maint_per_trip',14, '-', 'Maintenance cost per tip')
        landing_fee_per_trip    = Variable('landing_fee',50,  '-', 'landing fee per trip')
        pilot_cost_per_trip     = Variable('pilot_fee',50,  '-', 'pilot fee per trip')

        #Cost_battery_replacement_per_trip   = Variable('cost_batt_replace_per_trip', '-', 'Battery replacement cost per tip')
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")


        constraints=[Cost_Motors >= aircraft["W_{motor}"]/g * motor_Sp_Cost,
                            Cost_Structures >= aircraft["W_{struct}"]/g * struct_Sp_Cost,
                            Cost_Battery == aircraft["W_{batt}"]/g*aircraft["h_{batt}"] * battery_Sp_Cost,
                            Cost_Vehicle >= (Cost_Addl + Cost_Motors + Cost_Structures + Cost_Battery),
                            Cost_Vehicle_Spares >= (Cost_Vehicle)*spares_factor_vehicle,
                            Cost_Battery_Spares == (Cost_Battery)*spares_factor_battery,
                            useful_life_trips == trips_per_year * useful_life_vehicle,
                            Cost_vehicle_per_trip >= Cost_Vehicle_Spares/useful_life_trips,
                            Cost_battery_per_trip >= Cost_Battery_Spares*cycles_per_trip/cycle_life_battery,
                            Cost_Energy_per_trip >= aircraft["W_{batt}"]/g*aircraft["h_{batt}"] * energy_cost,
                            Cost_per_trip >= (Cost_battery_per_trip
                                             + Cost_Energy_per_trip
                                             #+ Cost_battery_replacement_per_trip
                                             + Cost_vehicle_per_trip
                                             + maintenance_cost_per_trip
                                             + pilot_cost_per_trip
                                             + landing_fee_per_trip)
                
            ]

        return constraints