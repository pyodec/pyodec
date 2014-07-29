init_from pyodec.core import FileDecoder, VariableList, FixedVariableList
import numpy as np
import os
import time
import gzip
from datetime import datetime as dt
from calendar import timegm

class ASCSdrD(FileDecoder):
    # variables
    init_fixed_vars = FixedVariableList()
    init_fixed_vars.addvar('HEIGHT','m AGL','int',np.arange(25)*10+10)
    init_vars = VariableList()
    init_vars.addvar('DATTIM',   'seconds since 1970-01-01 00:00 UTC',int,1,'S')
    init_vars.addvar('STNAME',   'Station Name',str,20,'')
    init_vars.addvar('WSPD',     'Wind speed','float32',(25,),'m/s')
    init_vars.addvar('WDIR',     'Wind direction','float32',(25,),'deg')
    init_vars.addvar('WVERT',    'Vertical wind speed','float32',(25,),'m/s')
    init_vars.addvar('UINT',     'U-beam intensity','float32',(25,),'mv')
    init_vars.addvar('VINT',     'V-beam intensity','float32',(25,),'mv')
    init_vars.addvar('WINT',     'W-beam intensity','float32',(25,),'mv')
    init_vars.addvar('SNRU',     'U-beam SNR','float32',(25,),'')
    init_vars.addvar('SNRV',     'V-beam SNR','float32',(25,),'')
    init_vars.addvar('SNRW',     'W-beam SNR','float32',(25,),'')
    init_vars.addvar('SDS',      '','float32',(25,),'')
    init_vars.addvar('SDW',      '','float32',(25,),'')
    init_vars.addvar('GUST',     'Wind gust speed','float32',(25,),'m/s')
    init_vars.addvar('TMPC',     'Air Temperature C','float32',1,'C')
    init_vars.addvar('BATV',     'Battery Voltage','float32',1,'V')
    init_vars.addvar('ANTSTAT',  'Anteanna Status',str,5,'')
    init_vars.addvar('HEAT',     'Heater Status',str,5,'')
    init_vars.addvar('GEN',      'Generator Status',str,5,'')
    init_vars.addvar('FUEL',     'Fuel Status',str,5,'')
    init_vars.addvar('RAIN',     'Precipitation Detector','float32',1,'')
    init_vars.addvar('SNOW',     'Snow Detector','float32',1,'')
    init_vars.addvar('RH',       'Relative Humidity','float32',1,'%')
    init_vars.addvar('PRES',     'Surface Pressure','float32',1,'hPa')
    init_vars.addvar('DEWP',     'Dew point temperature','float32',1,'C')
    
    # instance variables
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


# define any fixed variables which would be beneficial to our cause


decoder = ASCSdrD()