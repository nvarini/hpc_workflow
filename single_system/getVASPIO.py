# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from aiida import load_dbenv
load_dbenv()



import numpy as np
import pymatgen
import aiida.orm.querybuilder as qbe

from aiida.orm import Calculation, Code, Computer, Data, Node, Group
from aiida.orm import CalculationFactory, DataFactory
from aiida.backends.djsite.db import models
import pymatgen.transformations.standard_transformations as trafo
import pymatgen.io.vasp as vio
import os

StructureData = DataFactory('structure')
UpfData = DataFactory('upf')

scales = [[1, [1,1,1]], [2,[2,1,1]], [4, [2,2,1]], [6,[3,2,1]], [8,[2,2,2]], [12,[3,2,2]], [18,[3,3,2]], [27,[3,3,3]], [36,[4,3,3]], [48,[4,4,3]], [64,[4,4,4]], [100,[5,4,4]] ]


target_atoms = [40, 100]

import json

headfolder = os.getcwd()



def get_UPF_valenceElectrons(upfname = 'SSSP_v0.7_eff_PBE'):


    qb = qbe.QueryBuilder()
    
    
    #aidaparameters = []
    #aiida test pw

    
    def getUPFelectrons(a):
        #a = load_node(upfdatapk)
        opc = open(str(str(a.get_abs_path()) + '/path/' + a.get_attrs()['filename']), 'r')
        print str(str(a.get_abs_path()) + '/path/' + a.get_attrs()['filename'])
        psdict = a.get_attrs()
        psdict['abs_path'] = str(str(a.get_abs_path()) + '/path/' + a.get_attrs()['filename'])
        for line in opc.readlines():
            
            
            zval = None
            pseudotype = None
            cutoff = None
            if 'Z valence' in line:
                str_list = line.split(' ')
                
                str_list = [s for s in str_list if s]
                psdict['z_valence'] = float(str_list[0])
                
            elif 'z_valence=' in line:
                str_list = line.replace(' ', '')
                #str_list = [s for s in str_list if s]
                str_list = str_list.split('\n')[0]
                print str_list
                str_list = str_list.split('"')[-2]
                psdict['z_valence'] = float(str_list)
                
            elif 'pseudo_type=' in line:
                str_list = line.replace(' ', '')
                print str_list
                #str_list = [s for s in str_list if s]
                str_list = str_list.split('\n')[0]
                print str_list.split('"')
                str_list = str_list.split('"')[-2]
                psdict['pseudo_type'] = str_list
        opc.close()
        return {psdict['element'] : psdict}
                
                
    qb.append(Group, filters = {'name' :{'==': upfname}}, tag='groupid')
    qb.append(UpfData, member_of='groupid', tag = 'upf')
    allpseudos =  {}
    for i in qb.all():
        allpseudos.update(getUPFelectrons(i[0]))
    os.chdir(headfolder)
    fi = open(upfname + '.json', 'w')    
    json.dump(allpseudos, fi)
    fi.close()
    
    
    
    

def get_VASP_valenceElectrons(vaspfolder = '/scratch/hormann/formationenergies/scale_HPC/vasp_potcars/potpaw_PBE'):

    def getVASPelectrons(filename, element):
    
        opc = open(filename, 'r')
        
        psdict = {}
        psdict['element'] = element
        psdict['pseudo_name'] = filename.split('/')[-2]
        psdict['abs_path'] = filename
        psdict['pseudo_type'] = 'PAW'
        cutoff = None
        for i, line in enumerate(opc):
            if i == 0:
                psdict['pseudo_header'] = line.split('\n')[0].strip(' ')
            elif i==1:
                psdict['z_valence'] = float(line.split('\n')[0])
            
            elif 'ENMAX' in line:
                str_list = line.split(';')[0]
                str_list = float(str_list.split('=')[1])
                psdict['cutoff_eV'] = float(str_list)
                break
                
        opc.close()
        return {element : psdict}
                
    allelements = []

    allpseudos =  {}
    for folder in [x[0] for x in os.walk(vaspfolder)]:
        element = folder.split('/')[-1].split("_")[0]
        allelements.append(element)
    allelements = set(allelements)

    for en in allelements:
        allpseudos[en] = []

    for folder in [x[0] for x in os.walk(vaspfolder)]:
        if folder.split('/')[-1] != 'potpaw_PBE':
            element = folder.split('/')[-1].split("_")[0]
            filename = folder + '/POTCAR'
            
            allpseudos[element].append(getVASPelectrons(filename, element))


        #aedict[element].append()
    #aidaparameters = [a]aedict[en]
    #aiida test pw
    fi = open('VASP_potpaw_PBE.json', 'w')    
    json.dump(allpseudos, fi)
    fi.close() 
    
    

#####################################################    
#get pseudopotential information
#do this such that the absolute paths are correctly stored 
#
get_UPF_valenceElectrons()
#
#
get_VASP_valenceElectrons()
#
#####################################################





 

