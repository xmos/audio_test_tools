// Copyright (c) 2017-2019, XMOS Ltd, All rights reserved
#include "audio_test_tools.h"

#include <xs1.h>
#include <limits.h>
#include <stdio.h>
#include <xclib.h>
#include <math.h>

int att_is_double_word_aligned(int * p){
    if((int)p&7){
        return 0;
    } else {
        return 1;
    }
}

int16_t att_random_int16(unsigned &r){
    crc32(r, -1, CRC_POLY);
    return (int16_t)r;
}

uint16_t att_random_uint16(unsigned &r){
    crc32(r, -1, CRC_POLY);
    return (uint16_t)r;
}

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

double att_int16_to_double(int16_t x, int x_exp){
  return ldexp((double)x, x_exp);
}

double att_uint16_to_double(uint16_t x, int x_exp){
  return ldexp((double)x, x_exp);
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

int16_t att_double_to_int16(double d, const int d_exp){
    int m_exp;
    double m = frexp (d, &m_exp);

    double r = ldexp(m, m_exp - d_exp);
    int output_exponent;
    frexp(r, &output_exponent);
    if(output_exponent>15){
        printf("exponent is too high to cast to an int16_t (%d)\n", output_exponent);
        _Exit(1);
    }
    return r;
}

uint16_t att_double_to_uint16(double d, const int d_exp){
    int m_exp;
    double m = frexp (d, &m_exp);
    if(m<0.0){
        printf("negative trying to cast to a unsigned");
        _Exit(1);
    }
    return ldexp(m, m_exp - d_exp);
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


dsp_complex_fp att_complex_int16_to_double(dsp_complex_short_t x, int x_exp){
    dsp_complex_fp f;
    f.re = att_int16_to_double(x.re, x_exp);
    f.im = att_int16_to_double(x.im, x_exp);
    return f;
}

dsp_complex_fp att_complex_int32_to_double(dsp_complex_t x, int x_exp){
    dsp_complex_fp f;
    f.re = att_int32_to_double(x.re, x_exp);
    f.im = att_int32_to_double(x.im, x_exp);
    return f;
}

unsigned att_bfp_vector_complex_short(dsp_complex_short_t * B, int B_exp, dsp_complex_fp * f, size_t start, size_t count){
    int16_t * b_int = (int16_t *) B;
    double * f_double = (double *) f;
    return att_bfp_vector_int16(b_int, B_exp, f_double, start*2, count*2);
}

unsigned att_bfp_vector_uint16(uint16_t * B, int B_exp, double * f, size_t start, size_t count){
    unsigned max_diff = 0;
    for(size_t i=start;i<start + count;i++){
        uint16_t v = att_double_to_uint16(f[i], B_exp);

        int diff = v-B[i];
        if (diff < 0 ) diff = -diff;
        if( (unsigned)diff > max_diff){
            max_diff = (unsigned)diff;
        }
    }
    return max_diff;
}

unsigned att_bfp_vector_int16(int16_t * B, int B_exp, double * f, size_t start, size_t count){
    unsigned max_diff = 0;

    for(size_t i=start;i<start + count;i++){
        int16_t v = att_double_to_int16(f[i], B_exp);
        int diff = v-B[i];
        if (diff < 0 ) diff = -diff;
        if( (unsigned)diff > max_diff){
            max_diff = (unsigned)diff;
        }
    }
    return max_diff;
}

unsigned att_bfp_vector_complex(dsp_complex_t * B, int B_exp, dsp_complex_fp * f, size_t start, size_t count){
    int32_t * b_int = (int32_t *) B;
    double * f_double = (double *) f;
    return att_bfp_vector_int32(b_int, B_exp, f_double, start*2, count*2);
}

{unsigned, unsigned} att_bfp_vector_pair(dsp_complex_t * B, int ch_a_exp, int ch_b_exp, dsp_complex_fp * f, size_t start, size_t count){
    unsigned max_diff_re = 0;
    unsigned max_diff_im = 0;
    for(size_t i=start;i<start + count;i++){

        int32_t ch_a = att_double_to_int32(f[i].re, ch_a_exp);
        int32_t ch_b = att_double_to_int32(f[i].im, ch_b_exp);
        int diff = ch_a-B[i].re;
        if (diff < 0 ) diff = -diff;
        if( (unsigned)diff > max_diff_re)
            max_diff_re = (unsigned)diff;
        diff = ch_b-B[i].im;
        if (diff < 0 ) diff = -diff;
        if( (unsigned)diff > max_diff_im)
            max_diff_im = (unsigned)diff;

    }
    return {max_diff_re, max_diff_im};
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

void att_print_python_fd_short(dsp_complex_short_t * d, size_t length, int d_exp){
    printf("np.asarray([%.12f, ", att_int16_to_double( d[0].re, d_exp));
    for(size_t i=1;i<length;i++){
        printf("%.12f + %.12fj, ", att_int16_to_double( d[i].re, d_exp),
                att_int16_to_double( d[i].im, d_exp));
    }
    printf("%.12f])\n", att_int16_to_double( d[0].im, d_exp));
}
void att_print_python_td_short(dsp_complex_short_t * d, size_t length, int d_exp, int print_imag){
    printf("np.asarray([");
    if(print_imag){
        for(size_t i=0;i<length;i++)
            printf("%.12f, ", att_int16_to_double( d[i].im, d_exp));
    } else {
        for(size_t i=0;i<length;i++)
            printf("%.12f, ", att_int16_to_double( d[i].re, d_exp));
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
    printf("np.asarray([%.22f, ", d[0].re);
    for(size_t i=1;i<length;i++){
        printf("%.22f + %.22fj, ", d[i].re, d[i].im);
    }
    printf("%.22f])\n", d[0].im);
}
void att_print_python_td_fp(dsp_complex_fp * d, size_t length, int print_imag){
    printf("np.asarray([");
    if(print_imag){
        for(size_t i=0;i<length;i++)
            printf("%.22f, ", d[i].im);
    } else {
        for(size_t i=0;i<length;i++)
            printf("%.22f, ", d[i].re);
    }
    printf("])\n");
}

void att_print_python_int16(int16_t * d, size_t length, int d_exp){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++)
        printf("%.12f, ", att_int16_to_double( d[i], d_exp));
    printf("])\n");
}

void att_print_python_uint16(uint16_t * d, size_t length, int d_exp){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++)
        printf("%.22f, ", att_uint16_to_double( d[i], d_exp));
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

void att_print_python_double(double * d, size_t length){
    printf("np.asarray([");
    for(size_t i=0;i<length;i++)
        printf("%.22f, ", d[i]);
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

void att_make_1d_name(char name[], unsigned i){
    sprintf (name, "%s_%u", name, i);
}

void att_make_2d_name(char name[], unsigned i, unsigned j){
    sprintf (name, "%s_%u_%u", name, i, j);
}

void att_make_3d_name(char name[], unsigned i, unsigned j, unsigned k){
    sprintf (name, "%s_%u_%u_%u", name, i, j, k);
}

void att_trace_new_frame(unsigned &frame_no){
    printf("### Frame %u ###\n", frame_no);
    printf("current_frame = {}\n", frame_no);
    frame_no++;
}

void att_trace_complex_td(char name[], dsp_complex_t * d, int exponent, unsigned length, int print_imag){
    printf("current_frame.update({\"%s\": [[", name);
    for(unsigned i=0;i<length;i++)
        printf("%d, ", (d[i], int32_t[2])[print_imag]);
    printf("], %d]})\n", exponent);
}

void att_trace_complex_fd(char name[], dsp_complex_t * d, int exponent, unsigned length){
    printf("current_frame.update({\"%s\": [[%d,", name, d[0].re);
    for(unsigned i=1;i<length;i++){
        printf("%d+%dj, ", d[i].re, d[i].im);
    }
    printf("%d], %d]})\n", d[0].im, exponent);
}

void att_trace_complex_td_short(char name[], dsp_complex_short_t * d, int exponent, unsigned length, int print_imag){
    printf("current_frame.update({\"%s\": [[", name);
    for(unsigned i=0;i<length;i++)
        printf("%d, ", (d[i], int16_t[2])[print_imag]);
    printf("], %d]})\n", exponent);
}

void att_trace_complex_fd_short(char name[], dsp_complex_short_t * d, int exponent, unsigned length){
    printf("current_frame.update({\"%s\": [[%d,", name, d[0].re);
    for(unsigned i=1;i<length;i++){
        printf("%d+%dj, ", d[i].re, d[i].im);
    }
    printf("%d], %d]})\n", d[0].im, exponent);
}

void att_trace_uint64(char name[], uint64_t *d, int exponent, unsigned length){
    printf("current_frame.update({\"%s\": [[", name);
    for(unsigned i=0;i<length;i++)
        printf("%llu, ", d[i]);
    printf("], %d]})\n", exponent);
}
void att_trace_int64(char name[], int64_t *d, int exponent, unsigned length){
    printf("current_frame.update({\"%s\": [[", name);
    for(unsigned i=0;i<length;i++)
       printf("%lld, ", d[i]);
    printf("], %d]})\n", exponent);
}


void att_trace_uint32(char name[], uint32_t *d, int exponent, unsigned length){
    printf("current_frame.update({\"%s\": [[", name);
    for(unsigned i=0;i<length;i++)
        printf("%u, ", d[i]);
    printf("], %d]})\n", exponent);
}
void att_trace_int32(char name[], int32_t *d, int exponent, unsigned length){
    printf("current_frame.update({\"%s\": [[", name);
    for(unsigned i=0;i<length;i++)
       printf("%d, ", d[i]);
    printf("], %d]})\n", exponent);
}

void att_trace_uint16(char name[], uint16_t *d, int exponent, unsigned length){
    printf("current_frame.update({\"%s\": [[", name);
    for(unsigned i=0;i<length;i++)
        printf("%u, ", d[i]);
    printf("], %d]})\n", exponent);
}
void att_trace_int16(char name[], int16_t *d, int exponent, unsigned length){
    printf("current_frame.update({\"%s\": [[", name);
    for(unsigned i=0;i<length;i++)
       printf("%d, ", d[i]);
    printf("], %d]})\n", exponent);
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


void att_limit_bits(dsp_complex_t * a, unsigned length, unsigned bits){

    if(bits >= 32)
        return;

    unsigned hr = dsp_bfp_cls(a, length)-1;
    int mask = bitrev((1<<bits)-1);

    mask >>= hr;

    for(unsigned i=0;i<length;i++){
        a[i].re &= mask;
        a[i].im &= mask;
    }
}
