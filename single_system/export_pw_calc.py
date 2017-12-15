#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 19:55:04 2016

@author: hormann_formationenergies
"""

#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

import sys
import os

from aiida.common.example_helpers import test_and_get_code
from aiida.orm import DataFactory
from aiida.common.exceptions import NotExistent

# If set to True, will ask AiiDA to run in serial mode (i.e., AiiDA will not
# invoke the mpirun command in the submission script)
run_in_serial_mode = False

################################################################

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')


import shutil

def export_data(s, kpointsmesh, parametersdict, folder):
    
    submit_test = True
    codename = 'pw-5.2-local@localhost_imported'
    
    
    # If True, load the pseudos from the family specified below
    # Otherwise, use static files provided
    pseudo_family = 'SSSP_v0.7_eff_PBE'
    
    queue = None
    # queue = "Q_aries_free"
    settings = None
    #####
    
    code = test_and_get_code(codename, expected_code_type='quantumespresso.pw')
    
    
    elements = list(s.get_symbols_set())
    

    
    parameters = ParameterData(dict=parametersdict)
    
#    parameters = ParameterData(dict={
#        'CONTROL': {
#            'calculation': 'scf',
#            'restart_mode': 'from_scratch',
#            'wf_collect': True,
#            'tstress': True,
#            'tprnfor': True,
#        },
#        'SYSTEM': {
#            'ecutwfc': 40.,
#            'ecutrho': 320.,
#        },
#        'ELECTRONS': {
#            'conv_thr': 1.e-10,
#        }})
    
    kpoints = KpointsData()

    kpoints.set_kpoints_mesh(kpointsmesh)
    
    #settings = ParameterData(dict=settings_dict)
    
    ## For remote codes, it is not necessary to manually set the computer,
    ## since it is set automatically by new_calc
    #computer = code.get_remote_computer()
    #calc = code.new_calc(computer=computer)
    
    calc = code.new_calc()
    #calc.label = "Test QE pw.x"
    calc.description = "Test calculation with the Quantum ESPRESSO pw.x code"
    calc.set_max_wallclock_seconds(30 * 60)  # 30 min
    # Valid only for Slurm and PBS (using default values for the
    # number_cpus_per_machine), change for SGE-like schedulers
    calc.set_resources({"num_machines": 1})
    if run_in_serial_mode:
        calc.set_withmpi(False)
    ## Otherwise, to specify a given # of cpus per machine, uncomment the following:
    # calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 8})
    
    #calc.set_custom_scheduler_commands("#SBATCH --account=ch3")
    
    if queue is not None:
        calc.set_queue_name(queue)

    atoms = s.get_ase()
    supercell = StructureData() 
    supercell.set_ase(atoms.repeat([2,2,2])) 


    calc.use_structure(s)
    calc.use_parameters(parameters)
    

    calc.use_pseudos_from_family(pseudo_family)
    
    calc.use_kpoints(kpoints)
    
    if settings is not None:
        calc.use_settings(settings)
    #from aiida.orm.data.remote import RemoteData
    #calc.set_outdir(remotedata)
    
    
    if submit_test:
        subfolder, script_filename = calc.submit_test()
        print "Test_submit for calculation (uuid='{}')".format(
            calc.uuid)
        print "Submit file in {}".format(os.path.join(
            os.path.relpath(subfolder.abspath),
            script_filename
        ))
        
        shutil.copytree(os.path.relpath(subfolder.abspath), folder + '/QE_run')
