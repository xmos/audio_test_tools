/*
 * frame_file.c
 *
 *  Created on: May 3, 2019
 *      Author: mbruno
 */

#include "frame_file.h"

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

FILE *att_ff_open(
        const char *filename,
        const char *testname)
{
    FILE *ff;

    ff = fopen(filename, "wb");

    if (ff != NULL) {

        fprintf(ff, "ATT_FF\nTEST: %s\n\n", testname);
    }

    return ff;
}

void att_ff_close(
        FILE *ff)
{
    fclose(ff);
}

void att_ff_frame_start(
        FILE *ff,
        unsigned int frame_num)
{
    fprintf(ff, "FRAME: %u\n", frame_num);
}

void att_ff_frame_end(
        FILE *ff)
{
    fprintf(ff, "FRAME END\n\n");
}

void att_ff_array_write(
        FILE *ff,
        const char *array_name,
        void *a,
        att_ff_type_t type,
        unsigned int len)
{
    fprintf(ff, "DATA: %s:\n", array_name);
    for (int i = 0; i < len; i++) {

        switch (type) {
        case att_ff_type_s16: {
            int16_t *a_s16 = (int16_t *) a;
            fprintf(ff, "%hd", a_s16[i]);
            break;
        }
        case att_ff_type_u16: {
            uint16_t *a_u16 = (uint16_t *) a;
            fprintf(ff, "%hu", a_u16[i]);
            break;
        }
        case att_ff_type_s32: {
            int32_t *a_s32 = (int32_t *) a;
            fprintf(ff, "%d", (int) a_s32[i]);
            break;
        }
        case att_ff_type_u32: {
            uint32_t *a_u32 = (uint32_t *) a;
            fprintf(ff, "%u", (int) a_u32[i]);
            break;
        }
        case att_ff_type_float: {
            vtb_s32_float_t *a_f = (vtb_s32_float_t *) a;
            fprintf(ff, "%.3f", (double) a_f[i].m / (double) (uint32_t) (1 << -a_f[i].e));
            break;
        }
        }


        if (i < len - 1) {
            fprintf(ff, ",%s", (i & 0xF) == 0xF ? "\n" : " ");
        }
    }
    fprintf(ff, "\n");
}

