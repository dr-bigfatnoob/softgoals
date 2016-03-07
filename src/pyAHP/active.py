from __future__ import print_function, division
import sys,os
sys.path.append(os.path.abspath("."))
from utilities.lib import *
from pyAHP.de import DE
from pyAHP.model import Model
from pyAHP.where import Where, Row
__author__ = 'panzer'


class Report(O):
  id = 0
  def __init__(self):
    O.__init__(self)
    Report.id += 1
    self.id = Report.id
    self.decisions = None
    self.nodes = None

  def print(self):
    print("### Cluster %d"%self.id)
    print("#### Measures")
    print("```")
    columns = ["measure", "median", "iqr"]
    table = PrettyTable(columns)
    for key, val in self.decisions.items():
      table.add_row([key, val.median, val.iqr])
      #print("%s : Median = %0.2f, IQR = %0.2f\n"%(key, val.median, val.iqr))
    print(table)
    print("```")
    print("#### Nodes")
    print("```")
    columns = ["Node", "Cost", "Benefit"]
    table = PrettyTable(columns)
    for key, val in self.nodes.items():
      if val.cost.median == 0 and val.cost.iqr == 0 and \
        val.benefit.median == 0 and val.benefit.iqr == 0:
        continue
      table.add_row([key, "%0.2f +/- %0.2f"%(val.cost.median, val.cost.iqr)
                     , "%0.2f +/- %0.2f"%(val.benefit.median, val.benefit.iqr)])
    print(table)
    print("```\n")



def default_settings():
  return O(
    gens = 100,
    decisions_names = ["costs", "benefits", "softgoals", "decisions_set"],
    verbose = False
  )

class Active(O):
  """
  Identifying the importance of decisions
  """
  def __init__(self, model, **settings):
    """
    Initialize the Active Learner
    :param model:
    :return:
    """
    O.__init__(self)
    self.de = DE(model)
    self.settings = default_settings().update(**settings)


  def learn(self):
    best_points = []
    for _ in range(self.settings.gens):
      say(".")
      self.de.model.generate_costs_benefits()
      stat = self.de.run()
      last_gen = stat.generations[-1]
      gen_best_costs = set()
      gen_best_benefits = set()
      best_cost = sys.maxint
      best_benefit = -sys.maxint
      for point in last_gen:
        if point.objectives[1] > best_benefit:
          gen_best_benefits = set()
          gen_best_benefits.add(point)
        elif point.objectives[1] == best_benefit:
          gen_best_benefits.add(point)
        if point.objectives[0] < best_cost:
          gen_best_costs = set()
          gen_best_costs.add(point)
        elif point.objectives[0] == best_cost:
          gen_best_costs.add(point)
      best_points += list(gen_best_costs)
      best_points += list(gen_best_benefits)
    return best_points

  def cluster(self, best_points):
    rows = []
    for point in best_points:
      objs = point.objectives + [point.decisions_set]
      row = Row(objs)
      row.meta = O(costs=point.node_costs, benefits = point.node_benefits)
      rows.append(row)
    where = Where(rows, min_size = (len(rows)**0.5))
    print("")
    root = where.cluster(verbose=self.settings.verbose)
    clusters = where.get_leaves(root)
    return clusters

  def report_cluster(self, cluster):
    decisions_map = {}
    costs_map = {}
    benefits_map = {}
    report = Report()
    for row in cluster.get_rows():
      for index, decision in enumerate(row.decisions):
        decisions = decisions_map.get(index, [])
        decisions.append(decision)
        decisions_map[index] = decisions
      for node_id in row.meta.costs.keys():
        node_costs = costs_map.get(node_id, [])
        node_costs.append(row.meta.costs[node_id])
        costs_map[node_id] = node_costs
        node_benefits = benefits_map.get(node_id, [])
        node_benefits.append(row.meta.benefits[node_id])
        benefits_map[node_id] = node_benefits
    decisions_report = {}
    for index, name in enumerate(self.settings.decisions_names):
      median, iqr = median_iqr(decisions_map[index])
      decisions_report[name] =  O(median = median, iqr = iqr)
    report.decisions = decisions_report
    nodes_report = {}
    for node_id in costs_map.keys():
      name = self.de.model.get_tree().get_node(node_id).name
      costs = costs_map[node_id]
      benefits = benefits_map[node_id]
      costs_median, costs_iqr = median_iqr(costs)
      benefits_median, benefits_iqr = median_iqr(benefits)
      nodes_report[name] = O(cost=O(median=costs_median, iqr=costs_iqr),
                             benefit=O(median=benefits_median, iqr=benefits_iqr))
    report.nodes = nodes_report
    return report


def _main():
  from pyAHP.models.sample import tree
  model = Model(tree, generation_mode = "triangular")
  active = Active(model)
  best_points = active.learn()
  clusters = active.cluster(best_points)
  print("")
  for cluster in clusters:
    active.report_cluster(cluster).print()


if __name__ == "__main__":
  _main()