def make_VASP_POTCAR(vaspPOSCAR):
    """
    load first the analysed pseudopotentials: how many electrons and pseuodpotential type etc
    use the functions before to analyse pseudopotentials
    #get_UPF_valenceElectrons()
    #
    #
    #get_VASP_valenceElectrons()
    """
    import os.path
    vp = open('SSSP_v0.7_eff_PBE.json', 'r')
    UPF_electrons_dict = json.load(vp)
    vp.close()
    
    vp = open('VASP_potpaw_PBE.json', 'r')
    VASP_PO = json.load(vp)
    vp.close()
    
    headdir = os.path.dirname(vaspPOSCAR)
    print headdir
    
    def get_appropriateVASP(vaspdict, element, nr_electrons):
        """
        This will go through the vasp potcars and select the one with appropriate valence
        electron number
        """
        potlist = []
        for i in vaspdict[element]:
            if i[element]['z_valence'] == nr_electrons:
                potlist.append([i[element]["pseudo_name"], i[element]["abs_path"]])
        if len(potlist) == 0:
            print 'NO suitable POTCAR'
            return 0
        elif len(potlist) == 1:
            return potlist[0][1]
        else:
            
            nl = [i for i in potlist if 'GW' not in i[0]]
            if len(nl) == 1:
                return nl[0][1]
            else:
                nl = [i for i in nl if '_h' not in i[0]]
                if len(nl) == 1:
                    return nl[0][1]
                else:
                    nl = [i for i in nl if '_s' not in i[0]]
                    if len(nl) == 1:
                        return nl[0][1]
                    else:
                        print nl
                        print 'too many possible POTCARS'
                        return 0
    
    
    
    opc = open(vaspPOSCAR, 'r')
    
    for i, line in enumerate(opc):
        if i == 5:
            elementlist = line.split('\n')[0].split(' ')
            PC_list = []
            for e in elementlist:
                res = get_appropriateVASP(VASP_PO, e, UPF_electrons_dict[e]['z_valence'])
                if res == 0:
                    print "Problem of PSEUDOPOTENTIALS conversion"
                else:
                    PC_list.append(res)
            if len(PC_list) == len(elementlist):
                print headdir
                with open(headdir +'/POTCAR', 'w') as outfile:
                    for fname in PC_list:
                        with open(fname, 'r') as infile:
                            for line in infile:
                                outfile.write(line)


                                
                                
                                
                                
                                

def transform_inputs(pw):
    
    def get_eVfromRy(Ry):
        return np.round(Ry*13.605693, 8)
        
    def get_VASPlines(dictin):
        trafodict = {'scf': 'IBRION = -1', 'ecutwfc' : 'ENCUT', 'ecutrho' : 'ENAUG', 'conv_thr' : 'EDIFF', 'degauss' : 'SIGMA', 'gaussian' : 'ISMEAR = 0'}
    
        vasplines = []
        for i, j in dictin.items():
            if i == 'smearing':
                vasplines.append(trafodict[j])
            elif i == 'calculation':
                vasplines.append(trafodict[j])
            else:
                if i in trafodict.keys():
                    vasplines.append(trafodict[i] + ' = ' + str(get_eVfromRy(j)))
                
        return vasplines
    
    vasplines = ['system = test']
    for key, val in pw.items():
        vasplines.extend(get_VASPlines(val))
        
    return vasplines
                                    
                                
                                
                                
                                
                                
def make_VASP_INCAR(pwparameters, outfolder):
    """
    take QE as parameterdict as in AIIDA create appropriate INCAR
    modify transform_inputs function to get more supported transfer
    """
    
    
    inc = open(outfolder + 'INCAR', 'w')
        
    #aiidacalc.inp.kpoints.get_kpoints_mesh()[0]
    
    wf = transform_inputs(pwparameters)
    for line in wf:
        inc.write(line + '\n')
    inc.close()
                                


def make_VASP_KPOINTS(kpm, outfolder):
    """
        from kpoint mesh kpm = kpoints mesh as list
        makes Monkhorst pack grid. Should one use GAMMA in VASP
    """
    print kpm
    print outfolder
    kpw = open(outfolder + 'KPOINTS', 'w')
    
    wf = ['Automatic mesh', '0', 'Monkhorst-Pack', '{} {} {}'.format(kpm[0], kpm[1], kpm[2])]
    for line in wf:
        kpw.write(line + '\n')
    kpw.close()

                               

                                
def make_PW_input(parametersdata, kpointsmesh, structure, folder):
    from export_pw_calc import export_data
    export_data( structure, kpointsmesh, parametersdata, folder)




head = os.getcwd()


qb = qbe.QueryBuilder()


qb.append(Group, filters = {'name' :{'==': 'pw_calculations_for_HPCtesting'}}, tag='groupid')
qb.append(Calculation, member_of='groupid')

count = 0
print qb.all()


