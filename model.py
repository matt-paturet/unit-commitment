from mip.model import Model, xsum, minimize
from mip.constants import BINARY


class UnitCommitment:

    def __init__(self, generators, demand):

        self.generators = generators
        self.demand = demand

        self.period = range(1, len(self.demand) + 1)

        self.model = Model(name='UnitCommitment')
        self.p, self.u = {}, {}

    def build_model(self, fixed=False, u_fixed=None):

        for t in self.period:
            for g in self.generators.index:
                if fixed:
                    self.u[t, g] = self.model.add_var(lb=u_fixed[t, g], ub=u_fixed[t, g])
                else:
                    self.u[t, g] = self.model.add_var(var_type=BINARY)
                self.p[t, g] = self.model.add_var()

        # Max/min power
        for t in self.period:
            for g in self.generators.index:
                self.model.add_constr(self.p[t, g] <= self.generators.loc[g, 'p_max'] * self.u[t, g],
                                      name=f'pmax_constr[{t},{g}]')
                self.model.add_constr(self.p[t, g] >= self.generators.loc[g, 'p_min'] * self.u[t, g],
                                      name=f'pmin_constr[{t},{g}]')

        # Power balance
        for t in self.period:
            self.model.add_constr(
                xsum(self.p[t, g] for g in self.generators.index) == self.demand.loc[t, 'demand'],
                name=f'power_bal_constr[{t}]'
            )

        # Min on
        for t in self.period[1:]:
            for g in self.generators.index:
                min_on_time = min(t + self.generators.loc[g, 'min_on'] - 1, len(self.period))
                for tau in range(t, min_on_time + 1):
                    self.model.add_constr(self.u[tau, g] >= self.u[t, g] - self.u[t-1, g],
                                          name=f'min_on_constr[{t},{g}]')

        # Min off
        for t in self.period[1:]:
            for g in self.generators.index:
                min_off_time = min(t + self.generators.loc[g, 'min_off'] - 1, len(self.period))
                for tau in range(t, min_off_time + 1):
                    self.model.add_constr(1 - self.u[tau, g] >= self.u[t-1, g] - self.u[t, g],
                                          name=f'min_off_constr[{t},{g}]')

        # Objective function
        self.model.objective = minimize(
            xsum(
                xsum(
                    self.p[t, g] * self.generators.loc[g, 'c_var']
                    + self.u[t, g] * self.generators.loc[g, 'c_fix']
                    for g in self.generators.index
                ) for t in self.period
            )
        )

    def optimize(self):

        self.model.optimize()

        return self.u, self.p, self.model.objective.x, self.model.status.name

    def get_prices(self):

        u_fixed = {
            (t, g): self.u[t, g].x
            for g in self.generators.index
            for t in self.period
        }
        self.model.clear()
        self.build_model(fixed=True, u_fixed=u_fixed)
        self.optimize()

        return [self.model.constr_by_name(f'power_bal_constr[{t}]').pi for t in self.period]
