// Copyright (c) 2020, XMOS Ltd, All rights reserved
#ifndef ATT_TYPES_H_
#define ATT_TYPES_H_

/**
 * Definition of types in general use throughout the Audio Test Tools.
 */

#if defined(__XS3A__)
    #include "xs3_math.h"
#else
    #include "dsp.h"
#endif // defined(__XS3A__)

/**
 * Struct containing a complex floating point number.
 */
#if defined(__XS3A__)
    typedef complex_double_t att_complex_fp;
#else
    typedef dsp_complex_fp att_complex_fp;
#endif // defined(__XS3A__)

/**
 * Struct containing a complex number.
 * Both the real and imaginary parts are represented as short fixed point
 * values, with a Q value that depends on the use case.
 */
#if defined(__XS3A__)
    typedef complex_s16_t att_complex_short_t;
#else
    typedef dsp_complex_short_t att_complex_short_t;
#endif // defined(__XS3A__)

/**
 * Struct containing a complex number.
 * Both the real and imaginary parts are represented as fixed point
 * values, with a Q value that depends on the use case.
 */
#if defined(__XS3A__)
    typedef complex_s32_t att_complex_t;
#else
    typedef dsp_complex_t att_complex_t;
#endif // defined(__XS3A__)

#endif // ATT_TYPES_H_
