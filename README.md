## Setting up The FTIR Scan

In this .README I will walk you through how to setup your computer to run the FTIR scan code and show you what results should be produced. As of right now there is no explanation of FTIR in the document (there will be eventually) so hopefully you know what it is. If not you should still be able to take this measurement with these instructions. 

### (1) Setting up Your Python Environment

Here I will show you how to setup your python environment in the context of Anaconda/VS Code. If you use something else its probably similar just adapt it to your needs.

(1) Clone the repository

(2) Activate the anaconda terminal and navigate the the root directory of the repository

(3) run the command "conda env create -f environment.yaml" this will create the conda environment using the provided .yaml file

(4) activate the environment using "conda activate YAG_exp"




might need pyftdi installed, pylablib could be missing it.