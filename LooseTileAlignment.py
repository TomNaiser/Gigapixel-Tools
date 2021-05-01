# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 20:32:26 2019

@author: Thomas Naiser
"""


#Purpose: Reposition loose images in a PTGUI Gigapixel panorama project on an orthonal grid 
#Load PTGUI project file 
#identify loose images (without control points)
#assumption: images should be aligned on a regular grid -> align loose images on the grid
#save the modified PTGUI project

#24.04 Adapted to latest Version of PTGUI 12.2
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.transforms as mtransforms

#function to rotate and translate the standard shape to a new position
def plot_rectangle(width,height, midPoint, roll,faceCol):
    rect = patches.Rectangle((-0.5*width,-0.5*height),width,height,linewidth=1,edgecolor='k',facecolor=faceCol)

    r = mtransforms.Affine2D().rotate(roll)
    t =mtransforms.Affine2D().translate(midPoint[0],midPoint[1])
    tra = r + t + ax.transData
    rect.set_transform(tra)
    ax.add_patch(rect)
    


projectFilename="J:\JaudesbergAmmersee240421\JaudesbergTest.pts"
numRows=6
numCols=75


with open(projectFilename, "r") as read_file:
    AllProjectData = json.load(read_file)
    
projectData=AllProjectData['project']
imageData=projectData['imagegroups']

yaw=[]
pitch=[]
roll=[]
size=[]

imageStartIndex=1
imageIndex=imageStartIndex
    
numImages=len(imageData)  

#Read image position into lists
for im in imageData:
    position=im['position']
    params=position['params']
    
  
    yaw.append(params['yaw'])
    pitch.append(params['pitch'])
    roll.append(params['roll'])
    
    size.append(im['size'])
    
#Get Number of control points of each image
controlpoints=projectData['controlpoints']
cpList= []

#Clear SubLists
for imNum in range(0,numImages):
     cpList.append([])
     
#Find Controlpoints for each image
for cp in controlpoints:
    point0=cp['0'][0]
    point1=cp['1'][0]
    cpList[point0].append(point1)
    cpList[point1].append(point0)

#Calculate the number of ControlPoints  
numControlPoints=[]    
for sublist in cpList:
    numControlPoints.append(len(sublist))
    
    
scFactor=1
imWidth=5304
imHeight=7952
scaleFactor=0.0008

    
#show the alignment of the images in the project file prior to optimization
#set up the plot
fig = plt.figure(1)
fig.clf()
ax = fig.add_subplot(111)

imIndex=0    
for im in  imageData:    

    
    imSize=size[imIndex]
   
    rollAngle=roll[imIndex]
    pitchVal=pitch[imIndex]
    yawVal=yaw[imIndex]

    #plot color depending on number of controlpoints: green for more than 2 controlpoints , yellow for more than 0  control points, red for no control points
    imCol='g' 
    if numControlPoints[imIndex]<3:
        imCol='y'
    if numControlPoints[imIndex]==0:
        imCol='r'
    plot_rectangle(imWidth*scaleFactor,imHeight*scaleFactor, [yawVal,pitchVal], rollAngle*3.1415/180,imCol)
    imIndex+=1


plt.xlim(min(yaw)-imWidth*scaleFactor,max(yaw)+imWidth*scaleFactor)
plt.ylim(min(pitch)-imHeight*scaleFactor,max(pitch)+imHeight*scaleFactor)
plt.gca().set_aspect('equal', adjustable='datalim')


#Extrapolate yaw and pitch roll for images without control-points
newYaw=np.zeros((numCols,numRows))
newPitch=np.zeros((numCols,numRows))
newRoll=np.zeros((numCols,numRows))
imageLinked=np.zeros((numCols,numRows),dtype=bool)

numLinkedImages=0
#find the images already linked
for col in range (numCols):
    for row in range(numRows):
        imIndex=col*numRows+row
        
        if numControlPoints[imIndex]>3:
            newYaw[col,row]=yaw[imIndex]
            newPitch[col,row]=pitch[imIndex]            
            newRoll[col,row]=roll[imIndex]
            imageLinked[col,row]=1
            numLinkedImages=numLinkedImages+1
        else:
            newYaw[col,row]=yaw[imIndex]
            newPitch[col,row]=pitch[imIndex]            
            newRoll[col,row]=roll[imIndex]
            imageLinked[col,row]=0

#Repeat until all images are linked  
numLinkedImagesOld=numLinkedImages-1 #just a dummy value to enter to loop
iterationCount=0
while numLinkedImages>numLinkedImagesOld:# numLinkedImages<numImages:
    numLinkedImagesOld=numLinkedImages
    for col in range (numCols):
        for row in range(numRows):
            imIndex=col*numRows+row
            if imageLinked[col,row]==True: #image already linked -> continue with next image
                continue
            

            c=0    
            #image is not linked
            #Check if the neighborhood is suffiently linked to make an approximation of the image position
            try:
                linkedTR=imageLinked[col+1,row+1] #Top Right
            except IndexError:
                linkedTR=False
            try:    
                linkedR=imageLinked[col+1,row]  #Right
            except IndexError:
                linkedR=False
            try:    
                linkedBR=imageLinked[col+1,row-1] #Bottom Right
            except IndexError:
                linkedBR=False
            try:
                linkedB=imageLinked[col,row-1]
            except IndexError:
                linkedB=False
            try: 
                linkedBL=imageLinked[col-1,row-1]
            except IndexError:
                linkedBL=False
            try:
                linkedL=imageLinked[col-1,row]
            except IndexError:
                linkedL=False
            try:
                linkedTL=imageLinked[col-1,row+1]
            except IndexError:
                linkedTL=False
            try:
                linkedT=imageLinked[col,row+1]
            except IndexError:
                linkedT=False
            
            #Calculate the approximate position: base+(vectop-vecfoot)
            #Rotation is calculated as the mean rotation of 3 neighboring linked images
            
            if linkedB and linkedBL and linkedL:
                c=1
                base=(newYaw[col,row-1],newPitch[col,row-1])
                vectop=(newYaw[col-1,row],newPitch[col-1,row])
                vecfoot=(newYaw[col-1,row-1],newPitch[col-1,row-1])
                meanRoll=(newRoll[col,row-1]+newRoll[col-1,row]+newRoll[col-1,row-1])/3

                
            if linkedB and linkedBR and linkedR:
                c=2
                base=(newYaw[col,row-1],newPitch[col,row-1])
                vectop=(newYaw[col+1,row],newPitch[col+1,row])
                vecfoot=(newYaw[col+1,row-1],newPitch[col+1,row-1])
                meanRoll=(newRoll[col,row-1]+newRoll[col+1,row]+newRoll[col+1,row-1])/3

                
            if linkedT and linkedR and linkedTR:
                c=3
                base=(newYaw[col,row+1],newPitch[col,row+1])
                vectop=(newYaw[col+1,row],newPitch[col+1,row])
                vecfoot=(newYaw[col+1,row+1],newPitch[col+1,row+1])
                meanRoll=(newRoll[col,row+1]+newRoll[col+1,row]+newRoll[col+1,row+1])/3

                
            if linkedT and linkedL and linkedTL:
                c=4
                base=(newYaw[col,row+1],newPitch[col,row+1])
                vectop=(newYaw[col-1,row],newPitch[col-1,row])
                vecfoot=(newYaw[col-1,row+1],newPitch[col-1,row+1])
                meanRoll=(newRoll[col,row+1]+newRoll[col-1,row]+newRoll[col-1,row+1])/3

                          
            if c>0:
                approxYaw=base[0]+(vectop[0]-vecfoot[0])
                approxPitch=base[1]+(vectop[1]-vecfoot[1])
                approxRoll=meanRoll
                if (meanRoll>10):
                    k=1
                newYaw[col,row]=approxYaw
                newPitch[col,row]=approxPitch
                newRoll[col,row]=approxRoll
                imageLinked[col,row]=True
                
                numLinkedImages=numLinkedImages+1
                
                print(col,row,c,numLinkedImages)
    iterationCount=iterationCount+1         
       
#Plot panorama with approximated positions

#set up the plot
fig = plt.figure(2)
fig.clf()
ax = fig.add_subplot(111)

for col in range (numCols):
    for row in range(numRows):
        imIndex=col*numRows+row
        if imageLinked[col,row]==True: #image already linked -> continue with next image
            imCol='g'
        else:
            imCol='r'
    
        imSize=size[imIndex]
   
        rollAngle=newRoll[col,row]
        pitchVal=newPitch[col,row]
        yawVal=newYaw[col,row]
    

        plot_rectangle(imWidth*scaleFactor,imHeight*scaleFactor, [yawVal,pitchVal], rollAngle*3.1415/180,imCol)
        imIndex+=1

plt.xlim(min(yaw)-imWidth*scaleFactor,max(yaw)+imWidth*scaleFactor)
plt.ylim(min(pitch)-imHeight*scaleFactor,max(pitch)+imHeight*scaleFactor)
plt.gca().set_aspect('equal', adjustable='datalim')    


#Modify the project data
for col in range (numCols):
    for row in range(numRows):
        imIndex=col*numRows+row
 
        AllProjectData['project']['imagegroups'][imIndex]['position']['params']['roll']=newRoll[col,row]
        AllProjectData['project']['imagegroups'][imIndex]['position']['params']['pitch']=newPitch[col,row]
        AllProjectData['project']['imagegroups'][imIndex]['position']['params']['yaw']=newYaw[col,row]
		
        AllProjectData['project']['imagegroups'][imIndex]['linkable']['position']['params']['roll']=newRoll[col,row]
        AllProjectData['project']['imagegroups'][imIndex]['linkable']['position']['params']['pitch']=newPitch[col,row]
        AllProjectData['project']['imagegroups'][imIndex]['linkable']['position']['params']['yaw']=newYaw[col,row]
    

#Serialize the modified project data
outputFilename=projectFilename[:-4]+"mod.pts"
with open(outputFilename, 'w') as f:
    
    #json.dump(AllProjectData, f,indent=4)
    json.dump(AllProjectData, f,indent='\t')


#Remove carriage returns to preserve the input format
with open(outputFilename, 'r') as file:
    content = file.read()

with open(outputFilename, 'w', newline='\n') as file:
    file.write(content)
