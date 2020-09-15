// Copyright (c) 2020, XMOS Ltd, All rights reserved
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include "xscope_endpoint.h"
#include "unistd.h"
#include "xscope_settings.h"

// This is arbitraty size above 256B. We just set to typical 4ch setting. It defines how much we read from ip/file each block
#define INPUT_BLOCK_SIZE_BYTES  (240 * 4 * 4)

FILE *fpw = NULL;
static volatile unsigned int running = 1;
pthread_mutex_t lock;
static volatile int flow_counter = 0;

static volatile unsigned total_bytes_written = 0;

const unsigned megabyte = 1024 * 1024; //1MB
static volatile unsigned file_progress = 0;

//Note ftell can only handle 2^31 - 1 = 2GB files and so this cannot handle more than
//2^31 / (16000 * 4 * 4) = 8338s or 139 minutes
static volatile unsigned total_bytes_read = 0;
static volatile unsigned read_file_size = 0;

#define VERBOSE 0

void init_out_file(const char *file_name){
    fpw = fopen(file_name, "wb");
    if(!fpw){
        printf("Cannot open %s\n", file_name);
        assert(0);
    }
}

void close_out_file(void){
    fclose(fpw);
}

void xscope_print(
  unsigned long long timestamp,
  unsigned int length,
  unsigned char *data)
{
  if (length) {
    printf("Device: ");
    for (int i = 0; i < length; i++)
      printf("%c", *(&data[i]));
  }
}

void xscope_register(
  unsigned int id,
  unsigned int type,
  unsigned int r,
  unsigned int g,
  unsigned int b,
  unsigned char *name,
  unsigned char *unit,
  unsigned int data_type,
  unsigned char *data_name)
{
  printf("Host: xSCOPE register event (id [%d] name [%s])\n", id, name);
}

void xscope_record(
  unsigned int id,
  unsigned long long timestamp,
  unsigned int length,
  unsigned long long dataval,
  unsigned char *databytes)
{
    if(id == 2)
    {
        pthread_mutex_lock(&lock);
        flow_counter++;
        pthread_mutex_unlock(&lock);
        // printf("Host: more!\n");
        return;
    }
    else if(id == 1)
    {
        running = 0;
        return;
    }
    else if(id == 0){
        fwrite(databytes, 1, length, fpw);
        total_bytes_written += length;
        // printf("Host: written %u bytes to file (%u)\n", length, total_bytes_written);

        if(total_bytes_written - file_progress > megabyte){
            file_progress += megabyte;
            printf("Host read total: %uMB of %uMB, written %uMB\n", file_progress/megabyte,
                                                                   read_file_size/megabyte,
                                                                   total_bytes_written/megabyte);
        }
    }
    else{
        float mstimestamp = timestamp / 1000000000.0f;
        printf("Host: xSCOPE record event (id [%u] length [%u]\n", id, length);
    }
}

unsigned send_file(const char *name)
{
    unsigned char buf[INPUT_BLOCK_SIZE_BYTES];
    FILE *fp = fopen(name, "rb");
    if(!fp){
        printf("Cannot open %s\n", name);
        assert(0);
    }

    fseek(fp, 0L, SEEK_END); 
    read_file_size = ftell(fp);
    rewind(fp);

    unsigned n_bytes_read = 0;
    do
    {
        while(flow_counter <= 0);

        n_bytes_read = fread(buf, 1, sizeof(buf), fp);
        assert(n_bytes_read <= INPUT_BLOCK_SIZE_BYTES);
        for(unsigned idx = 0; idx < n_bytes_read / MAX_XSCOPE_SIZE_BYTES; idx++){
            int ret = xscope_ep_request_upload(MAX_XSCOPE_SIZE_BYTES, &buf[idx * MAX_XSCOPE_SIZE_BYTES]);
            if(ret) printf("Error, ret: %d\n", ret);
        }
        unsigned left_over = n_bytes_read % MAX_XSCOPE_SIZE_BYTES;
        if(left_over){
            int ret = xscope_ep_request_upload(left_over, &buf[(n_bytes_read / MAX_XSCOPE_SIZE_BYTES) * MAX_XSCOPE_SIZE_BYTES]);
            if(ret) printf("Error, ret: %d\n", ret);
        }
        total_bytes_read += n_bytes_read;
        
        pthread_mutex_lock(&lock);
        flow_counter--;
        pthread_mutex_unlock(&lock);

        if(VERBOSE){
            printf("Host: sent block %u (total: %u) (flow_counter: %d)\n", n_bytes_read, total_bytes_read, flow_counter);
        }
    }

    while (n_bytes_read);
    const char end_sting[] = END_MARKER_STRING;
    xscope_ep_request_upload(END_MARKER_LEN, (const unsigned char *)end_sting); //End
    assert(feof(fp) && !ferror(fp));
    // printf("Host: sent %u bytes\n", total_bytes_read);
    fclose(fp);
    return total_bytes_read;
}

int main(int argc, char *argv[])
{
    if (argc != 4){
        fprintf(stderr, "%s <infile.raw> <outfile.raw> <port>\n", argv[0]);
        exit(-1);
    }

    pthread_mutex_init(&lock, NULL);

    xscope_ep_set_print_cb(xscope_print);
    xscope_ep_set_register_cb(xscope_register);
    xscope_ep_set_record_cb(xscope_record);
    if(xscope_ep_connect("localhost", argv[3])){
        printf("ERROR: connecting to xscope server on port: %s\n", argv[3]);
        return -1;
    }

    init_out_file(argv[2]);
    unsigned total_bytes_read = send_file(argv[1]);

    while(running){
        usleep(10000); //Back off for 10ms to reduce processor usage
    }
    close_out_file();
    pthread_mutex_destroy(&lock);
    printf("Host: Exit received, %u bytes sent, %u bytes written (%u truncated due to framing)\n",
                       total_bytes_read, total_bytes_written, total_bytes_read-total_bytes_written);
    return 0;
}

