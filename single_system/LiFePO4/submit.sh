#!/bin/bash
a=$(verdi run LiFePO4.py  pw-6.1@fidis hpc.json)
#b=$(verdi run Matteo.py  pw-6.1-sirius@PizDaintGPU hpc-sirius.json)
f=$(date +%F-%k-%m-%S)
echo $a $b $c $d $e  > workflow_list_"${f}"
#echo $a  $c   > workflow_list_"${f}"
#echo  $b > workflow_list_"${c}"
