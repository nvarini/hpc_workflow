#!/bin/bash
hpcfile=hpc.json
hpcfile_sirius=hpc-sirius.json
pwfile=pw.json
dirname=$(awk 'NR==2 {print $3}' ${hpcfile}| grep -o '".*"'| sed 's/"//g')
scale=$(grep scale ${hpcfile} |awk '{print $3}')
a=$(verdi run submit_benchmarks.py  pw-6.1-sirius@PizDaintGPU  ${hpcfile_sirius} ${pwfile} )
b=$(verdi run submit_benchmarks.py  pw-6.1@fidis ${hpcfile} ${pwfile})
c=$(date +%F-%k-%m-%S)
echo $a $b  > workflow_list
mkdir -p ${dirname}${scale}
mv workflow_list ${dirname}${scale}

