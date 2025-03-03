Look in batchtest.py to see what our test job will do.

Edit ```batchtest.sh``` to use the right path for you

Do ```chmod +x``` to your batchtest.py/sh files to ensure the batch system can read them.

from the main directory:
```
mkdir logs
condor_submit batchtest.submit
```

check it:
```
condor_q
```