#!/bin/bash
hpcfile=hpc.json
hpcfile_sirius=hpc-sirius.json
pwfile=pw.json
dirname=$(awk 'NR==2 {print $3}' ${hpcfile}| grep -o '".*"'| sed 's/"//g')
scale=$(grep scale ${hpcfile} |awk '{print $3}')
b=$(verdi run submit_benchmarks.py  qe-6.2@fidis ${hpcfile} ${pwfile})
c=$(date +%F-%k-%m-%S)
echo $a $b  > workflow_list
mkdir -p ${dirname}${scale}
mv workflow_list ${dirname}${scale}

