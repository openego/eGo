"""
Module to collect useful functions for economic calculation of eGo

Todo:
 1) Investment costs of eTrago and eDisGo
 2) Total system costs

"""

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
def total_economic_costs(eTraGo):
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

    # results per carrier
    results = pd.DataFrame()
    results.etrago = pd.DataFrame()
    results.etrago['p_nom'] = eTraGo.generators.groupby('carrier')['p_nom'].sum() # in MW
    results.etrago['p_nom_opt'] =  eTraGo.generators.groupby('carrier')['p_nom_opt'].sum() # in MW
    results.etrago['marginal_cost'] =  eTraGo.generators.groupby('carrier')['marginal_cost'].sum() # in in [EUR]






    results.total
    p_nom_o_sum = eTraGo.generators.p_nom_opt.sum()  # in [MWh]
    p_nom_sum = eTraGo.generators.p_nom.sum()  # in [MWh]
    m_cost_sum = eTraGo.generators.marginal_cost.sum() # in [EUR]


    # cost per €/MWh
    price = m_cost_sum/p_nom_o_sum
    print(price)

    p_nom_o_sum - p_nom_sum


    # toal system caracteristic
    results.total = pd.DataFrame()
    results.total['p_nom'] = [eTraGo.generators.p_nom_opt.sum()] # in [MWh]
    results.total['calc_time'] = get_time_steps(args)

    # linies
    eTraGo.lines.length.sum()

    eTraGo.lines.marginal_cost.sum()
    eTraGo.lines.capital_cost.sum() # at the moment zero

    eTraGo.lines_t


    # generators




    return


eTraGo.buses
eTraGo.components



#eTraGo.foreign_trade
