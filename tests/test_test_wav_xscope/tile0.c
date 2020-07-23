#include <platform.h>
#include <print.h>
#include <string.h>
#include <stdlib.h>
#include <xcore/assert.h>
#include <xcore/channel.h>
#include <xcore/chanend.h>
#include <xcore/channel_transaction.h>
#include <xcore/parallel.h>
#include <xcore/select.h>
#include <xcore/hwtimer.h>
#include <xscope.h>
#include <stdio.h>

#define BLOCK_SIZE_BYTES    (240 * 4 * 4)
#define MAX_XSCOPE_SIZE_BYTES   256
#define END_MARKER_STRING   "finally_the_end!"
#define END_MARKER_LEN      (sizeof(END_MARKER_STRING) - 1)


DECLARE_JOB(xscope_read_file, (chanend_t, chanend_t));
void xscope_read_file(chanend_t c_xscope, chanend_t c_app_in)
{
    printf("xscope_read_file..\n");
    xscope_connect_data_from_host(c_xscope);

    unsigned total_bytes_read = 0;
    unsigned end_marker_found = 0;
    unsigned chunk_bytes_so_far = 0;

    // Queue up a few requests for file data so that the H->D buffer is always full
    // We will request more after each block is processed. We do this because
    // xscope seems unstable if we hammer it too hard with data sand rely on the chunk_buffer
    for (int i=0; i<4;i++) xscope_int(2, 0);

    do
    {
        unsigned chunk_complete = 0;
        chunk_bytes_so_far = 0;
        char block_buffer[BLOCK_SIZE_BYTES];
        char chunk_buffer[MAX_XSCOPE_SIZE_BYTES];
        do
        {
            int bytes_read = 0;
            SELECT_RES(CASE_THEN(c_xscope, read_host_data))
            {
            read_host_data:
                {
                    xscope_data_from_host(c_xscope, chunk_buffer, &bytes_read);
                    memcpy(&block_buffer[chunk_bytes_so_far], chunk_buffer, bytes_read);
                    chunk_bytes_so_far += bytes_read;
                    total_bytes_read += bytes_read;
                    break;
                }
            }

            end_marker_found = ((bytes_read == END_MARKER_LEN) && !memcmp(chunk_buffer, END_MARKER_STRING, END_MARKER_LEN)) ? 1 : 0;
            if(end_marker_found){
                chunk_bytes_so_far -= bytes_read;
                total_bytes_read -= bytes_read;
            }

            if(chunk_bytes_so_far == BLOCK_SIZE_BYTES || end_marker_found){
                chunk_complete = 1;
            }
        } while(!chunk_complete);

        if(chunk_bytes_so_far){
            //request more data 
            xscope_int(2, 0);
            // printf("Received: %u bytes\n", chunk_bytes_so_far);

            transacting_chanend_t tc = chan_init_transaction_master(c_app_in);
            t_chan_out_word(&tc, chunk_bytes_so_far);
            t_chan_out_buf_byte(&tc, (const uint8_t*)block_buffer, chunk_bytes_so_far);
            chan_complete_transaction(tc);
        }


    } while(!end_marker_found);

    transacting_chanend_t tc = chan_init_transaction_master(c_app_in);
    t_chan_out_word(&tc, 0);
    chan_complete_transaction(tc);

    printf("Finished reading from host; bytes read: %u\n", total_bytes_read);
}

DECLARE_JOB(app, (chanend_t, chanend_t));
void app(chanend_t c_app_in, chanend_t c_app_out){
    printf("app..\n");
    unsigned running = 1;
    do
    {
        unsigned char buffer[BLOCK_SIZE_BYTES];

        transacting_chanend_t tc = chan_init_transaction_slave(c_app_in);
        unsigned size = t_chan_in_word(&tc);
        if(size == 0) running = 0;
        t_chan_in_buf_byte(&tc, buffer, size);
        chan_complete_transaction(tc); 

        //Simulate some DSP
        // delay_milliseconds(15);

        tc = chan_init_transaction_master(c_app_out);
        t_chan_out_word(&tc, size);
        t_chan_out_buf_byte(&tc, buffer, size);
        chan_complete_transaction(tc);
    }
    while(running);
    printf("App received zero size - quitting\n");
}

DECLARE_JOB(xscope_write_file, (chanend_t));
void xscope_write_file(chanend_t c_app_out)
{
    printf("xscope_write_file..\n");

    unsigned char buffer[BLOCK_SIZE_BYTES];
    unsigned running = 1;
    do{
        transacting_chanend_t tc = chan_init_transaction_slave(c_app_out);
        unsigned size = t_chan_in_word(&tc);
        if(!size) running = 0;
        t_chan_in_buf_byte(&tc, buffer, size);
        chan_complete_transaction(tc); 

        //Chunk it up
        unsigned sent_so_far = 0;
        do{
            if(size - sent_so_far >=  MAX_XSCOPE_SIZE_BYTES){
                xscope_bytes(0, MAX_XSCOPE_SIZE_BYTES, &buffer[sent_so_far]);
                sent_so_far += MAX_XSCOPE_SIZE_BYTES;
            }
            else{
                xscope_bytes(0, size - sent_so_far, &buffer[sent_so_far]);
                sent_so_far = size;
            }
            hwtimer_t tmr = hwtimer_alloc();
            hwtimer_delay(tmr, 10000); /// Magic number found to make xscope stable on MAC, else you get WRITE ERROR ON UPLOAD ....
            hwtimer_free(tmr);
        }
        while (sent_so_far < size);
    }
    while(running);
    printf("xscope_write_file received zero size - quitting\n");
}


void main_tile0(chanend_t xscope_end, chanend_t memshare_end)
{
    xscope_mode_lossless();
    printf("Starting app and testing if printing works ok..\n");

    chanend_t c_app_in_a=chanend_alloc(), c_app_in_b=chanend_alloc();
    chanend_t c_app_out_a=chanend_alloc(), c_app_out_b=chanend_alloc();
    chanend_set_dest(c_app_in_a, c_app_in_b);
    chanend_set_dest(c_app_in_b, c_app_in_a);
    chanend_set_dest(c_app_out_a, c_app_out_b);
    chanend_set_dest(c_app_out_b, c_app_out_a);

    PAR_JOBS(
        PJOB(xscope_read_file, (xscope_end, c_app_in_a)),
        PJOB(app, (c_app_in_b, c_app_out_a)),
        PJOB(xscope_write_file, (c_app_out_b))
    );

    printf("tile0 done.\n");
    //exit
    xscope_int(1, 0);
    hwtimer_t tmr = hwtimer_alloc();
    hwtimer_delay(tmr, 10000000); //100ms
    hwtimer_free(tmr);
    exit(0);
}

