# PyInstaller runtime hook to fix numpy/pygame compatibility issue
import os
os.environ['NUMPY_EXPERIMENTAL_DTYPE_API'] = '1'
