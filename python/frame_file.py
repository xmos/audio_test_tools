
class att_ff(object):

    FRAME_START = 0
    FRAME_END = 1
    ARRAY = 2
    EOF = 3

    def __init__(self):
        self.ff = None
        self.frame_num = 0
        self.array = []
        self.array_name = ""

    def open_write(self, filename, testname):
        self.ff = open(filename, "wb")
        self.ff.write("ATT_FF\nTEST: " + testname + "\n\n")
        return

    def close(self):
        self.ff.close()
        return

    def frame_start(self):
        self.ff.write("FRAME: " + str(self.frame_num) + "\n")
        return

    def frame_end(self):
        self.ff.write("FRAME END\n\n")
        self.frame_num += 1
        return

    def array_write(self, array_name, a):
        self.ff.write("DATA: " + array_name + "\n")
        for i in range(len(a)):
            self.ff.write("%.3f" % a[i])
            if i < len(a) - 1:
                self.ff.write(",")
                if i % 16 == 15:
                    self.ff.write("\n")
                else:
                    self.ff.write(" ")
        self.ff.write("\nDATA END\n")
        return

    def open_read(self, filename):
        self.ff = open(filename, "r")
        return

    def get_array(self):
        self.array = []
        while True:
            line = self.ff.readline()
            if line == "":
                return

            line = line.strip()

            i = line.find("DATA END")
            if i == 0:
                return
            else:
                self.array.extend([float(v) for v in line.split(',') if v.strip()])

    def parse(self, fields):
        while True:
            line = self.ff.readline()

            if line == "":
                return att_ff.EOF

            line = line.strip()

            i = line.find("FRAME:")
            if i == 0:
                line = line.split(" ", 2)
                self.frame_num = int(line[1])
                return att_ff.FRAME_START

            i = line.find("FRAME END")
            if i == 0:
                return att_ff.FRAME_END

            i = line.find("DATA:")
            if i == 0:
                line = line.split(" ", 2)
                self.array_name = line[1]
                self.get_array()
                if len(fields) == 0 or self.array_name in fields:
                    return att_ff.ARRAY


