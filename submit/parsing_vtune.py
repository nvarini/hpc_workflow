import numpy
import matplotlib.pyplot as plt
import argparse
import colorsys
from aiida.workflows.user.hpc_workflow.postprocessing.aux_routines import *
from collections import defaultdict
import os
import subprocess


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


times = {}

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
                
                if ncalc is 0:
                    composition = calc.get_inputs_dict()['structure'].get_composition()
                    for k,v in composition.iteritems():
                        structure += k + str(v) 
                print "Vtune file is found at %s " % vtune_file
            else:
                print "Vtune profile file for calc %s is not available" % calc 
