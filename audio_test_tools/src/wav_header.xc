#include <string.h>
#include <stdio.h>
#include <fcntl.h>
#include <xclib.h>
#include <stdlib.h>
#include <unistd.h>
#include "audio_test_tools.h"

const char wav_default_header[ATT_WAV_HEADER_BYTES] = {
        0x52, 0x49, 0x46, 0x46,
        0x00, 0x00, 0x00, 0x00,
        0x57, 0x41, 0x56, 0x45,
        0x66, 0x6d, 0x74, 0x20,
        0x10, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x64, 0x61, 0x74, 0x61,
        0x00, 0x00, 0x00, 0x00,
};

#define RIFF_SECTION_SIZE (12)
#define FMT_SUBCHUNK_MIN_SIZE (24)

int att_get_wav_header_details(const char *filename, att_wav_header & s, unsigned &header_size){
  int fid = open ( filename , O_RDONLY );
  
  //read riff header section (12 bytes)
  read(fid, (char*)(&s.riff_header[0]), RIFF_SECTION_SIZE);

  if(memcmp(s.riff_header, "RIFF", 4) != 0)
  {
    printf("Error: couldn't find RIFF: 0x%x, 0x%x, 0x%x, 0x%x\n", s.riff_header[0], s.riff_header[1], s.riff_header[2], s.riff_header[3]);
    return 1;
  }

  if(memcmp(s.wave_header, "WAVE", 4) != 0)
  {
    printf("couldn't find WAVE:, 0x%x, 0x%x, 0x%x, 0x%x\n", s.wave_header[0], s.wave_header[1], s.wave_header[2], s.wave_header[3]);
    return 1;
  }
  
  //read fmt subchunk (24, 26 or 48 bytes depending on the extension). We read 24 bytes since this covers all information common to all 3 types 
  read(fid, (char*)&s.fmt_header[0], FMT_SUBCHUNK_MIN_SIZE);
  if(memcmp(s.fmt_header, "fmt ", 4) != 0)
  {
    printf("Error: couldn't find fmt: 0x%x, 0x%x, 0x%x, 0x%x\n", s.fmt_header[0], s.fmt_header[1], s.fmt_header[2], s.fmt_header[3]);
    return 1;
  }
  
  unsigned fmt_subchunk_actual_size = s.fmt_chunk_size + 8; //fmt_chunk_size doesn't include the fmt_header(4) and size(4) bytes
  unsigned fmt_subchunk_remaining_size = fmt_subchunk_actual_size - FMT_SUBCHUNK_MIN_SIZE;
  //go back to the beginning of fmt subchunk (24 bytes) and then go forward fmt_chunk_size + 8
  if(s.audio_format == (short)0xfffe)
  {
    //seek to the end of fmt subchunk and rewind 16bytes to the beginning of GUID
    lseek(fid, fmt_subchunk_remaining_size - 16, SEEK_CUR);
    //The first 2 bytes of GUID is the audio_format.
    read(fid, &s.audio_format, 2);
    //skip the rest of GUID
    lseek(fid, 14, SEEK_CUR);
  }
  else
  {
    lseek(fid, fmt_subchunk_remaining_size, SEEK_CUR);
  }

  if(s.audio_format != 1)
  {
    printf("Error: audio format(%d) is not PCM\n", s.audio_format);
    return 1;
  }
  
  //read header (4 bytes) for the next subchunk
  read(fid, (char*)&s.data_header[0], 4);
  //if next subchunk is fact, read subchunk size and skip it
  if(memcmp(s.data_header, "fact", 4) == 0)
  {
    uint32_t chunksize;
    read(fid, &chunksize, 4);
    lseek(fid, chunksize, SEEK_CUR);
    read(fid, (char*)(&s.data_header[0]), 4);
  }
  //only thing expected at this point is the 'data' subchunk. Throw error if not found.
  if(memcmp(s.data_header, "data", 4) != 0)
  {
    printf("Error: couldn't find data: 0x%x, 0x%x, 0x%x, 0x%x\n", s.data_header[0], s.data_header[1], s.data_header[2], s.data_header[3]);
    return 1;
  }
  //read data subchunk size. 
  read(fid, &s.data_bytes, 4);
  header_size = lseek(fid, 0, SEEK_CUR); //total file size should be header_size + data_bytes

  close(fid);
  return 0;
}

