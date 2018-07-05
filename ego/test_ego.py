from tools.io import eGo, egoBasic, eDisGoResults, eTraGoResults


c = egoBasic(jsonpath='scenario_setting.json')

c.edisgo_network
c.etrago_network

b = eTraGoResults(jsonpath='scenario_setting.json')


b.etrago_network.plot_line_loading
b.etrago_network.plot_line_loading(b.etrago_network)
b.etrago.storage_charges


ego = eGo(jsonpath='scenario_setting.json')

ego.etrago.storage_charges
ego.etrago_network.buses
ego


"""
Ausbau:
ego = eGo(jsonpath='scenario_setting.json')



ego.etrago_network # Original eTraGo Network  Klasse
ego.etrago.storage_charges # Aggregierte eGo Ergebnisse für etrago
ego.edisgo_network # Original eDisGo Network  Klasse ???
ego.edisgo # Aggregierte eGo Ergebnisse für edisgo
ego.total # eGo gesamt Ergebnisse über alle Spannungsebenen


"""
