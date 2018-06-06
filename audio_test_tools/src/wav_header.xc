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

int wav_header_to_struct(wav_header & s, char header[WAV_HEADER_BYTES]){


    memcpy(&s, header, WAV_HEADER_BYTES);

    if( (s.riff_header[0]!='R') ||
        (s.riff_header[1]!='I') ||
        (s.riff_header[2]!='F') ||
        (s.riff_header[3]!='F') ){
        memset(&s, 0, sizeof(s));
        return 1;
    }
    if( (s.wave_header[0]!='W') ||
        (s.wave_header[1]!='A') ||
        (s.wave_header[2]!='V') ||
        (s.wave_header[3]!='E') ){
        memset(&s, 0, sizeof(s));
        return 1;
    }
    if( (s.fmt_header[0]!='f') ||
        (s.fmt_header[1]!='m') ||
        (s.fmt_header[2]!='t') ||
        (s.fmt_header[3]!=' ') ){
        memset(&s, 0, sizeof(s));
        return 1;
    }
    if( (s.data_header[0]!='d') ||
        (s.data_header[1]!='a') ||
        (s.data_header[2]!='t') ||
        (s.data_header[3]!='a') ){
        memset(&s, 0, sizeof(s));
        return 1;
    }
    return 0;
}

int wav_form_header(char header[WAV_HEADER_BYTES],
        short audio_format,
        short num_channels,
        int sample_rate,
        short bit_depth,
        int num_frames){
    memcpy(header, wav_default_header, WAV_HEADER_BYTES);

    (header, wav_header).audio_format = audio_format;
    (header, wav_header).num_channels = num_channels;
    (header, wav_header).sample_rate = sample_rate;
    (header, wav_header).bit_depth = bit_depth;

    (header, wav_header).sample_alignment = num_channels* (bit_depth/8);
    int data_bytes = num_frames * num_channels * (bit_depth/8);
    (header, wav_header).data_bytes = data_bytes;
    (header, wav_header).wav_size = data_bytes + WAV_HEADER_BYTES - 8;

    return 0;
}

void wav_print_header(wav_header & s){

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

    printf("audio_format: ");
    switch(s.audio_format){
    case 0x1:
        printf("WAVE_FORMAT_PCM\n");
        break;
    case 0x3:
        printf("WAVE_FORMAT_IEEE_FLOAT\n");
        break;
    case 0x6:
        printf("WAVE_FORMAT_ALAW\n");
        break;
    case 0x7:
        printf("WAVE_FORMAT_MULAW\n");
        break;
    case 0xFFFE:
        printf("WAVE_FORMAT_MULAW\n");
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
}

unsigned wav_get_num_bytes_per_frame(wav_header &s){
    int bytes_per_sample = s.bit_depth/CHAR_BIT;
    return (unsigned)(bytes_per_sample * s.num_channels);
}

int wav_get_num_frames(wav_header &s){
    unsigned bytes_per_frame = wav_get_num_bytes_per_frame(s);
    return s.data_bytes / bytes_per_frame;
}

long wav_get_frame_start(wav_header &s, unsigned frame_number){
    return WAV_HEADER_BYTES + frame_number * wav_get_num_bytes_per_frame(s);
}

