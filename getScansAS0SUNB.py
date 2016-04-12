# -*- coding: utf-8 -*-
"""
Created on Thu Apr 07 12:08:05 2016

@author: Cristina G
"""

#!/usr/bin/python

import sys, os
import string
import shutil
import itertools
import stat
import glob ##Unix style pathname pattern expansion
import time
import re
import shlex, subprocess
import dcmtk_routines as dcmtk
from dictionaries import data_loc

'''
-----------------------------------------------------------
functions to get Dicom Exams on a local folder based on list of
Exam_list.txt(list of MRN StudyIDs DicomExam# )

usage:     import dcmtk_routines
    [INPUTS]
        # call main
        getScans(path_rootFolder, data_loc, fileline, PatientID, StudyID, AccessionN, oldExamID
        (requires: )

        # Call each one of these functions
        # 1) Check StudyId/AccessionN pair from MRI_MARTEL
        check_MRI_MARTEL(path_rootFolder, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN)

        # 2) Pull StudyId/AccessionN pair from MRI_MARTEL
        pull_MRI_MARTEL(path_rootFolder, data_loc, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN)

        # 3) Pull StudyId/AccessionN pair from pacs
        check_pacs(path_rootFolder, data_loc,  clinical_aet, clinical_port, clinical_IP, local_port, PatientID, StudyID, AccessionN)

        # 4) Annonimize StudyId/AccessionN pair from pacs
        #pull_pacs(path_rootFolder, data_loc,  clinical_aet, clinical_port, clinical_IP, local_port, PatientID, StudyID, AccessionN)


% Copyright (C) Cristina Gallego, University of Toronto, 2012 - 2013
% April 26/13 - Created first version that queries StudyId based on the AccessionNumber instead of DicomExamNo
% Sept 18/12 - Added additional options for retrieving only specific sequences (e.g T1 or T2)
% Nov 13/13 - Added all functionality in on module
% Apr 05/2016 - Added section3 datamining support
% Apr 07/2016 - Added getScansAS0SUNB to retrieve studies by Accession No from clinical PACS
-----------------------------------------------------------
'''

def get_only_filesindirectory(mydir):
     return [name for name in os.listdir(mydir)
            if os.path.isfile(os.path.join(mydir, name))]


def getScansAS0SUNB(path_rootFolder, data_loc, StudyID, AccessionN):
    """
    run : getScans(path_rootFolder, PatientID, StudyID, AccessionN):

    Inputs
    ======
    data_loc: (string)   Location of images to be pulled
    
    path_rootFolder: (string)   Automatically generated based on the location of file 
    
    PatientID : (int)    MRN
    
    StudyID : (int)    CAD StudyID
    
    AccessionN : (int)  CAD AccessionN
    """
    # rad station
    my_aet='SMIALBCAD2'
    local_port='5006'
    my_port='5006'
    hostID = '142.76.30.200'
    
    # research pacs
    remote_aet='MRI_MARTEL'
    remote_IP='142.76.29.187'
    remote_port='4006'
    
    clinical_aet="AS0SUNB"
    clinical_IP='142.76.62.102'
    clinical_port='104'
    Sids = []
    Sdesc = []
    temp_loc = os.path.dirname(os.path.abspath(__file__))
    
    try:
        flagfound = dcmtk.check_pacs(path_rootFolder, data_loc, my_aet, clinical_aet, clinical_port, clinical_IP, StudyID, AccessionN)
        if not flagfound:
            [Sids, Sdesc] = dcmtk.pull_pacs(path_rootFolder, data_loc, hostID, my_aet, clinical_aet, clinical_port, clinical_IP, local_port, StudyID, AccessionN)
    except (KeyboardInterrupt, SystemExit):
        print 'Unable to find study in MRI_MARTEL or AS0SUNB --- Abort'
        sys.exit()
        
    return 
    
    
               
if __name__ == '__main__':
    # Get Root folder ( the directory of the script being run)
    path_rootFolder = os.path.dirname(os.path.abspath(__file__))

    # Open filename list
    file_ids = open(sys.argv[1],"r")
    file_ids.seek(0)
    line = file_ids.readline()
       
    while ( line ) : 
        # Get the line: Study#, DicomExam#
        fileline = line.split()
        StudyID = fileline[0]
        dateID = fileline[1] #dateID = '2010-11-29' as '2010,11,29';
        AccessionN = fileline[2]
        
        #############################
        ###### Retrieving
        print "Retrieving Scans to local drive..."
        getScansAS0SUNB(path_rootFolder, data_loc, StudyID, AccessionN)
            
        #############################
        ## continue to next case
        line = file_ids.readline()
        print line
       
    file_ids.close()


