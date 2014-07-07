"""
Pyodec root functionality
"""
import importlib

def decode(source, decoder, *args, **kwargs):
    """
    import and execute a file or string decoder on a certain class
    """
    print "importing", decoder
    decoder = importlib.import_module("."+decoder,'pyodec.files')
    
    return decoder.decoder.decode(source, *args, **kwargs)




def detect(source):
    """
    run every decoder we have on some amount of the source file, 
    and return every decoder identifier which successfully read data from the chunk.
    """
    pass