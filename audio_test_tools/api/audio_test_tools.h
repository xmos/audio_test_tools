// Copyright (c) 2017-2018, XMOS Ltd, All rights reserved

#ifndef AUDIO_TEST_TOOLS_H_
#define AUDIO_TEST_TOOLS_H_

#include <stdint.h>
#include <stdlib.h>
#include "dsp.h"

typedef struct  {
    double re;
    double im;
} dsp_complex_fp;

#define CRC_POLY (0xEB31D82E)
#define ATT_WAV_HEADER_BYTES 44

/*
 * return non-zero when f is double word aligned
 * return zero otherwise.
 */
int att_is_double_word_aligned(int * f);


#ifdef __process_wav_conf_h_exists__
#include "process_wav_conf.h"
#define ATT_PW_INPUT_CHANNEL_PAIRS ((ATT_PW_INPUT_CHANNELS+1)/2)
#define ATT_PW_OUTPUT_CHANNEL_PAIRS ((ATT_PW_OUTPUT_CHANNELS+1)/2)
#endif

void att_pw_play(chanend c_comms);
void att_pw_pause(chanend c_comms);
void att_pw_stop(chanend c_comms);
void att_pw_play_until_sample_passes(chanend c_comms, long sample);

/*
 * This opens the 32 bit signed WAV file ATT_PW_INPUT_FILE_NAME of ATT_PW_INPUT_CHANNEL_PAIRS
 * channels. It will write to the file ATT_PW_OUTPUT_FILE_NAME of ATT_PW_OUTPUT_CHANNELS
 * channels.
 *
 * If c_comms is not null then the wav will begin paused and await instructions to continue.
 * If c_comms is null then the wav will play.
 *
 * Commands:
 *  - att_pw_play
 *          This will play the wav file
 *  - att_pw_pause
 *          This will pause the wav file playing. It is useful for issuing multiple commands
 *          to the DSP before continuing.
 *  - att_pw_play_until_sample_passes SAMPLE
 *          This will play the wav until the sample number passes SAMPLE
 *  - att_pw_stop
 *          This will stop the wav playing and finish the task.
 */
void att_process_wav(chanend c_app_to_dsp, chanend ?c_dsp_to_app, chanend ?c_comms);


/*
 * Wav file stuff
 */
typedef struct att_wav_header {
    // RIFF Header
    char riff_header[4];    // Should be "RIFF"
    int wav_size;           // File size - 8 = data_bytes + WAV_HEADER_BYTES - 8
    char wave_header[4];    // Should be "WAVE"

    // Format Subsection
    char fmt_header[4];     // Should be "fmt "
    int fmt_chunk_size;     // Size of the rest of this subchunk
    short audio_format;
    short num_channels;
    int sample_rate;
    int byte_rate;          // sample_rate * num_channels * (bit_depth/8)
    short sample_alignment; // num_channels * (bit_depth/8)
    short bit_depth;        // bits per sample

    // Data Subsection
    char data_header[4];    // Should be "data"
    int data_bytes;         // frame count * num_channels * (bit_depth/8)
} att_wav_header;

int att_get_wav_header_details(const char* filename, att_wav_header & s, unsigned &wav_header_size);
int att_wav_form_header(att_wav_header & header,
        short audio_format,
        short num_channels,
        int sample_rate,
        short bit_depth,
        int num_frames);

void att_wav_print_header(att_wav_header & s);

unsigned att_wav_get_num_bytes_per_frame(const att_wav_header &s);
int att_wav_get_num_frames(const att_wav_header &s);
long att_wav_get_frame_start(const att_wav_header &s, unsigned frame_number, uint32_t wavheader_size);

/*
 * Double precision DTF
 */
void att_make_sine_table(double * sine_lut, unsigned proc_frame_length);
void att_bit_reverse    ( dsp_complex_fp pts[], const uint32_t N );
void att_forward_fft    ( dsp_complex_fp pts[], const uint32_t N, const double sine[]);
void att_inverse_fft    ( dsp_complex_fp pts[], const uint32_t N, const double sine[]);
void att_split_spectrum ( dsp_complex_fp pts[], const uint32_t N );
void att_merge_spectra  ( dsp_complex_fp pts[], const uint32_t N );

//Returns the interpolated center bin and interpolated peak
{double, double} att_poly_interpolate(double left, double peak, double right, double center_bin);

/*
 * Random number generation
 */
int16_t  att_random_int16(unsigned &r);
uint16_t att_random_uint16(unsigned &r);
int32_t  att_random_int32(unsigned &r);
uint32_t att_random_uint32(unsigned &r);
int64_t  att_random_int64(unsigned &r);
uint64_t att_random_uint64(unsigned &r);

/*
 * Type conversion
 */
