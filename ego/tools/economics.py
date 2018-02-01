"""
Module to collect useful functions for economic calculation of eGo

Todo:
 1) Investment costs of eTrago and eDisGo
 2) Total system costs

"""
import io
import pandas as pd
import os
from tools.results import total_storage_charges

# calculate annuity per time step or periode
def annuity_per_period(capex, n, wacc, t):
    """
    Parameters
    ----------
    capex : float
        Capital expenditure (NPV of investment)
    n : int
        Number of years that the investment is used (economic lifetime)
    wacc : float
        Weighted average cost of capital

    ToDo:
    -----
    t : int
        Timesteps in hours
    i : float
    	interest rate
	...



    """

    return capex * (wacc * (1 + wacc) ** n) / ((1 + wacc) ** n - 1)  # ToDo change formular to hourly annuity costs

# calculation of total costs -> Maybe as class?!?
def total_economic_costs(eTraGo, filename='investment_costs.csv', args=args):
    """
    Parameters
    ----------
    eTraGo: pandas.Dataframe
    	PyPSA pandas.Dataframe of eTraGo

    ToDo:
    -----
    get all cost parameter
    calculate the total costs per time step (lukasol)
    Make a comparable output like costs/ hour
    include

    collect and sum up all importent results of
    generations and save it to an Excel file for a quick
    results overview

    """
    #eTraGo.results
    #eTraGo.components
    # add country_code for calculation

    # results per carrier /generators
    results = pd.DataFrame()
    results.etrago = pd.DataFrame()

    results.etrago['p_nom'] = eTraGo.generators.groupby('carrier')['p_nom'
                                                        ].sum() # in MW

    results.etrago['p_nom_opt'] =  eTraGo.generators.groupby('carrier')[
                                                    'p_nom_opt'].sum() # in MW
    # new calculation by _t.p * marginal_cost
    results.etrago['marginal_cost'] =  eTraGo.generators.groupby('carrier'
                                        )['marginal_cost'].mean() # in in [EUR]

    power_price = eTraGo.generators_t.p[eTraGo.generators[eTraGo.generators.\
                                control!='Slack'].index]* eTraGo.generators.\
                                marginal_cost[eTraGo.generators[eTraGo.generators.\
                                control!='Slack'].index] # without Slack -> neighboring states

    power_price = power_price.groupby(eTraGo.generators.carrier, axis=1).sum().sum()

    results.etrago['power_price'] =  power_price

    # use country code
    p_by_carrier =  pd.concat([eTraGo.generators_t.p
                       [eTraGo.generators[eTraGo.generators.control!='Slack'].index], #
                       eTraGo.generators_t.p[eTraGo.generators[eTraGo.
                       generators.control=='Slack'].index].iloc[:,0].
                       apply(lambda x: x if x > 0 else 0)], axis=1).\
                       groupby(eTraGo.generators.carrier, axis=1).sum() # in MWh

    results.etrago['p'] = p_by_carrier.sum()


    # get investment costs per carrier
    # work around later db table ->  check capital_cost as cost input?!?
    path = os.getcwd()
    filename='investment_costs.csv'
    invest = pd.DataFrame.from_csv(path +'/data/'+filename)
    scn_name= args['eTraGo']['scn_name']

    if scn_name in ['SH Status Quo', 'Status Quo']:
        invest_scn = 'Status Quo'

    if scn_name in ['SH NEP 2035', 'NEP 2035']:
        invest_scn = 'NEP 2035'

    if scn_name in ['SH eGo 100', 'eGo 100']:
        invest_scn = 'eGo 100'


    result_invest = pd.concat([invest[invest_scn],
                              eTraGo.generators.groupby('carrier')['p_nom'].sum()],
                              axis=1, join='inner')

    result_invest = pd.concat([invest[invest_scn],eTraGo.generators.groupby('carrier')['p_nom'].sum()], axis=1, join='inner')
    result_invest['carrier_costs'] = result_invest[invest_scn] * result_invest['p_nom'] *1000 # in MW

    results.etrago= results.etrago.assign(investment_costs=result_invest['carrier_costs'])
    del result_invest


    # storages
    #
    results.storages = total_storage_charges(network=eTraGo, plot=False)


    stores = eTraGo.storage_units
    test= eTraGo.storage_units.p_nom_opt[stores.index].groupby(eTraGo.storage_units.bus).sum().reindex(eTraGo.buses.index,fill_value=0.)
    # get get storages capital_cost in €/MWh
    eTraGo.storage_units_t.state_of_charge[eTraGo.storage_units[eTraGo.storage_units.p_nom_opt>0].index]




    # Linies and buses
    results.lines = pd.DataFrame()
    results.lines['length'] = eTraGo.lines.groupby('v_nom')['length'].sum() # lenght by v_nom in km

    # eTraGo.lines.capital_cost.sum() # at the moment zero



    eTraGo.loads_t.p.sum(axis=1).sum()

    power_price
    # Total system
    p_nom_o_sum = eTraGo.generators.p_nom_opt.sum()  # opt installed capacity in [MW]
    p_nom_sum = eTraGo.generators.p_nom.sum()  # installed capacity in [MW]
    power_price = power_price.sum() # in [EUR]
    p_nom_sum

    # total price [€/MWh]
    price = power_price/p_nom_o_sum

    # toal system caracteristic
    results.total = pd.DataFrame()
    results.total['p_nom'] = [eTraGo.generators.p_nom.sum()] # in [MW]
    results.total['time_steps'] = get_time_steps(args)
    results.total['power_price'] = price # in €
    results.total['total_dispatch'] = p_nom_o_sum - p_nom_sum


    eTraGo.lines.v_nom
    # linies
    eTraGo.lines.length.sum()

    eTraGo.lines.marginal_cost.sum()
    eTraGo.lines.info()

    eTraGo.lines.capital_cost.sum() # at the moment zero

    eTraGo.lines_t


    #add value check NAN etc.



    return

total_economic_costs(eTraGo,args=args)




#eTraGo.carriers.name
#eTraGo.buses
#eTraGo.components



#eTraGo.foreign_trade
