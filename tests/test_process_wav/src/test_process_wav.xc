// Copyright 2018-2021 XMOS LIMITED.
// This Software is subject to the terms of the XMOS Public Licence: Version 1.

#include <platform.h>
#include <string.h>
#include "voice_toolbox.h"
#include "audio_test_tools.h"

void null_dsp(chanend app_to_dsp, chanend dsp_to_app){

#define APP_TO_SUP_STATE VTB_RX_STATE_UINT64_SIZE(ATT_PW_INPUT_CHANNEL_PAIRS*2, ATT_PW_PROC_FRAME_LENGTH, ATT_PW_FRAME_ADVANCE, 0)
    uint64_t rx_state[APP_TO_SUP_STATE];

    vtb_rx_state_init(rx_state, ATT_PW_INPUT_CHANNEL_PAIRS*2, ATT_PW_PROC_FRAME_LENGTH, ATT_PW_FRAME_ADVANCE,
            null, APP_TO_SUP_STATE);

    vtb_ch_pair_t [[aligned(8)]] in_frame[ATT_PW_INPUT_CHANNEL_PAIRS][ATT_PW_PROC_FRAME_LENGTH];
    memset(in_frame, 0, sizeof(in_frame));
    vtb_ch_pair_t  [[aligned(8)]]output_frame[ATT_PW_OUTPUT_CHANNEL_PAIRS][ATT_PW_FRAME_ADVANCE];

    vtb_md_t md_rx, md_tx;

    while(1){

        vtb_rx_notification_and_data(app_to_dsp, rx_state, (in_frame, vtb_ch_pair_t[]), md_rx);

        //TODO copy input to output and lose
        memcpy(output_frame, in_frame, sizeof(output_frame));

        vtb_tx_notification_and_data(dsp_to_app, (output_frame, vtb_ch_pair_t[]), ATT_PW_OUTPUT_CHANNEL_PAIRS*2, ATT_PW_FRAME_ADVANCE, md_tx);
    }
}

int main(){
    chan app_to_dsp;
    chan dsp_to_app;

    par {
        on tile[0]:{
            att_process_wav(app_to_dsp, dsp_to_app, null);
            _Exit(0);
        }
        on tile[1]:null_dsp (app_to_dsp, dsp_to_app);
    }
    return 0;
}
