"""
This decodes MADIS Multi-agency profiler (MAP) NetCDFs to the best of our ability.
This uses pyodec and the state variable to distribute data for mulitple stations. 
All fixed variables from this dataset are also included in the data. probably a bug, but a tolerable one.
"""
from pyodec.core import FileDecoder, VariableList, FixedVariableList
import numpy as np
import os
import time
import gzip
import scipy.io.netcdf
# and make that prettier
nc = scipy.io.netcdf.netcdf_file

class MapDecoder(FileDecoder):
    vars = VariableList()
    fixed_vars = FixedVariableList()
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
                self.state['loc'] = [src.variables['latitude'][i],
                                     src.variables['longitude'][i],
                                     src.variables['elevation'][i]]
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
                    ''.join(src.variables['dataProvider'][i]),
                    'MADIS',
                    src.variables['stationType'][i], # some friggin number
                    'MAP',
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
                beams = src.variables['numBeamsUsed'][i]
                # a wee-bit of quality control.
                if len(lvls[:]) == 0 or beams == 0:
                    i+=1
                    # skip this station
                    continue
                self.fixed_vars.addvar('HEIGHT','mAGL','float32',lvls[:])
                self.fixed_vars.addvar('BEAMSUSED','','int',src.variables['numBeamsUsed'][i])
                self.fixed_vars.addvar('RASSMODESUSED','','int',src.variables['numRASSModesUsed'][i])
                self.fixed_vars.addvar('BEAMNAMES','','|S8', map(''.join,src.variables['beamNames'][i]))
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
                    varunit = ''
                    varname = ''
                    varrange = [0,0]
                    attrs = dir(var)
                    if 'long_name' in attrs:
                        varname = var.long_name
                    else: varname = ''
                    if 'units' in attrs:
                        varunit  = var.units
                    if 'valid_range' in dir(var):
                        varrange = var.valid_range
                    # record the variable
                    row.append(vardat)
                    self.vars.addvar(v,varname,vardtype,varshp,varunit,mn=varrange[0],mx=varrange[1])
                yield [tuple(row)]
                i+=1

decoder = MapDecoder()