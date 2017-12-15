 #!/usr/bin/env runaiida

from aiida.workflows.user.hpc_workflow.workflow_bench import BenchWorkflow
from aiida.workflows.user.hpc_workflow.hpc import HpcWorkflow
from rescale_structures import *
import json, argparse
from aiida.common.example_helpers import test_and_get_code
from aiida.orm.querybuilder import QueryBuilder
from aiida.orm import Group, JobCalculation

parser = argparse.ArgumentParser()
parser.add_argument("code", help="code and machine where you would like to run")
parser.add_argument("json_hpc", help="json file with HPC parameters")
parser.add_argument("json_pw", help="json file with PW parameters")
args = parser.parse_args()
   

StructureData = DataFactory('structure')
UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')

with open(args.json_hpc) as data_file:    
   json_hpc = json.load(data_file)
 
qb = QueryBuilder()
qb.append(JobCalculation,tag="mycalculation",project=["*"])
qb.append(Group,filters={"name":json_hpc["query_group"]},group_of="mycalculation")
calcs_list=qb.all()

pseudo_family = json_hpc['pseudo']
structures_wf = []
kpoints_wf = []
pw_parameters_wf = []
hpc_workflow_params = {}
keys = []
count=0


#for i in calcs_list[0:1]:
for i in calcs_list:
     calc = i[0]
     struct = calc.get_inputs_dict()['structure']
     kpoints = KpointsData()
     kmesh =  calc.get_inputs_dict()['kpoints'].get_kpoints_mesh()
     kpoints_wf.append(kmesh)
     kpoints.store()
     structures_wf.append(struct)
     scaled_struct, new_k = scale_structure(kmesh,struct,json_hpc['scale'])
     scaled_struct.store()
     param =  calc.get_inputs_dict()['parameters'].get_attrs()
     
     parameters = set_dict(param,args.json_pw,1,1)
     pw_parameters = ParameterData(dict=parameters)
     pw_parameters.store()
     pw_parameters_wf.append(pw_parameters)
     hpc_parameters =  ParameterData(dict=json_hpc)
     hpc_parameters.store()

     code = test_and_get_code(args.code, expected_code_type='quantumespresso.pw')
     UpfData.get_upf_group(pseudo_family)
     hpc_workflow_params.update({'pw_codename_'+str(count): args.code,
                'structure_'+str(count): struct,
                'hpc_params_'+str(count): hpc_parameters,
                'pseudo_family_'+str(count): pseudo_family,
                'kpoints_'+str(count):kmesh,
                'pw_parameters_'+str(count): pw_parameters,
                })
     keys.append(count)
     count+=1

wf_params = {}
bench = BenchWorkflow()
bench.set_params(hpc_workflow_params)
bench.store()
bench.start()
print 'Workflow PK: {}'.format(bench.pk)

