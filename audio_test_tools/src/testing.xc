// Copyright (c) 2017, XMOS Ltd, All rights reserved
#include "audio_test_tools.h"

#include <xs1.h>
#include <limits.h>
#include <stdio.h>
#include <xclib.h>
#include <math.h>

int32_t att_random_int32(unsigned &r){
    crc32(r, -1, CRC_POLY);
    return (int32_t)r;
}

uint32_t att_random_uint32(unsigned &r){
    crc32(r, -1, CRC_POLY);
    return (uint32_t)r;
}

int64_t att_random_int64(unsigned &r){
    crc32(r, -1, CRC_POLY);
    int64_t a = (int64_t)r;
    crc32(r, -1, CRC_POLY);
    int64_t b = (int64_t)r;
    return (int64_t)(a + (b<<32));
}

uint64_t att_random_uint64(unsigned &r){
    crc32(r, -1, CRC_POLY);
    int64_t a = (int64_t)r;
    crc32(r, -1, CRC_POLY);
    int64_t b = (int64_t)r;
    return (uint64_t)(a + (b<<32));
}

double att_int64_to_double(int64_t x, int x_exp){
  return ldexp((double)x, x_exp);
}

double att_uint64_to_double(uint64_t x, int x_exp){
  return ldexp((double)x, x_exp);
}

double att_int32_to_double(int32_t x, int x_exp){
  return ldexp((double)x, x_exp);
}

double att_uint32_to_double(uint32_t x, int x_exp){
  return ldexp((double)x, x_exp);
}

int32_t att_double_to_int32(double d, const int d_exp){
    int m_exp;
    double m = frexp (d, &m_exp);

    double r = ldexp(m, m_exp - d_exp);
    int output_exponent;
    frexp(r, &output_exponent);
    if(output_exponent>31){
        printf("exponent is too high to cast to an int32_t (%d)\n", output_exponent);
        _Exit(1);
    }
    return r;
}

uint32_t att_double_to_uint32(double d, const int d_exp){
    int m_exp;
    double m = frexp (d, &m_exp);
    if(m<0.0){
        printf("negative trying to cast to a unsigned");
        _Exit(1);
    }
    return ldexp(m, m_exp - d_exp);
}

int64_t att_double_to_int64(double d, const int d_exp){
    int m_exp;
    double m = frexp (d, &m_exp);

    double r = ldexp(m, m_exp - d_exp);
    int output_exponent;
    frexp(r, &output_exponent);
    if(output_exponent>63){
        printf("exponent is too high to cast to an int64_t (%d)\n", output_exponent);
        _Exit(1);
    }
    return r;
}

uint64_t att_double_to_uint64(double d, const int d_exp){
    int m_exp;
    double m = frexp (d, &m_exp);
    if(m<0.0){
        printf("negative trying to cast to a unsigned");
        _Exit(1);
    }
    return (uint64_t)ldexp(m, m_exp - d_exp);
}

dsp_complex_t att_double_to_complex(dsp_complex_fp d, const int d_exp){
    dsp_complex_t r;
    r.re = att_double_to_int32(d.re, d_exp);
    r.im = att_double_to_int32(d.im, d_exp);
    return r;
}


dsp_complex_fp att_complex_int32_to_double(dsp_complex_t x, int x_exp){
    dsp_complex_fp f;
    f.re = att_int32_to_double(x.re, x_exp);
    f.im = att_int32_to_double(x.im, x_exp);
    return f;
}


unsigned att_bfp_vector_complex(dsp_complex_t * B, int B_exp, dsp_complex_fp * f, size_t start, size_t count){
    int32_t * b_int = (int32_t *) B;
    double * f_double = (double *) f;
    return att_bfp_vector_int32(b_int, B_exp, f_double, start*2, count*2);
}