testparams = {
        'CONTROL': {
            'calculation': 'scf',
            'restart_mode': 'from_scratch',
            'wf_collect': False,
            'tstress': False,
            'disk_io': 'none',
        },
        'SYSTEM': {
            'ecutwfc': 40.,
            'ecutrho': 320.,
            'smearing': 'gaussian',
            'degauss': 0.02
            
        },
        'ELECTRONS': {
            'conv_thr': 1.e-10,
        }}



        
for i in qb.all():
    od =  i[0].get_outputs_dict()
    kpmesh = i[0].inp.kpoints.get_kpoints_mesh()[0]
    print kpmesh
    count += 1
    if count < 20:
        if 'output_structure' in od:
            struct = od['output_structure']
            #print len(struct.sites)
            
            
            os.mkdir(head + '/' + str(i[0].pk))
            os.mkdir(head + '/' + str(i[0].pk) + '/Normal_size')
            os.mkdir(head + '/' + str(i[0].pk) + '/Normal_size/VASP_run')
            folder_nameVASP = head + '/' + str(i[0].pk) + '/Normal_size/VASP_run/'
            structc = struct.copy()
            structc.set_pbc([True, True, True])
            pmgstruct = structc.get_pymatgen()     
            print type(pmgstruct) 
            PC = vio.Poscar(pmgstruct)
            PC.write_file(head + '/' + str(i[0].pk) + '/Normal_size/VASP_run/POSCAR')
            make_VASP_POTCAR(folder_nameVASP + 'POSCAR')
            make_VASP_KPOINTS(kpmesh, folder_nameVASP)
            make_VASP_INCAR(testparams, folder_nameVASP)
            
            """
            instead of testparams we should create a function that makes the appropriate input from 
            nicola mounets original inputs
            
            """
            make_PW_input(testparams, kpmesh, structc, head + '/' + str(i[0].pk) + '/Normal_size')
            
            
            """
            This is for rescaling cell
            trivial to extend to rescale kpoints. possibly rescale convthr
            """
#            
#            
#            
#            
#            
#            
#            
#            for ta in target_atoms:
#                scale = (ta/len(struct.sites))
#                minscale = np.argmin([abs(k[0]-scale) for k in scales])
#                optscale = scales[minscale]
#                print optscale[0]*len(struct.sites)
#                structc = struct.copy()
#                structc.set_pbc([True, True, True])
#                pmgstruct = structc.get_pymatgen()     
#                print type(pmgstruct) 
#                PC = vio.Poscar(pmgstruct)
#                PC.write_file(str(count)+'filename.vasp')
#                
#                tr = trafo.SupercellTransformation(scaling_matrix = np.diag(scales[minscale][1]))
#                scaledpmg = tr.apply_transformation(pmgstruct)
#                PC = vio.Poscar(scaledpmg)
#                PC.write_file(str(count)+'filename.vasp')
#                make_VASP_POTCAR(os.getcwd() + '/' + str(count)+'filename.vasp')
#                #aiidas = StructureData(pymatgen = scaledpmg)
#            
        else:
            struct = i[0].inp.structure
            print len(struct.sites)
            
            os.mkdir(head + '/' + str(i[0].pk))
            os.mkdir(head + '/' + str(i[0].pk) + '/Normal_size')
            os.mkdir(head + '/' + str(i[0].pk) + '/Normal_size/VASP_run')
            folder_nameVASP = head + '/' + str(i[0].pk) + '/Normal_size/VASP_run/'
            structc = struct.copy()
            structc.set_pbc([True, True, True])
            pmgstruct = structc.get_pymatgen()     
            print type(pmgstruct) 
            PC = vio.Poscar(pmgstruct)
            PC.write_file(head + '/' + str(i[0].pk) + '/Normal_size/VASP_run/POSCAR')
            make_VASP_POTCAR(folder_nameVASP + 'POSCAR')
            make_VASP_KPOINTS(kpmesh, folder_nameVASP)
            make_VASP_INCAR(testparams, folder_nameVASP)
            
            """
            instead of testparams we should create a function that makes the appropriate input from 
            nicola mounets original inputs
            
            """
            make_PW_input(testparams, kpmesh, structc, head + '/' + str(i[0].pk) + '/Normal_size')
            
            
            

            
            
#            for ta in target_atoms:
#                scale = (ta/len(struct.sites))
#                minscale = np.argmin([abs(k[0]-scale) for k in scales])
#                optscale = scales[minscale]
#                print optscale[0]*len(struct.sites)
#                
#                pmgstruct = struct.get_pymatgen()     
#                
#                PC = vio.Poscar(pmgstruct)
#                PC.write_file(str(count)+'filename.vasp')
#                
#                tr = trafo.SupercellTransformation(scaling_matrix = np.diag(scales[minscale][1]))
#                scaledpmg = tr.apply_transformation(pmgstruct)
#                PC = vio.Poscar(scaledpmg)
#                PC.write_file(str(count)+'filename.vasp')
#                #aiidas = StructureData(pymatgen = scaledpmg)
                
        print '---------------' 

        
       
