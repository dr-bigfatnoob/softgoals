from __future__ import print_function
__author__ = 'george'
import os, sys
from models.model import Model
from pystar.model import Model as Py_Model
from utilities.de import DE
from pystar.nsga2 import NSGA2
from utilities.plotter import plot_clusters, bar_plot, med_spread_plot
from utilities.kmeans import KMeans
from star1 import star1
from pystar.models.dot_models import modelers, optimal_indices, CSSAProgram

def process_ood(file_name):
  name = os.path.basename(file_name).split(".")[0]
  print("### " + name)
  print("```")
  model = Model(file_name)
  de = DE(model)
  stat = de.run()
  print("Time Taken : ", stat.runtime)
  stat.tiles()
  data_map = stat.median_spread()
  objs = stat.spit_objectives()
  headers = [obj.__name__.split("_")[-1] for obj in de.settings.obj_funcs]
  cluster_input = [headers] + objs
  print("")
  g = KMeans(k=2)
  clusters = g.run(cluster_input)
  med_spread_plot(data_map, headers, fig_name="img/gen_bin_"+name)
  plot_clusters(clusters,
                fig_name="img/bin_"+name,
                col_names=headers,
                s=50, edgecolors='none')
  print("```")
  print("![1](../../src/img/gen_bin_%s.png)"%name)
  return stat.runtime


def process_visio(file_name):
  from parser.VisioTree import VisioParser
  parser = VisioParser(file_name)
  parser.parse()

def test_pystar():
  from pystar.models.CSServices import graph
  from pystar.model import Model
  #print(graph.nodes)
  model = Model(graph)
  de = DE(model)
  stat = de.run()
  stat.tiles()
  last_gen = stat.generations[-1]
  maxs = [-1]*len(last_gen[0].objectives)
  bests = [None]*len(last_gen[0].objectives)
  for point in last_gen:
    for i in range(len(maxs)):
      if point.objectives[i] > maxs[i]:
        maxs[i] = point.objectives[i]
        bests[i] = point
  print(maxs)
  columns = ["id", "type", "value", "is_random", "name"]
  stat.tabulate(columns, bests[0])


def test_ome_tree():
  process_ood('../GMRepo/CMA12/bCMS_SR_Witness.ood')

def test_visio_tree():
  process_visio('../GMRepo/Counseling Service/Stage1_UnderstandingCS/XML/ParentsSD.vdx')
  #process_visio('../GMRepo/CMA12/bCMS_SR_CommunicationCompromiser.ood')


def test_ome_trees():
  directory = '../GMRepo/CMA12'
  times = {}
  for file_name in os.listdir(directory):
    if file_name.endswith(".ood"):
      dir_file_name = directory + "/" + file_name
      name = os.path.basename(dir_file_name).split(".")[0]
      try:
        times[name] = process_ood(dir_file_name)
      except RuntimeError as e:
        if e[0] == 500:
          print(dir_file_name)
          print(e[1])
          print("```")
        else:
          print(e)
          raise Exception()
      print("")
  bar_plot(times, 'img/random_runtimes.png')

def test_star1(model_name, show_optimal_index = True):
  for model in modelers:
    if model.__name__ == model_name:
      optimal_index = optimal_indices.get(model_name, None) if show_optimal_index else None
      star1.run(model(), SUB_FOLDER, optimal_index=optimal_index)

def test_nsga2(model_name):
  from pystar.models.dot_models import modelers, optimal_indices
  for model in modelers:
    if model.__name__ == model_name:
      NSGA2(Py_Model(model())).run()

def nsga2_main():
  args = sys.argv
  if len(args) < 2:
    print("Invalid args")
    exit()
  test_nsga2(args[1])

