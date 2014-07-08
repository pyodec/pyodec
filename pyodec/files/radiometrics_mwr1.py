from decoders.core import FileDecoder, VariableList, FixedVariableList
import numpy as np
from scipy.interpolate import interp1d as interp
import os
import time
import calendar

# its just easier to specify the heights manually
heights = [  0.  , 0.05, 0.1 , 0.15, 0.2 , 0.25, 0.3 , 0.35,
         0.4 , 0.45, 0.5 , 0.6 , 0.7 , 0.8 , 0.9 , 1.  ,
         1.1 , 1.2 , 1.3 , 1.4 , 1.5 , 1.6 , 1.7 , 1.8 ,
         1.9 , 2.  , 2.25, 2.5 , 2.75, 3.  , 3.25, 3.5 ,
         3.75, 4.  , 4.25, 4.5 , 4.75, 5.  , 5.25, 5.5 ,
         5.75, 6.  , 6.25, 6.5 , 6.75, 7.  , 7.25, 7.5 ,
         7.75, 8.  , 8.25, 8.5 , 8.75, 9.  , 9.25, 9.5 ,
         9.75, 10.  ]

# and this is the resolution/scale that we will save the data at
outheight = np.arange(0., 10.0, .05)


class RadMWR1D(FileDecoder):
    vars = VariableList()
    vars.addvar('DATTIM','Observation Time',int,1,'Seconds since 1970-01-01 00:00:00 UTC')
    vars.addvar('ZENITH_TEMP','', 'float32', (58,), 'K')
    vars.addvar('ZENITH_RH', '','float32', (58,), '%')
    vars.addvar('ZENITH_VAPDEN','', 'float32', (58,), 'g/m^3')
    vars.addvar('ZENITH_LIQDEN','', 'float32', (58,), 'g/m^3')
    vars.addvar('ANGLE_N_TEMP','', 'float32', (58,), 'K')
    vars.addvar('ANGLE_N_RH','', 'float32', (58,), '%')
    vars.addvar('ANGLE_N_VAPDEN','', 'float32', (58,), 'g/m^3')
    vars.addvar('ANGLE_N_LIQDEN','', 'float32', (58,), 'g/m^3')
    vars.addvar('ANGLE_S_TEMP','', 'float32', (58,), 'K')
    vars.addvar('ANGLE_S_RH','', 'float32', (58,), '%')
    vars.addvar('ANGLE_S_VAPDEN','', 'float32', (58,), 'g/m^3')
    vars.addvar('ANGLE_S_LIQDEN','', 'float32', (58,), 'g/m^3')
    vars.addvar('ANGLE_A_TEMP','', 'float32', (58,), 'K')
    vars.addvar('ANGLE_A_RH','', 'float32', (58,), '%')
    vars.addvar('ANGLE_A_VAPDEN','', 'float32', (58,), 'g/m^3')
    vars.addvar('ANGLE_A_LIQDEN','', 'float32', (58,), 'g/m^3')
    vars.addvar('TAIR', 'float32','', 1, 'K')
    vars.addvar('RELH', 'float32','', 1, '%')
    vars.addvar('PRES', 'float32','', 1, 'hPa')
    vars.addvar('TIR', 'float32','', 1, 'K')
    vars.addvar('RAIN', 'float32','', 1, 'bin')
    vars.addvar('INTVAP', 'float32','', 1, 'cm')
    vars.addvar('INTLIQ', 'float32','', 1, 'mm')
    vars.addvar('CLDBASE', 'float32','', 1, 'km')
    fixed_vars = FixedVariableList()
    fixed_vars.addvar('HEIGHT', 'm AGL', int, np.array(heights) * 1000)  # outheight*1000)
    # code
    ob_persist = [0] * 25
    def on_line(self, dat):
        l = dat.split(',')
        # check
        if l[2] == '201':
            # this is the last element of the ob!!!
            self.ob_persist[17] = float(l[3])  # tair (k)
            self.ob_persist[18] = float(l[4])  # RH
            self.ob_persist[19] = float(l[5])  # pres hPa
            self.ob_persist[20] = float(l[6])  # tIR (k)
            self.ob_persist[21] = float(l[7])  # rain
            # grab the time

            # if this is a good ob, return it!
            if self.ob_persist[0] > 0:
                prep = [r for r in self.ob_persist]
                self.ob_persist = [0] * 25
                return prep
            # reset the ob to be blank, although we did not actually return said ob
            self.ob_persist = [0] * 25

            # can compare rowlenghts to see if there is a problem later

        k = int(l[2])
        if len(l) < 2:
            return False
        elif k == 301:
            # integrated vapor, liquid and cloud heights
            # THIS HAPPENS TWICE IN MANY OBS - we only grab the last one
            self.ob_persist[22] = float(l[3])
            self.ob_persist[23] = float(l[4])
            self.ob_persist[24] = float(l[5])
        elif k == 31:
            # this is location/time data..
            # so, we will return the location information in a special way - a defined way
            if float(l[9]) < 6:
                # then there were not enough satellites for us to trust this fix
                return False
            # here we do the testing, did hte location change much?
            if "location" in self.state.keys():
                if abs(self.state['location'][0] - float(l[4]) / 100) > .01  or abs(self.state['location'][1] - float(l[5]) / 100) > .01:
                    # then something chaged!
                    tm = calendar.timegm(time.strptime(l[1], '%m/%d/%y %H:%M:%S'))
                    # reset the meta variable, so we don't call this too many times
                    self.state['location'] = [float(l[4]) / 100, float(l[5]) / 100]
                    return self.yield_update(['LOC', tm, float(l[4]) / 100, float(l[5]) / 100, float(l[10])])
        elif k < 401:
            # this is a variable of something other than the core vars -IGNORING
            return False
        else:
            # grab the time if it is not defined

            if self.ob_persist[0] == 0:
                self.ob_persist[0] = calendar.timegm(time.strptime(l[1], '%m/%d/%y %H:%M:%S'))
            try:
                dat = interp(heights, l[4:-1], 'nearest')
            except:
                # if this fails, this is a sign that the data is effectively null
                self.ob_persist[0] = 0
                return

            if 'Zen' == l[3][:3]:
                rowkey = 1
            if '(N)' in l[3]:
                rowkey = 5
            if '(S)' in l[3]:
                rowkey = 9
            if '(A)' in l[3]:
                rowkey = 13
            # and pick the variable
            if l[2] == '401':
                rowkey += 0
            elif l[2] == '402':
                rowkey += 2
            elif l[2] == '403':
                rowkey += 3
            else:
                rowkey += 1

            # and save the interpolated data
            self.ob_persist[rowkey] = l[4:-1]  # dat(outheight)
            # grab the time with 401/zenith, and that is how it is going to happen.

    def decode_proc(self, filepath, yieldcount=1000, location=False):
        # open the file
        self.ob_persist = [0] * 24
        self.meta = False
        if location:
            # they want to be updated if the location changes
            self.state['location'] = location
        fh = self.open_ascii(filepath)
        if not fh:
            print "NO SUCH FILE", filepath
            return
        for d in self.read_lines_gen(yieldcount, fh):
            # every 1000 obs, this should return somethin
            yield d

        fh.close()

decoder = RadMWR1D(fixed_vars=FV)


