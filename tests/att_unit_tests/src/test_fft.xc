// Copyright (c) 2018-2019, XMOS Ltd, All rights reserved
#include "att_unit_tests.h"

#define MAX_PROC_FRAME_LENGTH_LOG2 10
#define MAX_PROC_FRAME_LENGTH (1<<MAX_PROC_FRAME_LENGTH_LOG2)
#include "dsp.h"


/*
 * Computes the discrete Fourier transform (DFT) of the given complex vector, storing the result back into the vector.
 * The vector can have any length. This is a wrapper function. Returns true if successful, false otherwise (out of memory).
 */
int Fft_transform(double real[], double imag[], size_t n);


/*
 * Computes the inverse discrete Fourier transform (IDFT) of the given complex vector, storing the result back into the vector.
 * The vector can have any length. This is a wrapper function. This transform does not perform scaling, so the inverse is not a true inverse.
 * Returns true if successful, false otherwise (out of memory).
 */
int Fft_inverseTransform(double real[], double imag[], size_t n);

void test_fft(){

    unsigned r = 1;
    unsafe {
        const  volatile int32_t const * const unsafe dsp_sine_lut[11] = {
                0,
                0,
                dsp_sine_4,
                dsp_sine_8,
                dsp_sine_16,
                dsp_sine_32,
                dsp_sine_64,
                dsp_sine_128,
                dsp_sine_256,
                dsp_sine_512,
                dsp_sine_1024,
        };
    for(unsigned l=2;l<MAX_PROC_FRAME_LENGTH_LOG2;l++){
        unsigned max_diff= 0;
        for(unsigned t=0;t<1<<12;t++){
            unsigned init_r = r;
            unsigned proc_frame_length = (1<<l);
            double sine_lut[(MAX_PROC_FRAME_LENGTH/2) + 1];

            att_make_sine_table(sine_lut, proc_frame_length);

            dsp_complex_t [[aligned(8)]]a[MAX_PROC_FRAME_LENGTH];
            dsp_complex_fp [[aligned(8)]]A[MAX_PROC_FRAME_LENGTH];
            double real[MAX_PROC_FRAME_LENGTH], imag[MAX_PROC_FRAME_LENGTH];

            int exp = sext(att_random_int32(r), 5);
            for(unsigned i=0;i<proc_frame_length;i++){
                a[i].re = att_random_int32(r)>>1;
                a[i].im = att_random_int32(r)>>1;
                A[i].re = att_int32_to_double(a[i].re, exp);
                A[i].im = att_int32_to_double(a[i].im, exp);
                real[i] = A[i].re;
                imag[i] = A[i].im;
            }

            Fft_transform(real, imag, proc_frame_length);

//            printf("A_input = [");
//            for(unsigned i=0;i<proc_frame_length;i++){
//                printf("%f + %fj,", A[i].re, A[i].im);
//            }
//            printf("]\n");

            att_bit_reverse(A, proc_frame_length);
            att_forward_fft(A, proc_frame_length, sine_lut);

            dsp_fft_bit_reverse(a, proc_frame_length);
            dsp_fft_forward(a, proc_frame_length, (const int32_t *)dsp_sine_lut[l]);
            exp += l;

//            printf("A_output_ref = [");
//            for(unsigned i=0;i<proc_frame_length;i++){
//                printf("%f + %fj,", real[i], imag[i]);
//            }
//            printf("]\n");
//
//            printf("A_output = [");
//            for(unsigned i=0;i<proc_frame_length;i++){
//                printf("%f + %fj,", A[i].re, A[i].im);
//            }
//            printf("]\n");
//
//            printf("a_output = [");
//            for(unsigned i=0;i<proc_frame_length;i++){
//                printf("%f + %fj,", att_int32_to_double(a[i].re, exp), att_int32_to_double(a[i].im, exp));
//            }
//            printf("]\n");
//            printf("\n");
            unsigned diff = att_bfp_vector_complex(a, exp, A, 0, proc_frame_length);
            TEST_ASSERT_LESS_OR_EQUAL_UINT32_MESSAGE(l, diff, "Output delta is too large");

            for(unsigned i=0;i<proc_frame_length;i++){
                A[i].re = real[i];
                A[i].im = imag[i];
            }

            diff = att_bfp_vector_complex(a, exp, A, 0, proc_frame_length);
            TEST_ASSERT_LESS_OR_EQUAL_UINT32_MESSAGE(l, diff, "Output delta is too large");
        }
    }
    }
}



