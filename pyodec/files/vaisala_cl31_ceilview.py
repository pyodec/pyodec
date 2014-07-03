from decoders.core import FileDecoder
from decoders.messages.vaisalacl31 import decoder as msgdecode
import numpy as np
import os
import time
import gzip
import datetime
from calendar import timegm
"""
Read CL-31 .DAT files produced by ceilview
"""

class CVcl31(FileDecoder):
    #variables
    vars = VariableList()
    vars.addvar('DATTIM','seconds since 1970-01-01 00:00 UTC',int,1,'S') 
    vars += msgdecode.vars
    fixed_vars = msgdecode.fixed_vars
    
    chunks = 0
    def on_chunk(self, message):
        # this is an end-spliced message, so we will get the timestamp
        ob = message.split(unichr(001))
        # time is the last lin of the first chunk of this split
        tmstr = ob[0].strip().split('\n')[-1]
        try:
            otime = timegm(datetime.datetime.strptime(tmstr.strip(),'-%Y-%m-%d %H:%M:%S').timetuple())
        except:
            return False    
        data = msgdecode.decode(ob[1])
        if data is False:
            return False
        output = (otime,data[0],data[1])
        self.chunks +=1
        #print self.chunks
        return output
    
    def decode_proc(self, filepath, yieldcount=1000):
        # open the file
        if not os.path.exists(filepath):
            print "NO SUCH FILE"
            return 
        gzfh = gzip.open(filepath,'r')
        
        for d in self.read_chunks_gen(yieldcount, gzfh, end=unichr(004)):
            if d:
                yield d
        gzfh.close()

decoder = CVcl31()
