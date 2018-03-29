"""
Module to collect useful functions for economic calculation of eGo

Todo:
 1) Investment costs of eTrago and eDisGo
 2) Total system costs

"""
import io
import pandas as pd
import os

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

    ToDo
    ----
    t : int
        Timesteps in hours
    i : float
    	interest rate
	...
    """

    return capex * (wacc * (1 + wacc) ** n) / ((1 + wacc) ** n - 1)  # ToDo change formular to hourly annuity costs
