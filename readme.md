A Python module importable from Slicer3 which smoothly rotates, pans and zooms to take screenshots which can be pasted together

library for moving the camera in Slicer 3

Installation instructions:

* download smv.py
* open Slicer3
* open Python console
* add the location of the smv.py script to the Python Path:
    import sys
	sys.path.append('/home/tomb/exampleFolderWhereIDownloadedTheScriptTo/')
* Now type commands in this Python terminal window

* Example of use

```
back = -120
front = 100
from smv import *
startOver()
zoom(150)
moveToSlice(back)
saveSlicePics(front - back, 200)
saveSlicePics(spot - front, 100)
saveRotatePics(45, 0, 80)
saveZoomAndPanPics(20, 30, 0, 150, 200)
```


Dev thoughts / todos: 

* This library duplicates all the coordinates code for the camera - it's all in Slicer internals somewhere, but we're keeping separate track of it)
* Doesn't behave as some users expect since camera-up is always real up.  This is good for most situations, but different than manually rotating an image.
