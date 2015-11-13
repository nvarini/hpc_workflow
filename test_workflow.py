#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
from aiida.workflows.user.hpc_workflow.hpc import HpcWorkflow
import sys
from aiida.common.example_helpers import test_and_get_code

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')

############# INPUT #############

dontsend = False
try:
    codename = sys.argv[1]
except IndexError:
    codename = None

pseudo_family = 'ssp_eff_pbe'

# define structure
alat = 4.  # angstrom
cell = [[alat, 0., 0., ],
        [0., alat, 0., ],
        [0., 0., alat, ]]
s = StructureData(cell=cell)
s.append_atom(position=(0., 0., 0.), symbols=['Ba'])
s.append_atom(position=(alat / 2., alat / 2., alat / 2.), symbols=['Ti'])
s.append_atom(position=(alat / 2., alat / 2., 0.), symbols=['O'])
s.append_atom(position=(alat / 2., 0., alat / 2.), symbols=['O'])
s.append_atom(position=(0., alat / 2., alat / 2.), symbols=['O'])
s.store()


pw_parameters = ParameterData(dict={
    'CONTROL': {
        'calculation': 'scf',
        'restart_mode': 'from_scratch',
        'wf_collect': True,
        'tstress': True,
        'tprnfor': True,
    },
    'SYSTEM': {
        'ecutwfc': 40.,
        'ecutrho': 320.,
    },
    'ELECTRONS': {
        'conv_thr': 1.e-10,
    }})

pw_parameters.store()

kpoints = KpointsData()
kpoints_mesh = 2
kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh])
kpoints.store()

hpc_parameters =  ParameterData(dict={
    'nodes': 2,
    'procs': 16,
    'nd': [2,4], # optional
    'ntg': [1,2,4], # optional
    'omp_num_thread': 8,
    'max_wallclock_seconds': 10000,
    'mp_exec':{'command_for_tasks_per_node':'--tasks-per-node',
               'command_for_cpus_per_task':'--cpus-per-task'}
    })

hpc_parameters.store()
#################################

code = test_and_get_code(codename, expected_code_type='quantumespresso.pw')
UpfData.get_upf_group(pseudo_family)



workflow_params = {'pw_codename': codename,
                   'structure': s,
                   'hpc_params': hpc_parameters,
                   'pseudo_family': pseudo_family,
                   'kpoints':kpoints,
                   'pw_parameters': pw_parameters,
                   }

w = HpcWorkflow()
w.set_params(workflow_params)

if not dontsend:
    w.store()
    w.start()
    print 'Wf PK: {}'.format(w.pk)
