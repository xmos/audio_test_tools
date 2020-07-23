#include <platform.h>
#include <xscope.h>

extern "C" {
void main_tile0(chanend, chanend);
void main_tile1(chanend);
}

int main (void)
{
  chan xscope_chan, memshare_chan;
  par
  {
    xscope_host_data(xscope_chan);
    on tile[0]: main_tile0(xscope_chan, memshare_chan);
    on tile[1]: main_tile1(memshare_chan);
  }
  return 0;
}

