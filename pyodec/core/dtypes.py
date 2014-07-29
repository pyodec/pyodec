"""
    Implements several classes which are used by the core module to provide enhanced interactivity to the data objects produced. Moreover, this is designed to make the objects returned more numpy'y, while retaining list type attributes.
    
    Fundamentally, this will implement a row object, and a table object. Message decoders should return a row object, and sets of data should be returned as a table-type object.
    
SAD STORY: THESE DO NOT REALLY WORK. I THINK I WAS ESSENTIALLY REWRITING PANDAS IN THE PROCESS OF DOING THIS, SO IT IS STOPPPED. These codes are included in the library to both demonstrate the effort given towards enabling NumPy interfacing, and to allow someone else to take this and run further with it. For now they simply exist in the code base. And will probably be removed in some future commit, and will be donated to history.
"""
import numpy as np

class rowcols(list):
    # retain addition and all that stuff
    def __init__(self,obj=[],cols=[], dtype=False):
        if 'tolist' in dir(obj):
            objf = obj.tolist()
        else:
            objf = obj
        super(rowcols,self).__init__(objf)
        # compute the serlf recarray
        self.tup = self.__tup_comp()
        self.lst = self.__lst_comp()
        self.cols = cols
        self.dtype = False
        if dtype:
            self.dtype = np.dtype(dtype)
            # grab cols from the dtype - that's all it's for
        elif 'dtype' in dir(obj):
            self.dtype = np.dtype(obj.dtype)
        # compute the columns, either from the provided values, or the provided dtype
        self.__def_cols()
        self.__dtype_comp() # compute the dtype from myself
        self.rec = self.__rec_comp()
    def __def_cols(self):
        """
        define all column names, provided or otherwise
        """
        for i in range(len(self)):
            if i == len(self.cols):
                # see if there is a dtype at this position
                if len(self.dtype) > i:
                    self.cols.append(self.dtype[i][0])
                else:
                    self.cols.append('var'+str(i))
        self.cols = list(self.cols)
    def __rec_comp(self):
        """
        compute the recarray for this row
        """
        return np.array(self.tup,dtype=self.dtype)
    def __dtype_comp(self):
        """
        compute a dtype from the given elements, if one is not already given
        """
        self.dtype = []
        i=0
        for v in self:
            obj = np.array(v)
            if i > len(self.cols):
                name = val+str(i)
            else:
                name = self.cols[i]
            if len(obj.shape) == 0: 
                st = (name,obj.dtype)
            else:
                st = (name,obj.dtype,obj.shape)
            self.dtype.append(st)
            i+=1
    def __tup_comp(self):
        return tuple(self)
    def __lst_comp(self):
        
        return list(self)
    
    def __add__(self, new):
        # add cols
        cols = self.cols
        if 'cols' in dir(new):
            cols += new.cols
        # add lists
        return rowcols(list.__add__(self, new), cols)
    def __radd__(self, new):
        # add cols
        cols = self.cols
        if 'cols' in dir(new):
            cols += new.cols
        if 'dtype' in dir(new):
            cols += new.dtype.names
        # add lists
        return rowcols(list.__add__(self, new), cols)
    def __setitem__(self, index, value):
        # updated value, so update other stuff
        list.__setitem__(self, index, value)
        # and recompute things!
        self.tup = self.__tup_comp()
        self.lst = self.__lst_comp()
        self.__def_cols()
        self.__dtype_comp()
        self.rec = self.__rec_comp()
        

class obset(object):
    """
    a set of rowcol objects - a list by definition, but has a method to create other things
    """
    def __init__(self, obj=[]):
        """
        create this list-like object
        """
        if len(obj) > 0:
            if not self._test_rowcols(obj):
                raise IOError('Obsets can only accept rowcols objects')
            if not self.__shapetest(obj):
                raise IOError('You can only add objects of the same dtype')
            self._list = obj
        else:
            self._list = []
        
    def _test_rowcols(self, obj):
        """
        test all the rows in the new set of rows, to guarantee they are row
        """
        if len(obj) > 0:
            if any(map(lambda x:type(x) != rowcols, obj)):
                return False
            return True
        return False
    def __shapetest(self, new):
        """
        test that the new rowcols object is the same shape/dtype as the previous. Return
        true if there is an error
        """
        # make it into a list, just to be safe
        if type(new) != list:
            new = [new]
        # make sure this the same type as ANY self._list element
        # and that ALL new elements are the same
        test = False
        if '_list' in dir(self) and len(self._list) > 0:
            test = self._list[0].dtype
        if not test:
            test = new[0].dtype
        elif test != new[0].dtype: return False
        for e in new:
            if e.dtype != test:
                return False
        return True
        
        if len(self._list) == 0: return False
    def __iter__(self):
        for i in self._list:
            yield i
    def __add__(self, new):
        if not self._test_rowcols(new):
            raise IOError('Can only append rowcols objects')
        if not self.__shapetest(new):
            raise IOError('Shape mismatch with new element')
        return self._list + new
    def append(self, new):
        if not type(new) == rowcols:
            raise IOError('Can only append rowcols objects')
        if not self.__shapetest(new):
            raise IOError('Shape mismatch with new element')
        self._list += [new]
        