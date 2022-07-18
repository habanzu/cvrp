# cvrp

A repository for the bachelor's thesis of Georg Meinhardt in the summer term of 2022.
It provides an implementation of a Branch-and-Price algorithm for the Capacitated Vehicle Routing Problem.
Goal of the thesis is to analyse preliminary lower bounds.
The supervisor was Lukas Schuermann and the reviewers Prof. Dr. Petra Mutzel and Prof. Dr. Stephan Held.

## Installation
A working version of SCIP is required.
The easiest way is to install conda and then install pysciptopt via conda.
This will install SCIP as well.
Currently the command `conda install --channel conda-forge pyscipopt` is everything required.
Details can be found at the [pyscipopt repository]{https://github.com/scipopt/PySCIPOpt}.

Further Python libraries are required, all available via `pip` or `conda`.

To run the labelling algorithms, it is required to compile the C++ code.
In order to do so, open a terminal and switch to the directory `Labelling` (e.g. `cd cvrp/Labelling`).
Then execute `make` if you are running Mac OS or `make linux` if you are running Linux.
For linux, g++ needs to be installed.
For MacOS, clang needs to be installed, which should be shipped with the Xcode command line tools.

## Usage
To gain an idea how to use this code, take a look at the notebook `CVRP.ipynb` and run the cells from top to bottom.
Install all python modules as required and do not forget to compile the C++ code beforehand.
Further notebooks are described below.
The python files `test.py` and `run.py` have been used for the systematic test runs.
`test.py` will perform a test on a single instance, `run.py` will perform the test of a large class in parallel.

## Further Notebooks

## Data
The data of the test runs, on which the thesis is based, can be found in in the directory `output_data`.
`output_uchoa` and `output_E` contain the logs of the respective data set.
`output_farley` contains the evaluation results of the Farley Labelling run on the E dataset.
`output_iterations` contains the data, which as used in section 4.2.7 of the thesis (title: Avoiding Hard ESPPRC Relaxations).
The archive contains additional unstructured logs, which were produced during the test runs.
Notable to mention is `test_added_vars`, as it contains test runs on the E dataset on how many variables should be added after each pricing round.
This data was the baseline for deciding how many variables would be added in the test runs of the thesis.
It was not analysed further.

## Project status
The thesis has been submitted at the 19th July of 2022.
No further work has been done.
