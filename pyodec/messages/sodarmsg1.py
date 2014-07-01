from decoders.core import MessageDecoder, VariableList, FixedVariableList
import numpy as np
import re

"""
read a single messgae from a sodar, using the messageDecoder class
"""

class SdrMsg1(MessageDecoder):
    def decode(self, message):
        obset = []
        l = message.strip().split("\n")
        # get self-defined station name
        r1=l[0].split()
        obset.append(r1[0])
        
        # now read the data lines, 4:
        # note, these are backwards!
        obs = np.zeros((18,19))
        k=0
        for i in np.arange(18)*-1+21:
            dline=l[i].strip().split()
            obs[k]=dline[1:]
            k+=1
        # and make them column wise, and add that to the obset
        obset += obs.T.tolist()
        # and grab the status information from that other status line
        ln = l[2]
        # the other info is silly, and i don't care for it
        #TEMPC:
        ix=re.search("TEMPC:",ln).end()
        obset.append(float(ln[ix:ix+5]))
        #BATTV
        ix=re.search("BATTV:",ln).end()
        obset.append(float(ln[ix:ix+5]))
        # Antenna
        ix=re.search("ANTENNA STATUS:",ln).end()
        ind=re.search("AC STATUS:",ln).start()
        obset.append(ln[ix:ind])
        # AC Status
        ix=re.search("AC STATUS:",ln).end()
        ind=re.search("BATTV:",ln).start()
        obset.append(ln[ix:ind])
        # and save all the 3 status lines
        obset.append('\n'.join(l[:3]))
        return obset
        
        
    
V= VariableList()
V.addvar('STNAME',str,20,'')

V.addvar('WSPD','float32',(18,),'m/s')
V.addvar('WDIR','float32',(18,),'deg')
V.addvar('W','float32',(18,),'m/s')
V.addvar('SDW','float32',(18,),'')
V.addvar('WINT','float32',(18,),'mv')
V.addvar('GUST','float32',(18,),'m/s')
V.addvar('GDIR','float32',(18,),'m/s')
# U
V.addvar('U','float32',(18,),'m/s')
V.addvar('SDU','float32',(18,),'m/s')
V.addvar('NU','float32',(18,),'')
V.addvar('UINT','float32',(18,),'mv')
V.addvar('SNRU','float32',(18,),'')
# V
V.addvar('V','float32',(18,),'m/s')
V.addvar('SDV','float32',(18,),'m/s')
V.addvar('NV','float32',(18,),'')
V.addvar('VINT','float32',(18,),'mv')
V.addvar('SNRV','float32',(18,),'')

V.addvar('NW','float32',(18,),'')
V.addvar('SNRW','float32',(18,),'')

# status and strings
V.addvar('TMPC','float32',1,'C')
V.addvar('BATV','float32',1,'V')
V.addvar('ANTSTAT',str,5,'')
V.addvar('ACSTAT',str,5,'')
V.addvar('STATLINES',str,400,'')


FVars=FixedVariableList()
FVars.addvar('HEIGHT','m AGL',int,np.arange(18)*10 + 30)

decoder = SdrMsg1(vars=V,fixed_vars=FVars)





if __name__ == '__main__':
    msg = """WHPS 03/02/2014 00:15:00 TO 03/02/2014 00:30:00 VR1.48a  4500R   200    90    50    10     0     0
900 10 29 5 0 0 25 15 64 1000 6 5 7 -800 800 -800 800 -600 600 0 10 93 100 63 1 80 7 1 0 0 8 2 30 5 28 5 0 0 0 5 5
3 COMPONENT 18HTS ZENITH 16-16 ARA 093 SEPANG 090 MXHT 0 UNOISE    33 VNOISE    36 WNOISE    35 ANTENNA STATUS:FAULT AC STATUS:N/A BATTV:13.93 TEMPC: 8.6
  HT    SPD  DIR      W    SDW   IW   GSPD GDIR      U    SDU   NU   IU SNRU      V    SDV   NV   IV SNRV   NW SNRW
 200  99.99 9999  99.99  99.99   38  99.99 9999  99.99  99.99   12   34    4  99.99  99.99   23   36    4    4    4
 190  99.99 9999  99.99  99.99   36  99.99 9999  99.99  99.99   11   33    4  99.99  99.99   30   36    5    3    4
 180  99.99 9999  99.99  99.99   37  99.99 9999  99.99  99.99   11   33    4  99.99  99.99   33   36    4    3    4
 170  99.99 9999  99.99  99.99   35  99.99 9999  99.99  99.99    8   35    4  99.99  99.99   38   36    5    4    4
 160  99.99 9999  99.99  99.99   35  99.99 9999  99.99  99.99    9   34    4  99.99  99.99   29   36    4    4    4
 150  99.99 9999  99.99  99.99   37  99.99 9999  99.99  99.99   17   34    4  99.99  99.99   35   36    4    3    4
 140  99.99 9999  99.99  99.99   37  99.99 9999  99.99  99.99   16   34    4  99.99  99.99   37   36    5    3    4
 130  99.99 9999  99.99  99.99   39  99.99 9999  99.99  99.99    5   33    4  99.99  99.99   24   36    4    5    4
 120  99.99 9999  99.99  99.99   36  99.99 9999  99.99  99.99   13   34    4  99.99  99.99   36   36    5    5    4
 110  99.99 9999  99.99  99.99   36  99.99 9999  99.99  99.99   12   33    4  99.99  99.99   37   36    5    5    4
 100  99.99 9999  99.99  99.99   38  99.99 9999  99.99  99.99   13   35    4  99.99  99.99   28   36    4    3    4
  90  99.99 9999  99.99  99.99   37  99.99 9999  99.99  99.99   15   35    4  99.99  99.99   30   36    4    5    4
  80  99.99 9999  99.99  99.99   46  99.99 9999  99.99  99.99    9   36    4  99.99  99.99   18   36    4    9    4
  70  99.99 9999  99.99  99.99   73  99.99 9999  99.99  99.99   21   48    4  99.99  99.99   14   47    4   12    4
  60  99.99 9999  -0.26   0.84   58  99.99 9999  99.99  99.99   26   52    4  99.99  99.99   75   63    5   38    4
  50   2.01  118   0.02   0.47   57   5.61  132  -0.86   0.80   53   53    5  -1.81   1.54   33   48    5   49    5
  40   0.76   83   0.02   0.45   78   2.91  342   0.13   0.50  103   75    6  -0.75   0.38  101   73    6  100    6
  30   0.96  157  -0.03   0.32  151   3.11  166  -0.86   0.42  168  125    7  -0.42   0.31  131  122    7  153    7
"""
    print len(decoder.get_dtype())

    dat = [123123123]+decoder.decode(msg)
    print len(dat)
    np.array(dat,dtype=decoder.get_dtype())