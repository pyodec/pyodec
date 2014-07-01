"""
STI sodars, which are currently all in SOCAL, and operate on local time as best
I can tell..
"""
from decoders.core import FileDecoder
import decoders.messages.sodarmsg1 as sd
import time
import os
import datetime as dt



os.environ['TZ']='America/Los_Angeles'
time.tzset()


class STISdr(FileDecoder):
    #code
    def on_chunk(self, message):
        # grab the time from this message
        l=message.split('\n')
        if len(l)<21: return False
        start = time.mktime(dt.datetime.strptime(l[0][5:24],'%m/%d/%Y %H:%M:%S').timetuple())
        end = time.mktime(dt.datetime.strptime(l[0][28:47],'%m/%d/%Y %H:%M:%S').timetuple())
        obtime = (start+end)/2
        decode = sd.decoder.decode(message)
        dat = [obtime]+decode+[start,end]
        return dat
    
    def decode(self, filepath, yieldcount=1000):
        fil = FileDecoder.open_ascii(filepath)
        if not fil:
            print "NO SUCH FILE"
            return
        # delimeter is based on the date string, which is in CA time harumph
        h = fil.readline().split(":")

        try:
            # ID is the first element of the header, the common style
            float(h[2])
            ftime = dt.datetime.fromtimestamp(int(h[4]))
        except:
            # then this is an old style header
            ftime = dt.datetime.fromtimestamp(int(h[3]))
        for d in self.read_chunks_gen(yieldcount,fil, begin=' {:%m/%d/%Y} '.format(ftime)):
            yield d
            
        fil.close()
        

V=sd.decoder.vars
V.addvar('OBSTART','int',1,'Seconds since 1970 1 1 00:00:00 UTC')
V.addvar('OBEND','int',1,'Seconds since 1970 1 1 00:00:00 UTC')

decoder = STISdr(vars=V,fixed_vars=sd.decoder.fixed_vars)
    
if __name__ == "__main__":
    from calendar import timegm
    import numpy as np
    #for ob in decoder.decode('/data/ASN/RAW/IRVS_201403/888250737bc5fd4b6387a6abeef4dcd3.dat.gz'):
    for ob in decoder.decode('/data/ASN/RAW/IRVS_201403/534703e104603156710af77c44225415.dat.gz'):
        print len(ob)
        t = np.array(zip(*ob)[0])
        s=dt.datetime.utcfromtimestamp(ob[0][0])
        e=dt.datetime.utcfromtimestamp(ob[-1][0])
        while s.date() <= e.date():
            print s.date(),s
            day_start = timegm(s.date().timetuple())
            day_end = day_start + 86400
            print day_start,day_end
            print len(np.arange(t.shape[0])[(t>=day_start)&(t<day_end)].tolist())
            s+= dt.timedelta(days=1)