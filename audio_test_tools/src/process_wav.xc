// Copyright (c) 2017-2019, XMOS Ltd, All rights reserved

#include <fcntl.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <xscope.h>
#include <xs1.h>

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


union input_block_buffer_t {
    int32_t sample[ATT_PW_INPUT_CHANNELS * ATT_PW_FRAME_ADVANCE];
    char bytes[ATT_PW_INPUT_CHANNELS * ATT_PW_FRAME_ADVANCE * 4];
};

union output_block_buffer_t {
    int32_t sample[ATT_PW_OUTPUT_CHANNELS * ATT_PW_FRAME_ADVANCE];
    char bytes[ATT_PW_OUTPUT_CHANNELS * ATT_PW_FRAME_ADVANCE * 4];
};

void att_process_wav_xscope(chanend xscope_data_in, chanend c_app_to_dsp, chanend c_dsp_to_app, chanend ?c_comms){

#ifdef __process_wav_conf_h_exists__
    vtb_ch_pair_t [[aligned(8)]] out_frame[ATT_PW_INPUT_CHANNEL_PAIRS][ATT_PW_FRAME_ADVANCE];
    vtb_ch_pair_t [[aligned(8)]] processed_frame[ATT_PW_INPUT_CHANNEL_PAIRS][ATT_PW_PROC_FRAME_LENGTH];
    vtb_ch_pair_t [[aligned(8)]] out_prev_frame[ATT_PW_INPUT_CHANNEL_PAIRS][ATT_PW_PROC_FRAME_LENGTH - ATT_PW_FRAME_ADVANCE];

    memset(out_frame, 0, sizeof(out_frame));
    memset(processed_frame, 0, sizeof(processed_frame));
    memset(out_prev_frame, 0, sizeof(out_prev_frame));

   
    vtb_rx_state_t rx_state = vtb_form_rx_state(
                                 (vtb_ch_pair_t *) out_frame,
                                 (vtb_ch_pair_t *) out_prev_frame,
                                 null, /*delay buffer*/
                                 ATT_PW_FRAME_ADVANCE,
                                 ATT_PW_PROC_FRAME_LENGTH,
                                 ATT_PW_OUTPUT_CHANNELS,
                                 null /*delays*/);
    vtb_md_t rx_md;
    vtb_md_init(rx_md);

    vtb_tx_state_t tx_state = vtb_form_tx_state(ATT_PW_FRAME_ADVANCE, ATT_PW_INPUT_CHANNELS);
    vtb_md_t tx_md;
    vtb_md_init(tx_md);


    unsigned xscope_looping = 1;
    unsigned end_marker_found = 0;
    unsigned input_frame_counter = 0;
    unsigned output_frame_counter = 0;
    unsigned block_bytes_so_far = 0;
    unsigned total_bytes_read = 0;
    unsigned tx_from_dut_empty = 1;

    // Vars taken from non-xscope version to support control at a time
    int busy_playing = 1;

    unsigned waiting_for_time;
    if(isnull(c_comms)){
        waiting_for_time = UINT_MAX;
    } else {
        waiting_for_time = 0;
    }

    xscope_mode_lossless();
    xscope_connect_data_from_host(xscope_data_in);

    // Queue up a few requests for file data so that the H->D buffer in xscope is always full
    // We will request more after each block is processed. We do this because
    // xscope seems unstable if we hammer it too hard with data sand rely on the chunk_buffer
    for (int i=0; i<4;i++) xscope_int(2, 0);

    block_bytes_so_far = 0;
    union input_block_buffer_t input_block_buffer;

    while(xscope_looping){
        int bytes_read = 0;
        char chunk_buffer[MAX_XSCOPE_SIZE_BYTES];

        select{
            case tx_from_dut_empty => xscope_data_from_host(xscope_data_in, chunk_buffer, bytes_read):
                // printf("xscope_data_from_host\n");
                // Old att_process_wav logic for blocking control channel until certain sample time
                // This doesn't seem to actually work - supposed to block other side until time expires I think
                unsigned start_sample_of_frame = input_frame_counter*ATT_PW_FRAME_ADVANCE;
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
                                    xscope_looping = 0;
                                }
                                break;
                            }
                            break;
                        }
                    }
                }
                // End old logic

                memcpy(&input_block_buffer.bytes[block_bytes_so_far], chunk_buffer, bytes_read);
                end_marker_found = ((bytes_read == END_MARKER_LEN) && !memcmp(chunk_buffer, END_MARKER_STRING, END_MARKER_LEN)) ? 1 : 0;
                if(end_marker_found){
                    printf("end_marker_found\n");
                    //If the processing section is short, then rx will have already been processed so quit if so
                    if (output_frame_counter == input_frame_counter){
                        xscope_looping = 0;
                        break;
                    }
                }
                else{
                    block_bytes_so_far += bytes_read;
                    total_bytes_read += bytes_read;
                    // printf("block_bytes_so_far: %u\n", block_bytes_so_far);
                }

                if(block_bytes_so_far == (ATT_PW_INPUT_CHANNELS * ATT_PW_FRAME_ADVANCE * 4)){

                    //Input wav 4ch frame is ch0[0], ch1[0], ch2[0], ch3[0], ch0[1], ch1[1], ch2[1], ch3[1]..
                    //VTB 4ch frame is ch0[0], ch1[0], ch0[1], ch1[1]...ch0[239], ch1[239], ch2[0], ch1[3]...ch2[239], ch3[239]

                    printf("rx chunk_complete: %d\n", block_bytes_so_far);
                    vtb_ch_pair_t [[aligned(8)]] frame[ATT_PW_INPUT_CHANNELS][ATT_PW_FRAME_ADVANCE];

                    for(unsigned f=0; f<ATT_PW_FRAME_ADVANCE; f++){
                        for(unsigned ch=0;ch<ATT_PW_INPUT_CHANNELS;ch++){
                            unsigned ch_pair = ch/2;
                            unsigned i=(f * ATT_PW_INPUT_CHANNELS) + ch;
                            (frame[ch_pair][f], int32_t[2])[ch&1] = input_block_buffer.sample[i];
                        }
                    }

                    vtb_tx(c_app_to_dsp, tx_state, (frame, vtb_ch_pair_t[]), tx_md);

                    // printf("vtb_tx\n");
                    input_frame_counter++;
                    block_bytes_so_far = 0;
                    //request more data 
                    xscope_int(2, 0);
                    tx_from_dut_empty = 0;
                }
                else if(block_bytes_so_far > ATT_PW_INPUT_CHANNELS * ATT_PW_FRAME_ADVANCE * 4){
                    printf("Something has gone wrong, chunk bytes: %u\n", block_bytes_so_far);
                }
            break;

            case vtb_rx_notification(c_dsp_to_app, rx_state):
                // printf("vtb_rx_notification\n");
                vtb_rx_without_notification(c_dsp_to_app, rx_state, (processed_frame, vtb_ch_pair_t[]), rx_md);
                // printf("vtb_rx_without_notification\n");

                union output_block_buffer_t output_write_buffer;

                unsigned size = sizeof(output_write_buffer.sample);

                for (unsigned ch=0;ch<ATT_PW_OUTPUT_CHANNELS;ch++){
                    for(unsigned i=0;i<ATT_PW_FRAME_ADVANCE;i++){
                        output_write_buffer.sample[(i)*ATT_PW_OUTPUT_CHANNELS + ch] = (processed_frame[ch/2][i + (ATT_PW_PROC_FRAME_LENGTH-ATT_PW_FRAME_ADVANCE)], int32_t[2])[ch&1];
                    }
                }
                //Chunk it up
                unsigned sent_so_far = 0;
                do{
                    // printf("sent_so_far: %d\n", sent_so_far);
                    if(size - sent_so_far >=  MAX_XSCOPE_SIZE_BYTES){
                        xscope_bytes(0, MAX_XSCOPE_SIZE_BYTES, (char*)&output_write_buffer.bytes[sent_so_far]);
                        sent_so_far += MAX_XSCOPE_SIZE_BYTES;
                    }
                    else{
                        xscope_bytes(0, size - sent_so_far, (char*)&output_write_buffer.bytes[sent_so_far]);
                        sent_so_far = size;
                    }
                    delay_ticks(10000); /// Magic number found to make xscope stable on MAC, else you get WRITE ERROR ON UPLOAD ....
                }
                while (sent_so_far < size);
                printf("tx chunk complete: %d\n", size);


                output_frame_counter++;
                if(end_marker_found){
                    printf("output_frame_counter: %d,  input_frame_counter: %d\n", output_frame_counter, input_frame_counter);
                    if (output_frame_counter == input_frame_counter){
                        xscope_looping = 0;
                    }
                }
                tx_from_dut_empty = 1;
            break;
        }
    }

    // Quit
    xscope_int(1, 0);
    printf("Exit process wav\n");

#else
    printf("att_process_wav_xscope requires a process_wav_conf.h (and it is missing)\n");
    _Exit(1);
#endif
}
//#endif
