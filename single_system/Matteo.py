#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
from aiida.workflows.user.hpc_workflow.hpc import HpcWorkflow
from aiida.workflows.user.hpc_workflow.workflow_bench import BenchWorkflow
import sys
import math
import os
from aiida.common.example_helpers import test_and_get_code
from aiida.tools.codespecific.quantumespresso import pwinputparser
import json, argparse
from rescale_structures import *

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')

parser = argparse.ArgumentParser()
parser.add_argument("code", help="code and machine where you would like to run")
parser.add_argument("json_hpc", help="json file with HPC parameters")
args = parser.parse_args()

StructureData = DataFactory('structure')
UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')

pseudo_family = 'sssp_eff_pbe_2'
file_input = pwinputparser.PwInputFile(open('pw.in'))

structure = file_input.get_structuredata()
structure.store()


kpoints = file_input.get_kpointsdata()
kpoints_mesh = kpoints.get_kpoints_mesh()
kpoints.store()

file_input.namelists['SYSTEM'].pop('ibrav',None)
file_input.namelists['SYSTEM'].pop('nat',None)
file_input.namelists['SYSTEM'].pop('ntyp',None)

pw_parameters = ParameterData(dict=file_input.namelists)

pw_parameters.store()

with open(args.json_hpc) as data_file:    
   hpc_file = json.load(data_file)
hpc_parameters =  ParameterData(dict=hpc_file)
hpc_parameters.store()

codename = test_and_get_code(args.code, expected_code_type='quantumespresso.pw')
UpfData.get_upf_group(pseudo_family)

workflow_params = {'pw_codename': args.code,
                   'structure': structure,
                   'hpc_params': hpc_parameters,
                   'pseudo_family': pseudo_family,
                   'kpoints':kpoints_mesh,
                   'pw_parameters': pw_parameters,
                   }

w = HpcWorkflow()
w.set_params(workflow_params)

w.store()
w.start()

print 'Wf PK: {}'.format(w.pk)

