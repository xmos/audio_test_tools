// Copyright (c) 2017-2021, XMOS Ltd, All rights reserved
// This software is available under the terms provided in LICENSE.txt.
	.text
    .issue_mode  dual
	.globl	att_burn_thread_div
	.type	att_burn_thread_div,@function
	.cc_top att_burn_thread_div.function,att_burn_thread_div
#define NSTACKWORDS 0
att_burn_thread_div:
	{mkmsk r1, 32; mkmsk r2, 32}
div_loop:
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	divu r0, r1, r2
	bu div_loop

	// RETURN_REG_HOLDER
	.cc_bottom att_burn_thread_div.function
	.set	att_burn_thread_div.nstackwords, NSTACKWORDS
	.globl	att_burn_thread_div.nstackwords
	.set	att_burn_thread_div.maxcores,1
	.globl	att_burn_thread_div.maxcores
	.set	att_burn_thread_div.maxtimers,0
	.globl	att_burn_thread_div.maxtimers
	.set	att_burn_thread_div.maxchanends,0
	.globl	att_burn_thread_div.maxchanends
.Ltmp0:
	.size	att_burn_thread_div, .Ltmp0-att_burn_thread_div

	.globl	att_burn_thread
	.type	att_burn_thread,@function
	.cc_top att_burn_thread.function,att_burn_thread

att_burn_thread:
	bu att_burn_thread

	// RETURN_REG_HOLDER
	.cc_bottom att_burn_thread.function
	.set	att_burn_thread.nstackwords, NSTACKWORDS
	.globl	att_burn_thread.nstackwords
	.set	att_burn_thread.maxcores,1
	.globl	att_burn_thread.maxcores
	.set	att_burn_thread.maxtimers,0
	.globl	att_burn_thread.maxtimers
	.set	att_burn_thread.maxchanends,0
	.globl	att_burn_thread.maxchanends
.Ltmp1:
	.size	att_burn_thread, .Ltmp1-att_burn_thread


    .issue_mode  single

