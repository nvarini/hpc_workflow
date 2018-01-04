import numpy
import matplotlib.pyplot as plt
import argparse
import colorsys
from aiida.workflows.user.hpc_workflow.postprocessing.aux_routines import *
from collections import defaultdict
import os
import subprocess
import re
from aiida.orm.querybuilder import QueryBuilder
from aiida.orm import Group
from collections import defaultdict, OrderedDict
from operator import itemgetter
from matplotlib import colors as mcolors


parser = argparse.ArgumentParser()
parser.add_argument('-w','--workflow_pk',type=int,nargs='+',help="workflow number")
parser.add_argument('-s','--scale',type=int,nargs='+',help="Scaling of the original strucutre, 2 1 1")
parser.add_argument('-g','--group',type=str,help="Aiida original group")
args = parser.parse_args()
system_type = defaultdict(list)
times = {}
extra_types = []
subplots = []

def autolabel(rects):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                "%8.2f" % height,
                ha='center', va='bottom')


colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)

def generateColorGradient(RGB1, RGB2, n):
     dRGB = [float(x2-x1)/(n-1) for x1, x2 in zip(RGB1, RGB2)]
     gradient = [tuple([(x+k*dx) for x, dx in zip(RGB1, dRGB)]) for k in range(n)]
     return gradient


for num_work, wf_pk in enumerate(args.workflow_pk):
    wf = load_workflow(wf_pk)
    subworkflows = wf.get_steps()[1].get_sub_workflows()
    for wf in subworkflows:
        calcs = wf.get_step_calculations(wf.launch_calculation)
        structure = ''
        for ncalc,calc in enumerate(calcs):
            node = calc.get_retrieved_node()
            node_path = node.get_abs_path()
            vtune_file = node_path+'/path/profile.vtune'
            if os.path.exists(vtune_file):
                file_content = node.get_file_content('profile.vtune')
                file_content = file_content.split('\n')
                
                if ncalc is 0:
                    composition = calc.get_inputs_dict()['structure'].get_composition()
                    for k,v in composition.iteritems():
                        structure += k + str(v) 
                file_vtune = []
                
                for i in file_content[2:12]:
                    tmp = []
                    tmp.append(re.split("  +",i))
                    tmp[0][1] = float(tmp[0][1][:-1])
                    file_vtune.append(tmp[0][0:2]) 

                times.update({structure: file_vtune})
                #print "Vtune file is found at %s " % vtune_file
            else:
                print "Vtune profile file for calc %s is not available" % calc 
           

qb = QueryBuilder()
qb.append(JobCalculation,tag="mycalculation",project=["*"])
qb.append(Group,filters={"name":args.group},group_of="mycalculation")
calcs_list=qb.all()

scale_factor = reduce((lambda x, y: x*y),args.scale) 
for calc in calcs_list:
    composition = calc[0].get_inputs_dict()['structure'].get_composition()
    structure = ''
    modified_structure = ''
    for k,v in composition.iteritems():
        structure += k + str(v*scale_factor) 
    extra_type = calc[0].get_extra('type')
    system_type[extra_type].append(structure)
    if extra_type not in extra_types: extra_types.append(extra_type)

for i, j in enumerate(extra_types):
    string=str(1)+str(len(extra_types))+str(i+1)
    subplots.append(string)

count_subplot = 0
for system_k, system_v in system_type.iteritems():
    y_dict = {}
    x = []
    y = []
    labels = []
    labels_x = []
    count_labels = 1
    for times_k, times_v in times.iteritems():
        if times_k in system_v:
            y_dict[times_k] = times_v
            labels.append(times_k)
            labels_x.append(count_labels)
            count_labels += 1
    #y_dict = OrderedDict(sorted(y_dict.items(), key=itemgetter(1)))
    y_dict = OrderedDict(sorted(y_dict.items(), key=lambda x: int(x[1][0][1])))
    count = 1
    for k,v in y_dict.iteritems():
        for i, j in enumerate(v):
             x.append(count)
        count += 1 
    plt.subplot(subplots[count_subplot])
    #print subplots[count_subplot]
    count_subplot += 1
    y = np.array(y_dict.values())
    y_plot = y.take(1,axis=2).flatten().astype(np.float)
    
   # if count_subplot > 1 : plt.yticks([]) 
    #print y_dict
    plt.grid(True, axis='both')
    plt.subplots_adjust(top=0.92, bottom=0.08, left=0.10, right=0.95, hspace=0.25,
                    wspace=0.35)
    plt.plot(x, y_plot, 'o', color=(0,0,0))
    #plt.plot(x, y_plot, 'o')
    plt.xticks(labels_x, labels, rotation='vertical')

plt.show()
