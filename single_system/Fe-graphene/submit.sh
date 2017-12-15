#!/bin/bash
a=$(verdi run Fe-graphene.py  qe-6.2@fidis hpc.json)
f=$(date +%F-%k-%m-%S)
echo $a $b $c $d $e  > workflow_list_"${f}"
#echo $a  $c   > workflow_list_"${f}"
#echo  $b > workflow_list_"${c}"
