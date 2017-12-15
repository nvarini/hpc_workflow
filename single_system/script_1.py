#!/usr/bin/env runaiida

import subprocess
from aiida.orm.querybuilder import QueryBuilder
from aiida.orm.group import Group
from aiida.orm.calculation import Calculation
import aiida.cmdline.commands.calculation as calc

qb = QueryBuilder()
qb.append(Group, tag='groups', project=['*'], filters={'id': {'==': 1807}})
qb.append(Calculation, tag='calculations', project=['id'], member_of='groups')
query = qb.all()
pks = [] 
for i in query:
  pks.append(i[1])

pws = [load_node(pk) for pk in pks]
for pw in pws:
	subprocess.check_output(["mkdir","-p","QE/{}".format(pw.pk)])
	subprocess.check_output(["cp","{}".format(pw.get_abs_path('../raw_input/aiida.in')),
					"QE/{}/".format(pw.pk)])
	subprocess.check_output(["cp","{}".format(pw.get_abs_path('../raw_input/_aiidasubmit.sh')),
				"QE/{}/".format(pw.pk)])
	
	subprocess.check_output(["mkdir","-p","QE/{}/pseudo/".format(pw.pk)])
	for u in pw.get_inputs(DataFactory('upf')):
		subprocess.check_output(["cp","{}".format(u.get_abs_path(u.filename)),
				"QE/{}/pseudo/".format(pw.pk)])
