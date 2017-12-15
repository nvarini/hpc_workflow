#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

import numpy as np
import pymatgen
import collections
import json
import pymatgen.transformations.standard_transformations as trafo
from aiida.orm import DataFactory

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')

def scale_structure(kpmesh,struct,scales):
  """Rescale a structure and kmesh given the scales
  """
  new_k = [np.int(kpmesh[0][i]/scales[i]) for i in range(len(kpmesh[0]))]
  new_k = [new_k,kpmesh[1]]
  for i in range(len(new_k)):
    if new_k[i] is 0:
      new_k[i] = 1
  structc = struct.copy()
  structc.set_pbc([True, True, True])
  pmgstruct = structc.get_pymatgen()     
  tr = trafo.SupercellTransformation(scaling_matrix = np.diag(scales))
  scaledpmg = tr.apply_transformation(pmgstruct)
  structure = StructureData()
  structure.set_pymatgen(scaledpmg)
  return structure, new_k


def set_dict(parameters, parameters_json, nat_scaled=1, nat_original=1):
  """Set the parameter dictionary used for the calculation 
  """
  try:
    with open(parameters_json) as data_file:    
       parameters_file = json.load(data_file)
  except IOError as e:
    print "Cannot open parameters.json"

  parameters.pop('CELL',None)
  parameters.pop('IONS',None)
  parameters.pop('IONS',None)
  parameters['SYSTEM'].pop('input_dft',None)
  parameters['SYSTEM'].pop('nbnd',None)
  list_keys = ['CONTROL','ELECTRONS','SYSTEM']
  
  dict1={}
  update(parameters,parameters_file)
  return parameters


def update(d, u):
    """Update the d dictionary with the u
    """
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d
