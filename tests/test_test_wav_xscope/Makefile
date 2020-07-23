.PHONY: default_
default_: all

TARGET_FLAG ?= -target=XCORE-200-EXPLORER
# TARGET_FLAG ?= -target=XCORE-AI-EXPLORER
XCC ?= xcc
GCC ?= gcc

objects := tile0.o tile1.o main.o
depfiles = $(objects:%.o=%.d)
include $(wildcard $(depfiles))

main.xe : $(objects) config.xscope
	$(XCC) $(TARGET_FLAG) -o $@ $^

%.o : %.c
	$(XCC) -c -march=xs2a -o $@ $< -Wc,-mcmodel=small -O3 -MD -MF $*.d

%.o : %.xc
	$(XCC) -c $(TARGET_FLAG) -o $@ $< -MD -MF $*.d

host/xscope_host_endpoint : host/host.c
	$(GCC) -o $@ $< -I ${XMOS_TOOL_PATH}/include ${XMOS_TOOL_PATH}/lib/xscope_endpoint.so -std=c99

.PHONY: all
all: main.xe host/xscope_host_endpoint

.PHONY: clean
clean:
	rm -f $(wildcard $(objects) $(depfiles) host/xscope_host_endpoint)

