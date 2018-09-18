// Copyright (c) 2017-2018, XMOS Ltd, All rights reserved

#include <fcntl.h>
#include <xclib.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "audio_test_tools.h"


void process_wav(const char* input_file_1, const char* input_file_2, const char* output_file_1, const char* output_file_2){

    int file1, file2, out_file1, out_file2;
    att_wav_header output_header_struct;
    int i;

    file1 = open ( input_file_1, O_RDONLY );
    file2 = open ( input_file_2, O_RDONLY );
    out_file1 = open ( output_file_1 , O_WRONLY|O_CREAT, 0644 );
    out_file2 = open ( output_file_2 , O_WRONLY|O_CREAT, 0644 );

    if ((file1==-1)) {
        printf("file1 missing\n");
        _Exit(1);
    }

    if ((file2==-1)) {
        printf("file2 missing\n");
        _Exit(1);
    }


    att_wav_header header_struct_1;
    att_wav_header header_struct_2;
    unsigned size_header_1, size_header_2;
    printf("parse %s\n", input_file_1);
    if(att_get_wav_header_details("test_audio_16b.wav", header_struct_1, size_header_1) != 0)
    {
      printf("error in att_get_wav_header_details()\n");
      _Exit(1);
    }
    printf("parse %s\n", input_file_2);
    if(att_get_wav_header_details("test_audio_32b.wav", header_struct_2, size_header_2) != 0)
    {
      printf("error in att_get_wav_header_details()\n");
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

    att_wav_form_header(output_header_struct,
            header_struct_1.audio_format,
            header_struct_1.num_channels,
            header_struct_1.sample_rate,
            header_struct_1.bit_depth,
            att_wav_get_num_frames(header_struct_1));

    write(out_file1, (char*)&output_header_struct,  ATT_WAV_HEADER_BYTES);
    for(i=0; i<header_struct_1.data_bytes; i++)
    {
      char temp;
      read(file1, &temp, 1);
      write(out_file1, &temp, 1);
    }

    att_wav_form_header(output_header_struct,
            header_struct_2.audio_format,
            header_struct_2.num_channels,
            header_struct_2.sample_rate,
            header_struct_2.bit_depth,
            att_wav_get_num_frames(header_struct_2));

    write(out_file2, (char*)&output_header_struct,  ATT_WAV_HEADER_BYTES);
    for(i=0; i<header_struct_2.data_bytes; i++)
    {
      char temp;
      read(file2, &temp, 1);
      write(out_file2, &temp, 1);
    }
    close(file1);
    close(file2);
    close(out_file1);
    close(out_file2);

    _Exit(0);
}

int main(unsigned int argC, char *unsafe argV[argC]){
    process_wav((char *)argV[1], (char *)argV[2], (char *)argV[3], (char *)argV[4]);
    return 0;
}
