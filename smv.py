# Sloppy wrapper for making smooth slicer3 movies
# ThomasBallinger@gmail.com
"""
Library for moving the camera in Slicer 3
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

category: slicer, tomb
"""

# To Do:
# -allow more interesting functions than zooming units of one all the time
# -support timing estimates

import sys
try:
    import Slicer
except ImportError:
    print 'Import this module from within slicer, using the Python Interactor'
    raise ImportError('Module not imported in Slicer')
import re, math, os, tempfile, glob, numpy, subprocess, time
from Slicer import slicer

__all__ = ['getOutputFolder','startOver','saveDisplay','checkMovie','exportMovie','saveSlicePics','savePanPics','saveZoomPics','saveZoomAndPanPics','saveRotatePics','zoom','moveSlice','pan']

scene = Slicer.slicer.MRMLScene
cam = scene.GetNodeByID('vtkMRMLCameraNode1')
appli = Slicer.slicer.ApplicationGUI
slicesgui = appli.GetSlicesGUI()
firstslicegui = slicesgui.GetNthSliceGUI(0)
firstslicelogic = firstslicegui.GetLogic()
camera = cam.GetCamera()

output = tempfile.mkdtemp()
currentPictureNumber = 0

def getOutputFolder():
    """Returns the name of the output folder"""
    return output

def reacquireCam():
    global cam
    global camera
    global scene
    scene = Slicer.slicer.MRMLScene
    cam = scene.GetNodeByID('vtkMRMLCameraNode1')
    camera = cam.GetCamera()

def startOver():
    """Deletes all saved pictures from the output folder, starts numbering over at 0"""
    global currentPictureNumber
    os.system('rm -f '+output+'/*')
    currentPictureNumber = 0

def saveDisplay():
    """Save an image from the 3D display window as the next numbered image in the output directory"""
    global currentPictureNumber
    filename = output+'/'+str(currentPictureNumber)+'.png'
    Slicer.tk.tk.eval('SlicerSaveLargeImage %s 1'%filename)
    currentPictureNumber = currentPictureNumber + 1

def exportMovie(moviename,r=30,q=8):
    """Uses ffmpeg to make a movie from the images taken so far"""
    a=subprocess.Popen(['ffmpeg','-i',output+'/%d.png','-qmax',str(q),'-r',str(r), '-y',moviename])
    os.waitpid(a.pid,0)
    print 'created movie at ', os.path.abspath(moviename)

def checkMovie():
    """Uses eog to view your image files (linux only)"""
    os.system('eog '+output+'/* &')

def undoLastSet():
    raise NotImplementedError

def saveZoomPics(howFar,howManyFrames=0,save=True):
    """Save a bunch of images at filenameprefix-1 etc. while zooming howFar"""
    saveZoomAndPanPics(0,0,0,howFar,howManyFrames,save)

def updateAndSavePic():
    #appli.UpdateMain3DViewers()
    #camera.Modified()
    #appli.GetActiveRenderWindowInteractor().Render()
    Slicer.tk.tk.eval('update')
    saveDisplay()

def getTimeToUpdate():
    t0 = time.time()
    Slicer.tk.tk.eval('update')
    tf = time.time()
    return tf - t0

def timeEstimate(n):
    t=getTimeToUpdate()
    estimate = t*n
    return 'estimated time: %d.0 minutes' % int(estimate/60)

def saveSlicePics(howFar,howManyFrames=0,save=True,timeDelay=0):
    """Save a bunch of images at filenameprefix-1 etc. over howFar, one for each slice."""
    if not howManyFrames:
        save=False
        howManyFrames = 2
    howFar = float(howFar)
    howManyFrames = int(howManyFrames)
    startSlice = firstslicelogic.GetSliceOffset()
    interval = howFar / (howManyFrames-1)
    for i in range(howManyFrames):
        firstslicelogic.SetSliceOffset(i*interval + startSlice)
        if save:
            updateAndSavePic()

def savePanPics(r,u,f,howManyFrames=0,save=True):
    """Save a bunch of images at filenameprefix-1 etc. while moving right, up, and forward"""
    saveZoomAndPanPics(r,u,f,0,howManyFrames,save)

def saveRotatePics(theta,phi,howManyFrames=0,save=True,timeDelay=0, hackySetUp=False):
    """Save a bunch of images in output folder while rotating up and to the left"""
