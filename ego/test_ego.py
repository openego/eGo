from tools.io import eGo

ego = eGo(jsonpath='scenario_setting.json')

ego.etrago_line_loading()
ego.etrago_network.plot()

ego.edisgo_network


"""
Ausbau:
ego = eGo(jsonpath='scenario_setting.json')



ego.etrago_network # Original eTraGo Network  Klasse
ego.etrago.storage_charges # Aggregierte eGo Ergebnisse für etrago
ego.edisgo_network # Original eDisGo Network  Klasse ???
ego.edisgo # Aggregierte eGo Ergebnisse für edisgo
ego.total # eGo gesamt Ergebnisse über alle Spannungsebenen


"""
c = egoBasic(jsonpath='scenario_setting.json')

c.edisgo_network
c.etrago_network

b = eTraGoResults(jsonpath='scenario_setting.json')


b.etrago_network.plot_line_loading
b.etrago_network.plot_line_loading(b.etrago_network)
b.etrago.storage_charges
