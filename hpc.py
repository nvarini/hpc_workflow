# -*- coding: utf-8 -*-
from aiida.common import aiidalogger
from aiida.common.datastructures import CalcInfo
from aiida.orm.workflow import Workflow
from aiida.orm import Code, Computer
from aiida.orm import CalculationFactory, DataFactory
from aiida.orm.data.array.xy import XyData
import math
import numpy
import subprocess
import os, sys

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')
logger = aiidalogger.getChild('HpcWorkflow')

## ===============================================
##    Workflow for HPC analysis
## ===============================================


def scorep_analysis(calc):
    """
    Postprocess scorep file
    """
    string = "cube_stat  -p -t 100 scorep/profile.cubex > profile.cube_stat;" 
    calc.set_append_text(string)

def vtune_analysis(calc,analysis):
    """
    Postprocess vtune file
    """
    string = "amplxe-cl -report "+analysis+" -result-dir vtune_profile > profile.vtune"
    calc.set_append_text(string)


def create_pw_calculation(the_wf, parallelization_dict, 
                         only_initialization=False):
    """
    Returns a unstored calculation with inputs set
    """    

    # get the workflow parameters, profiler name, codename, structure,
    # pw input parameters
    work_params = the_wf.get_parameters()
    profiler = work_params['hpc_params'].get_dict()['profiler'][0]
    if len(work_params['hpc_params'].get_dict()['profiler']) > 1:
        analysis = work_params['hpc_params'].get_dict()['profiler'][1]
    with_sirius = work_params['hpc_params'].get_dict()['with_sirius']
    prepend_text_threads = work_params['hpc_params'].get_dict()['prepend_text_threads']
    prepend_text_others = work_params['hpc_params'].get_dict()['prepend_text_others']
    codename = work_params['pw_codename']
    pseudo_family = work_params['pseudo_family']
    structure = work_params['structure']
    kpoints_mesh = work_params['kpoints']
    pw_parameters = work_params['pw_parameters']

    #Build the Aiida calculation 
    code = Code.get_from_string(codename)
    computer = code.get_remote_computer()
    calc = code.new_calc()
    calc.use_code(code)
    calc.use_structure(structure)
    calc.use_pseudos_from_family(pseudo_family)
    calc.use_parameters(pw_parameters)
   
    kpoints = KpointsData()
    kpoints.set_kpoints_mesh(kpoints_mesh[0])
    calc.use_kpoints(kpoints)
    
    num_machines = parallelization_dict['num_machines']
    max_wallclock_seconds = parallelization_dict['max_wallclock_seconds']
    nd = parallelization_dict['nd']
    ntg = parallelization_dict['ntg']
    nk = parallelization_dict['nk']
    num_threads = parallelization_dict['num_threads']

    default_num_mpiprocs_per_machine = computer.get_default_mpiprocs_per_machine()
    num_mpiprocs_per_machine = default_num_mpiprocs_per_machine/num_threads

    prepend_text_string=''
    for i in prepend_text_threads:
      prepend_text_string+='export '+i+'={}'.format(num_threads)
      prepend_text_string+=';'
    for i in prepend_text_others:
      prepend_text_string+='export '+i+';'

    if profiler == 'scorep':
      prepend_text_string+="export SCOREP_EXPERIMENT_DIRECTORY=scorep"
    calc.set_prepend_text(prepend_text_string) # export KMP_AFFINITY=granularity=fine,compact,1,0; export I_MPI_PIN_DOMAIN=omp
    #
    parallelization_parameters = [] 
      
    
    
    calc.set_max_wallclock_seconds(max_wallclock_seconds)
    calc.set_resources({"num_machines": num_machines, 
                    "num_mpiprocs_per_machine": num_mpiprocs_per_machine})


    settings_dict = {}
    if only_initialization:
        if with_sirius is not "yes":
           settings_dict['ONLY_INITIALIZATION'] = True
        if profiler == 'vtune':
          settings = ParameterData(dict={'CMDLINE':parallelization_parameters, 'additional_retrieve_list': ['profile.vtune'] })
          prepend_mpirun = []
          calc.set_mpirun_extra_params(prepend_mpirun)

        settings = ParameterData(dict=settings_dict)
        calc.use_settings(settings)
    elif only_initialization == False and with_sirius == "no": 
       if(nd>1):
          parallelization_parameters.append('-nd')
          parallelization_parameters.append(str(nd))
       if(ntg>1):
          parallelization_parameters.append('-ntg')
          parallelization_parameters.append(str(ntg))
       if(nk>1):
          parallelization_parameters.append('-nk')
          parallelization_parameters.append(str(nk))

       if profiler == 'scorep':
         settings = ParameterData(dict={'CMDLINE':parallelization_parameters, 'additional_retrieve_list': ['profile.cube_stat'] })
         scorep_analysis(calc)
       elif profiler == 'vtune':
         settings = ParameterData(dict={'CMDLINE':parallelization_parameters, 'additional_retrieve_list': ['profile.vtune','vtune_profile'] })
         prepend_mpirun = str('amplxe-cl -collect '+analysis+' -result-dir vtune_profile').split()
         calc.set_mpirun_extra_params(prepend_mpirun)
         vtune_analysis(calc,analysis)
       else:
         settings = ParameterData(dict={'CMDLINE':parallelization_parameters})
       
       
       if work_params['hpc_params'].get_attrs()['gamma_only'] is True:
         settings.update_dict({'gamma_only': True})
    elif with_sirius == "yes" and only_initialization == False:
         parallelization_parameters.append('-sirius')
         prepend_mpirun = []
         prepend_mpirun.append('-n '+str(num_machines))
         prepend_mpirun.append('-c '+str(num_threads))
         calc.set_mpirun_extra_params(prepend_mpirun)
         settings = ParameterData(dict={'CMDLINE':parallelization_parameters})
    

    calc.use_settings(settings)
    return calc