# This is physics spherical coordinates, not wikipedia ones
    if not howManyFrames:
        save=False
        howManyFrames = 2

    theta = float(theta)
    phi = float(phi)
    theta = theta * (2 * math.pi) / 360
    phi = phi*(2 * math.pi) / 360
    (startx,starty,startz) = camera.GetPosition()
    r = math.sqrt(startx**2+starty**2+startz**2)
    startTheta = math.atan2(starty,startx)
    startPhi = math.acos(startz/r)

    (startx_up, starty_up, startz_up) = camera.GetViewUp()
    r_up = math.sqrt(startx_up**2 + starty_up**2 + startz_up**2)
    startTheta_up = math.atan2(starty_up, startx_up)
    startPhi_up = math.acos(startz_up/r_up)

    dTheta = theta / (howManyFrames - 1)
    dPhi = phi / (howManyFrames - 1)
    #print '%.2f %.2f : %.2f %.2f %.2f :: %.2f %.2f %.2f : %.2f %.2f ' % (startTheta, startPhi, startx,starty,startz,startx_up,starty_up,startz_up, startTheta_up, startPhi_up)
    for i in range(howManyFrames):
        theta = startTheta + dTheta*i
        phi = startPhi + dPhi*i
        x = r * math.sin(phi) * math.cos(theta)
        y = r * math.sin(phi) * math.sin(theta)
        z = r * math.cos(phi)
        cam.SetPosition(x,y,z)

        # Hacky solution - only works when rotations are along theta OR phi
        orth = numpy.cross((startx, starty, startz), (startx_up, starty_up, startz_up))
        u = orth / numpy.linalg.norm(orth)
        skewsym = numpy.matrix([
            [0, -u[2], u[1]],
            [u[2], 0, -u[0]],
            [-u[1], u[0], 0]])
        R = 1*skewsym + numpy.outer(u, u)
        vector = numpy.matrix([[x], [y], [z]])
        upVector = R*vector

        theta_up = startTheta_up + dTheta*i
        phi_up = startPhi_up + dPhi*i
        x_up = r_up * math.sin(phi_up) * math.cos(theta_up)
        y_up = r_up * math.sin(phi_up) * math.cos(theta_up)
        z_up = r_up * math.cos(phi_up)
        if hackySetUp:
            cam.SetViewUp(float(upVector[0]), float(upVector[1]), float(upVector[2]))
        if save:
            updateAndSavePic()
        #print '+%.2f +%.2f : %+.2f %+.2f %+.2f :: %+.2f %+.2f %+.2f : +%.2f +%.2f' % (theta, phi, x,y,z,x_up,y_up,z_up,theta_up, phi_up)

def saveZoomAndPanPics(r,u,f,howFar,howManyFrames=0,save=True,timeDelay=0):
    """Zoom and pan simultaneously"""
    howManyFrames = int(howManyFrames)
    if not howManyFrames:
        save=False
        howManyFrames = 2
    r = float(r)
    u = float(u)
    f = float(f)
    (startfx,startfy,startfz) = camera.GetFocalPoint()
    (startpx,startpy,startpz) = camera.GetPosition()
    distFromFocalPoint = math.sqrt((startpx-startfx)**2+(startpy-startfy)**2+(startpz-startfz)**2)
    if howFar >= distFromFocalPoint:
        return False
    (upx,upy,upz) = camera.GetViewUp()
    cameraToFocalPoint = [startfx-startpx,startfy-startpy,startfz-startpz]
    norm = numpy.linalg.norm(cameraToFocalPoint)
    (fdx,fdy,fdz) = cameraToFocalPoint/norm
    (rightx,righty,rightz) = numpy.cross([upx,upy,upz],[fdx,fdy,fdz])
    dx = (r*rightx+u*upx+f*fdx)/(howManyFrames-1)
    dy = (r*righty+u*upy+f*fdy)/(howManyFrames-1)
    dz = (r*rightz+u*upz+f*fdz)/(howManyFrames-1)
    zdx = (howFar*fdx)/(howManyFrames-1)
    zdy = (howFar*fdy)/(howManyFrames-1)
    zdz = (howFar*fdz)/(howManyFrames-1)
    for i in range(howManyFrames):
        camera.SetFocalPoint(startfx+dx*i,startfy+dy*i,startfz+dz*i)
        camera.SetPosition(startpx+(dx+zdx)*i,startpy+(dy+zdy)*i,startpz+(dz+zdz)*i)
        if save:
            updateAndSavePic()

def zoom(howFar):
    """Zoom without recording anything"""
    saveZoomPics(howFar)

def moveSlice(howFar):
    """Move forward slices without recording anything"""
    saveSlicePics(howFar)

def pan(r,u,f):
    """Pan to position without recording anything"""
    savePanPics(r,u,f)

def getZoom():
    """Gets current zoom level"""
    (startx,starty,startz) = camera.GetPosition()
    distFromOrigin = math.sqrt(startx**2+starty**2+startz**2)
    return distFromOrigin

def getSlice():
    return firstslicelogic.GetSliceOffset()

def getPan():
    return camera.GetFocalPoint()

def getPos():
    return camera.GetPosition()

def zoomTo(howFar):
    """Zoom without recording anything"""
    pass

def moveToSlice(slice):
    firstslicelogic.SetSliceOffset(slice)


def moveToPosition(x,y,z):
    pass

def panToPosition(x,y):
    """Pan to position without recording anything"""
    pass

def Jan2011Movie(front, back, spot, modelMadeVisible=[]):
    if not modelMadeVisible:
        startOver()
        zoom(150)
        moveToSlice(back)
        saveSlicePics(front - back, 200)
        modelMadeVisible.append(True)
        print('Turn on model visibility!')
        return
    elif modelMadeVisible:
        modelMadeVisible.remove(True)
        saveSlicePics(spot - front, 100)
        saveRotatePics(45, 0, 80)
        saveZoomAndPanPics(20, 30, 0, 150, 200)

def interleave(folder1,folder2,outputfolder,howMany):
    files1 = glob.glob(folder1+'/*.png')
    files2 = glob.glob(folder2+'/*.png')
    if len(files1) != len(files2):
        pass
    for i in range(howMany):
        normal = Image.open(folder1+'/'+str(i)+'.png')
        athlete = Image.open(folder2+'/'+str(i)+'.png')
        if normal.size != athlete.size:
            raise Exception('Images for concatenation are not the same size')
        newx = normal.size[0] + athlete.size[0]
        newy = max(normal.size[1],athlete.size[1])
        result = Image.new("RGBA",(newx,newy))
        result.paste(normal,(0,0))
        result.paste(athlete,(normal.size[0],0))
        result.save('outputfolder'+'/'+str(i)+'.png')

def help():
    """Prints information about commands that can be used"""
    for cmd in __all__:
        print cmd
        print ' ', globals()[cmd].__doc__
