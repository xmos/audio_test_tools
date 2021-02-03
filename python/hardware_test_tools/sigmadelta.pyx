import numpy as np 

#Reference implementations cythonised by adding typed vars and slightly re-ordered

def delta_sigma_5th_order(double[:] data_in , long long output_length):
  "This outputs a 1-bit delta sigma modulated data set from an input data set of floating point samples"

  # Coefficients
  cdef double [5] c = [0.791882, 0.304545, 0.069930, 0.009496, 0.000607];
  cdef double [2] f = [0.000496, 0.001789];

  # Initialization
  cdef double s0 = 0.0; # Integrators
  cdef double s1 = 0.0; # Integrators
  cdef double s2 = 0.0; # Integrators
  cdef double s3 = 0.0; # Integrators
  cdef double s4 = 0.0; # Integrators

  cdef double[:] data_out = np.ones(output_length)

  cdef long long i = 1
  cdef long long limit = min(len(data_in),output_length)

  while i < limit:
  # for i in range(1, min(len(data_in),output_length)):
      s4 = s4 + s3;
      s3 = s3 + s2 - f[1]*s4;
      s2 = s2 + s1;
      s1 = s1 + s0 - f[0]*s2;
      s0 = s0 + (data_in[i] - data_out[i-1]);
      s = c[0]*s0 + c[1]*s1 + c[2]*s2 + c[3]*s3 + c[4]*s4;

      if s < 0.0:
        data_out[i] = -1.0

      i += 1

  return data_out
