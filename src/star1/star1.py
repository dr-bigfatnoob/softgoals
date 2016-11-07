from __future__ import print_function, division
import sys, os, time
sys.path.append(os.path.abspath("."))
__author__ = 'george'
sys.dont_write_bytecode = True
from utilities.lib import *
from pystar.model import Model, Point
import pystar.template as template
from utilities.de import DE
from utilities.nsga2 import select as sel_nsga2
from utilities.plotter import med_spread_plot
from prettytable import PrettyTable
from utilities.sk import rdivDemo
import numpy as np
from matplotlib import pyplot as plt

def default():
  return O(
    k1 = 10,
    k2 = 10,
    best_percent = 20,
    gen_step = 2
  )

class Decision(O):
  def __init__(self, **params):
    O.__init__(self, **params)

  def __hash__(self):
    return hash(self.id)

class Star1(O):
  def __init__(self, model, **settings):
    O.__init__(self)
    self.model = model
    #self.model.bases.extend(self.get_conflicts());self.model.assign_costs()
    self.settings = default().update(**settings)
    self.de = DE(model, gens = self.settings.k1)


  def get_conflicts(self):
    model = self.model
    graph = model.get_tree()
    nodes = []
    for node in graph.get_nodes():
      if node.type == "softgoal" and len(node.from_edges) > 1:
        toggle = None
        for edge_id in node.from_edges:
          edge = graph.get_edge(edge_id)
          if edge.type == "contribution":
            temp_toggle = sign(template.Edge.get_contribution_weight(edge.value))
            if toggle is None: toggle = temp_toggle
            if temp_toggle != toggle:
              nodes.append(node)
              break
    return nodes

  def sample(self):
    stat = self.de.run()
    stat.settings.gen_step = self.settings.gen_step
    stat.tiles()
    best = set()
    for obj_index in range(len(self.de.settings.obj_funcs)):
      sorted_pop = sorted(stat.generations[-1], key=lambda x: x.objectives[obj_index], reverse=True)[:len(stat.generations[-1])//5]
      best.update(sorted_pop)
    rest = set()
    for gen in stat.generations:
      for point in gen:
        if not point in best:
          rest.add(point)
    return best, rest

  # def sample(self):
  #   stat = self.de.run()
  #   stat.settings.gen_step = self.settings.gen_step
  #   stat.tiles()
  #   population = set()
  #   for gen in stat.generations:
  #     for point in gen:
  #       population.add(point)
  #   best_size = int(len(population) * self.settings.best_percent/100)
  #   best = sel_nsga2(self.model, list(population), best_size)
  #   rest = population - set(best)
  #   return list(best), list(rest)

  def rank(self, best, rest):
    best_size = len(best)
    rest_size = len(rest)
    p_best = best_size / (best_size + rest_size)
    p_rest = rest_size / (best_size + rest_size)
    decisions = []
    for dec_node in self.model.bases:
      f_best, pos_count, neg_count = 0, 0, 0
      for point in best:
        if point.decisions[dec_node.id] > 0:
          pos_count += 1
        elif point.decisions[dec_node.id] < 0:
          neg_count += 1
      f_pos_best = pos_count / best_size
      l_pos_best = f_pos_best * p_best
      f_neg_best = neg_count / best_size
      l_neg_best = f_neg_best * p_best
      f_pos_rest, f_neg_rest = 0, 0
      for point in rest:
        if point.decisions[dec_node.id] > 0:
          f_pos_rest += 1
        else:
          f_neg_rest += 1
      f_pos_rest /= rest_size
      f_neg_rest /= rest_size
      l_pos_rest = f_pos_rest * p_rest
      l_neg_rest = f_neg_rest * p_rest
      if l_pos_best == 0 and l_pos_rest == 0:
        sup_pos = 0
      else:
        sup_pos = l_pos_best ** 2 / (l_pos_best + l_pos_rest)
      if l_neg_best == 0 and l_neg_rest == 0:
        sup_neg = 0
      else:
        sup_neg = l_neg_best ** 2 / (l_neg_best + l_neg_rest)
      decisions.append(Decision(id = dec_node.id, name = dec_node.name,
                                support=sup_pos, value = 1,
                                type = dec_node.type, container=dec_node.container,
                                cost = self.model.cost_map[dec_node.id]))
      decisions.append(Decision(id = dec_node.id, name = dec_node.name,
                                support=sup_neg, value = -1,
                                type = dec_node.type, container=dec_node.container,
                                cost = self.model.cost_map[dec_node.id]))
    decisions.sort(key=lambda x:x.support, reverse=True)
    sorted_decs = []
    aux = set()
    for dec in decisions:
      if dec.id not in aux:
        sorted_decs.append(dec)
        aux.add(dec.id)
    assert len(sorted_decs) == len(self.model.bases), "Mismatch after sorting support"
    return sorted_decs

  def generate(self, presets = None):
    population = list()
    while len(population) < self.settings.k2:
      point = Point(self.model.generate())
      if not point in population:
        for preset in presets:
          point.decisions[preset.id] = preset.value
        population.append(point)
    return population

  @staticmethod
  def objective_stats(generations):
    stats = []
    obj_len = len(generations[0][0].objectives)
    objective_map={}
    for i in range(obj_len):
      objectives = []
      data_map = {}
      meds = []
      iqrs = []
      for gen, pop in enumerate(generations):
        objs = [pt.objectives[i] for pt in pop]
        objectives.append(objs)
        med, iqr = median_iqr(objs)
        meds.append(med)
        iqrs.append(iqr)
      objective_map[i] = objectives
      data_map["meds"] = meds
      data_map["iqrs"] = iqrs
      stats.append(data_map)
    return stats, objective_map

  def evaluate(self, point, decisions):
    model = self.model
    if not point.objectives:
      model.reset_nodes(point.decisions)
      funcs = [Point.eval_softgoals, Point.eval_goals, Point.eval_paths]
      point.objectives = [func(model) for func in funcs]
      point.objectives.append(sum(decision.cost for decision in decisions if decision.value > 0))
      point._nodes = [node.clone() for node in model.get_tree().get_nodes()]
    return point.objectives

  def prune(self, support):
    gens = []
    for i in range(len(support)):
      decisions = support[:i]
      population = self.generate(decisions)
      for point in population:
        self.evaluate(point, decisions)
        # TODO - Mark Best objective model here
        #self.de.settings.evaluation(point, self.model, self.de.settings.obj_funcs)
      gens.append(population)
    obj_stats, objective_map = self.objective_stats(gens)
    return obj_stats, gens, objective_map

  def report(self, stats, sub_folder, fig_name):
    #headers = [obj.__name__.split("_")[-1] for obj in self.de.settings.obj_funcs]
    headers = ["softgoals", "goals", "costs"]
    med_spread_plot(stats, headers, fig_name="img/"+sub_folder+"/"+fig_name+".png")
    return "img/"+sub_folder+"/"+fig_name+".png"

  @staticmethod
  def get_elbow(gens, index, obj_index=None):
    pop = gens[index]
    pop = sorted(pop, key=lambda x: x.objectives[obj_index])
    point = pop[len(pop)//2]
    return point

def print_decisions(decisions):
  columns = ["rank", "name", "type", "value", "cost", "support"]
  table = PrettyTable(columns)
  for i, decision in enumerate(decisions):
    row = [i+1, decision.name, decision.type, decision.value, decision.cost, round(decision.support, 5)]
    table.add_row(row)
  print("\n### Decisions Ranked")
  print("```")
  print(table)
  print("```")

def smoothen(objective_map, decisions, keys=[0, 1]):
  smoothened = []
  for key in keys:
    objectives = objective_map[key]
    sk_data = []
    for index, (decision, dec_objectives) in enumerate(zip(decisions, objectives)):
      sk_data.append([str(index)]+dec_objectives)
    ranks = rdivDemo(sk_data, do_print=False, useA12=False, epsilon=0.5)
    rank_map = {}
    for rank, _, x in ranks:
      meds_iqrs = rank_map.get(rank, [[], []])
      med, iqr = median_iqr(x.all)
      meds_iqrs[0].append(med)
      meds_iqrs[1].append(iqr)
      rank_map[rank] = meds_iqrs
    smooth_objs = {}
    meds, iqrs = [], []
    for rank, _, x in ranks:
      meds_iqrs = rank_map[rank]
      med, iqr = custom_round(np.mean(meds_iqrs[0]), 10), custom_round(np.mean(meds_iqrs[1]), 10)
      meds.append(med)
      iqrs.append(iqr)
      smooth_objs["meds"] = meds
      smooth_objs["iqrs"] = iqrs
    smoothened.append(smooth_objs)
  return smoothened

def custom_round(val, base):
  return int(base*round(val/base))

def run(graph, subfolder, optimal_index = None):
  #graph = DelayModeratedBulletinBoard()
  #model = Model(cs_agent_sr_graph)
  start = time.time()
  model = Model(graph)
  print("## %s"%graph.name)
  print("```")
  star = Star1(model)
  best, rest = star.sample()
  decisions = star.rank(best, rest)
  obj_stats, gens, objective_map = star.prune(decisions)
  smoothened = smoothen(objective_map, decisions)
  smoothened += obj_stats[2:]
  med_iqr_plot = star.report(obj_stats[:2] + [obj_stats[3]], subfolder, graph.name)
  smoothened_plot = star.report(smoothened[:2]+[obj_stats[3]], subfolder, model.get_tree().name + "_smooth")
  print("```")
  print("![1](../../../src/%s)"%med_iqr_plot)
  print("### Smoothened Plot")
  print("![1](../../../src/%s)" % smoothened_plot)
  print_decisions(decisions)
  if optimal_index is not None:
    print("\n### Top %d Decisions from above table."%optimal_index)
    print("```")
    point = star.get_elbow(gens, optimal_index, obj_index = 0)
    columns = ["name", "type", "value"]
    table = PrettyTable(columns)
    for node in point.get_nodes():
      if node.value:
        row = [node.name, node.type, node.value]
        table.add_row(row)
    print(table)
    print("```")
  delta = time.time() - start
  print("\n### Time Taken : %s" % delta)


def plot_runtimes():
  x = ["CSServices", "CSFDandMarketing", "CSCounselling", "CSCounsellingMgmt", "CSITDepartment", "CSSAProgram", "KidsAndYouth"]
  nsga2 = [1002.4, 903.8, 930.6, 428.4, 224.5, 243.3, 132.3]
  our = [18.7, 20, 21.4, 6.1, 1.54, 0.97, 0.51]
  width = 0.35
  fig, ax = plt.subplots()
  ind = np.arange(len(x))
  rects1 = ax.bar(ind, our, width, color='r')
  rects2 = ax.bar(ind+width, nsga2, width, color='b')
  ax.legend((rects1[0], rects2[0]), ('Our Method', 'NSGA2'))
  plt.xticks(ind+2*width, x, rotation=-45, fontsize=9)
  plt.ylabel("Runtime (in seconds)")
  plt.yscale("log")
  plt.tight_layout()
  plt.savefig("sg_runtimes.png")

# plot_runtimes()
# if __name__ == "__main__":
#   from pystar.models.dot_models import CSCounsellingManagement
#   run(CSCounsellingManagement(), "correction2")