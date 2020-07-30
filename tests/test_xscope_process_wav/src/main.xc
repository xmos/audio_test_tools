// Copyright (c) 2020, XMOS Ltd, All rights reserved
#include <platform.h>
#include <xscope.h>
#include <string.h>
#include <stdio.h>

#include "voice_toolbox.h"
#include "audio_test_tools.h"

void app_control(chanend c_control_to_wav, chanend ?c_control_to_dsp){
    //Play the rest of the file
    att_pw_play(c_control_to_wav);
}


void pass_through_test_task(chanend app_to_dsp, chanend dsp_to_app, chanend ?c_control_to_dsp){

    vtb_ch_pair_t [[aligned(8)]] in_frame[ATT_PW_INPUT_CHANNEL_PAIRS][ATT_PW_FRAME_ADVANCE];
    vtb_ch_pair_t [[aligned(8)]] unprocessed_frame[ATT_PW_INPUT_CHANNEL_PAIRS][ATT_PW_PROC_FRAME_LENGTH];
    vtb_ch_pair_t [[aligned(8)]] in_prev_frame[ATT_PW_INPUT_CHANNEL_PAIRS][ATT_PW_PROC_FRAME_LENGTH - ATT_PW_FRAME_ADVANCE];

    memset(in_frame, 0, sizeof(in_frame));
    memset(unprocessed_frame, 0, sizeof(unprocessed_frame));
    memset(in_prev_frame, 0, sizeof(in_prev_frame));

    vtb_md_t rx_md;
    vtb_md_init(rx_md);
    
    vtb_rx_state_t rx_state = vtb_form_rx_state(
                                 (vtb_ch_pair_t *) in_frame,
                                 (vtb_ch_pair_t *) in_prev_frame,
                                 null, /*delay buffer*/
                                 ATT_PW_FRAME_ADVANCE,
                                 ATT_PW_PROC_FRAME_LENGTH,
                                 ATT_PW_INPUT_CHANNELS,
                                 null /*delays*/);



    vtb_ch_pair_t [[aligned(8)]] processed_frame[ATT_PW_OUTPUT_CHANNEL_PAIRS][ATT_PW_FRAME_ADVANCE];
    memset(processed_frame, 0, sizeof(processed_frame));

    vtb_tx_state_t tx_state = vtb_form_tx_state(ATT_PW_FRAME_ADVANCE, ATT_PW_OUTPUT_CHANNELS);

    vtb_md_t tx_md;
    vtb_md_init(tx_md);

    while(1){

        vtb_rx(app_to_dsp, rx_state, (unprocessed_frame, vtb_ch_pair_t[]), rx_md);

        delay_milliseconds(15);
        memcpy(processed_frame, in_frame, sizeof(in_frame));
        memcpy(&tx_md, &rx_md, sizeof(rx_md));

        vtb_tx(dsp_to_app, tx_state, (processed_frame, vtb_ch_pair_t[]), tx_md);
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

