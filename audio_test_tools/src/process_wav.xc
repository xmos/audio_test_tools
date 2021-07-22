// Copyright 2017-2021 XMOS LIMITED.
// This Software is subject to the terms of the XMOS Public Licence: Version 1.

#include <fcntl.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <xs1.h>

#include "voice_toolbox.h"
#include "audio_test_tools.h"

#ifdef TEST_WAV_XSCOPE
extern "C" {
#include "xscope_io_device.h"
}
#endif

typedef enum {
    ATT_PW_PLAY,
    ATT_PW_PAUSE,
    ATT_PW_PLAY_UNTIL_SAMPLE_PASSES,
    ATT_PW_STOP
} att_pw_commands;

void att_pw_play(chanend c_comms){
    c_comms <: ATT_PW_PLAY;
}

void att_pw_pause(chanend c_comms){
    c_comms <: ATT_PW_PAUSE;
}

void att_pw_stop(chanend c_comms){
    c_comms <: ATT_PW_STOP;
}

void att_pw_play_until_sample_passes(chanend c_comms, long sample){
    c_comms <: ATT_PW_PLAY_UNTIL_SAMPLE_PASSES;
    c_comms <: sample;
}

#ifdef TEST_WAV_XSCOPE
void att_process_wav_xscope(chanend xscope_data_in, chanend c_app_to_dsp, chanend ?c_dsp_to_app, chanend ?c_comms){
#else
void att_process_wav(chanend c_app_to_dsp, chanend ?c_dsp_to_app, chanend ?c_comms){
#endif

#ifdef __process_wav_conf_h_exists__
    // Initialise input

    char * input_file_name = ATT_PW_INPUT_FILE_NAME;
    int32_t input_read_buffer  [ATT_PW_PROC_FRAME_LENGTH*ATT_PW_INPUT_CHANNELS] = {0};
#ifdef TEST_WAV_XSCOPE
    xscope_io_init(xscope_data_in);
    xscope_file_t input_file = xscope_open_file(input_file_name, "rb");
#else
    int input_file = open ( input_file_name , O_RDONLY|O_BINARY);
    if ((input_file==-1)) {
        printf("x_file file missing (%s)\n", input_file_name);
        _Exit(1);
    }
#endif



    att_wav_header input_header_struct;
    unsigned input_wavheader_size;
#ifdef TEST_WAV_XSCOPE
    if(att_get_wav_header_details_xscope(&input_file, input_header_struct, input_wavheader_size) != 0){
        printf("error in att_get_wav_header_details()\n");
        _Exit(1);
    }
    xscope_fseek(&input_file, input_wavheader_size, SEEK_SET);
#else
    if(att_get_wav_header_details(input_file_name, input_header_struct, input_wavheader_size) != 0){
        printf("error in att_get_wav_header_details()\n");
        _Exit(1);
    }
    lseek(input_file, input_wavheader_size, SEEK_SET);
#endif

    if(input_header_struct.bit_depth != 32){
         printf("Error: unsupported wav bit depth (%d) for %s file. Only 32 supported\n", input_header_struct.bit_depth, input_file_name);
         _Exit(1);
     }

    if(input_header_struct.num_channels != ATT_PW_INPUT_CHANNELS){
        printf("Error: wav num x channels(%d) does not match (%u)\n", input_header_struct.num_channels, ATT_PW_INPUT_CHANNELS);
        _Exit(1);
    }

    unsigned input_frame_count = att_wav_get_num_frames(input_header_struct);
    unsigned frame_count = input_frame_count;
    unsigned block_count = frame_count / ATT_PW_FRAME_ADVANCE; //TODO check this - it might be off by one
    unsigned input_bytes_per_frame = att_wav_get_num_bytes_per_frame(input_header_struct);

    // Initialise output

    char * output_file_name = ATT_PW_OUTPUT_FILE_NAME;
    int output_write_buffer[ATT_PW_FRAME_ADVANCE*ATT_PW_OUTPUT_CHANNELS];
#ifdef TEST_WAV_XSCOPE
    xscope_file_t output_file;
#else
    int output_file;
#endif
    att_wav_header output_header_struct;
#define DSP_TO_APP_STATE VTB_RX_STATE_UINT64_SIZE(ATT_PW_OUTPUT_CHANNEL_PAIRS*2, ATT_PW_PROC_FRAME_LENGTH, ATT_PW_FRAME_ADVANCE, 0)
    uint64_t rx_state[DSP_TO_APP_STATE];

    if (!isnull(c_dsp_to_app)) {
#ifdef TEST_WAV_XSCOPE
        output_file = xscope_open_file(output_file_name, "wb");
#else
        output_file = open(output_file_name , O_WRONLY|O_CREAT|O_BINARY, 0644 );
#endif

        att_wav_form_header(output_header_struct,
                input_header_struct.audio_format,
                ATT_PW_OUTPUT_CHANNELS,
                input_header_struct.sample_rate,
                input_header_struct.bit_depth,
                block_count*ATT_PW_FRAME_ADVANCE);

#ifdef TEST_WAV_XSCOPE
        xscope_fwrite(&output_file, (char*)(&output_header_struct),  ATT_WAV_HEADER_BYTES);
#else
        write(output_file, (char*)(&output_header_struct),  ATT_WAV_HEADER_BYTES);
#endif

        vtb_rx_state_init(rx_state, ATT_PW_OUTPUT_CHANNEL_PAIRS*2, ATT_PW_PROC_FRAME_LENGTH, ATT_PW_FRAME_ADVANCE, null, DSP_TO_APP_STATE);
    }

    int busy_playing = 1;

    unsigned waiting_for_time;
    if(isnull(c_comms)){
        waiting_for_time = UINT_MAX;
    } else {
        waiting_for_time = 0;
    }

    for(unsigned b=0;b<block_count;b++){
        unsigned start_sample_of_frame = b*ATT_PW_FRAME_ADVANCE;

        if(start_sample_of_frame >= waiting_for_time){
            busy_playing = 0;
        }

        while (!busy_playing){
            select {
                case c_comms:> int cmd:{
                    switch(cmd){
                    case ATT_PW_PLAY:
                        busy_playing = 1;
                        waiting_for_time = UINT_MAX;
                        break;
                    case ATT_PW_PAUSE:
                        busy_playing = 0;
                        break;
                    case ATT_PW_PLAY_UNTIL_SAMPLE_PASSES:
                        busy_playing = 1;
                        c_comms :> waiting_for_time;
                        break;
                    case ATT_PW_STOP:
                        if (!isnull(c_dsp_to_app)) {
                            //TODO patch the header
#ifndef TEST_WAV_XSCOPE
                            close(output_file);
#endif
                        }
                        _exit(0);
                        break;
                    }
                    break;
                }
            }
        }

        long input_location =  att_wav_get_frame_start(input_header_struct, b * ATT_PW_FRAME_ADVANCE, input_wavheader_size);

#ifdef TEST_WAV_XSCOPE
        xscope_fseek (&input_file, input_location, SEEK_SET);

        xscope_fread(&input_file, (char*)&input_read_buffer[0],
                input_bytes_per_frame * ATT_PW_FRAME_ADVANCE);
#else
        lseek (input_file, input_location, SEEK_SET);

        read (input_file, (char*)&input_read_buffer[0],
                input_bytes_per_frame * ATT_PW_FRAME_ADVANCE);
#endif
        vtb_ch_pair_t [[aligned(8)]] frame[ATT_PW_INPUT_CHANNELS][ATT_PW_FRAME_ADVANCE];
        memset(frame, 0, sizeof(frame));

        for(unsigned f=0; f<ATT_PW_FRAME_ADVANCE; f++){
            for(unsigned ch=0;ch<ATT_PW_INPUT_CHANNELS;ch++){
                unsigned ch_pair = ch/2;
                unsigned i =(f * ATT_PW_INPUT_CHANNELS) + ch;
                (frame[ch_pair][f], int32_t[2])[ch&1] = input_read_buffer[i];
            }
        }

        vtb_md_t metadata;

        vtb_tx_notification_and_data(c_app_to_dsp, (frame, vtb_ch_pair_t[]),
                               ATT_PW_INPUT_CHANNEL_PAIRS*2, ATT_PW_FRAME_ADVANCE,
                               metadata);

        if (!isnull(c_dsp_to_app)) {
            vtb_ch_pair_t [[aligned(8)]] processed_frame[ATT_PW_OUTPUT_CHANNEL_PAIRS][ATT_PW_PROC_FRAME_LENGTH];
            memset(processed_frame, 0, sizeof(processed_frame));

            vtb_rx_notification_and_data(c_dsp_to_app, rx_state, (processed_frame, vtb_ch_pair_t[]), metadata);

            for (unsigned ch=0;ch<ATT_PW_OUTPUT_CHANNELS;ch++){
                for(unsigned i=0;i<ATT_PW_FRAME_ADVANCE;i++){
                    output_write_buffer[(i)*ATT_PW_OUTPUT_CHANNELS + ch] = (processed_frame[ch/2][i + (ATT_PW_PROC_FRAME_LENGTH-ATT_PW_FRAME_ADVANCE)], int32_t[2])[ch&1];
                }
            }
#ifdef TEST_WAV_XSCOPE
            xscope_fwrite(&output_file, (uint8_t *)output_write_buffer, output_header_struct.bit_depth/8 * ATT_PW_FRAME_ADVANCE * ATT_PW_OUTPUT_CHANNELS);
#else
            write(output_file, output_write_buffer, output_header_struct.bit_depth/8 * ATT_PW_FRAME_ADVANCE * ATT_PW_OUTPUT_CHANNELS);
#endif
        }

        for(unsigned i=0;i<(ATT_PW_PROC_FRAME_LENGTH-ATT_PW_FRAME_ADVANCE)*ATT_PW_INPUT_CHANNELS;i++){
            input_read_buffer[i] = input_read_buffer[i + ATT_PW_FRAME_ADVANCE*ATT_PW_INPUT_CHANNELS];
        }
    }
    if (!isnull(c_dsp_to_app)) {
#ifndef TEST_WAV_XSCOPE
        close(output_file);
#endif
    }
#else
    printf("att_process_wav requires a process_wav_conf.h (and it is missing)\n");
    _Exit(1);
#endif
#ifdef TEST_WAV_XSCOPE
    xscope_close_all_files();
#endif

}
//#endif