int att_wav_form_header(att_wav_header & header,
        short audio_format,
        short num_channels,
        int sample_rate,
        short bit_depth,
        int num_frames){
    memcpy((char*)&header, wav_default_header, ATT_WAV_HEADER_BYTES);

    header.audio_format = audio_format;
    header.num_channels = num_channels;
    header.sample_rate = sample_rate;
    header.bit_depth = bit_depth;

    header.byte_rate = sample_rate*bit_depth*num_channels/8;

    header.sample_alignment = num_channels* (bit_depth/8);
    int data_bytes = num_frames * num_channels * (bit_depth/8);
    header.data_bytes = data_bytes;
    header.wav_size = data_bytes + ATT_WAV_HEADER_BYTES - 8;

    return 0;
}

void att_wav_print_header(att_wav_header & s){
  printf("\nin att_wav_print_header()\n");

    for(unsigned i=0;i<4;i++)
        printf("%c", s.riff_header[i]);
    printf("\n");
    printf("wav_size: %d\n", s.wav_size);
    for(unsigned i=0;i<4;i++)
        printf("%c", s.wave_header[i]);
    printf("\n");
    for(unsigned i=0;i<4;i++)
        printf("%c", s.fmt_header[i]);
    printf("\n");
    printf("fmt_chunk_size: %d\n", s.fmt_chunk_size);

    switch(s.audio_format){
    case (short)0x1:
        printf("WAVE_FORMAT_PCM\n");
        break;
    case (short)0x3:
        printf("WAVE_FORMAT_IEEE_FLOAT\n");
        break;
    case (short)0x6:
        printf("WAVE_FORMAT_ALAW\n");
        break;
    case (short)0x7:
        printf("WAVE_FORMAT_MULAW\n");
        break;
    case (short)0xFFFE:
        printf("WAVE_FORMAT_EXTENDED\n");
        break;
    default:
        printf("invalid (%x)\n", s.audio_format);
        break;
    }

    printf("num_channels: %d\n", s.num_channels);
    printf("sample_rate: %d\n", s.sample_rate);
    printf("byte_rate: %d\n", s.byte_rate);
    printf("sample_alignment: %d\n", s.sample_alignment);
    printf("bit_depth: %d\n", s.bit_depth);
    for(unsigned i=0;i<4;i++)
        printf("%c", s.data_header[i]);
    printf("\n");
    printf("data_bytes: %d\n", s.data_bytes);

    int num_samples = s.data_bytes / (s.bit_depth/CHAR_BIT);
    int num_frames = num_samples / s.num_channels;
    printf("number of samples: %d\n", num_samples);
    printf("number of frames: %d\n", num_frames);
    printf("file length: %f seconds\n", (float)num_frames / (float)s.sample_rate);
    printf("out of att_wav_print_header()\n");

//    for(unsigned i=0;i<ATT_WAV_HEADER_BYTES;i++)
//        printf("%02x ", ((char*)&s)[i]);
//    printf("\n");

}

unsigned att_wav_get_num_bytes_per_frame(att_wav_header &s){
    int bytes_per_sample = s.bit_depth/CHAR_BIT;
    return (unsigned)(bytes_per_sample * s.num_channels);
}

int att_wav_get_num_frames(att_wav_header &s){
    unsigned bytes_per_frame = att_wav_get_num_bytes_per_frame(s);
    return s.data_bytes / bytes_per_frame;
}

long att_wav_get_frame_start(att_wav_header &s, unsigned frame_number, uint32_t wavheader_size){
    return wavheader_size + frame_number * att_wav_get_num_bytes_per_frame(s);
}

