Setting up the environment

in ppxlint: just set up a venv using the setup/setup_venv.sh script. 
elsewhere, assuming you don't have a local ROOT installation, use conda.
- Download and Install miniconda: https://docs.anaconda.com/miniconda/ (this is a lighter-weight version of full conda to download, but should be fine for anything you need)
- switch it on.
- create and set up the environment via setup/setup_conda.sh script.

Getting the data:

if you are working on ppxlint, just softlink it: ln -s /data/atlas/users/pacey/GamGam/GamGam /your/desired/folder/OxfordCMPP/data/ 
otherwise you can copy it over ssh to your machine:
scp -r -o 'ProxyJump username@bastion.physics.ox.ac.uk' username@pplxint12.physics.ox.ac.uk:/data/atlas/users/pacey/GamGam/GamGam /your/desired/folder/OxfordCMPP/data/

OR you can download it directly from here: https://atlas-opendata.web.cern.ch/Legacy13TeV/   GamGam.zip has everything.

