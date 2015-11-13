# -*- coding: utf-8 -*-
from aiida.common import aiidalogger
from aiida.orm.workflow import Workflow
from aiida.orm import Code, Computer
from aiida.orm import CalculationFactory, DataFactory

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')
logger = aiidalogger.getChild('HpcWorkflow')

## ===============================================
##    WorkflowXTiO3_EOS
## ===============================================

def create_pw_calculation(the_wf, parallelization_dict, 
                         gamma_only=False):
    """
    Returns a unstored calculation with inputs set
    """    
    work_params = the_wf.get_parameters()

    pw_codename = work_params['pw_codename']
    pseudo_family = work_params['pseudo_family']
    structure = work_params['structure']
    pw_parameters = work_params['pw_parameters']
    
    code = Code.get_from_string(pw_codename)
    computer = code.get_remote_computer()
    
    PwCalculation = CalculationFactory('quantumespresso.pw')
    
    calc = code.new_calc()
    calc.use_code(code)
    calc.use_structure(structure)
    calc.use_pseudos_from_family(pseudo_family)
    calc.use_parameters(pw_parameters)
    
    if not gamma_only:
        kpoints = wf_params['kpoints']
    else:
        kpoints = KpointsData()
        kpoints_mesh = 1
        kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh])
        
    calc.use_kpoints(kpoints)
    
    num_machines = parallelization_dict['num_machines']
    max_wallclock_seconds = parallelization_dict['max_wallclock_seconds']
    nd = parallelization_dict['nd']
    ntg = parallelization_dict['ntg']
    omp_num_threads = parallelization_dict['omp_num_threads']
    
    default_num_mpiprocs_per_machine = computer.get_default_mpiprocs_per_machine()
    num_mpiprocs_per_machine = 16# the right value, taking omp into account
    
    calc.set_max_wallclock_seconds(max_wallclock_seconds)
    calc.set_resources({"num_machines": num_machines, 
                    "num_mpiprocs_per_machine": num_mpiprocs_per_machine})

    calc.set_prepend_text(["export OMP_NUM_THREADS {}".format(omp_num_threads)])
    
    if nd is not None and ntg is not None:
        settings = ParameterData(dict={'CMDLINE':['-nd', nd, '-ntg',ntg]})
        calc.use_settings(settings)
    
    calc.set_mpirun_extra_params([str(parallelization_dict['mp_exec']['command_for_tasks_per_node']), 
                                  str(num_mpiprocs_per_machine),
                                  str(parallelization_dict['mp_exec']['command_for_cpus_per_task']), 
                                  str(omp_num_threads)])

    return calc


class HpcWorkflow(Workflow):

    def __init__(self, **kwargs):
        super(HpcWorkflow, self).__init__(**kwargs)

    ## ===============================================
    ##    Wf steps
    ## ===============================================

    @Workflow.step
    def start(self):
        wf_params = self.get_parameters()
        # Here place validation of the input
        validation_is_passed=True

        self.append_to_report("Hpc Workflow started")
        if validation_is_passed:
            self.next(self.launch_gamma_only_calc)
        else:
            self.next(self.exit)


    @Workflow.step
    def launch_gamma_only_calc(self):
        # use only gamma kpoint, but with complex part

        wf_params = self.get_parameters()
        
        parallelization_dict = {}        
        hpc_params = wf_params['hpc_params'].get_dict()

        parallelization_dict['num_machines'] = hpc_params['nodes']
        parallelization_dict['max_wallclock_seconds'] = hpc_params['max_wallclock_seconds']
        parallelization_dict['nd'] = None
        parallelization_dict['ntg'] = None
        parallelization_dict['omp_num_threads'] = 1
        parallelization_dict['mp_exec'] = {}
        parallelization_dict['mp_exec']['command_for_tasks_per_node'] = hpc_params['mp_exec']['command_for_tasks_per_node']
        parallelization_dict['mp_exec']['command_for_cpus_per_task']  = hpc_params['mp_exec']['command_for_cpus_per_task']

        calc = create_pw_calculation(self, 
                                     parallelization_dict,
                                     gamma_only=True)
        calc.store_all()
        self.attach_calculation(calc)
#        self.next(self.launch_subworkflows_for_mpi_and_omp)
        self.next(self.exit)


    @Workflow.step
    def launch_subworkflows_for_mpi_and_omp(self):
        raise NotImplementedError
        self.attach_workflow(wf)
    

    @Workflow.step
    def get_results_for_mpi_and_omp(self):
        # gather the best results for ntg and nd, in the case of mpi or omp
        raise NotImplementedError

    @Workflow.step
    def launch_irred_kpoints(self):
        # launch a calculation 
        # to find the number of pools usable
        raise NotImplementedError
        
        
    @Workflow.step
    def pool_study(self):
        raise NotImplementedError





class NdandntgWorkflow(Workflow):
    def __init__(self, **kwargs):
        super(NdandntgWorkflow, self).__init__(**kwargs)
        
    @Workflow.step
    def start(self):
        # launch a series of run with
        # - stil gamma only
        # - 3 runs changing ntg
        # - 3 runs changing nd
        raise NotImplementedError

    @Workflow.step
    def best_of_nd_and_ntg(self):
    # a run in which we choose the best parameters of the previous step
        raise NotImplementedError
        list_of_calcs = self.get_step_calculations(self.start)


    @Workflow.step
    def return_results(self):
        raise NotImplementedError

        key='my_preferred'
        value = 2
        self.add_result(key, value)

