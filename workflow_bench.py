import os
from aiida.orm.workflow import Workflow
from aiida.workflows.user.hpc_workflow.hpc import HpcWorkflow
from aiida.orm import  DataFactory
from aiida.common import aiidalogger


StructureData = DataFactory('structure')
UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
pseudo_family = 'ssp_eff_pbe'
logger = aiidalogger.getChild('BenchWorkflow')

class BenchWorkflow(Workflow):
    def __init__(self, **kwargs):
        super(BenchWorkflow, self).__init__(**kwargs)
        self.times = [] 

    ## ===============================================
    ##    Wf steps
    ## ===============================================
    @Workflow.step
    def start(self):
        work_params = self.get_parameters()
        self.append_to_report("HPC params are: {}".format(work_params['hpc_params_0'].get_attrs()))
        self.next(self.launch_hpcworkflow)

    @Workflow.step
    def launch_hpcworkflow(self):
        wf_params = self.get_parameters()
        numbers_of_structures = len(wf_params)/6
        self.append_to_report("Dependent workflows")
        for i in range(numbers_of_structures):
           codename = wf_params['pw_codename_'+str(i)]
	   structure = wf_params['structure_'+str(i)]
           hpc_parameters = wf_params['hpc_params_'+str(i)]
           pseudo_family = wf_params['pseudo_family_'+str(i)]
	   kpoints = wf_params['kpoints_'+str(i)]
	   pw_parameters = wf_params['pw_parameters_'+str(i)]
           workflow_params = {'pw_codename': codename,
                              'structure': structure,
                              'hpc_params': hpc_parameters,
                              'pseudo_family': pseudo_family,
                              'kpoints':kpoints,
                              'pw_parameters': pw_parameters,
                             }

           wf_hpc = HpcWorkflow()
           wf_hpc.set_params(workflow_params)
           wf_hpc.store()
           self.attach_workflow(wf_hpc)
           wf_hpc.start()
           self.append_to_report("PK: {}".format(wf_hpc.pk))

        self.next(self.hpcworkflow_report)

    @Workflow.step
    def hpcworkflow_report(self):
        self.append_to_report("HPC params are: {}".format(self.get_all_calcs()[0].get_computer()))
        self.next(self.exit)



