TARGET = XCORE-200-EXPLORER

APP_NAME = test_wav

SOURCE_DIRS = src

INCLUDE_DIRS = src

XCC_FLAGS = -O2 -g -Wall -fcmdline-buffer-bytes=2048 -report

USED_MODULES = audio_test_tools lib_voice_toolbox

#=============================================================================
# The following part of the Makefile includes the common build infrastructure
# for compiling XMOS applications. You should not need to edit below here.

XMOS_MAKE_PATH ?= ../../..
include $(XMOS_MAKE_PATH)/xcommon/module_xcommon/build/Makefile.common
