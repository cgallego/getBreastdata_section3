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

import datetime
import query_database
from dictionaries import data_loc

import dcmtk_routines as dcmtk
from add_newrecords import *

"""
----------------------------------------------------------------------
This script will

@ Copyright (C) Cristina Gallego, University of Toronto, 2013
----------------------------------------------------------------------
"""
            
if __name__ == '__main__':
    # Get Root folder ( the directory of the script being run)
    path_rootFolder = os.path.dirname(os.path.abspath(__file__))

    # Open filename list
    file_ids = open(sys.argv[1],"r")
    file_ids.seek(0)
    line = file_ids.readline()
    lesion_id = 296
       
    while ( line ) : 
        # Get the line: Study#, DicomExam#
        fileline = line.split()
        StudyID = fileline[0]
        PatientID = StudyID # in case of not MRN
        dateID = fileline[1] #dateID = '2010-11-29' as '2010,11,29';
        AccessionN = fileline[2]
        
        #############################
        ###### Retrieving
        print "Retrieving Scans to local drive..."
        [foundflag, Sids, Sdesc] = dcmtk.getScans(path_rootFolder, data_loc, fileline, PatientID, StudyID, AccessionN, oldExamID=False)
        
        #############################
        ###### Querying
        #############################
        if foundflag:
            print "Executing SQL biomatrix connection..."
            # Format query StudyID
            if (len(StudyID) == 4 ): fStudyID=StudyID
            if (len(StudyID) == 3 ): fStudyID='0'+StudyID
            if (len(StudyID) == 2 ): fStudyID='00'+StudyID
            if (len(StudyID) == 1 ): fStudyID='000'+StudyID
            # Format query for biomatrix redateID
            redateID = datetime.datetime(int(dateID[0:4]), int(dateID[5:7]), int(dateID[8:10]))
            
            #############################
            ## initialize query
            query = query_database.Query()
            # query radiology info
            radiolInfo = query.queryRadiolinfo(fStudyID, redateID)
            # query exam finding info
            # this returns query.findreport with lesion info
            # and correspondin query.nonmassreport, query.massreport, query.focireport
            [is_mass, colLabelsmass, is_nonmass, colLabelsnonmass, is_foci, colLabelsfoci] = query.queryExamFindings(fStudyID, redateID)
            # query exam finding if procedure 
            # this return query.gtpathology
            query.queryifProcedure(fStudyID, redateID)
            
            #############################
            # Send record to db
            newrecords = AddNewRecords()        
            print "\n Adding record case to DB..."
            
            for i in range(len(query.findreport)):
                newrecords.lesion_2DB( query.findreport.iloc[i] )
                newrecords.radiology_2DB(lesion_id, radiolInfo.iloc[0])
            
#                if(is_mass):
#                    newrecords.mass_2DB(lesion_id, query.massreport.iloc[i], Sids, Sdesc )
                if(is_nonmass):
                    newrecords.nonmass_2DB( lesion_id, query.nonmassreport.iloc[i], Sids, Sdesc )
#                if(is_foci):
#                    newrecords.foci_2DB(lesion_id, query.focireport.iloc[i], Sids, Sdesc  )
            
                if(query.gtpathology):
                    sel_procedure = 0
                    sel_procedure_date = []
                    for k in range(len(query.gtpathology)):
                        prodateID = query.gtpathology.iloc[k]['proc.proc_dt_datetime']
                        pro = datetime.datetime.strptime(prodateID.isoformat(),"%Y-%m-%d")
                        img = datetime.datetime.strptime(redateID.isoformat(),"%Y-%m-%dT%H:%M:%S")
                        # find the difference in days between procedure date and exam
                        timdelta = pro-img
                        days = timdelta.days
                        sel_procedure_date.append(days)
                
                    # if procedure posterior to imaging, save that
                    # if not find closest to exam available
                    sel_procedure_date = abs(array(sel_procedure_date))
                    print "Days between procedure and imaging = %d " % sel_procedure_date[sel_procedure_date == min(sel_procedure_date)][0]
                    sel_procedure = np.argmin(sel_procedure_date)
                            
                    newrecords.gtpathology_2DB(lesion_id, query.gtpathology.iloc[sel_procedure]  )
            
                lesion_id += 1
            
        #############################
        ## continue to next case
        line = file_ids.readline()
        print line
        
       
    file_ids.close()