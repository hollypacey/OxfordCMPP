# Downloading the Git code

Can use either the github or gitlab.cern repos.
Recommend to set up SSH keys on your machine for authentication. Instructions here to generate a new key and upload it: [github](https://docs.github.com/en/authentication/connecting-to-github-with-ssh) [gitlab](https://docs.gitlab.com/user/ssh/)

go to the repo url and in the drop down menu for 'code' copy the ssh path.
in the directory you want to work in:

```
git clone <ssh path>
```


# Setting up the environment

## The tutorials that use ROOT: 

Ideally use ppxlint: just set up a venv using the ```setup/setup_root_venv.sh``` scripts. 

Elsewhere, assuming you don't have a local ROOT installation, use conda. Although ROOT-via_Conda doesn't work on Windows, so for the root tutorial please try to ssh instead.
- Download and Install miniconda: https://docs.anaconda.com/miniconda/ (this is a lighter-weight version of full conda to download, but should be fine for anything you need)
- switch it on. via ```eval "$(/your/path/to/miniconda/bin/conda shell.bash hook)"```
- create and set up the environment via setup/setup_conda_root.sh script.

## The pythonic tutorials:

Either set up a venv using the ```setup/setup_venv.sh``` scripts. 

Or use conda to set up the virtual environment:
- Download and Install miniconda: https://docs.anaconda.com/miniconda/ (this is a lighter-weight version of full conda to download, but should be fine for anything you need)
- switch it on, via ```eval "$(/your/path/to/miniconda/bin/conda shell.bash hook)"```
- create and set up the environment via ```setup/setup_conda.sh``` script.

# Getting the part1 data:

if you are working on ppxlint, just softlink it:
```
ln -s /data/atlas/users/pacey/GamGam/GamGam /your/desired/folder/oxfordcmpp/data/ 
```
otherwise you can copy it over ssh to your machine:
```
scp -r -o 'ProxyJump username@bastion.physics.ox.ac.uk' username@pplxint12.physics.ox.ac.uk:/data/atlas/users/pacey/GamGam/GamGam /your/desired/folder/oxfordcmpp/data/
```

OR you can download it directly from here: [here](https://atlas-opendata.web.cern.ch/Legacy13TeV/) GamGam.zip has everything.

# Launching a Jupyter notebook remotely 
We want to run Jupyter remotely on pplxint but open the notebook in a browser on our laptop.

### From a linux machine:
Ensure you are X11 forwarding either by including including the `-X` flag when running `ssh` (`ssh -X {username}@pplxint12.physics.ox.ac.uk`) or by adding the following to your `~/.ssh/config`:
```
Host *.physics.ox.ac.uk
    # This sets the username ssh will try to use by default for anything under the physics domain
    User <my_physics_username>
    ForwardX11Trusted yes
    ForwardX11 yes
Host *.physics.ox.ac.uk !bastion.physics.ox.ac.uk
    # This tells ssh to "jump" via another system, this is needed to get in from outside the network.
    ProxyJump bastion.physics.ox.ac.uk
```
See IT support pages [here](https://itsupport.physics.ox.ac.uk/front/helpdesk.faq.php?id=1015) and [here](https://itsupport.physics.ox.ac.uk/front/helpdesk.faq.php?id=1097) for more info.

It *should* be sufficient to now just launch the notebook on pplxint in your terminal session via `jupyter notebook {notebook}.ipynb`, and a new browser window will open.

### From a macbook:

1) Install XQuartz. If you have a department macbook you can do this via the Self Service application.
2) Restart.
3) Connect to pplxint (`ssh {username}@pplxint12.physics.ox.ac.uk`)
4) Activate your conda/virtual environment.
5) `jupyter notebook password` --> enter a password (will be used to access a Jupyter session).
6) Launch a Jupyter session on the remote server: `jupyter notebook --no-browser &`
Make a note of the port used (You should see some printout like `Jupyter Server is running at: http://localhost:{port}/)`
7) On a local terminal window, run `ssh -N -f -L 8888:localhost:{port} {username}@pplxint12.physics.ox.ac.uk`
8) Fire up your browser and type `localhost:8888`. Enter the password you set in step (5). You should now have the remote Jupyter session running in your browser.

(See https://www.blopig.com/blog/2018/03/running-jupyter-notebook-on-a-remote-server-via-ssh/ for explanation on these steps)

# Set up via VSCode

## ssh into pplxint via VSCode:
- For windows: Install and setup windows openssh first [info](https://code.visualstudio.com/docs/remote/troubleshooting#_installing-a-supported-ssh-client)
- Then setup ssh in vscode [info](https://code.visualstudio.com/docs/remote/ssh). Follow instructions to make ssh keys for bastion and pplxint12/13.
  Involves making a ~/.ssh/config that will look roughly like this:
```
Host bastion
HostName bastion.physics.ox.ac.uk
IdentityFile ~/.ssh/bastion_key
MACs = <your mac address>
User <your username>

Host pplxint12
Hostname pplxint12.physics.ox.ac.uk
IdentityFile ~/.ssh/pplxint12_key
ProxyJump bastion
User <your username>
```

## Use jupyter via VScode:

some info [here](https://code.visualstudio.com/docs/datascience/jupyter-notebooks)
- Setup an environment that has jupyter, ipython, ipykernel installed.
- open notebook via ```jupyter-notebook file.ipynb``` or via the explorer.
- on the top right click 'select kernel', click 'Python Environments...' in the top menu, then select the appropriate venv/conda path.

