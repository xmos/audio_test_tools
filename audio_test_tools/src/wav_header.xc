#include <string.h>
#include <stdio.h>
#include "audio_test_tools.h"

const char wav_default_header[WAV_HEADER_BYTES] = {
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

int att_wav_header_to_struct(att_wav_header & s, char header[MAX_WAV_HEADER_BYTES], uint32_t &header_size){
  int read_offset = 0;
  unsafe
  {
    char * unsafe a =(char*)(&s.riff_header[0]); 
    memcpy(a, header, 12);
  }

  read_offset += 12;
  if( (s.riff_header[0]!='R') ||
      (s.riff_header[1]!='I') ||
      (s.riff_header[2]!='F') ||
      (s.riff_header[3]!='F') )
  {
    printf("couldn't find RIFF :(, 0x%x, 0x%x, 0x%x, 0x%x\n", s.riff_header[0], s.riff_header[1], s.riff_header[2], s.riff_header[3]);
    return 1;
  }

  if( (s.wave_header[0]!='W') ||
      (s.wave_header[1]!='A') ||
      (s.wave_header[2]!='V') ||
      (s.wave_header[3]!='E') ){
    printf("couldn't find WAVE :(, 0x%x, 0x%x, 0x%x, 0x%x\n", s.wave_header[0], s.wave_header[1], s.wave_header[2], s.wave_header[3]);
    return 1;
  }
  unsafe
  { 
    char * unsafe a = (char*)&s.fmt_header[0];
    memcpy(a, &header[read_offset], 24);
  }
  read_offset += 24;
  if( (s.fmt_header[0]!='f') ||
      (s.fmt_header[1]!='m') ||
      (s.fmt_header[2]!='t') ||
      (s.fmt_header[3]!=' ') )
  {
    printf("couldn't find fmt :(, 0x%x, 0x%x, 0x%x, 0x%x\n", s.fmt_header[0], s.fmt_header[1], s.fmt_header[2], s.fmt_header[3]);
    return 1;
  }

  //go back to the beginning of fmt subchunk (24 bytes) and then go forward fmt_chunk_size + 8
  if(s.audio_format == (short)0xfffe)
  {
    read_offset = read_offset - 24 + s.fmt_chunk_size + 8; //go to end of fmt subchunk
    //rewind 16 bytes to read the audio_format
    read_offset -= 16;
    memcpy(&s.audio_format, &header[read_offset], 2);
    read_offset += 16;
  }
  else
  {
    read_offset = read_offset - 24 + s.fmt_chunk_size + 8; //go to end of fmt subchunk
  }

  unsafe
  { 
    char * unsafe a = (char*)&s.data_header[0];
    memcpy(a, &header[read_offset], 4);
  }
  read_offset += 4;
  //check if this is the 'fact' chunk
  if( (s.data_header[0]=='f') &&
      (s.data_header[1]=='a') &&
      (s.data_header[2]=='c') &&
      (s.data_header[3]=='t') )
  {
    uint32_t chunksize;
    memcpy(&chunksize, &header[read_offset], 4);
    read_offset += (4 + chunksize);
    memcpy((char*)(&s.data_header[0]), &header[read_offset], 4);
    read_offset += 4;
  }
  if( (s.data_header[0]!='d') ||
      (s.data_header[1]!='a') ||
      (s.data_header[2]!='t') ||
      (s.data_header[3]!='a') )
  {
    printf("couldn't find data :(, 0x%x, 0x%x, 0x%x, 0x%x\n", s.data_header[0], s.data_header[1], s.data_header[2], s.data_header[3]);
    return 1;
  }
  memcpy(&s.data_bytes, &header[read_offset], 4);
  read_offset += 4;
  header_size = read_offset;
  return 0;
}

int att_wav_form_header(char header[MAX_WAV_HEADER_BYTES],
        short audio_format,
        short num_channels,
        int sample_rate,
        short bit_depth,
        int num_frames){
    memcpy(header, wav_default_header, WAV_HEADER_BYTES);

    (header, att_wav_header).audio_format = audio_format;
    (header, att_wav_header).num_channels = num_channels;
    (header, att_wav_header).sample_rate = sample_rate;
    (header, att_wav_header).bit_depth = bit_depth;

    (header, att_wav_header).byte_rate = sample_rate*bit_depth*num_channels/8;

    (header, att_wav_header).sample_alignment = num_channels* (bit_depth/8);
    int data_bytes = num_frames * num_channels * (bit_depth/8);
    (header, att_wav_header).data_bytes = data_bytes;
    (header, att_wav_header).wav_size = data_bytes + WAV_HEADER_BYTES - 8;

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

//    for(unsigned i=0;i<WAV_HEADER_BYTES;i++)
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