class HpcWorkflow(Workflow):

    def __init__(self, **kwargs):
        super(HpcWorkflow, self).__init__(**kwargs)
        self.times = [] 

    ## ===============================================
    ##    Wf steps
    ## ===============================================

    @Workflow.step
    def start(self):
        wf_params = self.get_parameters()
        # Here place validation of the input
        self.append_to_report("Hpc Workflow started")
        self.next(self.dry_run)

    @Workflow.step
    def dry_run(self):
        wf_params = self.get_parameters()
        hpc_params = wf_params['hpc_params'].get_dict()
        nodes_dry_run = hpc_params['nodes'][0]
        parallelization_dict = self.set_hpc_parameters(nodes_dry_run,1,1,1,\
                               hpc_params['num_threads'][0])
        if hpc_params['with_sirius'] == "yes":
            only_initialization = False 
        else:
            only_initialization = True
        self.append_to_report("Only initialization is %s"%str(only_initialization))
        calc = create_pw_calculation(self, 
                                     parallelization_dict,
                                     only_initialization)
        calc.store_all()
        self.attach_calculation(calc)
        self.next(self.launch_calculation)
        #self.next(self.exit)

    @Workflow.step
    def launch_calculation(self):
        wf_params = self.get_parameters()
        hpc_params = wf_params['hpc_params'].get_dict()
        #extras = wf_params['extras']
        is_automatic = wf_params['hpc_params'].get_dict()['automatic']
        with_sirius = wf_params['hpc_params'].get_dict()['with_sirius']
        dry_run = self.get_step_calculations(self.dry_run)[0]
        num_kpoints = dry_run.res.number_of_k_points
        nzsmooth = dry_run.res.smooth_fft_grid[2]
        input_dict = dry_run.get_inputs_dict()['parameters']
        sys_dict = input_dict.get_dict()['SYSTEM']   
        for k, v in sys_dict.iteritems():
          if k is 'nspin' and v is 2:
           num_kpoints = num_kpoints*2 
        pw_codename = wf_params['pw_codename']
        code = Code.get_from_string(pw_codename)
        computer = code.get_remote_computer()
        parallelization_dicts = []

        configuration_threads = []
        configuration_nd = []
        for num_nodes in hpc_params['nodes']:
          iteration_thread = 0
          for num_threads in hpc_params['num_threads']:
            iteration_nd = 0 
            if is_automatic == 'yes':
               nprocs = math.floor(computer.get_default_mpiprocs_per_machine()/num_threads)
               nk_list = list(self.divisorGenerator(num_kpoints))
               for i in nk_list:
                 if float(nprocs%i) == 0.0:
                    nk = int(nprocs) if with_sirius is True  else i #math.floor(np.max(1,nprocs/num_kpoints))
		    ntg = int(math.floor(nk/nzsmooth))
		    if ntg == 0 or with_sirius is True:
		      ntg = 1
		    elif ntg>1:
		      ntg = int(math.floor(self.power_log(x=nk/nzsmooth)))
			
		    nd=int(math.floor(math.sqrt(num_nodes*nk/2))**2)
		    self.append_to_report(str(nk))
		    parallelization_dicts.append(self.set_hpc_parameters(num_nodes,nk,nd,ntg,num_threads))
		    configuration_threads.append(iteration_thread)
		    configuration_nd.append(iteration_nd)
		    iteration_thread+=1
		    iteration_nd+=1
            else: 
               nd=1
               nprocs = math.floor(computer.get_default_mpiprocs_per_machine()/num_threads)
               ntg=1
               nk=1
               parallelization_dicts.append(self.set_hpc_parameters(num_nodes,nk,nd,ntg,num_threads))
	       configuration_threads.append(iteration_thread)
	       iteration_thread+=1
	       iteration_nd+=1
              
              
        for parallelization_dict in parallelization_dicts:
            calc = create_pw_calculation(self, 
                                         parallelization_dict)
            calc.store_all()
            calc.set_extra('parallelization_dict',parallelization_dict)
            calc.set_extra('configuration_nd',configuration_nd)
            calc.set_extra('configuration_threads',configuration_threads)
            #calc.set_extra('system type',extras)
            self.attach_calculation(calc)

        self.next(self.exit)
	

 
    def power_log(self,x):
        import math
        return 2**(math.floor(math.log(x, 2)))


    def set_hpc_parameters(self, number_nodes, nk, nd, ntg, number_threads ):
 	parallelization_dict = {}
	wf_params = self.get_parameters()
        hpc_params = wf_params['hpc_params'].get_dict()
        parallelization_dict['num_machines'] = number_nodes
        parallelization_dict['max_wallclock_seconds'] = hpc_params['max_wallclock_seconds']
        parallelization_dict['nd'] = nd
        parallelization_dict['ntg'] = ntg
        parallelization_dict['num_threads'] = number_threads
        parallelization_dict['nk'] = nk
        return parallelization_dict

    def divisorGenerator(self,n):
       large_divisors = []
       for i in xrange(1, int(math.sqrt(n) + 1)):
           if n % i == 0:
              yield i
           if i*i != n:
              large_divisors.append(n / i)
       for divisor in reversed(large_divisors):
           yield divisor


    @Workflow.step
    def get_results_for_mpi_and_omp(self):
        "collect the timing in a xydata"
        all_calcs = list(self.get_step_calculations(self.launch_calculation))
        configuration_nd = []
        configuration_threads = []
        for c in all_calcs:
           if 'wall_time' in c.out.output_parameters.get_dict():
              index = all_calcs.index(c)
	      configuration_nd.append(c.get_extra('configuration_nd')[index])
              configuration_threads.append(c.get_extra('configuration_threads')[index])

        time = [c.res.wall_time_seconds for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        h_psi_time = [c.res.h_psi_time_seconds for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        s_psi_time = [c.res.s_psi_time_seconds for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        fft_time = [c.res.fft_time_seconds for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        fft_scatter_time = [c.res.fft_scatter_time_seconds for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        cdiaghg_time = [c.res.cdiaghg_time_seconds for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        init_run_time = [c.res.init_run_time_seconds for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        wfcinit_time = [c.res.wfcinit_time_seconds for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        c_bands_time = [c.res.c_bands_time_seconds for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        nodes = [c.get_extra('parallelization_dict')['num_machines'] for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        threads = [c.get_extra('parallelization_dict')['num_threads'] for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        nd = [c.get_extra('parallelization_dict')['nd'] for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        ntg = [c.get_extra('parallelization_dict')['ntg'] for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
	nk = [c.get_extra('parallelization_dict')['nk'] for c in all_calcs if 'wall_time' in c.out.output_parameters.get_dict()]
        


        timesdata = XyData()
	timesdata.set_x(x_array=numpy.array(time), x_name='Wall time', x_units='seconds' )
        
        timesdata.set_y(y_arrays=[numpy.array(nodes), numpy.array(threads), numpy.array(nd), numpy.array(ntg), numpy.array(nk), numpy.array(configuration_threads), numpy.array(configuration_nd), numpy.array(h_psi_time), numpy.array(fft_time), numpy.array(fft_scatter_time), numpy.array(s_psi_time), numpy.array(wfcinit_time), numpy.array(cdiaghg_time), numpy.array(init_run_time) ] ,
                         y_names = ['Nodes','Threads','Ndiag', 'Task Groups', 'NPools','configuration_threads','configuration_nd','h_psi_time','fft_time','fft_scatter_time','s_psi_time','wfcinit_time','cdiaghg_time','init_run_time'],
                         y_units = ['','','','','','','','','','','','','',''])
        
        timesdata.store()

        self.add_result('TimesData',timesdata)
        
        self.add_result('h_psi_time',h_psi_time)
        self.add_result('s_psi_time',s_psi_time)
        self.add_result('fft_time',fft_time)
        self.add_result('fft_scatter_time',fft_scatter_time)
        self.add_result('cdiaghg_time',cdiaghg_time)
        self.add_result('init_run_time',init_run_time)
        self.add_result('wfcinit_time',wfcinit_time)
        self.add_result('c_bands_time',c_bands_time)



	self.next(self.exit)  