unsigned att_bfp_vector_uint32(uint32_t * B, int B_exp, double * f, size_t start, size_t count){
    unsigned max_diff = 0;
    for(size_t i=start;i<start + count;i++){
        uint32_t v = att_double_to_uint32(f[i], B_exp);

        int diff = v-B[i];
        if (diff < 0 ) diff = -diff;
        if( (unsigned)diff > max_diff){
            max_diff = (unsigned)diff;
        }
    }
    return max_diff;
}

unsigned att_bfp_vector_int32(int32_t * B, int B_exp, double * f, size_t start, size_t count){
    unsigned max_diff = 0;

    for(size_t i=start;i<start + count;i++){
        int32_t v = att_double_to_int32(f[i], B_exp);
        int diff = v-B[i];
        if (diff < 0 ) diff = -diff;
        if( (unsigned)diff > max_diff){
            max_diff = (unsigned)diff;
        }
    }
    return max_diff;
}


unsigned long long att_bfp_vector_uint64(uint64_t * B, int B_exp, double * f, size_t start, size_t count){
    unsigned long long max_diff = 0;
    for(size_t i=start;i<start + count;i++){
        uint64_t v = att_double_to_uint64(f[i], B_exp);

        long long diff = v-B[i];
        if (diff < 0 ) diff = -diff;
        if( (unsigned long long)diff > max_diff){
            max_diff = (unsigned long long)diff;
        }
    }
    return max_diff;
}

unsigned long long att_bfp_vector_int64(int64_t * B, int B_exp, double * f, size_t start, size_t count){
    unsigned max_diff = 0;

    for(size_t i=start;i<start + count;i++){
        int64_t v = att_double_to_int64(f[i], B_exp);
        long long diff = v-B[i];
        if (diff < 0 ) diff = -diff;
        if( (unsigned long long)diff > max_diff){
            max_diff = (unsigned long long)diff;
        }
    }
    return max_diff;
}

void att_print_int_python_int32(int32_t * d, size_t length){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++){
        printf("%d, ", d[i]);
    }
    printf("])\n");
}
void att_print_int_python_uint32(uint32_t * d, size_t length){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++){
        printf("%u, ", d[i]);
    }
    printf("])\n");
}
void att_print_int_python_int64(int64_t * d, size_t length){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++){
        printf("%lld, ", d[i]);
    }
    printf("])\n");
}
void att_print_int_python_uint64(uint64_t * d, size_t length){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++){
        printf("%llu, ", d[i]);
    }
    printf("])\n");
}


void att_print_int_python_fd(dsp_complex_t * d, size_t length){
    printf("np.asarray([%d, ", d[0].re);
    for(size_t i=1;i<length;i++){
        printf("%d + %dj, ", d[i].re, d[i].im);
    }
    printf("%d])\n", d[0].im);
}

void att_print_int_python_td(dsp_complex_t * d, size_t length, int print_imag){
    printf("np.asarray([");
    if(print_imag){
        for(size_t i=0;i<length;i++)
            printf("%d, ", d[i].im);
    } else {
        for(size_t i=0;i<length;i++)
            printf("%d, ", d[i].re);
    }
    printf("])\n");
}

void att_print_python_fd(dsp_complex_t * d, size_t length, int d_exp){
    printf("np.asarray([%.12f, ", att_int32_to_double( d[0].re, d_exp));
    for(size_t i=1;i<length;i++){
        printf("%.12f + %.12fj, ", att_int32_to_double( d[i].re, d_exp),
                att_int32_to_double( d[i].im, d_exp));
    }
    printf("%.12f])\n", att_int32_to_double( d[0].im, d_exp));
}
void att_print_python_td(dsp_complex_t * d, size_t length, int d_exp, int print_imag){
    printf("np.asarray([");
    if(print_imag){
        for(size_t i=0;i<length;i++)
            printf("%.12f, ", att_int32_to_double( d[i].im, d_exp));
    } else {
        for(size_t i=0;i<length;i++)
            printf("%.12f, ", att_int32_to_double( d[i].re, d_exp));
    }
    printf("])\n");
}

