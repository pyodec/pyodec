from pyodec.core import FileDecoder, VariableList
from pyodec.messages.vaisalacl31 import decoder as msgdecode
import numpy as np
import os
import time
import gzip

"""
CL-31 message #2 with epoch timestamps
"""

class Epcl31D(FileDecoder):
    def on_chunk(self, message):
        # this is an end-spliced message, so we will get the timestamp
        ob = message.split(unichr(001))
        try:
            tmstr = ob[0].strip().split()[-1]
            # don't add extra newlines after the time string if you want to be happy
            otime = float(tmstr)
        except:
            return False
        try:
            data = msgdecode.decode(ob[1])
        except:
            # there was something ugly in this data... serial hiccups.
            data=False
        if data is False:
            return None
        output = (otime,data[0],data[1])
        return output
    
    def decode_proc(self, filepath, yieldcount=1000):
        # open the file
        if not os.path.exists(filepath):
            print "NO SUCH FILE"
            return 
        gzfh = self.open_ascii(filepath)
        for d in self.read_chunks_gen(yieldcount, gzfh,end=unichr(004)):
            yield d
        gzfh.close()

decoder = Epcl31D(inherit=msgdecode)
# prepend DATTIM to the variable list by adding and resetting the variable. A necessary hijack
dattim_var = VariableList()
dattim_var.addvar('DATTIM','seconds since 1970-01-01 00:00 UTC',int,1,'S') 
decoder.vars = dattim_var + decoder.vars

if __name__ == '__main__':
    import sys
    print decoder.vars
    exit();
    src = sys.argv[1]
    k=0
    for o in decoder.decode(src):
        k+=len(o)
        print 'ob',k
        