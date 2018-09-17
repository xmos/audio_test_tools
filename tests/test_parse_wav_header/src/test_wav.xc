// Copyright (c) 2017-2018, XMOS Ltd, All rights reserved

#include <fcntl.h>
#include <xclib.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "audio_test_tools.h"


void process_wav(){

    int file1, file2;

    file1 = open ( "test_audio_16b.wav" , O_RDONLY );
    file2 = open ( "test_audio_32b.wav" , O_RDONLY );

    if ((file1==-1)) {
        printf("file1 missing\n");
        _Exit(1);
    }

    if ((file2==-1)) {
        printf("file2 missing\n");
        _Exit(1);
    }

    char header_1[MAX_WAV_HEADER_BYTES], header_2[MAX_WAV_HEADER_BYTES];
    read (file1, header_1, MAX_WAV_HEADER_BYTES);
    read (file2, header_2, MAX_WAV_HEADER_BYTES);

    att_wav_header header_struct_1;
    att_wav_header header_struct_2;
    uint32_t size_header_1, size_header_2;
    if(att_wav_header_to_struct(header_struct_1, header_1, size_header_1) != 0)
    {
      printf("error in att_wav_header_to_struct()\n");
      _Exit(1);
    }
    if(att_wav_header_to_struct(header_struct_2, header_2, size_header_2) != 0)
    {
      printf("error in att_wav_header_to_struct()\n");
      _Exit(1);
    }

    if((size_header_1 != 44) || (size_header_2 != 80))
    {
      printf("error in header parsing. size_header_1 = %d, size_header_2 = %d\n", size_header_1, size_header_2);
      _Exit(1);
    }

    if((header_struct_1.audio_format != 0x1) || (header_struct_2.audio_format != 0x1))
    {
      printf("error in audio_format parsing (%d, %d)\n", header_struct_1.audio_format, header_struct_2.audio_format);
      _Exit(1);
    }
    if((header_struct_1.num_channels != 0x2) || (header_struct_2.num_channels != 0x2))
    {
      printf("error in num_channels parsing (%d, %d)\n", header_struct_1.num_channels, header_struct_2.num_channels);
      _Exit(1);
    }
    if((header_struct_1.sample_rate != 16000) || (header_struct_2.sample_rate != 16000))
    {
      printf("error in sample_rate parsing (%d, %d)\n", header_struct_1.sample_rate, header_struct_2.sample_rate);
      _Exit(1);
    }
    if((header_struct_1.byte_rate != 64000) || (header_struct_2.byte_rate != 128000))
    {
      printf("error in byte_rate parsing (%d, %d)\n", header_struct_1.byte_rate, header_struct_2.byte_rate);
      _Exit(1);
    }
    if((header_struct_1.bit_depth != 16) || (header_struct_2.bit_depth != 32))
    {
      printf("error in bit_depth parsing (%d, %d)\n", header_struct_1.bit_depth, header_struct_2.bit_depth);
      _Exit(1);
    }
    if((header_struct_1.data_bytes != 64) || (header_struct_2.data_bytes != 128))
    {
      printf("error in data_bytes parsing (%d, %d)\n", header_struct_1.data_bytes, header_struct_2.data_bytes);
      _Exit(1);
    }
    
    lseek (file1, size_header_1, SEEK_SET);
    lseek (file2, size_header_2, SEEK_SET);        

    _Exit(0);
}

int main(unsigned int argC, char *unsafe argV[argC]){
    process_wav();
    return 0;
}
