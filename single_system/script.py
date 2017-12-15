from aiida.orm.querybuilder import QueryBuilder
from aiida.orm.group import Group
from aiida.orm.calculation import Calculation
import aiida.cmdline.commands.calculation as calc

qb = QueryBuilder()
qb.append(Group, tag='groups', project=['*'], filters={'id': {'==': 1807}})
qb.append(Calculation, tag='calculations', project=['id'], member_of='groups')
query = qb.all()
for i in query:
  print i 
