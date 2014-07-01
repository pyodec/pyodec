from pyodec.core import FileDecoder, VariableList, FixedVariableList
import numpy as np
import os
import time
import gzip
from datetime import datetime as dt
from calendar import timegm

class ASCSdrD(FileDecoder):
    i=0
    select_keys=[]
    def on_line(self, line):
        self.i+=1
        l = line.split(',')
        if self.i == 1:
            # header line, learn great things!
            # we are going to learn exactly what place in each row, the variables are
            # this is assuming only 250 values per variable - this is in the order of the HDF
            l = np.array(l[2:], dtype='|S10')
            rng = np.arange(l.shape[0])
            self.select_keys = [
                rng[l=='sitename'],
                rng[(l == 'ws10') | (l == 'ws250')],
                rng[(l == 'wd10') | (l == 'wd250')],
                rng[(l == 'w10') | (l == 'w250')],
                rng[(l == 'iu10') | (l == 'iu250')],
                rng[(l == 'iv10') | (l == 'iv250')],
                rng[(l == 'iw10') | (l == 'iw250')],
                rng[(l == 'snru10') | (l == 'snru250')],
                rng[(l == 'snrv10') | (l == 'snrv250')],
                rng[(l == 'snrw10') | (l == 'snrw250')],
                rng[(l == 'sds10') | (l == 'sds250')],
                rng[(l == 'sdw10') | (l == 'sdw250')],
                rng[(l == 'gspd10') | (l == 'gspd250')],
                rng[l == 'tempc'],
                rng[l == 'batv'],
                rng[l == 'antstatus'],  # str
                rng[l == 'heater'],  # str
                rng[l == 'genon'],  # str
                rng[l == 'fuel'],  # str
                rng[l == 'rain'],
                rng[l == 'snow'],
                rng[l == 'rh'],
                rng[l == 'pressure'],
                [-1],  # I am assuming dewpoint will remain last ('dewpt')
            ]
            return False
        try:
            # get the date
            d = l[0] + l[1]
            t = time.mktime(time.strptime(d, '%m/%d/%Y%H:%M:%S'))
        except ValueError:
            return None
        # again. we are going to assume the dataset is not changing!
        data = l[2:]
        row = [t]
        for k in self.select_keys:
            if len(k) == 2:
                row.append(np.array(data[k[0]:k[1] + 1],dtype=np.float32)) 
            else:
                row.append(data[k[0]])
        # and produce this delightful set of datas!
        return row
    
    
    def decode_proc(self, filepath, limit=1000):
        # open the file
        if not os.path.exists(filepath):
            print "NO SUCH FILE"
            return 
        gzfh = gzip.open(filepath,'r')
        for d in self.read_lines_gen(limit, gzfh):
            #every 1000 obs, this should return somethin
            yield d
            
        gzfh.close()


# define the dtypes of the variables we produce here (in the correct order!)
V = VariableList()
V.addvar('DATTIM','seconds since 1970-01-01 00:00 UTC',int,1,'S')
V.addvar('STNAME','Station Name',str,20,'')
V.addvar('WSPD','Wind speed','float32',(25,),'m/s')
V.addvar('WDIR','Wind gust','float32',(25,),'deg')
V.addvar('WVERT','','float32',(25,),'m/s')
V.addvar('UINT','','float32',(25,),'mv')
V.addvar('VINT','','float32',(25,),'mv')
V.addvar('WINT','','float32',(25,),'mv')
V.addvar('SNRU','','float32',(25,),'')
V.addvar('SNRV','','float32',(25,),'')
V.addvar('SNRW','','float32',(25,),'')
V.addvar('SDS','','float32',(25,),'')
V.addvar('SDW','','float32',(25,),'')
V.addvar('GUST','','float32',(25,),'m/s')
V.addvar('TMPC','','float32',1,'C')
V.addvar('BATV','','float32',1,'V')
V.addvar('ANTSTAT','',str,5,'')
V.addvar('HEAT','',str,5,'')
V.addvar('GEN','',str,5,'')
V.addvar('FUEL','',str,5,'')
V.addvar('RAIN','','float32',1,'')
V.addvar('SNOW','','float32',1,'')
V.addvar('RH','','float32',1,'%')
V.addvar('PRES','','float32',1,'hPa')
V.addvar('DEWP','','float32',1,'C')

# define any fixed variables which would be beneficial to our cause
FV = FixedVariableList()
FV.addvar('HEIGHT','m AGL','int',np.arange(25)*10+10)

decoder = ASCSdrD(vars=V, fixed_vars=FV)