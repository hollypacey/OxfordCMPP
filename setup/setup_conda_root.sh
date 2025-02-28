# set up your conda installation
# eval "$(/your/path/toe/miniconda/bin/conda shell.bash hook)"

conda create -c conda-forge --name cmpp_root_env root python=3.8
conda activate cmpp_root_env 

conda install anaconda::jupyter
conda install anaconda::ipykernel
conda install anaconda::ipython

