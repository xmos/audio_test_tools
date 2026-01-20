# Copyright 2020-2022 XMOS LIMITED.
# This Software is subject to the terms of the XMOS Public Licence: Version 1.
import os
import subprocess
import sys
import re
from contextlib import contextmanager
import re

import numpy as np
import matplotlib.pyplot as plt
import scipy.io.wavfile
from time import sleep
from pathlib import Path
import random
from sys import platform
from .prepare_hw_test_wav import gen_pdm_and_pack_ref
import math

APP_NAME = "app_xk_xvf3510_l71"
XMOS_ROOT = Path(os.environ["XMOS_ROOT"])
SW_XVF3510 = XMOS_ROOT / "sw_xvf3510"
APP_PATH = SW_XVF3510 / APP_NAME
SRC_TEST_PATH = SW_XVF3510 / "tests/src_test"

host_utility_locations = {
    "vfctrl_usb": APP_PATH / "host" / "dsp_control",
    "vfctrl_json": APP_PATH / "host" / "dsp_control",
    "data_partition_generator": XMOS_ROOT / "lib_flash_data_partition" / "host" / "data_partition_generator",
    "dfu_suffix_generator": XMOS_ROOT / "lib_dfu" / "host" / "suffix_generator",
    "dfu_usb": APP_PATH / "host" / "dfu_control"
}

class HardwareTestException(Exception):
    """ Exception class for Hardware Test errors """
    pass

@contextmanager
def pushd(new_dir):
    last_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(last_dir)

def get_firmware_version():
    with pushd(SW_XVF3510):
        changelog_file = Path("CHANGELOG.rst")
        assert changelog_file.is_file()
        with open(changelog_file) as c:
            return c.read().splitlines()[3].strip()


def verbose_sleep(seconds: int):
    for i in range(seconds):
        print(".", end="", flush=True)
        sleep(1)
    print()


def prepare_host(extra_utilities = []):
    return build_host(extra_utilities)


def prepare_firmware(host, xe_path=None, data_partition_image=None, build_flags=""):
    rand_str = str(random.randint(1, 4096))
    if xe_path is None:
        xe_path = build_firmware(False, build_flags + f" --message {rand_str}")
    run_firmware(xe_path, data_partition_image)
    check_bld_message(host, rand_str)

def build_host(extra_utilities):
    binaries = {}
    for utility in ["vfctrl_usb"] + extra_utilities:
        CMakeCache_file = host_utility_locations[utility] / "CMakeCache.txt"
        if CMakeCache_file.is_file():
            CMakeCache_file.unlink()
        print("Building %s..." % utility)
        with pushd(host_utility_locations[utility]):
            if utility != "vfctrl_json":
                subprocess.run(["cmake", "."])
            else:
                subprocess.run(["cmake", ".", "-DJSON=ON"])
            subprocess.run(["make"])
            print()
        path = host_utility_locations[utility] / "bin" / utility
        assert path.is_file()
        binaries[utility] = str(path)
    return binaries

