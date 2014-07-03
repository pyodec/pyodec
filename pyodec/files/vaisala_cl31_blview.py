from decoders.core import FileDecoder
from decoders.messages.vaisalacl31his import decoder as msgdecode
import numpy as np
import os
import time
import gzip

class VHisCL31D(FileDecoder):
    def on_line(self, line):
        if len(line) < 700:
            return None
        dat = msgdecode.decode(line)
        if dat:
            print dat[0],dat[1].shape
            return dat
        return False
    
    def decode_proc(self, filepath, yieldcount=1000):
        # open the file
        if not os.path.exists(filepath):
            print "NO SUCH FILE"
            return 
        gzfh = gzip.open(filepath,'r')
        for d in self.read_lines_gen(yieldcount, gzfh):
            yield d
        gzfh.close()

decoder = VHisCL31D(inherit=msgdecode)

if __name__ == "__main__":
    src = '/data/ASN/RAW/ROOSC_201301/a5480d2cf2198d25ea4668c1f44e0e8e.dat.gz'
    k=0
    for o in decoder.decode(src):
        k+=len(o)
        d=o
        print d[0][0],d[1][0],d[2][0],d[3][0],
        #exit()
        #print 'ob',k,