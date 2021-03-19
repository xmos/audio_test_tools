TARGET = XCORE-AI-EXPLORER

APP_NAME = 

SOURCE_DIRS = src .

XCC_FLAGS = -O2 -g -Wall -report -DTEST_WAV_XSCOPE=1

USED_MODULES = lib_voice_toolbox audio_test_tools xscope_fileio

#=============================================================================
# The following part of the Makefile includes the common build infrastructure
# for compiling XMOS applications. You should not need to edit below here.

XMOS_MAKE_PATH ?= ../../..
include $(XMOS_MAKE_PATH)/xcommon/module_xcommon/build/Makefile.common
