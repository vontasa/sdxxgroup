### Pyomo master for AMPL Bender's example, available
### from http://www.ampl.com/NEW/LOOP2/stoch2.mod

from coopr.pyomo import *

model = AbstractModel()
model.name = "Master"

##############################################################################

model.NUMSCEN = Param(within=PositiveIntegers)

model.SCEN = RangeSet(model.NUMSCEN)

# products
model.PROD = Set()

# number of weeks
model.T = Param(within=PositiveIntegers)

# derived set containing all valid week indices and subsets of interest.
model.WEEKS = RangeSet(model.T)

model.TWOPLUSWEEKS = RangeSet(2, model.T)

# tons per hour produced
model.rate = Param(model.PROD, within=PositiveReals)

# hours available in week
model.avail = Param(model.WEEKS, within=NonNegativeReals)

# limit on tons sold in week
model.market = Param(model.PROD, model.WEEKS, within=NonNegativeReals)

# cost per ton produced
model.prodcost = Param(model.PROD, within=NonNegativeReals)

# carrying cost/ton of inventory
model.invcost = Param(model.PROD, within=NonNegativeReals)

# initial inventory
model.inv0 = Param(model.PROD, within=NonNegativeReals)

# projected revenue/ton, per scenario.
model.revenue = Param(model.PROD, model.WEEKS, model.SCEN, within=NonNegativeReals)

def prob_validator(value, s, model):
   return (value >= 0) and (value <= 1.0)
model.prob = Param(model.SCEN, validate=prob_validator)

##############################################################################

model.Make1 = Var(model.PROD, within=NonNegativeReals)
model.Make1.declare_attribute("rc")
model.Make1.declare_attribute("lrc")
model.Make1.declare_attribute("urc")

model.Inv1 = Var(model.PROD, within=NonNegativeReals)
model.Inv1.declare_attribute("rc")
model.Inv1.declare_attribute("lrc")
model.Inv1.declare_attribute("urc")

def sell_bounds(p, model):
   return (0, model.market[p, 1])
model.Sell1 = Var(model.PROD, within=NonNegativeReals, bounds=sell_bounds)
model.Sell1.declare_attribute("rc")
model.Sell1.declare_attribute("lrc")
model.Sell1.declare_attribute("urc")

model.Min_Stage2_Profit = Var(within=NonNegativeReals)
model.Min_Stage2_Profit.declare_attribute("rc")
model.Min_Stage2_Profit.declare_attribute("lrc")
model.Min_Stage2_Profit.declare_attribute("urc")

##############################################################################

model.CUTS = Set(within=PositiveIntegers, ordered=True)

def price_validator(value, model):
   return value >= -0.000001

model.time_price = Param(model.TWOPLUSWEEKS, model.SCEN, \
                         model.CUTS, default=0.0, validate=price_validator)

model.bal2_price = Param(model.PROD, model.SCEN, model.CUTS, \
                         default=0.0, validate=price_validator)

model.sell_lim_price = Param(model.PROD, model.TWOPLUSWEEKS, \
                             model.SCEN, model.CUTS, \
                             default=0.0, validate=price_validator)

def time1_rule(model):
   return (None, sum([1.0 / model.rate[p] * model.Make1[p] for p in model.PROD]) - model.avail[1], 0.0)
model.Time1 = Constraint(rule=time1_rule)

def balance1_rule(p, model):
   return  model.Make1[p] + model.inv0[p] - (model.Sell1[p] + model.Inv1[p]) == 0.0
model.Balance1 = Constraint(model.PROD, rule=balance1_rule)

# cuts are generated on-the-fly, so no rules are necessary.
model.Cut_Defn = Constraint(model.CUTS, noruleinit=True)

def expected_profit_rule(model):
   return sum([model.prob[s] * model.revenue[p, 1, s] * model.Sell1[p] - \
               model.prob[s] * model.prodcost[p] * model.Make1[p] - \
               model.prob[s] * model.invcost[p] * model.Inv1[p] \
               for p in model.PROD for s in model.SCEN]) + \
          model.Min_Stage2_Profit

model.Expected_Profit = Objective(rule=expected_profit_rule, sense=maximize)