def build_firmware(verbose=False, build_flags="", config="usb_adaptive", blank=False):
    if blank:
        return None
    print("Building firmware...")
    with pushd(APP_PATH):
        args = f"configure clean build -j1 --config {config} {build_flags}"
        ret = subprocess.run(["waf", *args.split()], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(ret.stdout)
        print()
    return APP_PATH / "bin" / "app_xk_xvf3510_l71_usb_adaptive.xe"

def build_src_xe(verbose=False):
    print("Building src xe...")
    with pushd(SRC_TEST_PATH):
        args = f"configure clean build"
        ret = subprocess.run(["waf", *args.split()], capture_output=True, text=True)
        if verbose:
            print(ret.stdout)
        print()
    return SRC_TEST_PATH / "bin/src_test.xe"


def run_firmware(xe_path, data_partition_image=None):
    print("Calling xflash...")

    if data_partition_image != None:
        subprocess.run(["xflash", "--boot-partition-size", "1048576", "--data", data_partition_image, xe_path, "--no-compression"])
    else:
        subprocess.run(["xflash", xe_path, "--no-compression"])

    print("Waiting for firmware to boot...")
    verbose_sleep(15)

def erase_flash(xn_file):
    print("Calling xflash --erase-all...")
    subprocess.run(["xflash", "--erase-all", "--target-file", xn_file])

def build_data_image(host, which, compatibility_ver=None, bcd_ver=None, config_file=None, crc_error_data=False, verbose=False):
    config_path = APP_PATH / "data-partition"

    if config_file == None:
        config_file = config_path / "hardware_test.json"
        with open(config_path / "usb_adaptive.json") as file_in:
            with open(config_file, "w") as file_out:
                contents = file_in.read()
                contents = re.sub(r"\n\s+\"item_files\":\s*\[\n\s+\]",
                                  "\n    \"item_files\": [\n        {\n" +
                                  "            \"path\": \"hardware_test_usb_params.txt\",\n" +
                                  "            \"comment\": \"\"\n" +
                                  "        }\n    ]", contents)
                file_out.write(contents)
        with open(config_path / "input" / "xmos_usb_params.txt") as file_in:
            with open(config_path / "hardware_test_usb_params.txt", "w") as file_out:
                if bcd_ver != None:
                    file_out.write("SET_USB_BCD_DEVICE %d\n" % bcd_ver) # bcdDevice comes first so it's before USB start command
                file_out.write(file_in.read())

    extra_args = []
    if compatibility_ver:
        extra_args.extend(["--force-compatibility-version", compatibility_ver])
    if verbose:
        extra_args.append('--verbose')
    cmd_opts = [config_path / "xvf3510_data_partition_generator.py",
                "--vfctrl-host-bin-path", host["vfctrl_json"],
                "--dpgen-host-bin-path", host["data_partition_generator"],
                config_file] + extra_args
    ret = subprocess.run([sys.executable, *cmd_opts.split()], capture_output=True, text=True)
    if verbose:
        print(ret.stdout)
    if not compatibility_ver:
        compatibility_ver = get_firmware_version()
    return config_path / "output" / ("data_partition_%s_%s_v%s.bin" % (which, Path(config_file).stem, compatibility_ver.replace(".", "_")))


def dfu_add_suffix(host, boot_bin, data_bin):
    boot_dfu = boot_bin + ".dfu"
    data_dfu = data_bin + ".dfu"
    host['dfu_suffix_generator']("0x20B1", "0x0014", "0x0001", boot_bin, boot_dfu)
    host['dfu_suffix_generator']("0x20B1", "0x0014", "0x0001", data_bin, data_dfu)
    return boot_dfu, data_dfu


def dfu_write_upgrade(host, boot_dfu, data_dfu, skip_boot_image=False, verbose=False):
    print("Writing upgrade...")
    extra_args = []
    if skip_boot_image:
        extra_args += ['--skip-boot-image']
    if not verbose:
        extra_args += ['--quiet']
    ret = subprocess.run([host['dfu_usb'], *extra_args.split(), "write_upgrade", boot_dfu, data_dfu], capture_output=True, text=True)
    if verbose:
        print(ret.stdout)
    print("Waiting for firmware to reboot...")
    verbose_sleep(15)


def check_bld_message(host_bin_paths, expected_msg, vfctrl_flags=""):
    print("Checking firware version...")
    msg = host_bin_paths["vfctrl_usb"].bake("--no-check-version").get_bld_msg().strip()
    if f"GET_BLD_MSG: {expected_msg}" not in msg:
        raise HardwareTestException(
            f"'{expected_msg}' not found in build message. Build message:\n{msg}"
        )


def get_xplay_version():
    try:
        ret = subprocess.run(["xplay", "--version"], capture_output=True, check=True, text=True)
        output = ret.stdout
    except subprocess.CalledProcessError:
        output = "1.0" # heuristic: if it does not understand version command it must be 1.0
    return re.search(r"\b\d+\.\d+\b", output).group(0)


def find_alsa_device(alsa_output, vendor_str_search="Adaptive"):
    """ Looks for the vendor_str_search in aplay or arecord output """

    vendor_str_found = False
    for line in alsa_output:
        if vendor_str_search not in line:
            continue
        vendor_str_found = True
        card_num = int(line[len('card '):line.index(':')])
        dev_str = line[line.index('device'):]
        dev_num = int(dev_str[len('device '):dev_str.index(':')])
    if not vendor_str_found:
        raise HardwareTestException(
            f'Could not find "{vendor_str_search}"" in alsa output:\n'
            f"{alsa_output}"
        )
    return card_num, dev_num

def find_aplay_device(vendor_str_search="Adaptive"):
    ret = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
    return find_alsa_device(ret.stdout.splitlines(), vendor_str_search)


def find_arecord_device(vendor_str_search="Adaptive"):
    ret = subprocess.run(["arecord", "-l"], capture_output=True, text=True)
    return find_alsa_device(ret.stdout.splitlines(), vendor_str_search)

def find_xplay_device_idx(product_string, in_out_string):
    XPLAY_REQUIRED_VERSION = "1.2"
    if get_xplay_version() != XPLAY_REQUIRED_VERSION:
        raise HardwareTestException("Did not detect xplay version %s" % XPLAY_REQUIRED_VERSION)
    xplay_device_idx = None
    ret = subprocess.run(["xplay", "-l"], capture_output=True, text=True)
    lines = ret.stdout.splitlines()
    for line in lines:
        found = re.search(r"Found Device (\d): %s.*%s" % (product_string, in_out_string), line)
        if found:
            xplay_device_idx = found.group(1)
    if xplay_device_idx is None:
        raise HardwareTestException(
            f'Could not find "{product_string}" in xplay output:\n'
            f"{lines}")
    return xplay_device_idx

class audio_player:
    def __init__(self, audio_file, device_string, rate):
        if platform == "darwin":
            self.dev = find_xplay_device_idx(device_string, "/[^0][0-9]*out") # non-zero output channel count
        else:
            self.dev = find_aplay_device(device_string)
        self.play_file = audio_file
        self.process = None
        self.rate = rate

    def play_background(self):
        if platform == "darwin":
            cmd = f"-p {self.play_file} -r {self.rate} -d {self.dev}"
            self.process = subprocess.Popen(["xplay", *cmd.split()])
        else:
            cmd = f"{self.play_file} -r {self.rate} -D hw:{self.dev[0]},{self.dev[1]}"
            self.process = subprocess.Popen(["aplay", *cmd.split()])

    def end_playback(self):
        if self.process.poll() is None:
            self.process.terminate()

    def wait_to_complete(self):
        self.process.wait()

    def play_to_completion(self):
        self.play_background()
        self.wait_to_complete()

class audio_recorder:
    def __init__(self, audio_file, device_string, rate, start_trim_s=0.0, end_trim_s=0.0):
        if platform == "darwin":
            self.dev = find_xplay_device_idx(device_string, " [^0][0-9]*in/") # non-zero input channel count
        else:
            self.dev = find_arecord_device(device_string)
        self.process = None
        self.tmp_wav_file = "tmp.wav"
        self.record_file = audio_file
        self.rate = rate
        self.start_trim_s = start_trim_s
        self.end_trim_s = end_trim_s

    def record_background(self):
        if platform == "darwin":
            cmd = f"-R {self.record_file} -r {self.rate} -b 32 -d {self.dev}"
            self.process = subprocess.Popen(["xplay", *cmd.split()])
        else:
            cmd = f"{self.tmp_wav_file} -f S32_LE -c 2 -r {self.rate} -D plughw:{self.dev[0]},{self.dev[1]}"
            self.process = subprocess.Popen(["arecord", *cmd.split()])

    def end_recording(self):
        self.process.terminate()
        if platform == "darwin":
            # xplay leaves the header unpopulated on terminate so fix it
            subprocess.run(["sox", "--ignore-length", f"{self.record_file}", f"{self.tmp_wav_file}"])
        ret = subprocess.run(["soxi", "-D", f"{self.tmp_wav_file}"], capture_output=True, text=True)
        capture_len = float(ret.stdout)
        assert capture_len > (self.start_trim_s + self.end_trim_s), f"Not enough recorded audio: {capture_len}s, {self.start_trim_s + self.end_trim_s}s needed"
        cmd = f"{self.tmp_wav_file} {self.record_file} trim {self.start_trim_s} {-self.end_trim_s}"
        subprocess.run(["sox", *cmd.split()])

def record_and_play(play_file, play_device, record_file, record_device, rate=None, play_rate=None, rec_rate=None, trim_ends_s=0.0):
    if play_rate is None and rec_rate is None:
        play_rate = rec_rate = rate
    player = audio_player(play_file, play_device, play_rate)
    recorder = audio_recorder(record_file, record_device, rec_rate, start_trim_s=trim_ends_s, end_trim_s=trim_ends_s)
    recorder.record_background()
    print("Recording and playing audio...")
    player.play_to_completion()
    recorder.end_recording()
    # Belt and braces as xplay doesn't alway exit nicely
    if platform == "darwin":
        subprocess.run(["killall", "xplay"])

def play_and_record(play_file, play_device, record_file, record_device, rate=None, play_rate=None, rec_rate=None, trim_ends_s=0.0):
    if play_rate is None and rec_rate is None:
        play_rate = rec_rate = rate
    player = audio_player(play_file, play_device, play_rate)
    recorder = audio_recorder(record_file, record_device, rec_rate, start_trim_s=trim_ends_s, end_trim_s=trim_ends_s)
    player.play_background()
    recorder.record_background()
    print("Playing and recording audio...")
    player.wait_to_complete()
    recorder.end_recording()
    # Belt and braces as xplay doesn't alway exit nicely
    if platform == "darwin":
        subprocess.run(["killall", "xplay"])

def prepare_4ch_wav_for_harness(input_file_name, output_file_name = "output.wav"):
    gen_pdm_and_pack_ref(input_file_name, output_file_name)
    return output_file_name


def correlate_and_diff(output_file, input_file, out_ch_start_end, in_ch_start_end, skip_seconds_start, skip_seconds_end, tol, corr_plot_file=None, verbose=False):
    rate_usb_out, data_out = scipy.io.wavfile.read(output_file)
    rate_usb_in, data_in = scipy.io.wavfile.read(input_file)
    print(f"rate_usb_in={rate_usb_in}, rate_usb_out={rate_usb_out}")
    if rate_usb_out != rate_usb_in:
        assert False, "input and output file rates are not equal"

    #TODO handle dtypes not being same
    assert data_in.dtype == data_out.dtype, "input and output data_type are not same"

    assert out_ch_start_end[1]-out_ch_start_end[0] == in_ch_start_end[1]-in_ch_start_end[0], "input and output files have different channel nos."


    skip_samples_start = int(rate_usb_out * skip_seconds_start)
    skip_samples_end = int(rate_usb_out * skip_seconds_end)
    data_in = data_in[:,in_ch_start_end[0]:in_ch_start_end[1]+1]
    data_out = data_out[:,out_ch_start_end[0]:out_ch_start_end[1]+1]

    data_in_small = data_in[skip_samples_start:64000+skip_samples_start, :].astype(np.float64)
    data_out_small = data_out[skip_samples_start:64000+skip_samples_start, :].astype(np.float64)

    #TODO find correlations channel-wise
    corr = scipy.signal.correlate(data_in_small[:, 0], data_out_small[:, 0], "full")
    delay = (corr.shape[0] // 2) - np.argmax(corr)
    print(f"delay = {delay}")

    if corr_plot_file != None:
        plt.plot(corr)
        plt.savefig(corr_plot_file)
        plt.clf()
    delay_orig = delay

    #assert if output is ahead of the input
    #assert delay >= 0, "scipy.signal.correlate indicates output ahead of input!"
    #TODO figure out why delay is negative in the first place
    if delay < 0:
        temp = data_in
        data_in = data_out
        data_out = temp
        delay = -delay


    data_size = min(data_in.shape[0], data_out.shape[0])
    data_size -= skip_samples_end

    print(f"compare {data_size - skip_samples_start} samples")

    if verbose:
        for i in range(100):
            print("%d, %d"%(data_in[skip_samples_start+i, 0], data_out[skip_samples_start + delay+i, 0]))

    num_channels = out_ch_start_end[1]-out_ch_start_end[0]+1
    all_close = True
    for ch in range(num_channels):
        print(f"comparing ch {ch}")
        close = np.isclose(
                    data_in[skip_samples_start : data_size - delay, ch],
                    data_out[skip_samples_start + delay : data_size, ch],
                    atol=tol,
                )
        print(f"ch {ch}, close = {np.all(close)}")

        if verbose:
            int_max_idxs = np.argwhere(close[:] == False)
            print("shape = ", int_max_idxs.shape)
            print(int_max_idxs)
            if np.all(close) == False:
                if int_max_idxs[0] != 0:
                    count = 0
                    for i in int_max_idxs:
                        if count < 100:
                            print(i, data_in[skip_samples_start+i, ch], data_out[skip_samples_start + delay + i, ch])
                            count += 1

        diff = np.abs((data_in[skip_samples_start : data_size - delay, ch]) - (data_out[skip_samples_start + delay : data_size, ch]))
        max_diff = np.amax(diff)
        print(f"max diff value is {max_diff}")
        all_close = all_close & np.all(close)

    print(f"all_close: {np.all(all_close)}")
    return all_close, delay_orig

# This function finds all of the zero crossings and then does and RMS calculation for each cycle
# It to indicate a stretched wave, amplitude change or signal dropout
# This only really works for sine waves and uses time domain techniques
# Note num_half_cycles_per_rms which takes account of (kind of) aliasing of the time domain,
# for example when we see a 3kHz sine wave sampled at 16kHz. You get patter repeating every 3 whole cycles
# In the frequency domain it's all fine but in time domain you need to expect that the PCM samples will
# vary over 3 cycles in a repeated pattern.
def analyse_sine_rms(input_file, in_channel, num_half_cycles_per_rms, verbose=False):
    rate_usb_in, data_in = scipy.io.wavfile.read(input_file)
    audio = data_in[:,in_channel].astype(np.float64) / 2**31

    print(f"Computing stats on {audio.shape[0]} samples")

    def get_zero_crossings(array):
        sdiff = np.diff(np.sign(array))
        rising_1 = (sdiff == 2)
        rising_2 = (sdiff[:-1] == 1) & (sdiff[1:] == 1)
        rising_all = rising_1
        rising_all[1:] = rising_all[1:] | rising_2

        falling_1 = (sdiff == -2) #the signs need to be the opposite
        falling_2 = (sdiff[:-1] == -1) & (sdiff[1:] == -1)
        falling_all = falling_1
        falling_all[1:] = falling_all[1:] | falling_2

        indices_rising = np.where(rising_all)[0]
        indices_falling = np.where(falling_all)[0]
        indices_both = np.where(rising_all | falling_all)[0]

        return indices_both

    zero_crossings = get_zero_crossings(audio)
    if zero_crossings.shape[0] == 0:
        return 0.0, 0.0, 0.0, 0.0

    num_samples = zero_crossings[-num_half_cycles_per_rms] - zero_crossings[0]
    num_samps_per_half_cycle = (num_samples/(zero_crossings.shape[0]-num_half_cycles_per_rms))
    measured_freq = rate_usb_in/2/num_samps_per_half_cycle

    if verbose:
        print(f"Zero crossings: {zero_crossings.shape[0]}, freq: {measured_freq}")
    rms_array = []

    # Now calculate the RMS for each half wave in turn. Takes about 5s per miute of audio
    for wave_count in range(0,zero_crossings.shape[0] - 1, num_half_cycles_per_rms):
        idx0 = zero_crossings[wave_count]
        idx1 = zero_crossings[wave_count + 1]
        rms = np.sqrt(np.mean(np.absolute(audio[idx0:idx1])**2))
        # print(idx0, idx1, audio[idx0:idx1], rms)
        rms_array.append(rms)
    rms_array = np.array(rms_array)

    if verbose:
        print(f"argmin: {np.argmin(rms_array)}, argmax: {np.argmax(rms_array)}")
        print(f"num_samps_per_half_cycle: {num_samps_per_half_cycle}")
        print(rms_array.shape, rms_array)
        cycles = 3
        half_cycles = cycles * 2
        for idx in range(0,100,half_cycles):
            print(np.sum(rms_array[idx:idx+half_cycles]))
        print(audio)
        print(zero_crossings)


    return rms_array.mean(), rms_array.max(), rms_array.min(), measured_freq

def is_sine_good(input_file, channel, expected_hz, sine_peak_amplitude, rtol=0.0001, rtol_gain=0.1, verbose=False, num_half_cycles_per_rms=1):
    # Note we don't use abs_tol as numbers are never normally close to zero so leave as default zero
    expected_rms = sine_peak_amplitude / math.sqrt(2)

    if verbose:
        print(f"Analysing file {input_file}, channel {channel}")
    mean_rms, max_rms, min_rms, measured_freq = analyse_sine_rms(input_file, channel, num_half_cycles_per_rms, verbose=False)

    if verbose:
        print(f"Expected RMS: {expected_rms}, mean RMS: {mean_rms}, max RMS: {max_rms}, min RMS: {min_rms}")
        print(f"Expected Hz: {expected_hz}, Actual Hz: {measured_freq}")
    dropout_ok = math.isclose(mean_rms, min_rms, rel_tol=rtol)
    injected_noise_ok = math.isclose(mean_rms, max_rms, rel_tol=rtol)
    volume_flat = dropout_ok or injected_noise_ok
    gain_ok = math.isclose(mean_rms, expected_rms, rel_tol=rtol_gain)
    frequency_ok = math.isclose(expected_hz, measured_freq, rel_tol=rtol)

    if verbose:
        print(f"Dropout OK: {dropout_ok}")
        print(f"Injected noise OK: {injected_noise_ok}")
        print(f"Volume flat OK: {volume_flat}")
        print(f"Gain OK: {gain_ok}, ratio: {mean_rms/expected_rms}")
        print(f"Frequency OK: {frequency_ok}")

    return dropout_ok and injected_noise_ok and gain_ok

def get_app_directory():
    return str(APP_PATH)

def reset_target():
    print("Resetting target...")

    subprocess.run(["xgdb", "-batch", "-ex", "connect --reset-to-mode-pins", "-ex", "detach")

    # alternative way to reboot using DFU utility
    #host['dfu_usb'].reboot()

    print("Waiting for firmware to boot...")
    verbose_sleep(15)