double att_int16_to_double(int16_t x, int x_exp);
double att_uint16_to_double(uint16_t x, int x_exp);
double att_int32_to_double(int32_t x, int x_exp);
double att_uint32_to_double(uint32_t x, int x_exp);
double att_int64_to_double(int64_t x, int x_exp);
double att_uint64_to_double(uint64_t x, int x_exp);
int16_t att_double_to_int16(double d, const int d_exp);
uint16_t att_double_to_uint16(double d, const int d_exp);
int32_t att_double_to_int32(double d, const int d_exp);
uint32_t att_double_to_uint32(double d, const int d_exp);
int64_t att_double_to_int64(double d, const int d_exp);
uint64_t att_double_to_uint64(double d, const int d_exp);

dsp_complex_fp att_complex_int16_to_double(dsp_complex_short_t x, int x_exp);
dsp_complex_fp att_complex_int32_to_double(dsp_complex_t x, int x_exp);

q8_24 att_uint32_to_q24(uint32_t v, int v_exp);

/*
 * Float/Fixed vector comparision
 */
unsigned att_bfp_vector_complex_short(dsp_complex_short_t * B, int B_exp, dsp_complex_fp * f, size_t start, size_t count);
unsigned att_bfp_vector_uint16(uint16_t * B, int B_exp, double * f, size_t start, size_t count);
unsigned att_bfp_vector_int16(int16_t * B, int B_exp, double * f, size_t start, size_t count);
unsigned att_bfp_vector_complex(dsp_complex_t * B, int B_exp, dsp_complex_fp * f, size_t start, size_t count);
unsigned att_bfp_vector_uint32(uint32_t * B, int B_exp, double * f, size_t start, size_t count);
unsigned att_bfp_vector_int32(int32_t * B, int B_exp, double * f, size_t start, size_t count);
unsigned long long att_bfp_vector_uint64(uint64_t * B, int B_exp, double * f, size_t start, size_t count);
unsigned long long att_bfp_vector_int64(int64_t * B, int B_exp, double * f, size_t start, size_t count);

/*
 * Python pretty printers
 */

void att_print_int_python_fd(dsp_complex_t * d, size_t length);
void att_print_int_python_td(dsp_complex_t * d, size_t length, int print_imag);
void att_print_int_python_int32(int32_t * d, size_t length);
void att_print_int_python_uint32(uint32_t * d, size_t length);
void att_print_int_python_int64(int64_t * d, size_t length);
void att_print_int_python_uint64(uint64_t * d, size_t length);


void att_print_python_fd_shortd(dsp_complex_short_t * d, size_t length, int d_exp);
void att_print_python_td_short(dsp_complex_short_t * d, size_t length, int d_exp, int print_imag);
void att_print_python_fd(dsp_complex_t * d, size_t length, int d_exp);
void att_print_python_td(dsp_complex_t * d, size_t length, int d_exp, int print_imag);
void att_print_python_int16(int16_t * d, size_t length, int d_exp);
void att_print_python_uint16(uint16_t * d, size_t length, int d_exp);
void att_print_python_int32(int32_t * d, size_t length, int d_exp);
void att_print_python_uint32(uint32_t * d, size_t length, int d_exp);
void att_print_python_int64(int64_t * d, size_t length, int d_exp);
void att_print_python_uint64(uint64_t * d, size_t length, int d_exp);
void att_print_python_fd_fp(dsp_complex_fp * d, size_t length);
void att_print_python_td_fp(dsp_complex_fp * d, size_t length, int print_imag);

/*
 * DSP tracers
 */
#define ATT_FRAME_NUMBER_INIT (-1)
void att_trace_new_frame(unsigned & frame_number);
void att_trace_complex_fd_short(char name[], dsp_complex_short_t * d, int exponent, unsigned length);
void att_trace_complex_td_short(char name[], dsp_complex_short_t * d, int exponent, unsigned length, int print_imag);
void att_trace_complex_fd(char name[], dsp_complex_t * d, int exponent, unsigned length);
void att_trace_complex_td(char name[], dsp_complex_t * d, int exponent, unsigned length, int print_imag);

void att_trace_uint16(char name[], uint16_t *d, int exponent, unsigned length);
void att_trace_int16(char name[], int16_t *d, int exponent, unsigned length);
void att_trace_uint32(char name[], uint32_t *d, int exponent, unsigned length);
void att_trace_int32(char name[], int32_t *d, int exponent, unsigned length);
void att_trace_uint64(char name[], uint64_t *d, int exponent, unsigned length);
void att_trace_int64(char name[], int64_t *d, int exponent, unsigned length);

void att_make_1d_name(char name[], unsigned i);
void att_make_2d_name(char name[], unsigned i, unsigned j);
void att_make_3d_name(char name[], unsigned i, unsigned j, unsigned k);

/*
 * Thread burning
 */

void att_burn_thread();
void att_burn_thread_div();

/*
 * Other
 */
void att_divide_array(unsigned * array, unsigned array_length, unsigned space_to_divide, int use_all_space, unsigned &r);

//Limit the number of significant bit of information in a complex array.
void att_limit_bits(dsp_complex_t * a, unsigned length, unsigned bits);

#endif /* AUDIO_TEST_TOOLS_H_ */
