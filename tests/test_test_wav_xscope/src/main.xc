// Copyright (c) 2020, XMOS Ltd, All rights reserved
#include <platform.h>
#include <xscope.h>
#include <string.h>

#include "voice_toolbox.h"
#include "audio_test_tools.h"

void app_control(chanend c_control_to_wav, chanend c_control_to_dsp){

    //Play the file
    att_pw_play(c_control_to_wav);
}

#define IC_TOTAL_INPUT_CHANNEL_PAIRS    2
#define IC_TOTAL_OUTPUT_CHANNEL_PAIRS   2
#define IC_PROC_FRAME_LENGTH            512
#define IC_FRAME_ADVANCE                240
#define DELAY                           180

void pass_through_test_task(chanend app_to_dsp, chanend dsp_to_app, chanend ?c_control){

#define DSP_STATE VTB_RX_STATE_UINT64_SIZE(IC_TOTAL_INPUT_CHANNEL_PAIRS*2, IC_PROC_FRAME_LENGTH, IC_FRAME_ADVANCE, DELAY*((IC_TOTAL_INPUT_CHANNEL_PAIRS*2) - 1))
    uint64_t rx_state[DSP_STATE];
    uint32_t delays[IC_TOTAL_INPUT_CHANNEL_PAIRS*2] ={0};


    vtb_rx_state_init(rx_state, IC_TOTAL_INPUT_CHANNEL_PAIRS*2, IC_PROC_FRAME_LENGTH, IC_FRAME_ADVANCE,
            delays, DSP_STATE);

    vtb_ch_pair_t [[aligned(8)]] in_frame[IC_TOTAL_INPUT_CHANNEL_PAIRS][IC_PROC_FRAME_LENGTH];
    memset(in_frame, 0, sizeof(in_frame));


    while(1){

        vtb_md_t metadata;
        vtb_rx_notification_and_data(app_to_dsp, rx_state, (in_frame, vtb_ch_pair_t[]), metadata);

        int channel_hr[IC_TOTAL_INPUT_CHANNEL_PAIRS*2] = {0};
        for(unsigned ch_pair=0;ch_pair<IC_TOTAL_INPUT_CHANNEL_PAIRS;ch_pair++){
            channel_hr[ch_pair*2 + 0] = vtb_get_channel_hr(in_frame[ch_pair], IC_PROC_FRAME_LENGTH, 0);
            channel_hr[ch_pair*2 + 1] = vtb_get_channel_hr(in_frame[ch_pair], IC_PROC_FRAME_LENGTH, 1);
        }


        vtb_tx_notification_and_data(dsp_to_app, (in_frame, vtb_ch_pair_t[]),
                               IC_TOTAL_OUTPUT_CHANNEL_PAIRS*2,
                               IC_FRAME_ADVANCE, metadata);
    }
}


int main(){
    chan xscope_chan;
    chan app_to_dsp;
    chan dsp_to_app;
    chan c_control_to_dsp;
    chan c_control_to_wav;

    par {
        xscope_host_data(xscope_chan);

        on tile[0]:{
            app_control(c_control_to_wav, c_control_to_dsp);
        }
        on tile[0]:{
            att_process_wav_xscope(xscope_chan, app_to_dsp, dsp_to_app, c_control_to_wav);
            _Exit(0);
        }
        on tile[1]: pass_through_test_task(app_to_dsp, dsp_to_app, c_control_to_dsp);
    }
    return 0;
}

