/*
 * frame_file.c
 *
 *  Created on: May 3, 2019
 *      Author: mbruno
 */

#include "frame_file.h"

#include <platform.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * Cannot include vtb_float.h because it unfortunately
 * uses XC pass by reference syntax. Instead define the
 * vtb_s32_float_t struct type below.
 */
//#include "vtb_float.h"

/**
 * Floating point struct with S32 mantissa.
 */
typedef struct {
    int32_t m;  ///< Mantissa.
    int e;      ///< Exponent.
} vtb_s32_float_t;

typedef struct {
    double re;
    double im;
} dsp_complex_fp;


static void write_full_scope_indexed(
        const att_ff_context_t* ctx,
        const char* var_name,
        const int index)
{
    //Write full scope
    for(int i = 0; i <= ctx->current_depth; i++){

        if(ctx->scope_stack[i] != NULL)
            fprintf(ctx->file, "%s", ctx->scope_stack[i]);

        //Write the scope's index if it has one
        if(ctx->index_stack[i] != ATT_FF_NO_INDEX)
            fprintf(ctx->file, "[%d]", ctx->index_stack[i]);

        if(ctx->scope_stack[i] != NULL)
            fprintf(ctx->file, ".");
    }

    fprintf(ctx->file, "%s", var_name);

    if(index != -1)
        fprintf(ctx->file, "[%d]", index);

    fprintf(ctx->file, ": ", var_name);
}

static void write_full_scope(
        const att_ff_context_t* ctx,
        const char* var_name)
{
    write_full_scope_indexed(ctx, var_name, -1);
}

static void write_dimensions(
        const att_ff_context_t* ctx,
        const int* dimensions,
        const int dimension_count)
{
    fprintf(ctx->file, "<");
    for(int i = 0; i < dimension_count; i++){
        fprintf(ctx->file, "%d", dimensions[i]);
        if(i < (dimension_count-1))
            fprintf(ctx->file, ",");
    }
    fprintf(ctx->file, "> ");
}

static void write_array(
        const att_ff_context_t* ctx,
        const void* v,
        const att_ff_type_t type,
        const unsigned len)
{
    FILE* f = ctx->file;

    const  int16_t* v_s16 = ( int16_t*) v;
    const uint16_t* v_u16 = (uint16_t*) v;
    const  int32_t* v_s32 = ( int32_t*) v;
    const uint32_t* v_u32 = (uint32_t*) v;
    const double*   v_dbl = (  double*) v;
    const vtb_s32_float_t* v_vtb_float = (vtb_s32_float_t*) v;
    const dsp_complex_fp* v_cplx_fp = (dsp_complex_fp*) v;

    for(int i = 0; i < len; i++){
        switch(type){
            case att_ff_type_s16: 
                fprintf(f, "%hd", v_s16[i]);
                break;
            case att_ff_type_u16: 
                fprintf(f, "%hu", v_u16[i]);
                break;
            case att_ff_type_s32: 
                fprintf(f, "%d", (int) v_s32[i]);
                break;
            case att_ff_type_u32: 
                fprintf(f, "%u", (unsigned) v_u32[i]);
                break;
            case att_ff_type_vtb_float: {
                int32_t m = v_vtb_float[i].m;
                uint64_t denom = (((uint64_t) 1) << -v_vtb_float[i].e);
                if(m == 0) denom = 1;
                fprintf(f, "%0.32f", (double) m / (double) denom);
                break;
            }
            case att_ff_type_double:
                fprintf(f, "%0.032f", v_dbl[i]);
                break;
            case att_ff_type_complex_fp:
                fprintf(f, "(%0.032f, %0.032f)", v_cplx_fp[i].re, v_cplx_fp[i].im);
                break;
            case att_ff_type_double_pair_ch_a:
                fprintf(f, "%0.032f", v_cplx_fp[i].re);
                break;
            case att_ff_type_double_pair_ch_b:
                fprintf(f, "%0.032f", v_cplx_fp[i].im);
                break;
        }

        if(i < len-1)
            fprintf(f, ", ");
    }

}


unsigned att_ff_open(
        att_ff_context_t* ctx,
        char** scope_stack,
        int* index_stack,
        const char max_scope_depth,
        const char *filename)
{
    FILE *ff;
    ff = fopen(filename, "wb");

    if (ff == NULL) {
        return 0;
    }

    ctx->file = ff;
    ctx->scope_stack = scope_stack;
    ctx->index_stack = index_stack;
    ctx->max_scope_depth = max_scope_depth;
    ctx->current_depth = -1;

    fprintf(ctx->file, "!VERSION: 0\n");
 
    return 1;
}

