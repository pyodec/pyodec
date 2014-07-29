"""
This decoder is similar to the MADIS MAP network decoder, except it produces
data for stations in the NOAA profiler network. Many things are the same though.
"""
from pyodec.core import FileDecoder, VariableList, FixedVariableList
import numpy as np
import os
import time
import gzip
import scipy.io.netcdf
# and make that prettier
nc = scipy.io.netcdf.netcdf_file

class NpnDecoder(FileDecoder):
    init_vars = VariableList()
    init_fixed_vars = FixedVariableList()
    def decode_proc(self, fpath, length, **kwargs):
        # each file contains only a single observation from a number of stations.
        # gather metadata and data for each station, 
        # variables are defined for each iteration
        # 
        self.vars = False
        self.fixed_vars = False
        with self.open_ascii(fpath) as g:
            # and open the netcdf
            src = nc(g)
            i=0
            # loop through the stations we found
            for stnid in map(''.join,src.variables[src.idVariables]):
                data = {}
                self.state['identifier']= stnid
                # and some specialty variables - can be used if they are taken
                self.state['loc'] = [src.variables['staLat'][i],
                               src.variables['staLon'][i],
                               src.variables['staElev'][i]]
                self.state['metacols'] = [
                    'STID',
                    'OWNER',
                    'PROVIDER',
                    'instrument_type',
                    'NETWORK',
                    'name',
                ]
                self.state['metavars'] = [
                    ''.join(stnid),
                    'NOAA',
                    'MADIS',
                    'Radar Wind Profiler', # NNP don't really diffferentiate between units
                    'NPN',
                    '', # this is sad, but true - full string name is not included in the files
                    
                ]
                # now determine the dataset characteristics as best we can...
                self.vars = VariableList()
                self.fixed_vars = FixedVariableList()
                # and create the row object, starting with the
                row = [src.variables[src.timeVariables][i]]
                self.vars.addvar('DATTIM','Observation Time',int,1,'Seconds since 1970-01-01 00:00:00 UTC')
                # determine some scope information for this station
                # grab the levels of data for this station. if the length is 0, then move on
                lvls = src.variables['levels'][i]
                if len(lvls[:]) == 0:
                    i+=1
                    continue
                self.fixed_vars.addvar('HEIGHT','mAGL','float32',lvls[:])
                self.fixed_vars.addvar('QCTESTS','','|S60',map(''.join,src.variables['QCT']))
                self.fixed_vars.addvar('ICTESTS','','|S72',map(''.join,src.variables['ICT']))
                self.fixed_vars.addvar('BEAMNAMES','','|S8', map(''.join,src.variables['beamNames']))
                for v in src.variables:
                    # loop through the variables - please let the variables be fixed!!!!
                    var = src.variables[v]
                    if not var.isrec:
                        # the variable is not record-based, so, move along
                        continue
                    # grab the actual data for this station of this variable
                    vardat = var[i]
                    vardtype = str(vardat.dtype)
                    # but, these datatypes are not really allowed by pytables, so fix
                    if "i" in vardtype:
                        vardtype='int'
                    elif 'f' in vardtype:
                        vardtype='float32'
                    varshp = var.shape[1:] # the first dim is the staion, so, not that
                    varunit = False;
                    if 'long_name' in dir(var):
                        varname = var.long_name
                    else: varname = ''
                    try:
                        varunit  = var.units
                     
                    except AttributeError:
                        if varunit is False:
                            varunit = ''
                    # record the variable
                    row.append(vardat)
                    self.vars.addvar(v,varname,vardtype,varshp,varunit)
                yield [tuple(row)]
                i+=1

decoder = NpnDecoder()