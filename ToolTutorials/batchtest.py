#!/usr/bin/python

# This is a random batch test job that reads a CSV file, and writes some of the rows to an output CSV file.
# # don't forget to call before you submit:
# chmod +x batchtest.py

import csv
import argparse

#_____________________________________________________________________________
if __name__ == "__main__":

    # setup command line arguments for our input and output files.
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input CSV file", default="")
    parser.add_argument("-o", "--output", help="output CSV file", default="")

    args = parser.parse_args()

    input_csv = args.input
    output_csv = args.output

    # read in a csv file
    with open(input_csv, newline="") as incsvfile:
        csvreader = csv.reader(incsvfile, delimiter=",")
        
        # open an output csv file
        with open(output_csv, "w", newline="") as outcsvfile:
            csvwriter = csv.writer(outcsvfile, delimiter=",")

            # iterate over the rows in the input            
            for row in csvreader:
                print(row)
                # add it to the output if the row matches a certain pattern (in our example we'll see which Oxford colleges are grad-only)
                if ("Yes" in row[2] and "No" in row[1]): csvwriter.writerow(row)


            

