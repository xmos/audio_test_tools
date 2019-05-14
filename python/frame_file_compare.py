# Copyright (c) 2019, XMOS Ltd, All rights reserved

import numpy as np
import matplotlib.pyplot as plt
import frame_file
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input1", help="input frame file 1")
    parser.add_argument("input2", help="input frame file 2")
    parser.add_argument("--fields", help="names of the fields to compare")
    parser.add_argument("--tolerance", type=float, default = 0.001, help="The amount two values can differ by")

    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()

    if args.fields is not None:
        fields = [f.strip() for f in args.fields.split(',') if f.strip()]
    else:
        fields = []

    ff1 = frame_file.att_ff()
    ff1.open_read(args.input1)

    ff2 = frame_file.att_ff()
    ff2.open_read(args.input2)
    
    while True:
        p = ff1.parse(fields)
        p2 = ff2.parse(fields)

        if p != p2:
            print "Frame file mismatch"
            return

        if p == ff1.FRAME_START:
            #print "Frame " + str(ff1.frame_num) + " begin"
            pass
        elif p == ff1.ARRAY:
            if ff1.array_name == ff2.array_name and len(ff1.array) == len(ff2.array):
                diff = np.abs(np.array(ff1.array) - np.array(ff2.array))
                diffwhere = np.argwhere(diff > args.tolerance)
                if len(diffwhere) > 0:
                    print "Field " + ff1.array_name + " in frame " + str(ff1.frame_num) + " does not match at elements " + str(diffwhere.tolist())
                    return
            else:
                print "Frame file mismatch"
                return
        elif p == ff1.FRAME_END:
            #print "Frame " + str(ff1.frame_num) + " end"
            pass
        elif p == ff1.EOF:
            break


if __name__ == "__main__":
    main()

