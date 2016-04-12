# -*- coding: utf-8 -*-
"""
Created on Tue Jul 07 11:29:08 2015

@author: windows
"""

import sys, os
import string
import shutil
import itertools
import stat
import glob ##Unix style pathname pattern expansion
import time
import re
from os.path import join
from os import listdir, rmdir
from shutil import copy2, move, rmtree
import subprocess
import re

from sqlalchemy.orm import sessionmaker
from mylocalbase import mynewengine
import mylocaldatabase

def moveDICOMS(rootdir, patpath, lesionpath, lesionindicat, cadID, accessionN, dicomN, iside, dynID, T2ID):
    '''
    patpath = massdir+os.sep+str(cadID)
    lesionpath = massdir+os.sep+str(cadID)+os.sep+str(accessionN)
    '''
    # out files/folders   
    os.chdir(str(rootdir))
    if not os.path.exists(str(cadID)):
        os.makedirs(str(cadID))
    os.chdir(str(cadID))   
    cmd = 'cp '+patpath+os.sep+lesionindicat+' '+lesionindicat
    print cmd
    p1 = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE)
    p1.wait()
       
    if not os.path.exists(str(accessionN)):
        os.makedirs(str(accessionN))
    os.chdir(str(accessionN))
    
    # parse throuh the DCE-MRI series 
    phases_series=[]
    testSID = str(dynID)
    if 'S' in str(testSID):
        #print testSID[1:]
        chosen_phase = int(testSID[1:])
    else:
        chosen_phase = int(testSID)
    
    if(testSID[0] == 'S'):
        phases_series.append('S'+str(chosen_phase))
                        
        for chSer in [chosen_phase+1, chosen_phase+2, chosen_phase+3, chosen_phase+4]:
            phases_series.append( 'S'+str(chSer) )    
    else:
        phases_series.append(str(chosen_phase))
                        
        for chSer in [chosen_phase+1, chosen_phase+2, chosen_phase+3, chosen_phase+4]:
            phases_series.append( str(chSer) )
            
    for kseries in range(len(phases_series)):
        print "moving ... %s " % lesionpath+os.sep+phases_series[kseries]
        move(lesionpath+os.sep+phases_series[kseries], phases_series[kseries])
    
    # now process T2ID
    print "moving ... %s " % lesionpath+os.sep+T2ID
    move(lesionpath+os.sep+T2ID, T2ID)
    
    if T2ID =='S4' and iside in ['Right','R']:
        otherT2ID = 'S3'
        nonfatT1 = 'S5'

    if T2ID =='S4' and iside in ['Left','L']:
        otherT2ID = 'S5'
        nonfatT1 = 'S6'
        
    if T2ID =='S3' and iside in ['Left','L']:
        otherT2ID = 'S4'
        nonfatT1 = 'S5'

    if T2ID =='S5' and iside in ['Left','L']:
        otherT2ID = 'S6'
        nonfatT1 = 'S7'
        
    if T2ID =='S5' and iside in ['Right','R']:
        otherT2ID = 'S4'
        nonfatT1 = 'S6'
        
    if T2ID =='S6' and iside in ['Right','R']:
        otherT2ID = 'S5'
        nonfatT1 = 'S7'

    if T2ID =='S7' and iside in ['Left','L']:
        otherT2ID = 'S8'
        nonfatT1 = 'S9'
        
    if T2ID =='S7' and iside in ['Right','R']:
        otherT2ID = 'S6'
        nonfatT1 = 'S8'
        
    if T2ID =='003' and iside in ['Left','L']:
        otherT2ID = '004'
        nonfatT1 = '005'
        
    if T2ID =='004' and iside in ['Right','R']:
        otherT2ID = '003'
        nonfatT1 = '005'
    
    # now process T2ID
    print "moving ... %s " % lesionpath+os.sep+otherT2ID
    move(lesionpath+os.sep+otherT2ID, otherT2ID)

    # now process T2ID
    print "moving ... %s " % lesionpath+os.sep+nonfatT1
    move(lesionpath+os.sep+nonfatT1, nonfatT1)
    
    return

############################################################################## 
# Create the database: the Session. 
Session = sessionmaker()
Session.configure(bind=mynewengine)  # once engine is available
session = Session() #instantiate a Session

#process masses
massdatainfo = []
for cad_case, lesion in session.query(mylocaldatabase.Lesion_record, mylocaldatabase.Mass_record).order_by(mylocaldatabase.Lesion_record.lesion_id).\
    filter(mylocaldatabase.Lesion_record.lesion_id==mylocaldatabase.Mass_record.lesion_id).all():
        print cad_case.lesion_id, cad_case.cad_pt_no_txt, cad_case.exam_a_number_txt, cad_case.exam_img_dicom_txt, cad_case.exam_dt_datetime, cad_case.exam_find_side_int, lesion.DynSeries_id, lesion.T2Series_id    
        massdatainfo.append([cad_case.lesion_id, cad_case.cad_pt_no_txt, cad_case.exam_a_number_txt, cad_case.exam_img_dicom_txt, cad_case.exam_dt_datetime, cad_case.exam_find_side_int, lesion.DynSeries_id, lesion.T2Series_id] )
        
