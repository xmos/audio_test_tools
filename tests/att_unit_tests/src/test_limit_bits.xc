// Copyright 2018-2021 XMOS LIMITED.
// This Software is subject to the terms of the XMOS Public Licence: Version 1.
#include "att_unit_tests.h"

#define PROC_FRAME_LENGTH 256

void test_limit_bits(){

    unsigned r = 1;

    dsp_complex_t [[aligned(8)]]a[PROC_FRAME_LENGTH];
    dsp_complex_t [[aligned(8)]]a_copy[PROC_FRAME_LENGTH];

    for(unsigned l=0;l<1<<16;l++){

        unsigned min_hr    = zext(att_random_uint32(r), 5);
        unsigned bit_limit = zext(att_random_uint32(r), 5);

        unsigned a_shr = 0;
        for(unsigned i=0;i<PROC_FRAME_LENGTH;i++){
            a[i].re = att_random_int32(r)>>(a_shr+min_hr);
            a[i].im = att_random_int32(r)>>(a_shr+min_hr);
        }
        memcpy(a_copy, a, sizeof(a));

        unsigned a_hr = dsp_bfp_cls(a, PROC_FRAME_LENGTH)-1;

        att_limit_bits(a, PROC_FRAME_LENGTH, bit_limit);

        unsigned mask = bitrev((1<<bit_limit)-1);
        for(unsigned i=0;i<PROC_FRAME_LENGTH;i++){

            int32_t re = a_copy[i].re;
            re <<= a_hr;
            re &= mask;
            re >>= a_hr;
            TEST_ASSERT_EQUAL_INT32_MESSAGE(re, a[i].re, "Real aren't equal");

            int32_t im = a_copy[i].im;
            im <<= a_hr;
            im &= mask;
            im >>= a_hr;
            TEST_ASSERT_EQUAL_INT32_MESSAGE(im, a[i].im, "Imag aren't equal");
        }

    }


}