void att_ff_close(
        att_ff_context_t* ctx)
{
    fclose(ctx->file);
    ctx->file = NULL;
}

void att_ff_scope_push(
        att_ff_context_t* ctx,
        char* scope_name,
        const att_ff_index_type_t index_type)
{
    if(ctx->current_depth == ctx->max_scope_depth){
        printf("att_ff: error - max stack depth reached.\n");
        _Exit(1);
    }

    if(scope_name == NULL && index_type == ATT_FF_NO_INDEX){
        printf("att_ff: error - NULL scope must be indexed.\n");
        _Exit(1);
    }

    ctx->current_depth++;
    ctx->scope_stack[ctx->current_depth] = scope_name;
    ctx->index_stack[ctx->current_depth] = (int) index_type;
}

void att_ff_scope_pop(
        att_ff_context_t* ctx)
{  
    if(ctx->current_depth == -1){
        printf("att_ff: error - attempted to pop bottom of stack.\n");
        _Exit(1);
    }

    ctx->current_depth--;
}

void att_ff_index_set(
        att_ff_context_t* ctx,
        const int index)
{
    if(ctx->current_depth == -1){
        printf("att_ff: error - attempted to set index at bottom of stack.\n");
        _Exit(1);
    }

    ctx->index_stack[ctx->current_depth] = index;
}

void att_ff_index_increment(
        att_ff_context_t* ctx)
{
    if(ctx->current_depth == -1){
        printf("att_ff: error - attempted to increment index at bottom of stack.\n");
        _Exit(1);
    }

    ctx->index_stack[ctx->current_depth]++;
}

void att_ff_write_int(
        const att_ff_context_t* ctx,
        const char* name,
        const int value)
{
    int tmp[] = {value};
    write_full_scope(ctx, name);
    write_array(ctx, tmp, att_ff_type_s32, 1);
    fprintf(ctx->file, "\n");
}

void att_ff_write_double(
        const att_ff_context_t* ctx,
        const char* name,
        const double value)
{
    double tmp[] = {value};
    write_full_scope(ctx, name);
    write_array(ctx, tmp, att_ff_type_double, 1);
    fprintf(ctx->file, "\n");
}

void att_ff_write_scalar_indexed(
        const att_ff_context_t* ctx,
        const char* name,
        const void* value,
        const att_ff_type_t type,
        const int index)
{
    write_full_scope_indexed(ctx, name, index);
    write_array(ctx, value, type, 1);
    fprintf(ctx->file, "\n");
}

void att_ff_write_vector_indexed(
        const att_ff_context_t* ctx,
        const char* vec_name,
        const void* vector,
        const att_ff_type_t type,
        const unsigned len,
        const int index)
{
    int dims[] = {len};
    write_full_scope_indexed(ctx, vec_name, index);
    write_dimensions(ctx, dims, 1);
    write_array(ctx, vector, type, len);
    fprintf(ctx->file, "\n");
}

void att_ff_write_ndim_matrix_indexed(
        const att_ff_context_t* ctx,
        const char* mat_name,
        const void* matrix,
        const int* dimensions,
        const int dimension_count,
        const att_ff_type_t type,
        const int index)
{
    unsigned flat_len = 1;
    for(int i = 0; i < dimension_count; i++)
        flat_len *= dimensions[i];

    write_full_scope_indexed(ctx, mat_name, index);
    write_dimensions(ctx, dimensions, dimension_count);
    write_array(ctx, matrix, type, flat_len);
    fprintf(ctx->file, "\n");
}

void att_ff_write_scalar(
        const att_ff_context_t* ctx,
        const char* name,
        const void* value,
        const att_ff_type_t type)
{
    att_ff_write_scalar_indexed(ctx, name, value, type, -1);
}

void att_ff_write_vector(
        const att_ff_context_t* ctx,
        const char* vec_name,
        const void* vector,
        const att_ff_type_t type,
        const unsigned len)
{
    att_ff_write_vector_indexed(ctx, vec_name, vector, type, len, -1);
}

void att_ff_write_ndim_matrix(
        const att_ff_context_t* ctx,
        const char* mat_name,
        const void* matrix,
        const int* dimensions,
        const int dimension_count,
        const att_ff_type_t type)
{
    att_ff_write_ndim_matrix_indexed(ctx, mat_name, matrix, dimensions, dimension_count, type, -1);
}