#process non-masses
nonmassdatainfo = []
for cad_case, lesion in session.query(mylocaldatabase.Lesion_record, mylocaldatabase.Nonmass_record).order_by(mylocaldatabase.Lesion_record.lesion_id).\
    filter(mylocaldatabase.Lesion_record.lesion_id==mylocaldatabase.Nonmass_record.lesion_id).all():
        print cad_case.lesion_id, cad_case.cad_pt_no_txt, cad_case.exam_a_number_txt, cad_case.exam_img_dicom_txt, cad_case.exam_dt_datetime, cad_case.exam_find_side_int, lesion.DynSeries_id, lesion.T2Series_id      
        nonmassdatainfo.append([cad_case.lesion_id, cad_case.cad_pt_no_txt, cad_case.exam_a_number_txt, cad_case.exam_img_dicom_txt, cad_case.exam_dt_datetime, cad_case.exam_find_side_int, lesion.DynSeries_id, lesion.T2Series_id] )
        
        
# start to move series to
rootdir = 'Z:\Breast\DICOMS'
massdir = 'Z:'+os.sep+'Cristina'+os.sep+'MassNonmass'+os.sep+'\mass'
nonmassdir = 'Z:'+os.sep+'Cristina'+os.sep+'MassNonmass'+os.sep+'nonmass'

for j in range(216):
    nonmassdatainfo.pop(0)

for i in range(len(nonmassdatainfo)):
    print nonmassdatainfo[i]
    ilesion =  nonmassdatainfo[i]
    cadID = int(ilesion[1])
    try:    accessionN = int(ilesion[2]) 
    except: accessionN = 0
    dicomN = str(ilesion[3])
    idatetime = ilesion[4]
    iside = str(ilesion[5])
    dynID = str(ilesion[6])
    T2ID = str(ilesion[7])
    
    # check first if DICOMS already moved to destination
    if not os.path.exists(rootdir+os.sep+str(cadID)+os.sep+str(accessionN)) or  os.path.exists(rootdir+os.sep+str(cadID)+os.sep+str(dicomN)):
        # in files/folders
        patpath = nonmassdir+os.sep+str(cadID)
        # account for dicomN instead of AccessionN
        if os.path.exists( nonmassdir+os.sep+str(cadID)+os.sep+str(accessionN) ):
            lesionpath = nonmassdir+os.sep+str(cadID)+os.sep+str(accessionN)
            lesionindicat = str(accessionN)+'_seriesStudy.txt'
        else:
            lesionpath = nonmassdir+os.sep+str(cadID)+os.sep+str(dicomN)
            lesionindicat = str(dicomN)+'_seriesStudy.txt'
                
        moveDICOMS(rootdir, patpath, lesionpath, lesionindicat, cadID, accessionN, dicomN, iside, dynID, T2ID)
        #if int(raw_input('input 1 to continue or 0 to skip removing files: ')):
        # deal with the rest
        alldirs = listdir(lesionpath)
        # exclude DynPhases
        remainingdirs = [x for x in alldirs if x not in 'DynPhases']
        for idir in remainingdirs: 
            # check if directory
            if os.path.isdir(lesionpath+os.sep+str(idir)):
                print "removing .. %s" % idir
                files = listdir(lesionpath+os.sep+str(idir))
                ## to delete any directory recursively...
                for ifile in files:
                    if ifile == '.' or ifile == '..': continue
                    ipath = lesionpath + os.sep + str(idir) + os.sep + ifile
                    os.unlink(ipath)
                rmtree(lesionpath+os.sep+idir)
                
        # deal with remaining folders inside DynPhases
        allDyn = listdir(lesionpath+os.sep+'DynPhases')
        remainingdirs = [x for x in allDyn if not re.search('VOI', x, re.IGNORECASE)]
        for idir in remainingdirs: 
            # check if directory
            if os.path.isdir(lesionpath+os.sep+'DynPhases'+os.sep+str(idir)):
                print "removing .. %s" % idir
                files = listdir(lesionpath+os.sep+'DynPhases'+os.sep+str(idir))
                ## to delete any directory recursively...
                for ifile in files:
                    if ifile == '.' or ifile == '..': continue
                    ipath = lesionpath + os.sep + 'DynPhases' + os.sep + str(idir) + os.sep + ifile
                    os.unlink(ipath)
                rmtree(lesionpath+os.sep+'DynPhases'+os.sep+idir)
   
       
       
