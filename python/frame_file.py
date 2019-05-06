def att_ff_open(filename, testname):
    ff = open(filename, "wb")
    ff.write("ATT_FF\nTEST: " + testname + "\n\n")
    return ff

def att_ff_close(ff):
    ff.close()
    return

def att_ff_frame_start(ff, frame_num):
    ff.write("FRAME: " + str(frame_num) + "\n")
    return

def att_ff_frame_end(ff):
    ff.write("FRAME END\n\n")
    return

def att_ff_array_write(ff, array_name, a):
    ff.write("DATA: " + array_name + "\n")
    for i in range(len(a)):
        ff.write("%.3f" % a[i])
        if i < len(a) - 1:
            ff.write(",")
            if i % 16 == 15:
                ff.write("\n")
            else:
                ff.write(" ")
    ff.write("\n")
    return

