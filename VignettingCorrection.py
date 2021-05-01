# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 14:22:11 2021

@author: Tom
"""
import os
from pathlib import Path
from skimage import io

from skimage import exposure
from skimage.transform import rescale,resize
from skimage import img_as_uint
from skimage.transform import pyramid_gaussian

from PIL import Image as pilImage

from pathlib import Path
import numpy as np
import napari
import tifffile
from skimage.transform import rotate
from tifffile import imsave


#Here the sky images (showing clear blue sky only) are stored
calibration_data_folder="calibrationImages"
filenameExt=".tif"
filenameBase="DSC"

#Here we get the images to be processed
process_folder='J:/JaudesbergAmmersee240421/Processed/'


#Here the processed output Images will be saved
targetFolder="targets/"


#Perform the calbration first and calculate a calibration mask
tifFilesList=[]
	
paths=Path(calibration_data_folder).glob(filenameBase+"*"+filenameExt)
for path in paths:
	tifFilesList.append(str(path))
	

for i,fn in enumerate(tifFilesList):
	im=tifffile.imread(fn)
	print (i)
	if i==0:
		sumArray=np.array([im.shape],dtype=np.uint32)
	else:
		sumArray=np.add(sumArray,im)

averageArray=(sumArray*(1/(i+1))).astype(np.uint32)

#The averageArray contains the skys gradient - to eliminate that we added a 180 degree turned copy and calculate the average
#This assumes that vignetting is symmetric around the center of the image
rotatedAverageArray=averageArray[::-1,::-1]
correctedAverage=(np.add(averageArray,rotatedAverageArray)).astype(np.uint32)
correctedAverage=np.multiply(0.5,correctedAverage).astype(np.uint32)


#Calculate maximum intensities channelwise
maxIntensities=[]
for i in range(3):
	maxIntensities.append(np.max(correctedAverage[:,:,i]))

maxArray=np.ones_like(correctedAverage)
for i in range(3):
	maxArray[:,:,i]=maxArray[:,:,i]*maxIntensities[i]
	
calibrationMaskArray=np.divide(maxArray,correctedAverage)	

viewer = napari.view_image(correctedAverage, name='correctedAverage')

viewer = napari.view_image(calibrationMaskArray, name='calibrationMaskArray')

normArray=np.divide(correctedAverage,maxArray)	
viewer = napari.view_image(normArray, name='normalizationImage')


correctedImage=np.multiply(im,calibrationMaskArray).astype(np.uint32)
clippedImage=np.clip(correctedImage,0,65535).astype(np.uint16)	#Clip values exceeding the 16bit range

viewer.add_image(correctedImage,name="correctedImage")


#Process the images located in the process_folder and save them in the target folder
paths=Path(process_folder).glob(filenameBase+"*"+filenameExt)
processFilesList=[]
for path in paths:
	processFilesList.append(str(path))

num2BProcessed=len(processFilesList)

numProcessed=1
for inputFileName in processFilesList:
	fileName=inputFileName[-12:]		# Filename like  DSCxxxxx.tif has 12 characters
	targetFileName=targetFolder+fileName

	print("saving #"+str(numProcessed)+" of "+str(num2BProcessed)+"  : "+targetFileName)
	
	im=tifffile.imread(inputFileName)
	correctedImage=np.multiply(im,calibrationMaskArray).astype(np.uint32)
	clipped_and_correcteImage=np.clip(correctedImage,0,65535).astype(np.uint16)	#Clip values exceeding the 16bit range
	imsave(targetFileName,clipped_and_correcteImage)
	
	cmdString='G:\Programme\ExifTool\exiftool -TagsFromFile '+inputFileName+' "-all:all>all:all" '+targetFileName
	exifToolOutput=os.system(cmdString)
	numProcessed=numProcessed+1


