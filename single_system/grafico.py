import numpy
import matplotlib.pyplot as plt
import argparse
import colorsys
from collections import defaultdict
from aux_routines import *

parser = argparse.ArgumentParser()
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
for i in args.workflow_pk:
    w = load_workflow(i)
    wf_params = w.get_parameters()
    pw_codename = wf_params['pw_codename']
    code = Code.get_from_string(pw_codename)
    computer = code.get_remote_computer()
    nprocs_per_node = int(computer.get_default_mpiprocs_per_machine())
    all_calcs = list(w.get_step_calculations(w.launch_calculation))
    for j in list(all_calcs[i] for i in [0,1,2,3]):
       times[count].append(j.res.wall_time_seconds)
       speedup[count].append(float(times[count][0])/j.res.wall_time_seconds)
       nodes[count].append(j.get_attrs()['jobresource_params']['num_machines'])
    count+=1

N = len(times[0])
width = 0.35
ind = np.arange(N)

fig, ax = plt.subplots()
rects1 = ax.bar(ind, times[0], width, color='g')
rects2 = ax.bar(ind+width, times[1], width, color='b')
# add some text for labels, title and axes ticks
ax.set_ylabel('Time to solution(seconds)')
ax.set_xlabel('Number of nodes')
ax.set_xticks(ind+width/2)
ax.set_xticklabels(nodes[0])

ax.legend((rects1[0], rects2[0]), ('pw-6.1@fidis', 'pw+sirius@PizDaint'))
ax.set_title('BaTiO3')

autolabel(rects1)
autolabel(rects2)
plt.savefig('tts.png')

fig1, ax = plt.subplots()
rects1 = ax.bar(ind, speedup[0], width, color='g')
rects2 = ax.bar(ind+width, speedup[1], width, color='b')
# add some text for labels, title and axes ticks
ax.set_ylabel('Speedup')
ax.set_xlabel('Number of nodes')
ax.set_xticks(ind+width/2)
ax.set_xticklabels(nodes[0])
ax.set_title('BaTiO3')

ax.legend((rects1[0], rects2[0]), ('pw-6.1@fidis', 'pw+sirius@PizDaint'), loc=2)

autolabel(rects1)
autolabel(rects2)


plt.savefig('speedup.png')

