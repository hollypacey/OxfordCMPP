#! /bin/bash

# don't forget to chmod +x this file as well

#print out the date for fun
date

# in this case we'll move to our code directory and use userargs to direct out input/output
#cd /your/path/to/oxfordcmpp/
cd /home/pacey/CMPP/


# if you needed to set up an env here you could have e.g.
# source venv/bin/activate

python ToolTutorials/batchtest.py -i data/colleges.csv -o data/grad_only_colleges.csv