void att_print_python_fd_fp(dsp_complex_fp * d, size_t length){
    printf("np.asarray([%.12f, ", d[0].re);
    for(size_t i=1;i<length;i++){
        printf("%.12f + %.12fj, ", d[i].re,d[i].im);
    }
    printf("%.12f])\n", d[0].im);
}
void att_print_python_td_fp(dsp_complex_fp * d, size_t length, int print_imag){
    printf("np.asarray([");
    if(print_imag){
        for(size_t i=0;i<length;i++)
            printf("%.12f, ", d[i].im);
    } else {
        for(size_t i=0;i<length;i++)
            printf("%.12f, ", d[i].re);
    }
    printf("])\n");
}

void att_print_python_int32(int32_t * d, size_t length, int d_exp){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++)
        printf("%.12f, ", att_int32_to_double( d[i], d_exp));
    printf("])\n");
}

void att_print_python_uint32(uint32_t * d, size_t length, int d_exp){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++)
        printf("%.22f, ", att_uint32_to_double( d[i], d_exp));
    printf("])\n");
}

void att_print_python_int64(int64_t * d, size_t length, int d_exp){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++)
        printf("%.12f, ", att_int64_to_double( d[i], d_exp));
    printf("])\n");
}

void att_print_python_uint64(uint64_t * d, size_t length, int d_exp){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++)
        printf("%.22f, ", att_uint64_to_double( d[i], d_exp));
    printf("])\n");
}

static uint64_t shr64(uint64_t v, int s){
    if(s<0){
        return v << (-s);
    } else {
        return v >> s;
    }
}

{uint32_t, int} att_get_fd_frame_power(dsp_complex_t * X, int X_shift, size_t bin_count){
    uint64_t power = 0;
    unsigned hr = dsp_bfp_cls(X, bin_count) - 1;
    unsigned hr_removal = 2*hr;

    unsigned bin_count_log_2 = 32 - clz(bin_count);
    int power_shift = 2*X_shift - 1 - bin_count_log_2;
    for(size_t s = 0; s < bin_count; s++){
        int64_t re = X[s].re;
        int64_t im = X[s].im;
        uint64_t t = (uint64_t)((re*re) + (im*im));
        power += shr64(t, (bin_count_log_2-1 - hr_removal));
    }
    return {power>>32, power_shift - hr_removal};
}


{uint32_t, int} att_get_td_frame_power(dsp_complex_t * x, int x_shift, size_t frame_length, int imag_channel){
    uint64_t power = 0;

    unsigned mask = 0;
    for(size_t s = 0; s < frame_length; s++){
        if(imag_channel){
            int32_t v=x[s].im;
            if(v<0)v=-v;
            mask |= v;
        } else {
            int32_t v=x[s].re;
            if(v<0)v=-v;
            mask |= v;
        }
    }

    unsigned hr = clz(mask) - 1;
    unsigned hr_removal = 2*hr;

    unsigned frame_length_log_2 = 32 - clz(frame_length);
    int power_shift = 2*x_shift - frame_length_log_2;
    for(size_t s = 0; s < frame_length; s++){
        if(imag_channel){
            uint64_t t = (uint64_t)((int64_t)x[s].im*(int64_t)x[s].im);
            power += shr64(t,(frame_length_log_2-2 - hr_removal));
        } else {
            uint64_t t = (uint64_t)((int64_t)x[s].re*(int64_t)x[s].re);
            power += shr64(t,(frame_length_log_2-2 - hr_removal));
        }
    }
    return {power>>32, power_shift - hr_removal};
}

/*
 * This partitions a space (0 to space_to_divide-1) into array_length chunks. Chunks may be zero length.
 */
void att_divide_array(unsigned * array, unsigned array_length, unsigned space_to_divide, int use_all_space, unsigned &r){
    unsigned base = 0;
    for(unsigned i=0;i<array_length-use_all_space;i++){
        unsigned chunk = (att_random_uint32(r)%(space_to_divide - base));
        array[i] = chunk;
        base += chunk;
    }
    if(use_all_space)
        array[array_length-1] = space_to_divide - base;
}
