from pyodec.core import FileDecoder
from pyodec.messages.vaisalact12k import decoder as msgdecode
import numpy as np
import os
import time
import gzip
from datetime import datetime as dt
from calendar import timegm
"""
U of Utah CT-12k: UW string times stored *before* the message
"""

class uuct12kD(FileDecoder):
    def on_chunk(self, message):
        # this is an end-spliced message, so we will get the timestamp

        ob = message.split("\n",1)
        data = ob[1].replace("\n   ","\n") # remove their spaces
        try:
            tmobj = dt.strptime(ob[0].strip().split('\n')[-1],"%Y%m%d %H%M%S")
            # don't add extra newlines after the time string if you want to be happy
            otime = timegm(tmobj.timetuple())
        except:
            return False
        data = msgdecode.decode(data)
        if data is False:
            return None
        output = (otime,data[0],data[1])
        return output
    
    def decode_proc(self, filepath, yieldcount=1000):
        # open the file
        if not os.path.exists(filepath):
            print "NO SUCH FILE"
            return 
        gzfh = gzip.open(filepath,'r')
        # grab the header - this is an ASN characteristic, sorry general public
        h = gzfh.readline().split(':')
        try:
            # ID is the first element of the header, the common style
            float(h[2])
            ftime = dt.utcfromtimestamp(int(h[4]))
        except:
            # then this is an old style header
            ftime = dt.utcfromtimestamp(int(h[3]))
            # and it can blow up if it is neither of these
        # I am hoping their system plays nice here, and keeps the file schedule as is
        for d in self.read_chunks_gen(yieldcount, gzfh,begin="{:%Y%m%d} ".format(ftime)):
            yield d
        gzfh.close()

decoder = uuct12kD(inherit=msgdecode)
# have to add time to the variable list, since the message decoder doe not decode time
dattim_var = VariableList()
dattim_var.addvar('DATTIM','seconds since 1970-01-01 00:00 UTC',int,1,'S') 
decoder.vars = dattim_var + decoder.vars