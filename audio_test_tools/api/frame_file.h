/*
 * frame_file.h
 *
 *  Created on: May 6, 2019
 *      Author: mbruno
 */


#ifndef FRAME_FILE_H_
#define FRAME_FILE_H_

#include <stdio.h>
#include <stdint.h>

#ifdef __XC__
extern "C" {
#endif

FILE *att_ff_open(
        const char *filename,
        const char *testname);

void att_ff_close(
        FILE *ff);

void att_ff_frame_start(
        FILE *ff,
        unsigned int frame_num);

void att_ff_frame_end(
        FILE *ff);

typedef enum {
    att_ff_type_s16,
    att_ff_type_u16,
    att_ff_type_s32,
    att_ff_type_u32,
    att_ff_type_float
} att_ff_type_t;

void att_ff_array_write(
        FILE *ff,
        const char *array_name,
        void *a,
        att_ff_type_t type,
        unsigned int len);

#ifdef __XC__
}
#endif

#endif /* FRAME_FILE_H_ */
