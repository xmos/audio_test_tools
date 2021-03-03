# Copyright (c) 2020-2021, XMOS Ltd, All rights reserved
# This software is available under the terms provided in LICENSE.txt.
import time
from scipy import signal
import numpy as np 
import sys
import math
import os
import pyximport; pyximport.install()
if __name__ == "__main__":
    from pdm_helpers import pack_pdm_to_words, pdm_modulator
else:
    from .pdm_helpers import pack_pdm_to_words, pdm_modulator
from bash import bash
import struct
import soundfile as sf

pdm_rate = 3072000
delete_temp_files = True

def pack_pdm_to_words_ref(word_0_bits, word_1_bits):
    shift = 0
    pdm_word_0 = 0
    pdm_word_1 = 0

    while(shift < 16):
        pdm_word_0 |=  word_0_bits[shift] << shift
        pdm_word_1 |=  word_1_bits[shift] << shift
        shift += 1

    return pdm_word_0, pdm_word_1

# Note we have a cython version of this in sigmadelta.pyx
def pack_pdm_and_ref(input_rate, pdm_files, ref_file, output_file):
    pdm_size = os.path.getsize(pdm_files[0])
    ref_size = os.path.getsize(ref_file)
    num_input_samps = int(ref_size / 4 / 2)
    num_pdm_words_per_sample = 4 if input_rate == 48000 else 12


    upsample_ratio = pdm_size / num_input_samps
    print(f"pdm samples: {pdm_size}, ref samples: {num_input_samps}, ratio: {upsample_ratio}, seconds: {num_input_samps/input_rate}")

    assert upsample_ratio == 64.0 or upsample_ratio == 192.0, "non integer relationship between pdm and ref file sizes"

    with open(ref_file,'rb') as ref, \
         open(pdm_files[0],'rb') as pdm_0, \
         open(pdm_files[1],'rb') as pdm_1, \
         open(output_file,'wb') as out_packed:


        for frame_count in range(num_input_samps):
            write_buffer = np.zeros(2 + 2 * num_pdm_words_per_sample, dtype=np.uint32)

            write_idx = 2
            for word in range(num_pdm_words_per_sample):


                word_0_bits = pdm_0.read(16)
                word_1_bits = pdm_1.read(16)

                # pdm_word_0, pdm_word_1 = pack_pdm_to_words_ref(word_0_bits, word_1_bits)
                pdm_word_0, pdm_word_1 = pack_pdm_to_words(word_0_bits, word_1_bits)

                # print("bit_0", bit_0)
                # print(bin(pdm_word_0<<16))
                write_buffer[write_idx] = (pdm_word_0 << 16)
                # print(write_buffer[write_idx])
                write_buffer[write_idx + num_pdm_words_per_sample] = (pdm_word_1 << 16)

                write_idx += 1

            write_buffer[0:2] = struct.unpack("ii", ref.read(2 * 4))
            out_packed.write(write_buffer)
            # print(frame_count)


def pcm2pdm(input_file, output_file):
    if input_file.endswith("wav"):
        in_wav = sf.SoundFile(input_file, 'r')
        n_frames = in_wav.seek(0, sf.SEEK_END)
        in_wav.seek(0)
        assert in_wav.channels == 1, "Mono wav please"
        assert in_wav.samplerate == pdm_rate, "{pdm_rate}Hz wav please"

        file_read_fn = in_wav.read
        file_tell_fn = in_wav.tell
        file_close_fn = in_wav.close
    # Must be raw so assume 32b LE packed raw
    else:
        in_raw = open(input_file,'rb')
        n_frames = in_raw.seek(0, 2) // 4
        # print(f"using raw, {n_frames} frames")
        def in_raw_read_frame(n):
            samples = np.frombuffer(in_raw.read(n*4), dtype=np.int32)
            samples = samples.astype(np.float64) / 2**31
            return samples
        file_read_fn = in_raw_read_frame
        in_raw.seek(0, 0)
        def in_raw_tell_frames():
            return in_raw.tell() // 4
        file_tell_fn = in_raw_tell_frames
        file_close_fn = in_raw.close

    with open(output_file,'wb') as out_pdm:
        print(f"Modulating {n_frames} samples")
        mod = pdm_modulator()

        block_size = 1000000

        while file_tell_fn() < n_frames:
            t0 = time.time()
            pcm_block = file_read_fn(block_size)

            t1 = time.time()
            # print(len(pcm_block), type(pcm_block), type(pcm_block[0]))
            pdm_block = mod.push_block(pcm_block)

            out_pdm.write(pdm_block)
            t2 = time.time()
            # print(t1-t0, t2-t1)
    file_close_fn()

def gen_pdm_and_pack_ref(input_file_name, output_file_name):
    # Just grab the wav sample rate
    _data, input_rate = sf.read(input_file_name, frames=1)
    cmd = f"soxi -r {input_file_name}"
    input_rate = float(bash(cmd).stdout)
    cmd = f"soxi -D {input_file_name}"
    len_s = float(bash(cmd).stdout)

    # turn ref into raw 2ch 32b PCM files for later
    print("Extracting reference signal..")
    reference_file = "reference.raw"
    cmd = f"sox {input_file_name} -b 32 -e signed-integer {reference_file} remix 3 4"
    bash(cmd)

    # Generate PDM by upsampling then modulating, 1 channel at a time to avoid large TMP files
    pdm_files = []
    for channel in [1,2]:
        print(f"Upsampling mic channel {channel}..")
        # assert len_s <= 359.0, f"Sox limitation on 2^30 samples which is 349s 3072000MHz mono wav (len: {len_s})"
        # pcm_file = f"pcm_upsampled_ch_{channel}.wav"
        # cmd = f"sox {input_file_name} -r {pdm_rate} {pcm_file} remix {channel}"
        pcm_file = f"pcm_upsampled_ch_{channel}.raw"
        cmd = f"sox {input_file_name} -r {pdm_rate} -t s32 {pcm_file} remix {channel}"
        bash(cmd)
        print(f"Converting mic channel {channel} to PDM..")
        pdm_file = f"pcm_ch_{channel}.pdm"
        pcm2pdm(pcm_file, pdm_file)
        pdm_files.append(pdm_file)
        if delete_temp_files:
            os.remove(pcm_file)

    print("Packing PCM and PDM files to raw..")
    output_raw_file = "boggled.raw"
    pack_pdm_and_ref(input_rate, pdm_files, reference_file, output_raw_file)
    for pdm_file in pdm_files:
        if delete_temp_files:
            os.remove(pdm_file)
    if delete_temp_files:
        os.remove(reference_file)

    out_chans = 26 if input_rate == 16000 else 10

    print("Converting raw to wav..")
    cmd = f"sox -b 32 -e signed-integer -c {out_chans} -r {input_rate} {output_raw_file} {output_file_name}"
    bash(cmd)
    if delete_temp_files:
        os.remove(output_raw_file)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        input_file_name = sys.argv[1]
    else:
        input_file_name = "input.wav"
    gen_pdm_and_pack_ref(input_file_name, "output.wav")
    sys.exit(0)
