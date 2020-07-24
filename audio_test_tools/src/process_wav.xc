// Copyright (c) 2017-2019, XMOS Ltd, All rights reserved

#include <fcntl.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <xscope.h>
#include <xs1.h>

//#ifdef _VOICE_TOOLBOX_H_
#include "voice_toolbox.h"
#include "audio_test_tools.h"

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

void att_process_wav(chanend c_app_to_dsp, chanend ?c_dsp_to_app, chanend ?c_comms){

#ifdef __process_wav_conf_h_exists__
    // Initialise input

    char * input_file_name = ATT_PW_INPUT_FILE_NAME;
    int32_t input_read_buffer  [ATT_PW_PROC_FRAME_LENGTH*ATT_PW_INPUT_CHANNELS];
    int input_file = open ( input_file_name , O_RDONLY|O_BINARY);

    if ((input_file==-1)) {
        printf("x_file file missing (%s)\n", input_file_name);
        _Exit(1);
    }

    att_wav_header input_header_struct;
    unsigned input_wavheader_size;
    if(att_get_wav_header_details(input_file_name, input_header_struct, input_wavheader_size) != 0){
      printf("error in att_get_wav_header_details()\n");
      _Exit(1);
    }
    lseek(input_file, input_wavheader_size, SEEK_SET);

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
    int output_file;
    att_wav_header output_header_struct;
#define DSP_TO_APP_STATE VTB_RX_STATE_UINT64_SIZE(ATT_PW_OUTPUT_CHANNEL_PAIRS*2, ATT_PW_PROC_FRAME_LENGTH, ATT_PW_FRAME_ADVANCE, 0)
    uint64_t rx_state[DSP_TO_APP_STATE];

    if (!isnull(c_dsp_to_app)) {
        output_file = open( output_file_name , O_WRONLY|O_CREAT|O_BINARY, 0644 );

        att_wav_form_header(output_header_struct,
                input_header_struct.audio_format,
                ATT_PW_OUTPUT_CHANNELS,
                input_header_struct.sample_rate,
                input_header_struct.bit_depth,
                block_count*ATT_PW_FRAME_ADVANCE);

        write(output_file, (char*)(&output_header_struct),  ATT_WAV_HEADER_BYTES);

        vtb_rx_state_init(rx_state, ATT_PW_OUTPUT_CHANNEL_PAIRS*2, ATT_PW_PROC_FRAME_LENGTH, ATT_PW_FRAME_ADVANCE, null, DSP_TO_APP_STATE);
    }

    int playing = 1;

    unsigned waiting_for_time;
    if(isnull(c_comms)){
        waiting_for_time = UINT_MAX;
    } else {
        waiting_for_time = 0;
    }

    for(unsigned b=0;b<block_count;b++){
        unsigned start_sample_of_frame = b*ATT_PW_FRAME_ADVANCE;

        if(start_sample_of_frame >= waiting_for_time){
            playing = 0;
        }

        while (!playing){
            select {
                case c_comms:> int cmd:{
                    switch(cmd){
                    case ATT_PW_PLAY:
                        playing = 1;
                        waiting_for_time = UINT_MAX;
                        break;
                    case ATT_PW_PAUSE:
                        playing = 0;
                        break;
                    case ATT_PW_PLAY_UNTIL_SAMPLE_PASSES:
                        playing = 1;
                        c_comms :> waiting_for_time;
                        break;
                    case ATT_PW_STOP:
                        if (!isnull(c_dsp_to_app)) {
                            //TODO patch the header
                            close(output_file);
                        }
                        _exit(0);
                        break;
                    }
                    break;
                }
            }
        }

        long input_location =  att_wav_get_frame_start(input_header_struct, b * ATT_PW_FRAME_ADVANCE, input_wavheader_size);

        lseek (input_file, input_location, SEEK_SET);

        read (input_file, (char*)&input_read_buffer[0],
                input_bytes_per_frame * ATT_PW_FRAME_ADVANCE);

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

            write(output_file, output_write_buffer, output_header_struct.bit_depth/8 * ATT_PW_FRAME_ADVANCE * ATT_PW_OUTPUT_CHANNELS);
        }

        for(unsigned i=0;i<(ATT_PW_PROC_FRAME_LENGTH-ATT_PW_FRAME_ADVANCE)*ATT_PW_INPUT_CHANNELS;i++){
            input_read_buffer[i] = input_read_buffer[i + ATT_PW_FRAME_ADVANCE*ATT_PW_INPUT_CHANNELS];
        }
    }
    if (!isnull(c_dsp_to_app)) {
        close(output_file);
    }
#else
    printf("att_process_wav requires a process_wav_conf.h (and it is missing)\n");
    _Exit(1);
#endif
}
//#endif