void test_ifft(){

    unsigned r = 1;

    unsafe {
        const volatile int32_t  const * const unsafe dsp_sine_lut[11] = {
                0,
                0,
                dsp_sine_4,
                dsp_sine_8,
                dsp_sine_16,
                dsp_sine_32,
                dsp_sine_64,
                dsp_sine_128,
                dsp_sine_256,
                dsp_sine_512,
                dsp_sine_1024,
        };

        for(unsigned l=2;l<MAX_PROC_FRAME_LENGTH_LOG2;l++){
            unsigned max_diff= 0;
            for(unsigned t=0;t<1<<12;t++){
                unsigned init_r = r;
                unsigned proc_frame_length = (1<<l);
                double sine_lut[(MAX_PROC_FRAME_LENGTH/2) + 1];

                att_make_sine_table(sine_lut, proc_frame_length);

                dsp_complex_t [[aligned(8)]]a[MAX_PROC_FRAME_LENGTH];
                dsp_complex_fp [[aligned(8)]]A[MAX_PROC_FRAME_LENGTH];
                double real[MAX_PROC_FRAME_LENGTH], imag[MAX_PROC_FRAME_LENGTH];

                int exp = sext(att_random_int32(r), 5);
                for(unsigned i=0;i<proc_frame_length;i++){
                    a[i].re = att_random_int32(r)>>(1+l);
                    a[i].im = att_random_int32(r)>>(1+l);
                    A[i].re = att_int32_to_double(a[i].re, exp);
                    A[i].im = att_int32_to_double(a[i].im, exp);
                    real[i] = A[i].re;
                    imag[i] = A[i].im;
                }



    //            printf("A_input = [");
    //            for(unsigned i=0;i<proc_frame_length;i++){
    //                printf("%f + %fj,", A[i].re, A[i].im);
    //            }
    //            printf("]\n");

                att_bit_reverse(A, proc_frame_length);
                att_inverse_fft(A, proc_frame_length, sine_lut);

                dsp_fft_bit_reverse(a, proc_frame_length);
                dsp_fft_inverse(a, proc_frame_length, (const int32_t *)dsp_sine_lut[l]);
                exp -= l;

                Fft_inverseTransform(real, imag, proc_frame_length);
    //            printf("A_output = [");
    //            for(unsigned i=0;i<proc_frame_length;i++){
    //                printf("%f + %fj,", A[i].re, A[i].im);
    //            }
    //            printf("]\n");
    //
    //            printf("a_output = [");
    //            for(unsigned i=0;i<proc_frame_length;i++){
    //                printf("%f + %fj,", att_int32_to_double(a[i].re, exp), att_int32_to_double(a[i].im, exp));
    //            }
    //            printf("]\n");
    //            printf("\n");
                unsigned diff = att_bfp_vector_complex(a, exp, A, 0, proc_frame_length);
                TEST_ASSERT_LESS_OR_EQUAL_UINT32_MESSAGE(1<<l, diff, "Output delta is too large");;

                for(unsigned i=0;i<proc_frame_length;i++){
                    A[i].re = real[i];
                    A[i].im = imag[i];
                }

                diff = att_bfp_vector_complex(a, exp, A, 0, proc_frame_length);
                TEST_ASSERT_LESS_OR_EQUAL_UINT32_MESSAGE(1<<l, diff, "Output delta is too large");;
            }
        }
    }
}
