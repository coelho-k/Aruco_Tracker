"""
Framework   : OpenCV Aruco
Description : Calibration of camera and using that for finding pose of multiple markers
Status      : Working
References  :
    1) https://docs.opencv.org/3.4.0/d5/dae/tutorial_aruco_detection.html
    2) https://docs.opencv.org/3.4.3/dc/dbb/tutorial_py_calibration.html
    3) https://docs.opencv.org/3.1.0/d5/dae/tutorial_aruco_detection.html
"""

import numpy as np
import cv2
import cv2.aruco as aruco
import glob
import time
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
import mathutils

####---------------------- CALIBRATION ---------------------------
# termination criteria for the iterative algorithm
'''
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
# checkerboard of size (7 x 6) is used
objp = np.zeros((6*7,3), np.float32)
objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)

# arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

# iterating through all calibration images
# in the folder
images = glob.glob('images/*.jpg')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    plt.imshow(gray); plt.show()

    # find the chess board (calibration pattern) corners
    ret, corners = cv2.findChessboardCorners(gray, (7,6),None)
    print(corners)

    # if calibration pattern is found, add object points,
    # image points (after refining them)
    if ret == True:
        objpoints.append(objp)

        # Refine the corners of the detected corners
        corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
        imgpoints.append(corners2)

        # Draw and display the corners
        img = cv2.drawChessboardCorners(img, (7,6), corners2,ret)


ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)
'''

mtx =  np.array([
            [
                462.138671875,
                0.0,
                320.0
            ],
            [
                0.0,
                462.138671875,
                240.0
            ],
            [
                0.0,
                0.0,
                1.0
            ]
        ])

# Is 0 the way to define no distortion ?
dist = np.array([[1e-10,1e-10,1e-10,1e-10,1e-10]])

images = glob.glob('aruco-renders-2/aruco-renders-2/scene-000000/*.png')

# BlenderCAM
# To convert to numpyCAM, change the 'x' rotation from 180 -> 0
ref = np.array([
                        [
                            0.6659689545631409,
                            0.7459794878959656,
                            6.100576399603597e-08,
                            -0.05059482902288437
                        ],
                        [
                            0.3886394202709198,
                            -0.34695571660995483,
                            -0.8535698056221008,
                            0.07008799910545349
                        ],
                        [
                            -0.6367455124855042,
                            0.5684510469436646,
                            -0.5209788084030151,
                            0.4610074758529663
                        ],
                        [
                            0.0,
                            0.0,
                            0.0,
                            1.0
                        ]
                    ])

###------------------ ARUCO TRACKER ---------------------------

#ret, frame = cap.read()
#if ret returns false, there is likely a problem with the webcam/camera.
#In that case uncomment the below line, which will replace the empty frame 
#with a test image used in the opencv docs for aruco at https://www.docs.opencv.org/4.5.3/singlemarkersoriginal.jpg

#frame = cv2.imread('images/test image.jpg')
#print(frame.dtype)
frame = cv2.imread('aruco-renders-2/aruco-renders-2/scene-000000/000005.rgb.png') 

# operations on the frame
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# set dictionary size depending on the aruco marker selected
aruco_dict = aruco.Dictionary_get(aruco.DICT_ARUCO_ORIGINAL)

# detector parameters can be set here (List of detection parameters[3])
parameters = aruco.DetectorParameters_create()
parameters.adaptiveThreshConstant = 7

# lists of ids and the corners belonging to each id
corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
print('No of corners = ', len(corners))

# font for displaying text (below)
font = cv2.FONT_HERSHEY_SIMPLEX

# check if the ids list is not empty
# if no check is added the code will crash
if np.all(ids != None):

    # TODO: Do a check for blendercam or numpycam
    # IF blendercam: x rotation is 180
    # IF numpycam: x rotation is 0
    r = R.from_euler('x', 0, degrees=True).as_matrix()
    print(r)
    # estimate pose of each marker and return the values
    # rvet and tvec-different from camera coefficients
    # 0 index means only using first Aruco marker from corner list
    rvec, tvec ,_ = aruco.estimatePoseSingleMarkers(corners, 0.05, mtx, dist)
    # rvec = np.matmul(r, rvec[0].T)
    print(rvec.shape, tvec.shape)
    print('Rvec = ', rvec)

    rvec_3x3 = cv2.Rodrigues(rvec[0])
    rvec_3x3 = np.array(rvec_3x3[0])
    #rvec_3x3 = np.linalg.inv(rvec_3x3)
    #rvec_3x3 = np.matmul(r, rvec_3x3)

    tvec_3x1 = np.array(tvec[0])
    print('Rot = ', rvec_3x3)
    print('Trans = ', tvec_3x1)


    world2cam = np.zeros((4,4))
    world2cam[0:3,0:3] = rvec_3x3
    world2cam[0:3,3] = tvec_3x1
    world2cam[3,3] = 1
    world2cam = np.linalg.inv(world2cam)
    rx = world2cam[0:3,0:3].copy()
    rx = rx @ r
    world2cam[0:3,0:3] = rx
    #print('world2cam = ', world2cam)
    mat = mathutils.Matrix(world2cam)
    print('Matrix world2cam = ', mat)
    print('GT = ', ref)

    r, _ = cv2.Rodrigues(world2cam[0:3,0:3].dot(ref[0:3,0:3].T))
    rotation_error_from_identity = np.linalg.norm(r)
    print('Rotation error = ', rotation_error_from_identity)

    for i in range(0, ids.size):
        # draw axis for the aruco markers
        aruco.drawAxis(frame, mtx, dist, rvec[i], tvec[i], 0.1)

    # draw a square around the markers
    aruco.drawDetectedMarkers(frame, corners)

    # code to show ids of the marker found
    strg = ''
    for i in range(0, ids.size):
        strg += str(ids[i][0])+', '

    cv2.putText(frame, "Id: " + strg, (0,64), font, 1, (0,255,0),2,cv2.LINE_AA)


else:
    # code to show 'No Ids' when no markers are found
    cv2.putText(frame, "No Ids", (0,64), font, 1, (0,255,0),2,cv2.LINE_AA)

# display the resulting frame
cv2.imshow('frame',frame)
cv2.imwrite('output.jpg', frame)
if cv2.waitKey(1) & 0xFF == ord('q'):
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()




