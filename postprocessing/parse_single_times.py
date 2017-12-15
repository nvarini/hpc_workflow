import numpy
import matplotlib.pyplot as plt
import argparse
import colorsys
from aiida.workflows.user.hpc_workflow.postprocessing.aux_routines import *
from collections import defaultdict
from cycler import cycler

parser = argparse.ArgumentParser()
parser.add_argument("title",type=str,help="Physical system")
parser.add_argument("number_nodes",type=int,help="Number of nodes desired for the plot")
parser.add_argument("workflow_pk",type=int,nargs='+',help="workflow number")
args = parser.parse_args()

def autolabel(rects):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                "%8.2f" % height,
                ha='center', va='bottom')

def count_elements(array,counts):
  for i in array:
    if i not in counts:
      counts.append(i)

times = defaultdict(list)
speedup = defaultdict(list)
nodes = defaultdict(list)

count = 0

string_for_title = []
for i in args.workflow_pk:
    w = load_workflow(i)
    wf_params = w.get_parameters()
    pw_codename = wf_params['pw_codename']
    code = Code.get_from_string(pw_codename)
    computer = code.get_remote_computer()
    nprocs_per_node = int(computer.get_default_mpiprocs_per_machine())
    all_calcs = list(w.get_step_calculations(w.launch_calculation))
    nodes_for_plot = np.arange(0,min(args.number_nodes,len(all_calcs)))
    for j in list(all_calcs[i] for i in nodes_for_plot):
       times[count].append(j.res.wall_time_seconds)
       speedup[count].append(float(times[count][0])/j.res.wall_time_seconds)
       nodes[count].append(j.get_attrs()['jobresource_params']['num_machines'])
    string_for_title.append(w.get_parameters()['pw_codename'])
    count+=1

N = len(times[0])
width = 1.0/(len(args.workflow_pk)+1.0) 
ind = np.arange(N)

fig, ax = plt.subplots()
rects = []
prop_iter = iter(plt.rcParams['axes.prop_cycle'])
for i in np.arange(0,len(args.workflow_pk)):
    rects.append(ax.bar(ind+i*width,times[i],width,\
                color=next(prop_iter)['color']))
    

ax.set_ylabel('Time to solution(seconds)')
ax.set_xlabel('Number of nodes')
ax.set_xticks(ind+width/2)
ax.set_xticklabels(nodes[0])

ax.legend(rects,string_for_title)
ax.set_title(args.title)

for i in np.arange(0,len(args.workflow_pk)):
    autolabel(rects[i])
plt.savefig('tts.png')

fig1, ax = plt.subplots()

rects = []
prop_iter = iter(plt.rcParams['axes.prop_cycle'])
for i in np.arange(0,len(args.workflow_pk)):
    rects.append(ax.bar(ind+i*width,speedup[i],width,\
                color=next(prop_iter)['color']))
 
ax.set_ylabel('Speedup')
ax.set_xlabel('Number of nodes')
ax.set_xticks(ind+width/2)
ax.set_xticklabels(nodes[0])
ax.set_title(args.title)

ax.legend(rects,string_for_title)

for i in np.arange(0,len(args.workflow_pk)):
    autolabel(rects[i])

plt.savefig('speedup.png')

