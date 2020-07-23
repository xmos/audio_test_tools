#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include "xscope_endpoint.h"
#include "unistd.h"

#define BLOCK_SIZE_BYTES        (240 * 4 * 4)
#define MAX_XSCOPE_SIZE_BYTES   256
#define END_MARKER_STRING   "finally_the_end!"
#define END_MARKER_LEN      (sizeof(END_MARKER_STRING) - 1)

FILE *fpw = NULL;
static volatile unsigned int running = 1;
static volatile unsigned total_bytes_written = 0;
pthread_mutex_t lock;
static volatile int flow_counter = 0;

void init_out_file(const char *file_name){
    fpw = fopen(file_name, "wb");
    assert(fpw);
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
        return;
    }
    if(id == 1)
    {
        running = 0;
        return;
    }
    else if(id == 0){
        fwrite(databytes, 1, length, fpw);
        total_bytes_written += length;
        printf("Host: written %u bytes to file (%u)\n", length, total_bytes_written);
    }
    else{
        float mstimestamp = timestamp / 1000000000.0f;
        printf("Host: xSCOPE record event (id [%u] length [%u]\n", id, length);
    }
}

void send_file(const char *name)
{
    unsigned char buf[BLOCK_SIZE_BYTES];
    unsigned total_bytes_read = 0;
    FILE *fp = fopen(name, "rb");
    assert(fp);

    unsigned n_bytes_read = 0;
    do
    {
        while(flow_counter <= 0);

        n_bytes_read = fread(buf, 1, sizeof(buf), fp);
        assert(n_bytes_read <= BLOCK_SIZE_BYTES);
        for(unsigned idx = 0; idx < n_bytes_read / MAX_XSCOPE_SIZE_BYTES; idx++){
            xscope_ep_request_upload(MAX_XSCOPE_SIZE_BYTES, &buf[idx * MAX_XSCOPE_SIZE_BYTES]);
        }
        unsigned left_over = n_bytes_read % MAX_XSCOPE_SIZE_BYTES;
        if(left_over){
            xscope_ep_request_upload(left_over, &buf[n_bytes_read / MAX_XSCOPE_SIZE_BYTES]);
        }
        total_bytes_read += n_bytes_read;
        
        pthread_mutex_lock(&lock);
        flow_counter--;
        pthread_mutex_unlock(&lock);

        printf("Host: sent block %u (total: %u) (flow_counter: %d)\n", n_bytes_read, total_bytes_read, flow_counter);
    } 
    while (n_bytes_read);
    const char end_sting[] = END_MARKER_STRING;
    xscope_ep_request_upload(END_MARKER_LEN, (const unsigned char *)end_sting); //End
    assert(feof(fp) && !ferror(fp));
    printf("Host: sent %u bytes\n", total_bytes_read);
fclose(fp);
}

int main(int argc, char *argv[])
{
    pthread_mutex_init(&lock, NULL);

    assert(argc == 3);
    char *out_file = malloc(strlen(argv[1]) + 10);
    strcpy(out_file, argv[1]);
    strcat(out_file, "2");


    xscope_ep_set_print_cb(xscope_print);
    xscope_ep_set_register_cb(xscope_register);
    xscope_ep_set_record_cb(xscope_record);
    xscope_ep_connect("localhost", argv[2]);

    init_out_file(out_file);
    send_file(argv[1]);

    while(running){
        usleep(10000); //Back off for 10ms to reduce processor usage
    }
    close_out_file();
    free(out_file);
    pthread_mutex_destroy(&lock);
    printf("Host: Exit received, %u bytes written\n", total_bytes_written);
    return 0;
}

