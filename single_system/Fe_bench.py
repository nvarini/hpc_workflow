#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
from aiida.workflows.user.hpc_workflow.hpc import HpcWorkflow
import sys
import math
import os
from aiida.common.example_helpers import test_and_get_code
from aiida.tools.codespecific.quantumespresso import pwinputparser
from aiida.common.exceptions import NotExistent
import json

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')


try:
    codename = sys.argv[1]
except IndexError:
    codename = None

pseudo_family = 'ssp_eff_pbe'
file_input = pwinputparser.PwInputFile(open('scf_Fe.in'))

structure = file_input.get_structuredata()
structure.store()


kpoints = file_input.get_kpointsdata()
kpoints_mesh = kpoints.get_kpoints_mesh()
kpoints.store()

#pw_parameters = ParameterData(dict=file_input.namelists)

pw_parameters = ParameterData(dict={
    'CONTROL': {
        'calculation': 'scf',
        'restart_mode': 'from_scratch',
    },
    'SYSTEM': {
        'ecutwfc': 36.75, 
        'occupations': 'smearing',
        'smearing': 'gaussian',
        'degauss': 0.01,
        'nspin' :  2,
        'starting_magnetization(3)':1.0,
    },
    'ELECTRONS': {
        'conv_thr': 1.e-8,
        'mixing_beta': 0.3,
        'mixing_mode': 'plain',
    }})


pw_parameters.store()

with open('conf.json') as data_file:    
   data_benchmark = json.load(data_file)
hpc_parameters =  ParameterData(dict=data_benchmark)
#hpc_parameters =  ParameterData(dict={
#    'nodes': [1,2,4,8,16],
#    'num_threads': [1,2,4,8],
#    'max_wallclock_seconds': 15000,
#    })

hpc_parameters.store()
#################################

code = test_and_get_code(codename, expected_code_type='quantumespresso.pw')
UpfData.get_upf_group(pseudo_family)



workflow_params = {'pw_codename': codename,
                   'structure': structure,
                   'hpc_params': hpc_parameters,
                   'pseudo_family': pseudo_family,
                   'kpoints':kpoints,
                   'pw_parameters': pw_parameters,
                   }

w = HpcWorkflow()
w.set_params(workflow_params)

w.store()
w.start()

print 'Wf PK: {}'.format(w.pk)