def growth_charts():
  softgoals = [[60, 70, 70, 60, 60, 60],
               [50, 60, 60, 50, 50, 40],
               [70, 60, 60, 50, 40, 30],
               [70, 70, 70, 80, 70, 60],
               [81, 78, 75, 83, 80, 80],
               [50, 50, 60, 50, 50, 50],
               [50, 40, 50, 30, 30, 20]]
  goals = [[50, 60, 60, 70, 60, 40],
           [50, 50, 60, 70, 60, 60],
           [70, 70, 60, 50, 50, 40],
           [60, 70, 80, 90, 80, 70],
           [75, 50, 50, 65, 65, 65],
           [30, 60, 70, 70, 70, 70],
           [50, 40, 40, 50, 40, 70]]
  costs = [[0, 16, 25, 28, 31, 35],
           [0, 15, 23, 25, 28, 32],
           [0, 10, 10, 12, 15, 20],
           [0, 7, 13, 18, 18, 18],
           [0, 2, 2, 3, 3, 5],
           [0, 10, 17, 21, 23, 24],
           [0, 2, 5, 7, 9, 10]]
  names = ["Counselling", "Management", "Marketing",
           "ITDepartment", "SAProgram", "Services", "Kids&Youth"]
  x_axis = [0, 20, 40, 60, 80, 100]

  colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan', 'black']
  import matplotlib.pyplot as plt
  def line_plot(data, name, y_label):
    # print(x_axis)
    # plt.plot(x_axis, data[0], color=colors[0], linestyle='-', label=names[0])
    for i in range(len(data)):
      plt.plot(x_axis, data[i], color=colors[i], linestyle='-', label=names[i])
    plt.title(name)
    plt.xlabel("% of decisions")
    plt.ylabel(y_label)
    plt.tight_layout()
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.04), ncol=4, fontsize=8)
    plt.savefig("run_%s.png"%name)
    plt.clf()
  line_plot(softgoals, "softgoals", "% satisfied")
  line_plot(goals, "goals", "% satisfied")
  line_plot(costs, "costs", "total cost")

def growth_charts2():
  softgoals = [[60, 60, 70, 80, 70, 60],
               [50, 50, 60, 60, 50, 40],
               [70, 70, 70, 60, 60, 30],
               [70, 70, 60, 70, 70, 60],
               [80, 80, 80, 80, 80, 80],
               [50, 50, 50, 50, 50, 50],
               [50, 40, 50, 50, 40, 20]]
  goals = [[50, 60, 70, 60, 70, 40],
           [50, 50, 50, 60, 60, 60],
           [70, 70, 70, 70, 60, 40],
           [60, 50, 50, 80, 80, 70],
           [70, 70, 70, 60, 55, 60],
           [30, 50, 60, 60, 70, 70],
           [50, 50, 70, 60, 60, 70]]
  costs = [[0, 5, 10, 20, 28, 35],
           [0, 4,  8, 20, 24, 32],
           [0, 6,  8, 11, 12, 20],
           [0, 2,  4,  9, 17, 18],
           [0, 1,  2,  3,  3,  5],
           [0, 4,  7, 13, 19, 24],
           [0, 0,  0 , 4,  7, 10]]
  names = ["Counselling", "Management", "Marketing",
           "ITDepartment", "SAProgram", "Services", "Kids&Youth"]


  x_axis = [0, 6, 12, 25, 50, 100]

  colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan', 'brown']
  import matplotlib.pyplot as plt
  def line_plot(data, name, y_label, legend=False):
    flatten = [item for sublist in data for item in sublist]
    low, high = max(min(flatten)-5, 0), max(flatten)+5
    for i in range(len(data)):
      plt.plot(x_axis, data[i], color=colors[i], linestyle='-', label=names[i])
    plt.title(name)
    plt.xlabel("% Decisions", fontsize=15)
    plt.xticks(x_axis)
    plt.ylim(low, high)
    plt.ylabel(y_label, fontsize=15)
    plt.tick_params(axis='both', which='major', labelsize=15)
    if legend:
      lgd = plt.legend(loc='center right', bbox_to_anchor=(1, 0.5))
      plt.savefig("run_%s.png" % name, bbox_extra_artists=(lgd,), bbox_inches='tight')
      plt.clf()
    else:
      plt.tight_layout()
      plt.savefig("run_%s.png" % name)
      plt.clf()


  line_plot(softgoals, "SoftGoals", "% Satisfied")
  line_plot(goals, "Goals", "% Satisfied")
  line_plot(costs, "Costs", "Total Cost")
  line_plot(costs, "Legend", "Total Cost", True)




def main():
  args = sys.argv
  if len(args) <= 2:
    print("Invalid args")
    exit()
  show_optimal_index = True if args[2] is not None and args[2] == 'y' else False
  test_star1(args[1], show_optimal_index)

SUB_FOLDER = "correction"

if __name__ == "__main__":
  main()
  # growth_charts2()
  # star1.run(CSSAProgram(), SUB_FOLDER, optimal_index=True)
  # test_star1("CSCounselling", True)
  # nsga2_main()
  # from pystar.models.dot_models import modelers
  # for model in modelers:
  #   m = model()
  #   print(model.__name__, len(m.nodes), len(m.edges))




