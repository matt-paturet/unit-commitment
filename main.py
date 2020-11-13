import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from model import UnitCommitment

generators = pd.read_csv('data/generators.csv', index_col=0)
demand = pd.read_csv('data/demand.csv', index_col=0)

uc = UnitCommitment(generators, demand)
uc.build_model()
u, p, cost, status = uc.optimize()
prices = uc.get_prices()

# Plot results
time_period = list(uc.period)
fig = make_subplots(rows=2, cols=2, specs=[[{'colspan': 2}, None], [{'type': 'table'}, {}]],
                    subplot_titles=(f'Unit Dispatch - total cost £{cost:.0f} (opt status: {status})',
                                    'Generator details', 'Price'))
fig.add_table(header=dict(values=list(generators.reset_index().columns)),
              cells=dict(values=[generators.reset_index()[c] for c in generators.reset_index().columns]),
              row=2, col=1)
fig.add_scatter(x=time_period, y=prices, name='Prices', mode='lines+markers', row=2, col=2)
fig.add_scatter(x=time_period, y=demand['demand'], name='Demand', line_shape='spline', row=1, col=1)
for g in generators.index:
    fig.add_bar(x=time_period, y=[p[t, g].x for t in time_period], name=g, row=1, col=1)

fig.update_layout(barmode='stack', legend=dict(traceorder='reversed'))
fig.update_yaxes(title='MW', row=1, col=1)
fig.update_yaxes(title='£/MWh', row=2, col=2)
fig.show()
