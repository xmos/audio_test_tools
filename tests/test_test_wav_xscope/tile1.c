#include <print.h>
#include <stddef.h>
#include <stdio.h>
#include <xcore/assert.h>
#include <xcore/channel.h>
#include <xcore/channel_transaction.h>
#include <xcore/hwtimer.h>
#include <xcore/parallel.h>
#include <xcore/select.h>



void main_tile1(chanend_t memshare_end)
{
    printf("tile1 done..\n");
}
