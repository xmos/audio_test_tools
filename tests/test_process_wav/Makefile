ifeq ($(XCOREAI),0)
TARGET = XCORE-200-EXPLORER
APP_NAME = test_process_wav
XCC_FLAGS = -O2 -g -Wall -report
else
TARGET = XCORE-AI-EXPLORER
APP_NAME = test_process_wav
XCC_FLAGS_AI = -O2 -g -Wall -report
endif


SOURCE_DIRS = src
INCLUDE_DIRS = src

USED_MODULES = audio_test_tools lib_dsp lib_voice_toolbox

#=============================================================================
# The following part of the Makefile includes the common build infrastructure
# for compiling XMOS applications. You should not need to edit below here.

XMOS_MAKE_PATH ?= ../../..
include $(XMOS_MAKE_PATH)/xcommon/module_xcommon/build/Makefile.common
