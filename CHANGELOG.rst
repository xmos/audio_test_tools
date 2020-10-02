Audio test tools change log
===========================

4.3.0
-----

  * ADDED: test_wav_xscope test feature
  * ADDED: lib_xs3_math as a library upon which this one depends
  * ADDED: ATT-specific synonyms for DSP and XS3-math types
  * CHANGED: use Voice Toolbox to count leading sign bits instead of DSP library

4.2.0
-----

  * ADDED: new function for parsing wav data: audio_wav_utils.iter_frames

4.1.1
-----

  * CHANGED: minimum version of lib_dsp required moved to 6.0.0
  * CHANGED: use v0.12.1 of Jenkins shared library

4.1.0
-----

  * FIXED: audio_generation.py get_noise for non-integer durations

4.0.0
-----

  * CHANGED: Build files updated to support new "xcommon" behaviour in xwaf.

3.0.0
-----

  * CHANGED: Have a separate file contain wav file processing related python functions.


2.1.0
-----

  * ADDED: Use pipenv to set up python environment

2.0.0
-----

  * REMOVED: moved dsp_complex_fp to lib_dsp
  * FIXED: Fixed scaling of floating point fft

1.6.0
-----

  * ADDED: common_utils.py for loading/saving json/ini configs (with '//' comments)
  * FIXED: Enabled more tests on Jenkins
  * REMOVED: Function to load ini files

1.5.0
-----

  * ADDED: Pipfile + setup.py for pipenv support

1.4.0
-----

  * ADDED: Function to parse and convert ini files
  * ADDED: python_setup.bat
  * CHANGED: Read and write files as binary in process_wav.xc
  * UPDATED: Python code be python 3 compatible

1.3.0
-----

  * CHANGED: Updated lib_voice_toolbox dependency to v5.0.0

1.2.1
-----

  * CHANGED: att_process_wav output wav is now optional

1.2.0
-----

  * ADDED: seed parameter to audio_generation.get_noise function
  * FIXED: audio_utils.convert_to_32_bit not checking if data is already int32

1.1.0
-----

  * Added function to limit the number of bits represented by a complex array
  * Added 16 bit functions

1.0.3
-----

  * ADDED: get_erle() function, moved from lib_audio_pipelines
  * ADDED: generation of delayed echo function

1.0.2
-----

  * Updated version information

0.0.0
-----

  * Initial version
