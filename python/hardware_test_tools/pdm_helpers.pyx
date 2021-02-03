import numpy as np 

cdef class pdm_modulator:
    cdef public double [5] c
    cdef public double [2] f
    cdef public double s0# Integrators
    cdef public double s1
    cdef public double s2
    cdef public double s3
    cdef public double s4
    cdef public double clip_level_pos
    cdef public double clip_level_neg
    cdef public double last_pdm
    cdef public int clipped

    def __init__(self):
        self.c = [0.791882, 0.304545, 0.069930, 0.009496, 0.000607]
        self.f = [0.000496, 0.001789]
        self.clip_level_pos = 0.55
        self.clip_level_neg = -self.clip_level_pos
        self.clipped = False
        self.s0 = self.s1 = self.s2 = self.s3 = self.s4 = last_pdm = 0.0

    def push_sample(self, double sample):
        if sample > self.clip_level_pos:
            sample = self.clip_level_pos
            self.clipped  = True
        if sample < self.clip_level_neg:
            sample = self.clip_level_neg
            self.clipped = True

        self.s4 = self.s4 + self.s3;
        self.s3 = self.s3 + self.s2 - self.f[1]*self.s4;
        self.s2 = self.s2 + self.s1;
        self.s1 = self.s1 + self.s0 - self.f[0]*self.s2;
        self.s0 = self.s0 + (sample - self.last_pdm);

        cdef double s = self.c[0]*self.s0 + self.c[1]*self.s1 + self.c[2]*self.s2 + self.c[3]*self.s3 + self.c[4]*self.s4;
        cdef double pdm

        if s < 0.0:
            pdm = -1.0
        else:
            pdm = 1.0
        self.last_pdm = pdm

        return pdm


    def push_block(self, double[:] pcm_block):
        cdef long long size = pcm_block.shape[0]
        pdm_block = np.zeros(size, dtype=np.uint8)

        cdef long long idx = 0
        cdef unsigned char byte
        cdef double pcm
        cdef double pdm_double

        while(idx < size):
            pcm = pcm_block[idx]
            pdm_double = self.push_sample(pcm)
            # print(pcm, pdm)
            if(pdm_double > 0):
                # byte = struct.pack("B", 1)
                byte = 1
            else:
                # byte = struct.pack("B", 0)
                byte = 0
            pdm_block[idx] = byte
            idx += 1
        if self.clipped:
            print(f"Warning: One or more microphone sample exceeded {self.clip_level_pos} so was clipped to prevent instability...")
            self.clipped = False
        return pdm_block


def pack_pdm_to_words(unsigned char[16] word_0_bits, unsigned char[16] word_1_bits):
    cdef unsigned shift = 0
    cdef unsigned pdm_word_0 = 0
    cdef unsigned pdm_word_1 = 0

    while(shift < 16):
        pdm_word_0 |=  word_0_bits[shift] << shift
        pdm_word_1 |=  word_1_bits[shift] << shift
        shift += 1

    return pdm_word_0, pdm_word_1