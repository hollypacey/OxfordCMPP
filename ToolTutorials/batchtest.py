#!/usr/bin/python

# This is a random batch test job that reads a CSV file, and writes some of the rows to an output CSV file.
# # don't forget to call before you submit:
# chmod +x batchtest.py

import csv
import argparse

#_____________________________________________________________________________
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input CSV file", default="")
    parser.add_argument("-o", "--output", help="output CSV file", default="")

    args = parser.parse_args()

    input_csv = args.input
    output_csv = args.output

    with open(input_csv, newline="") as incsvfile:
        csvreader = csv.reader(incsvfile, delimiter=",")
        
        with open(output_csv, "w", newline="") as outcsvfile:
            csvwriter = csv.writer(outcsvfile, delimiter=",")
            
            for row in csvreader:
                print(row)
                if ("Yes" in row[2] and "No" in row[1]): csvwriter.writerow(row)


            

