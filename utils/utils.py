import os

def createDirs(path):
    """
    Function to create any directories needed to store the output of a function.

    Args:
        path (str): the path of directories you want to exist

    Returns:
        void
    """
    base = path.split("/")[0]
    dirs = path.split("/")[1:]
    tmp_dir = ""
    for folder in dirs:
        tmp_dir = tmp_dir + "/" + folder
        print(tmp_dir)
        print(base+"/"+tmp_dir)
        if not os.path.isdir(base+"/"+tmp_dir):
            try:
                os.mkdir(base+"/"+tmp_dir)
                print("creating: ", base+"/"+tmp_dir)
            except OSError as error:
                print(error)
