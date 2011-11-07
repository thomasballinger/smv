A Python module importable from Slicer3 which smoothly rotates, pans and zooms to take screenshots which can be pasted together


library for moving the camera in Slicer 3
Example of use:
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

