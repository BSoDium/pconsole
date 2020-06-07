

class BufferFile:
    def __init__(self, write):
        self.write = write
    def readline(self): pass
    def writelines(self, l): map(self.append, l)
    def flush(self):    pass
    def isatty(self):   return 1
