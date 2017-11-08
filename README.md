# HPC benchmarks workflow

This repository contain the HPC workflow to generate benchmarks for Quantum-ESPRESSO
with AiiDA. 

# Installation

Under aiida/workflows/user

$git clone https://github.com/nvarini/hpc_workflow.git

# How to submit a benchmark(s)

In the directory submit there are few files that show how benchmarks can be submitted
-hpc.json contain the parameter needed to generate the benchmarks
-pw.json allows to define qe namelists parameters
-rescale_structures.py allows to rescale the structure 
-script.sh shows how to submit on a given machine(s)
-submit_benchmarks.py contain the logic that read the desider AiiDA group and generate the benchmarks

# How to postprocess and generate the performance graph



