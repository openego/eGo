"""
Module to collect useful functions for economic calculation of eGo

Todo:
 1) Investment costs of eTrago and eDisGo
 2) 

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
def total_economic_costs(eTraGo_network):
    """
    Parameters
    ----------
    eTraGo_network : pandas.Dataframe
    	PyPSA pandas.Dataframe of eTraGo


    ToDo:
    -----
    get all cost parameter
    calculate the total costs per time step (lukasol)
    Make a comparable output like costs/ hour
    include



    """


    return