void att_process_wav_xscope(chanend xscope_data_in, chanend c_app_to_dsp, chanend c_dsp_to_app, chanend ?c_comms){

#ifdef __process_wav_conf_h_exists__
   
#define DSP_TO_APP_STATE VTB_RX_STATE_UINT64_SIZE(ATT_PW_OUTPUT_CHANNEL_PAIRS*2, ATT_PW_PROC_FRAME_LENGTH, ATT_PW_FRAME_ADVANCE, 0)
    uint64_t rx_state[DSP_TO_APP_STATE];
    vtb_rx_state_init(rx_state, ATT_PW_OUTPUT_CHANNEL_PAIRS*2, ATT_PW_PROC_FRAME_LENGTH, ATT_PW_FRAME_ADVANCE, null, DSP_TO_APP_STATE);

    int playing = 1;
    unsigned input_frame_counter = 0;
    unsigned output_frame_counter = 0;
    unsigned chunk_bytes_so_far = 0;
    unsigned total_bytes_read = 0;

    unsigned waiting_for_time;
    if(isnull(c_comms)){
        waiting_for_time = UINT_MAX;
    } else {
        waiting_for_time = 0;
    }


    // Queue up a few requests for file data so that the H->D buffer is always full
    // We will request more after each block is processed. We do this because
    // xscope seems unstable if we hammer it too hard with data sand rely on the chunk_buffer
    for (int i=0; i<4;i++) xscope_int(2, 0);

    while(playing){
        int bytes_read = 0;

        unsigned chunk_complete = 0;
        chunk_bytes_so_far = 0;
        char block_buffer[BLOCK_SIZE_BYTES];
        char chunk_buffer[MAX_XSCOPE_SIZE_BYTES];
        
        vtb_ch_pair_t [[aligned(8)]] processed_frame[ATT_PW_OUTPUT_CHANNEL_PAIRS][ATT_PW_PROC_FRAME_LENGTH];
        memset(processed_frame, 0, sizeof(processed_frame));

        vtb_rx_state_t rx_state;
        // vtb_md_t tx_md;
        vtb_md_t rx_md;

        select{
            case xscope_data_from_host(xscope_data_in, chunk_buffer, bytes_read):

                    memcpy(&block_buffer[chunk_bytes_so_far], chunk_buffer, bytes_read);
                    chunk_bytes_so_far += bytes_read;
                    total_bytes_read += bytes_read;

                    unsigned end_marker_found = ((bytes_read == END_MARKER_LEN) && !memcmp(chunk_buffer, END_MARKER_STRING, END_MARKER_LEN)) ? 1 : 0;
                    if(end_marker_found){
                        chunk_bytes_so_far -= bytes_read;
                        total_bytes_read -= bytes_read;
                    }

                    if(chunk_bytes_so_far == BLOCK_SIZE_BYTES || end_marker_found){
                        chunk_complete = 1;
                    }

                if(chunk_bytes_so_far){
                    //request more data 
                    xscope_int(2, 0);
                    // printf("Received: %u bytes\n", chunk_bytes_so_far);

                    vtb_ch_pair_t [[aligned(8)]] frame[ATT_PW_INPUT_CHANNELS][ATT_PW_FRAME_ADVANCE];

                    for(unsigned f=0; f<ATT_PW_FRAME_ADVANCE; f++){
                        for(unsigned ch=0;ch<ATT_PW_INPUT_CHANNELS;ch++){
                            unsigned ch_pair = ch/2;
                            unsigned i =(f * ATT_PW_INPUT_CHANNELS) + ch;
                            (frame[ch_pair][f], int32_t[2])[ch&1] = chunk_buffer[i];
                        }
                    }

                    vtb_md_t metadata;

                    vtb_tx_notification_and_data(c_app_to_dsp, (frame, vtb_ch_pair_t[]),
                                           ATT_PW_INPUT_CHANNEL_PAIRS*2, ATT_PW_FRAME_ADVANCE,
                                           metadata);

                    input_frame_counter++;
                }

            break;

            case vtb_rx_notification(c_dsp_to_app, rx_state):
                vtb_rx_without_notification(c_dsp_to_app, rx_state, (processed_frame, vtb_ch_pair_t[]), rx_md);

                int output_write_buffer[ATT_PW_FRAME_ADVANCE*ATT_PW_OUTPUT_CHANNELS];

                unsigned size = sizeof(output_write_buffer);

                for (unsigned ch=0;ch<ATT_PW_OUTPUT_CHANNELS;ch++){
                    for(unsigned i=0;i<ATT_PW_FRAME_ADVANCE;i++){
                        output_write_buffer[(i)*ATT_PW_OUTPUT_CHANNELS + ch] = (processed_frame[ch/2][i + (ATT_PW_PROC_FRAME_LENGTH-ATT_PW_FRAME_ADVANCE)], int32_t[2])[ch&1];
                    }
                }
                //Chunk it up
                unsigned sent_so_far = 0;
                do{
                    if(size - sent_so_far >=  MAX_XSCOPE_SIZE_BYTES){
                        xscope_bytes(0, MAX_XSCOPE_SIZE_BYTES, (char*)&output_write_buffer[sent_so_far]);
                        sent_so_far += MAX_XSCOPE_SIZE_BYTES;
                    }
                    else{
                        xscope_bytes(0, size - sent_so_far, (char*)&output_write_buffer[sent_so_far]);
                        sent_so_far = size;
                    }
                    delay_ticks(10000); /// Magic number found to make xscope stable on MAC, else you get WRITE ERROR ON UPLOAD ....
                }
                while (sent_so_far < size);

                output_frame_counter++;
            break;

            case c_comms:> int cmd:{
                switch(cmd){
                case ATT_PW_PLAY:
                    playing = 1;
                    waiting_for_time = UINT_MAX;
                    break;
                case ATT_PW_PAUSE:
                    playing = 0;
                    break;
                case ATT_PW_PLAY_UNTIL_SAMPLE_PASSES:
                    playing = 1;
                    c_comms :> waiting_for_time;
                    break;
                case ATT_PW_STOP:
                    _exit(0);
                    break;
                }
            break;
        }
    }



        // if(start_sample_of_frame >= waiting_for_time){
        //     playing = 0;
        // }






        // WHAT IS THIS  FOR!??
        // for(unsigned i=0;i<(ATT_PW_PROC_FRAME_LENGTH-ATT_PW_FRAME_ADVANCE)*ATT_PW_INPUT_CHANNELS;i++){
        //     input_read_buffer[i] = input_read_buffer[i + ATT_PW_FRAME_ADVANCE*ATT_PW_INPUT_CHANNELS];
        // }
    }
#else
    printf("att_process_wav_xscope requires a process_wav_conf.h (and it is missing)\n");
    _Exit(1);
#endif
}
//#endif
