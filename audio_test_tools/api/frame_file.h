// Copyright (c) 2017-2019, XMOS Ltd, All rights reserved

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

#define ATT_FF_SCOPE_STACK_SIZE(MAX_DEPTH) (sizeof(char*)*(MAX_DEPTH))
#define ATT_FF_INDEX_STACK_SIZE(MAX_DEPTH) (sizeof(int)*(MAX_DEPTH))

#ifdef __XC__
extern "C" {
#endif

typedef struct {
    FILE * file;
    char ** scope_stack;
    int* index_stack;
    unsigned max_scope_depth;
    int current_depth;
} att_ff_context_t;

typedef enum {
    ATT_FF_NO_INDEX = -1,
    ATT_FF_INDEXED = 0,
} att_ff_index_type_t;


typedef enum {
    att_ff_type_s16,
    att_ff_type_u16,
    att_ff_type_s32,
    att_ff_type_u32,
    att_ff_type_vtb_float,
    att_ff_type_double,
    att_ff_type_complex_fp,
    att_ff_type_double_pair_ch_a,
    att_ff_type_double_pair_ch_b,
} att_ff_type_t;

unsigned att_ff_open(
        att_ff_context_t* ctx,
        char** scope_stack,
        int* index_stack,
        const char max_scope_depth,
        const char *filename);

void att_ff_close(
        att_ff_context_t* ctx);

void att_ff_scope_push(
        att_ff_context_t* ctx,
        char* scope_name,
        const att_ff_index_type_t index_type);

void att_ff_scope_pop(
        att_ff_context_t* ctx);

void att_ff_index_set(
        att_ff_context_t* ctx,
        const int index);

void att_ff_index_increment(
        att_ff_context_t* ctx);

void att_ff_write_int(
        const att_ff_context_t* ctx,
        const char* name,
        const int value);

void att_ff_write_double(
        const att_ff_context_t* ctx,
        const char* name,
        const double value);

void att_ff_write_scalar(
        const att_ff_context_t* ctx,
        const char* name,
        const void* value,
        const att_ff_type_t type);

void att_ff_write_vector(
        const att_ff_context_t* ctx,
        const char* vec_name,
        const void* vector,
        const att_ff_type_t type,
        const unsigned len);

void att_ff_write_ndim_matrix(
        const att_ff_context_t* ctx,
        const char* mat_name,
        const void* matrix,
        const int* dimensions,
        const int dimension_count,
        const att_ff_type_t type);

        
void att_ff_write_scalar_indexed(
        const att_ff_context_t* ctx,
        const char* name,
        const void* value,
        const att_ff_type_t type,
        const int index);

void att_ff_write_vector_indexed(
        const att_ff_context_t* ctx,
        const char* vec_name,
        const void* vector,
        const att_ff_type_t type,
        const unsigned len,
        const int index);

void att_ff_write_ndim_matrix_indexed(
        const att_ff_context_t* ctx,
        const char* mat_name,
        const void* matrix,
        const int* dimensions,
        const int dimension_count,
        const att_ff_type_t type,
        const int index);

#ifdef __XC__
}
#endif

#endif /* FRAME_FILE_H_ */
