# -*- coding: utf-8 -*-
"""
DICOM script to pull images to local files from research PACS

Created on Tue Apr 05 15:22:04 2016

@author: Cristina Gallego
"""

import os, os.path
import sys
import string
import time
from sys import argv, stderr, exit
import shlex, subprocess
import re

import numpy as np
import dicom
import psycopg2
import sqlalchemy as al
import sqlalchemy.orm
import pandas as pd

import processDicoms
from dictionaries import data_loc, mha_data_loc
from query_localdatabase import *
from add_newrecords import *

"""
----------------------------------------------------------------------
This script will

@ Copyright (C) Cristina Gallego, University of Toronto, 2013
----------------------------------------------------------------------
"""

def DICOM2mha(mha_data_loc, data_loc, StudyID, AccessionN, preDynSeries):
    
    # perform conversion
    DicomDirectory = data_loc+os.sep+str(int(StudyID))+os.sep+AccessionN+os.sep+preDynSeries
    filename = str(int(StudyID))+'_'+AccessionN+'_'+preDynSeries
    
    ### split bilateral series into left and right
     # read and sort by location
    [len_listSeries_files, sorted_FileNms_slices_stack] = processDicoms.ReadDicomfiles(DicomDirectory) 
    
    # Get dicom header, retrieve
    dicomInfo_series = dicom.read_file(DicomDirectory+os.sep+str(sorted_FileNms_slices_stack.iloc[0]['slices'])) 
     # write output to file sout
    seriesout =  mha_data_loc+os.sep+filename+'_dicomMeta.txt'
    sout = open(seriesout, 'a')    
    print >> sout, dicomInfo_series
    sout.close()
    
    # convert DynSeries_id
    # -a append dicom tag (Acquisition_Time) (0008, 0032) Acquisition Time  eg: '094455'
    # equivalent of using pydicom to retrieve tag
    # (0008,0032) AT S Acquisition Time       # hh.mm.ss.frac
    # e.g ti = str(dicomInfo_series[0x0008,0x0032].value) 
    if not os.path.exists( mha_data_loc+os.sep+filename+'@'+str(dicomInfo_series[0x0008,0x0032].value)+'.mha' ):
        cmd = 'dcm23d'+os.sep+'bin'+os.sep+'dcm23d.exe -i '+DicomDirectory+' -o '+mha_data_loc+' -n '+ filename +' -a'
        print '\n---- Begin conversion of ' + preDynSeries ;
        p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        p1.wait()
    
        # now iterate throught rest of dynamic series
        for k in range(1,5):
            kthDynSeries = int(preDynSeries)+k
            filename = str(int(StudyID))+'_'+AccessionN+'_'+str(kthDynSeries)
            DicomDirectory = data_loc+os.sep+str(int(StudyID))+os.sep+AccessionN+os.sep+str(kthDynSeries)
            
            cmd = 'dcm23d'+os.sep+'bin'+os.sep+'dcm23d.exe -i '+DicomDirectory+' -o '+mha_data_loc+' -n '+ filename +' -a'
            print '\n---- Begin conversion of ' + str(kthDynSeries) ;
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            p.wait()
    
    return 
            
            
if __name__ == '__main__':
    # Get Root folder ( the directory of the script being run)
    path_rootFolder = os.path.dirname(os.path.abspath(__file__))
    lesion_id = 1
    
    while ( lesion_id ) :            
        #############################
        ###### Query local databse
        #############################
        print " Querying local databse..."
        querylocal = Querylocal()
        dflesion = querylocal.queryby_lesionid(lesion_id)
        
        # process query
        lesion_record = [dflesion.Lesion_record.__dict__]
        dfinfo = pd.DataFrame.from_records(lesion_record)
        nmlesion_record = [dflesion.Nonmass_record.__dict__]
        dfnmlesion = pd.DataFrame.from_records(nmlesion_record)
        
        #############################
        ###### DICOM to mha
        #############################
        StudyID = dfinfo.iloc[0]['cad_pt_no_txt']
        AccessionN = dfinfo.iloc[0]['exam_a_number_txt']
        preDynSeries = dfnmlesion.iloc[0]['DynSeries_id']
            
        ## initialize query
        DICOM2mha(mha_data_loc, data_loc, StudyID, AccessionN, preDynSeries)
        
        lesion_id += 1
            
        #############################
        ## continue to next case
        print lesion_id
        
        if lesion_id > 400:
            lesion_id = []
        
