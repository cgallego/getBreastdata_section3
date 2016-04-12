# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 21:35:46 2013

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
from dictionaries import my_aet, data_loc

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

'''

def get_only_filesindirectory(mydir):
     return [name for name in os.listdir(mydir)
            if os.path.isfile(os.path.join(mydir, name))]


def getScans(path_rootFolder, data_loc, fileline, PatientID, StudyID, AccessionN, oldExamID):
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
    from dictionaries import my_aet, hostID, local_port, clinical_aet, clinical_IP, clinical_port, remote_aet, remote_IP, remote_port

    Sids = []
    Sdesc = []
    dateID = fileline[1] 
    try:
        [already, flag, Sids, Sdesc] = check_MRI_MARTEL(data_loc, path_rootFolder, my_aet, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN, dateID)
        if(oldExamID==False and flag==True and already==False):
            [Sids, Sdesc] = pull_MRI_MARTEL(data_loc, path_rootFolder, my_aet, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN, countImages=False)
        if(oldExamID==True and flag==True and already==False):
            ExamID = fileline[3]
            pull_MRI_MARTELold(data_loc, path_rootFolder, my_aet, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN, ExamID, countImages=False)
            
    except (KeyboardInterrupt, SystemExit):
        check_pacs(path_rootFolder, data_loc, hostID, clinical_aet , clinical_port, clinical_IP, local_port, PatientID, StudyID, AccessionN)
        pull_pacs(path_rootFolder, data_loc, hostID, clinical_aet, clinical_port, clinical_IP, local_port, PatientID, StudyID, AccessionN)
    except (KeyboardInterrupt, SystemExit):
        print 'Unable to find study in MRI_MARTEL or AS0SUNB --- Abort'
        sys.exit()
        
    return flag, Sids, Sdesc
    
    
def check_MRI_MARTEL(data_loc, path_rootFolder, my_aet, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN, dateID):

    # prepare directories        
    if not os.path.exists(path_rootFolder+os.sep+'checkdata'):
        os.makedirs(path_rootFolder+os.sep+'checkdata')
    if not os.path.exists(path_rootFolder+os.sep+'outcome'):
        os.makedirs(path_rootFolder+os.sep+'outcome')
         
    # Get Root folder ( the directory of the script being run)
    os.chdir(path_rootFolder) 
    are_pushed_img = False
    already = False
    selListOfSeriesID = []
    selListOfSeriesDescription = []
    
    if not os.path.exists(data_loc+os.sep+StudyID+os.sep+AccessionN):
        cmd='findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
                -k 0008,0020="" -k 0008,0050='+AccessionN+' -k 0020,0011="" -k 0008,0052="SERIES" \
                -k 0020,000D="" -k 0020,000e="" -k 0020,1002="" -k 0008,0070="" \
                -aet '+my_aet+' -aec '+remote_aet+' '+remote_IP+' '+remote_port+' > '+ 'checkdata'+os.sep+'findscu_'+AccessionN+'_SERIES.txt' 
                  
        print '\n---- Begin query with ' + remote_aet + ' by PatientID ....' ;
        print "cmd -> " + cmd
        p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
        p1.wait()
        
        # Create fileout to print listStudy information
        # if StudyID folder doesn't exist create it        
        if not os.path.exists(path_rootFolder+os.sep+str(StudyID)):
            os.makedirs(path_rootFolder+os.sep+str(StudyID))
         
        os.chdir(path_rootFolder+os.sep+str(StudyID))
         
        # if AccessionN folder doesn't exist create it        
        if not os.path.exists(str(AccessionN)):
            os.makedirs(str(AccessionN))
            
        os.chdir(str(path_rootFolder))    
        
        #################################################
        # Check mthat accession exists
        readQueryFile1 = open('checkdata'+os.sep+'findscu_'+AccessionN+'_SERIES.txt' , 'r')
        readQueryFile1.seek(0)
        line = readQueryFile1.readline()
        print '---------------------------------------\n'
        ListOfExamsUID = []  
        ListOfSeriesUID = []
        ListOfSeriesID = []
        count = 0
        match = 0
        
        while ( line ) : 
            if '(0008,0020) DA [' in line:    #SerieDate
                item = line
                exam_date = item[item.find('[')+1:item.find(']')]        
                #print 'exam_date => ' + exam_date    
                line = readQueryFile1.readline()
                
            elif '(0010,0020) LO [' in line:    #patient_id
                item = line
                patient_id = item[item.find('[')+1:item.find(']')]        
                #print 'patient_id => ' + patient_id    
                line = readQueryFile1.readline()
                
            elif '(0010,0010) PN [' in line:    #patient_name
                item = line
                patient_name = item[item.find('[')+1:item.find(']')] # this need to be anonymized
                patient_name = "AnonName"
                #print 'patient_name => ' + patient_name    
                line = readQueryFile1.readline()
                
            elif '(0008,1030) LO [' in line:    #exam_description
                item = line
                exam_description = item[item.find('[')+1:item.find(']')]        
                #print 'exam_description => ' + exam_description
                line = readQueryFile1.readline()
                
            elif '(0020,000d) UI [' in line:    #exam_uid
                item = line
                exam_uid = item[item.find('[')+1:item.find(']')]        
                #print 'exam_uid => ' + exam_uid    
                ListOfExamsUID.append(exam_uid)
                line = readQueryFile1.readline()
                
            elif '(0008,0050) SH [' in line:    #exam_number
                item = line
                accession_number = item[item.find('[')+1:item.find(']')]        
                #print 'accession_number => ' + accession_number    
                line = readQueryFile1.readline()
                
            elif '(0008,103e) LO [' in line:    #series_description
                item = line
                series_description = item[item.find('[')+1:item.find(']')]        
                #print 'series_description => ' + series_description
                line = readQueryFile1.readline()
                
            elif '(0020,000e) UI [' in line:    #series_uid
                item = line
                series_uid = item[item.find('[')+1:item.find(']')]        
                #print 'series_uid => ' + series_uid
                ListOfSeriesUID.append(series_uid)
                line = readQueryFile1.readline()
                        
            elif '(0020,0011) IS [' in line:    #series_number
                item = line
                series_number = item[item.find('[')+1:item.find(']')]
                series_number = series_number.rstrip()
                ListOfSeriesID.append(series_number)
                #print 'series_number => ' + series_number
                
                if(match == 0):  # first series so far
                    match = 1
                    print " \nAccessionN: %1s %2s %3s %4s %5s \n" % (accession_number, patient_name, patient_id, exam_date, exam_description)
                    print " series: # %2s %3s %4s \n" % ('series_number', 'series_description', '(#Images)')
        
                line = readQueryFile1.readline()
                
            elif( (line.rstrip() == '--------') and (match == 1) ):
                                
                print ' series %2d: %3d %4s' % (int(count), int(series_number), series_description)
                # ------------ FInish obtaining SERIES info 
                      
                line = readQueryFile1.readline()
                count += 1;
            else:
                line = readQueryFile1.readline()
                                              
        readQueryFile1.close()
            
        #################################################    
        if(ListOfSeriesID):
            for IDseries in ListOfSeriesID[0]:
                IDser = 0
                # if ExamID folder doesn't exist create it    
                os.chdir(str(StudyID))
                os.chdir(str(AccessionN))
                if not os.path.exists(str(ListOfSeriesID[int(IDser)])):
                    os.makedirs(str(ListOfSeriesID[int(IDser)]))
                
                os.chdir(str(ListOfSeriesID[int(IDser)]))
                
                # Proceed to retrive images
                # query protocol using the DICOM C-FIND primitive. 
                # For Retrieval the C-MOVE protocol requires that all primary keys down to the hierarchy level of retrieve must be provided
                cmd = path_rootFolder+os.sep+'movescu -S +P '+ local_port +' -k 0008,0052="SERIES" -k 0020,000d=' + ListOfExamsUID[int(IDser)] + ' -k 0020,000e=' + ListOfSeriesUID[int(IDser)] + '\
                -aec ' + remote_aet + ' -aet ' + my_aet + ' -aem ' + my_aet + ' ' + remote_IP + ' ' + remote_port
                print cmd
                        
                # Image transfer takes place over the C-STORE primitive (Storage Service Class). 
                # All of that is documented in detail in pa  rt 4 of the DICOM standard.
                p1 = subprocess.Popen(cmd, shell=False)
                p1.wait()
                
                # After transfer Get total number of files to Anonymize
                path_Series_files = path_rootFolder+os.sep+str(StudyID)+os.sep+str(AccessionN)+os.sep+str(ListOfSeriesID[int(IDser)])
                listSeries_files = get_only_filesindirectory(path_Series_files)
                print "\n===========\nLength of retrieved series images"
                print len(listSeries_files)
                
                if listSeries_files:
                    are_pushed_img = True
                else:
                    are_pushed_img = False
            
                # Go back - go to next 
                os.chdir(path_rootFolder)  
                IDser += 1
        
        if are_pushed_img == False:
            fil=open('outcome/Errors_findscu_MRI_MARTEL.txt','a+')
            fil.write(str(StudyID)+'\t'+str(dateID)+'\t'+str(AccessionN)+'\tAccession number not found in '+remote_aet+'\n')
            fil.close()
            print "\n===============\n"
            print 'Accession number NOT found in '+remote_aet
            #sys.exit('Error. Accession number not found in '+remote_aet)
        else:
            print "\n===============\n"
            print 'Accession number found in '+remote_aet
        
        #Cleanup the tmp directory.
        os.chdir(path_rootFolder)
        try:
            if os.path.isdir(StudyID):
                shutil.rmtree(StudyID, ignore_errors=True)    #os.rmdir(StudyNo)    #remove    # removedirs
        except ValueError:
            print "Error Deleting a Directory is problematic."
    
    else:                
        [already, selListOfSeriesID, selListOfSeriesDescription] = parse_series(data_loc, StudyID, AccessionN)

    return already, are_pushed_img, selListOfSeriesID, selListOfSeriesDescription
    
    
def parse_series(data_loc, StudyID, AccessionN):

    selListOfSeriesID = []
    selListOfSeriesDescription = []
    already = False
    
    #################################################
    # Check accession file that exists
    if os.path.exists('outcome'+os.sep+'findscu_'+AccessionN+'_SERIES.txt'):
        already = True
        readQueryFile1 = open('outcome'+os.sep+'findscu_'+AccessionN+'_SERIES.txt' , 'r')
        readQueryFile1.seek(0)
        line = readQueryFile1.readline()
        ListOfSeriesUID = []
        ListOfSeriesID = []
        ListOfSeriesDescription = []  
        count = 0
        match = 0
        
        while ( line ) :         
            if '(0008,103e) LO [' in line:    #series_description
                item = line
                series_description = item[item.find('[')+1:item.find(']')]        
                #print 'series_description => ' + series_description
                ListOfSeriesDescription.append(series_description)
                line = readQueryFile1.readline()
                
            elif '(0020,000e) UI [' in line:    #series_uid
                item = line
                series_uid = item[item.find('[')+1:item.find(']')]        
                #print 'series_uid => ' + series_uid
                ListOfSeriesUID.append(series_uid)
                line = readQueryFile1.readline()
                        
            elif '(0020,0011) IS [' in line:    #series_number
                item = line
                series_number = item[item.find('[')+1:item.find(']')]
                series_number = series_number.rstrip()
                series_number = series_number.lstrip()
                ListOfSeriesID.append(series_number)
                #print 'series_number => ' + series_number
                
                if(match == 0):  # first series so far
                    match = 1
                    print " series: # %2s %3s %4s \n" % ('series_number', 'series_description', '(#Images)')
    
                line = readQueryFile1.readline()
                
            elif( (line.rstrip() == '--------') and (match == 1) ):
                print ' series %2d: %3d %4s' % (int(count), int(series_number), series_description)
                # ------------ FInish obtaining SERIES     
                line = readQueryFile1.readline()
                count += 1;
            else:
                line = readQueryFile1.readline()
                
        readQueryFile1.close()
    
        IDser = 0
        selListOfSeriesID = []
        selListOfSeriesDescription = []
        
        for IDseries in ListOfSeriesID:
            os.chdir(str(data_loc))
            
            # if ExamID folder doesn't exist create it    
            os.chdir(str(StudyID))
            os.chdir(str(AccessionN))
            print os.getcwd()
            
            if('FSE T2' in ListOfSeriesDescription[IDser] or 'VIBRANT' in ListOfSeriesDescription[IDser]):
                if not os.path.exists(str(ListOfSeriesID[IDser])):
                    os.makedirs(str(ListOfSeriesID[IDser]))
                
                os.chdir(str(ListOfSeriesID[IDser]))
                selListOfSeriesID.append( ListOfSeriesID[IDser] )
                selListOfSeriesDescription.append( ListOfSeriesDescription[IDser] )
            
            # Go back - go to next 
            os.chdir(str(data_loc))    
            IDser += 1
            
        if not selListOfSeriesID:
            print("HERRRE")
        
        
    return already, selListOfSeriesID, selListOfSeriesDescription     
    
    

def pull_MRI_MARTEL(data_loc, path_rootFolder, my_aet, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN, countImages=False):

     # Create fileout to print listStudy information
    if not os.path.exists(str(data_loc)+os.sep+str(StudyID)):
        os.makedirs(str(data_loc)+os.sep+str(StudyID))

    # if AccessionN folder doesn't exist create it
    if not os.path.exists(str(data_loc)+os.sep+str(StudyID)+os.sep+str(AccessionN)):
        os.makedirs(str(data_loc)+os.sep+str(StudyID)+os.sep+str(AccessionN))
    
    os.chdir(path_rootFolder)    
    cmd='findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
            -k 0008,0020="" -k 0008,0050='+AccessionN+' -k 0020,0011="" -k 0008,0052="SERIES" \
            -k 0020,000D="" -k 0020,000e="" -k 0020,1002="" -k 0008,0070="" \
            -aet '+my_aet+' -aec '+remote_aet+' '+remote_IP+' '+remote_port+' > '+ 'outcome'+os.sep+'findscu_'+AccessionN+'_SERIES.txt' 
    
    # the DICOM query model is strictly hierarchical and the information model hierarchy is PATIENT - STUDY - SERIES - INSTANCE
    # Each query can only retrieve information at exactly one of these levels, and the unique keys of all higher levels must be provided as part of the query. In practice that means you first have to identify a patient, then you can identify studies for that patient, then you can check which series within one study exist and finally you could see which instances (DICOM objects, images) there are within one series. 
    # First findscu will retrive SERIES for a given STUDYID
#    cmd = 'findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
#    -k 0008,0020="" -k 0020,0010=' + ExamID + ' -k 0020,0011="" -k 0008,0052="SERIES" \
#	-k 0020,000D="" -k 0020,000e="" -k 0020,1002="" -k 0008,0070="" \
#	-aet ' + my_aet + ' -aec ' + remote_aet + ' ' + remote_IP + ' ' + remote_port+
#          
    print '\n---- Begin query with ' + remote_aet + ' by PatientID ....' ;
    print "cmd -> " + cmd
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()
    
    #################################################
    # 2nd-Part: # Required for pulling images.
    # Added by Cristina Gallego. July 2013
    ################################################
    imagepath = str(data_loc)+os.sep+str(StudyID)+os.sep+str(AccessionN)
    print 'imagepath: ', imagepath

    #################################################
    # Check accession file that exists
    readQueryFile1 = open('outcome'+os.sep+'findscu_'+AccessionN+'_SERIES.txt' , 'r')
    readQueryFile1.seek(0)
    line = readQueryFile1.readline()
    print '---------------------------------------\n'
    ListOfExamsUID = []  
    ListOfSeriesUID = []
    ListOfSeriesID = []
    ListOfSeriesDescription = []
    count = 0
    match = 0
    images_in_series = 0
    
    # write output to file sout
    seriesout =  imagepath+'_seriesStudy.txt'
    sout = open(seriesout, 'a')
    
    while ( line ) : 
        if '(0008,0020) DA [' in line:    #SerieDate
            item = line
            exam_date = item[item.find('[')+1:item.find(']')]        
            #print 'exam_date => ' + exam_date    
            line = readQueryFile1.readline()
            
        elif '(0010,0020) LO [' in line:    #patient_id
            item = line
            patient_id = item[item.find('[')+1:item.find(']')]        
            #print 'patient_id => ' + patient_id    
            line = readQueryFile1.readline()
            
        elif '(0010,0010) PN [' in line:    #patient_name
            item = line
            patient_name = item[item.find('[')+1:item.find(']')] # this need to be anonymized
            patient_name = "AnonName"
            #print 'patient_name => ' + patient_name    
            line = readQueryFile1.readline()
            
        elif '(0008,1030) LO [' in line:    #exam_description
            item = line
            exam_description = item[item.find('[')+1:item.find(']')]        
            #print 'exam_description => ' + exam_description
            line = readQueryFile1.readline()
            
        elif '(0020,000d) UI [' in line:    #exam_uid
            item = line
            exam_uid = item[item.find('[')+1:item.find(']')]        
            #print 'exam_uid => ' + exam_uid    
            ListOfExamsUID.append(exam_uid)
            line = readQueryFile1.readline()
            
        elif '(0008,0050) SH [' in line:    #exam_number
            item = line
            accession_number = item[item.find('[')+1:item.find(']')]        
            #print 'accession_number => ' + accession_number    
            line = readQueryFile1.readline()
            
        elif '(0008,103e) LO [' in line:    #series_description
            item = line
            series_description = item[item.find('[')+1:item.find(']')]        
            #print 'series_description => ' + series_description
            ListOfSeriesDescription.append(series_description)
            line = readQueryFile1.readline()
            
        elif '(0020,000e) UI [' in line:    #series_uid
            item = line
            series_uid = item[item.find('[')+1:item.find(']')]        
            #print 'series_uid => ' + series_uid
            ListOfSeriesUID.append(series_uid)
            line = readQueryFile1.readline()
                    
        elif '(0020,0011) IS [' in line:    #series_number
            item = line
            series_number = item[item.find('[')+1:item.find(']')]
            series_number = series_number.rstrip()
            series_number = series_number.lstrip()
            ListOfSeriesID.append(series_number)
            #print 'series_number => ' + series_number
            
            if(match == 0):  # first series so far
                match = 1
                print " \nAccessionN: %1s %2s %3s %4s %5s \n" % (accession_number, patient_name, patient_id, exam_date, exam_description)
                print >> sout, " \nAccessionN: %1s %2s %3s %4s %5s \n" % (accession_number, patient_name, patient_id, exam_date, exam_description)
                print " series: # %2s %3s %4s \n" % ('series_number', 'series_description', '(#Images)')
                print >> sout, " series: # %2s %3s %4s \n" % ('series_number', 'series_description', '(#Images)')

            line = readQueryFile1.readline()
            
        elif( (line.rstrip() == '--------') and (match == 1) ):
            if (countImages==True): # some servers don't return 0020,1002, so count the series
                os.chdir(str(data_loc))
                
                cmd = 'findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
                -k 0010,0020="" -k 0008,1030="" -k 0008,0020="" -k 0008,0050='+AccessionN+' -k 0020,0011="" -k 0008,0052="IMAGE" \
                -k 0020,000D="" -k 0020,000e='+series_uid+' -k 0020,0013="" -k 0020,0020="" -k 0008,0023="" -k 0008,0033="" -k 00028,0102="" \
                -aet ' + my_aet + ' -aec ' + remote_aet + ' ' + remote_IP + ' ' + remote_port + ' > outcome'+os.sep+'findscu_'+AccessionN+'_IMAGE.txt'
                
                print '\n---- Begin query number of images ' + remote_aet + ' ....' ;
                print "cmd -> " + cmd
                p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
                p1.wait()
                
                #The images are queried and result is saved in tmp\\findscu_SERIES."
                fileout_image = 'outcome'+os.sep+'findscu_'+AccessionN+'_IMAGE.txt'
                readQueryFile2 = open(fileout_image, 'r')
                readQueryFile2.seek(0) # Reposition pointer at the beginning once again
                im_line = readQueryFile2.readline()
                
                while ( im_line ) :
                    if '(0020,0013) IS [' in im_line: #image_number
                        item = im_line
                        image_number = item[item.find('[')+1:item.find(']')]
                        #print 'image_number => ' + image_number
                        images_in_series += 1 
                        
                    im_line = readQueryFile2.readline()    
                
                readQueryFile2.close()
            
                if( images_in_series > 1): 
                    plural_string = "s"
                else: plural_string = "" 
                    
                print ' series %2d: %3d %4s %5d image%s' % (int(count), int(series_number), series_description, int(images_in_series), plural_string)
                print >> sout, ' series %2d: %3d %4s %5d image%s' % (int(count), int(series_number), series_description, int(images_in_series), plural_string)
                  # ------------ FInish obtaining SERIES info  countImages==True
                readQueryFile2.close()
            else:
                print ' series %2d: %3d %4s' % (int(count), int(series_number), series_description)
                print >> sout, ' series %2d: %3d %4s' % (int(count), int(series_number), series_description)
                # ------------ FInish obtaining SERIES info  countImages==False
                   
            line = readQueryFile1.readline()
            count += 1;
            images_in_series=0
        else:
            line = readQueryFile1.readline()
            
    readQueryFile1.close()
    sout.close()
    IDser = 0
    selListOfSeriesID = []
    selListOfSeriesDescription = []
    
    for IDseries in ListOfSeriesID:
        os.chdir(str(data_loc))
        
        # if ExamID folder doesn't exist create it    
        os.chdir(str(StudyID))
        os.chdir(str(AccessionN))
        print os.getcwd()
        
        if('FSE T2' in ListOfSeriesDescription[IDser] or 'VIBRANT' in ListOfSeriesDescription[IDser]):
            if not os.path.exists(str(ListOfSeriesID[IDser])):
                os.makedirs(str(ListOfSeriesID[IDser]))
            
            os.chdir(str(ListOfSeriesID[IDser]))
            selListOfSeriesID.append( ListOfSeriesID[IDser] )
            selListOfSeriesDescription.append( ListOfSeriesDescription[IDser] )
            
            # Proceed to retrive images
            # query protocol using the DICOM C-FIND primitive. 
            # For Retrieval the C-MOVE protocol requires that all primary keys down to the hierarchy level of retrieve must be provided
            cmd = path_rootFolder+os.sep+'movescu -S +P '+ local_port +' -k 0008,0052="IMAGE" -k 0020,000d=' + ListOfExamsUID[int(IDser)] + ' -k 0020,000e=' + ListOfSeriesUID[int(IDser)] + '\
            -aec ' + remote_aet + ' -aet ' + my_aet + ' -aem ' + my_aet + ' ' + remote_IP + ' ' + remote_port
            print cmd
            
            # Image transfer takes place over the C-STORE primitive (Storage Service Class). 
            # All of that is documented in detail in pa  rt 4 of the DICOM standard.
            p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
            p1.wait()
        
        # Go back - go to next 
        os.chdir(str(data_loc))    
        IDser += 1
        
    ########## END PULL #######################################
    return selListOfSeriesID, selListOfSeriesDescription
    

def pull_MRI_MARTELold(data_loc, my_aet, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN, ExamID, countImages):

    os.chdir(str(data_loc))
    # the DICOM query model is strictly hierarchical and the information model hierarchy is PATIENT - STUDY - SERIES - INSTANCE
    # Each query can only retrieve information at exactly one of these levels, and the unique keys of all higher levels must be provided as part of the query. In practice that means you first have to identify a patient, then you can identify studies for that patient, then you can check which series within one study exist and finally you could see which instances (DICOM objects, images) there are within one series. 
    # First findscu will retrive SERIES for a given STUDYID
    cmd = 'findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
    -k 0008,0020="" -k 0020,0010=' + ExamID + ' -k 0020,0011="" -k 0008,0052="SERIES" \
	-k 0020,000D="" -k 0020,000e="" -k 0020,1002="" -k 0008,0070="" \
	-aet ' + my_aet + ' -aec ' + remote_aet + ' ' + remote_IP + ' ' + remote_port+' > '+ 'outcome'+os.sep+'findscu_'+AccessionN+'_SERIES.txt' 
                
    print '\n---- Begin query with ' + remote_aet + ' by PatientID ....' ;
    print "cmd -> " + cmd
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()
    
    #################################################
    # 2nd-Part: # Required for pulling images.
    # Added by Cristina Gallego. July 2013
    #################################################
    readQueryFile1 = open(data_loc+'/checkdata/checkdata_'+AccessionN+'.txt', 'r')
    readQueryFile1.seek(0)
    line = readQueryFile1.readline()

    imagepath = data_loc+'/'+str(StudyID)+'/'+str(AccessionN)
    print 'imagepath: ', imagepath

    if not(os.path.exists(imagepath)):
        os.mkdir(imagepath)

     #################################################
    # Check mthat accession exists
    readQueryFile1 = open('outcome'+os.sep+'findscu_'+AccessionN+'_SERIES.txt' , 'r')
    readQueryFile1.seek(0)
    line = readQueryFile1.readline()
    print '---------------------------------------\n'
    ListOfExamsUID = []  
    ListOfSeriesUID = []
    ListOfSeriesID = []
    count = 0
    match = 0
    images_in_series = 0
    
    # write output to file sout
    seriesout =  imagepath+'_seriesStudy.txt'
    sout = open(seriesout, 'a')
    
    while ( line ) : 
        if '(0008,0020) DA [' in line:    #SerieDate
            item = line
            exam_date = item[item.find('[')+1:item.find(']')]        
            #print 'exam_date => ' + exam_date    
            line = readQueryFile1.readline()
            
        elif '(0010,0020) LO [' in line:    #patient_id
            item = line
            patient_id = item[item.find('[')+1:item.find(']')]        
            #print 'patient_id => ' + patient_id    
            line = readQueryFile1.readline()
            
        elif '(0010,0010) PN [' in line:    #patient_name
            item = line
            patient_name = item[item.find('[')+1:item.find(']')] # this need to be anonymized
            patient_name = "AnonName"
            #print 'patient_name => ' + patient_name    
            line = readQueryFile1.readline()
            
        elif '(0008,1030) LO [' in line:    #exam_description
            item = line
            exam_description = item[item.find('[')+1:item.find(']')]        
            #print 'exam_description => ' + exam_description
            line = readQueryFile1.readline()
            
        elif '(0020,000d) UI [' in line:    #exam_uid
            item = line
            exam_uid = item[item.find('[')+1:item.find(']')]        
            #print 'exam_uid => ' + exam_uid    
            ListOfExamsUID.append(exam_uid)
            line = readQueryFile1.readline()
        

        elif '(0020,0010) SH [' in line:	#exam_number
            item = line
            exam_number = item[item.find('[')+1:item.find(']')]		
            accession_number = AccessionN      
            #print 'exam_number => ' + exam_number	
            line = readQueryFile1.readline()
    
        elif '(0008,103e) LO [' in line:    #series_description
            item = line
            series_description = item[item.find('[')+1:item.find(']')]        
            #print 'series_description => ' + series_description
            line = readQueryFile1.readline()
            
        elif '(0020,000e) UI [' in line:    #series_uid
            item = line
            series_uid = item[item.find('[')+1:item.find(']')]        
            #print 'series_uid => ' + series_uid
            ListOfSeriesUID.append(series_uid)
            line = readQueryFile1.readline()
                    
        elif '(0020,0011) IS [' in line:    #series_number
            item = line
            series_number = item[item.find('[')+1:item.find(']')]
            series_number = series_number.rstrip()
            series_number = series_number.lstrip()
            ListOfSeriesID.append(series_number)
            #print 'series_number => ' + series_number
            
            if(match == 0):  # first series so far
                match = 1
                print " \nAccessionN: %1s %2s %3s %4s %5s \n" % (accession_number, patient_name, patient_id, exam_date, exam_description)
                print >> sout, " \nAccessionN: %1s %2s %3s %4s %5s \n" % (accession_number, patient_name, patient_id, exam_date, exam_description)
                print " series: # %2s %3s %4s \n" % ('series_number', 'series_description', '(#Images)')
                print >> sout, " series: # %2s %3s %4s \n" % ('series_number', 'series_description', '(#Images)')

            line = readQueryFile1.readline()
        
#        elif '(0020,1002) IS [' in line:    #images_in_series
#            item = line
#            images_in_series = item[item.find('[')+1:item.find(']')]        
#            print 'images_in_series => ' + images_in_series
#            line = readQueryFile1.readline()
#            
        elif( (line.rstrip() == '--------') and (match == 1) ):
            if (countImages==True): # some servers don't return 0020,1002, so count the series
                os.chdir(str(data_loc))
                cmd = 'findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
                -k 0010,0020="" -k 0008,1030="" -k 0008,0020="" -k 0008,0050='+AccessionN+' -k 0020,0010=' + ExamID + ' -k 0020,0011="" -k 0008,0052="IMAGE" \
                -k 0020,000D="" -k 0020,000e='+series_uid+' -k 0020,0013="" -k 0020,0020="" -k 0008,0023="" -k 0008,0033="" -k 00028,0102="" \
                -aet ' + my_aet + ' -aec ' + remote_aet + ' ' + remote_IP + ' ' + remote_port + ' > outcome'+os.sep+'findscu_'+AccessionN+'_IMAGE.txt'
                
                print '\n---- Begin query number of images ' + remote_aet + ' ....' ;
                print "cmd -> " + cmd
                p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
                p1.wait()
                
                #The images are queried and result is saved in tmp\\findscu_SERIES."
                fileout_image = 'outcome'+os.sep+'findscu_'+AccessionN+'_IMAGE.txt'
                readQueryFile2 = open(fileout_image, 'r')
                readQueryFile2.seek(0) # Reposition pointer at the beginning once again
                im_line = readQueryFile2.readline()
                
                while ( im_line ) :
                    if '(0020,0013) IS [' in im_line: #image_number
                        item = im_line
                        image_number = item[item.find('[')+1:item.find(']')]
                        #print 'image_number => ' + image_number
                        images_in_series += 1 
                        
                    im_line = readQueryFile2.readline()    
                
                readQueryFile2.close()
            
                if( images_in_series > 1): 
                    plural_string = "s"
                else: plural_string = "" 
                    
                print ' series %2d: %3d %4s %5d image%s' % (int(count), int(series_number), series_description, int(images_in_series), plural_string)
                print >> sout, ' series %2d: %3d %4s %5d image%s' % (int(count), int(series_number), series_description, int(images_in_series), plural_string)
                  # ------------ FInish obtaining SERIES info  countImages==True
                readQueryFile2.close()
            else:
                print ' series %2d: %3d %4s' % (int(count), int(series_number), series_description)
                print >> sout, ' series %2d: %3d %4s' % (int(count), int(series_number), series_description)
                # ------------ FInish obtaining SERIES info  countImages==False
                   
            line = readQueryFile1.readline()
            count += 1;
            images_in_series=0
        else:
            line = readQueryFile1.readline()
            
    readQueryFile1.close()
    sout.close()
    IDser = 0
    
    for IDseries in ListOfSeriesID:
        # if ExamID folder doesn't exist create it    
        os.chdir(str(StudyID))
        os.chdir(str(AccessionN))
        if not os.path.exists('S'+str(ListOfSeriesID[int(IDser)])):
            os.makedirs('S'+str(ListOfSeriesID[int(IDser)]))
        
        os.chdir('S'+str(ListOfSeriesID[int(IDser)]))
        
        # Proceed to retrive images
        # query protocol using the DICOM C-FIND primitive. 
        # For Retrieval the C-MOVE protocol requires that all primary keys down to the hierarchy level of retrieve must be provided
        cmd = data_loc+os.sep+'movescu -S +P '+ local_port +' -k 0008,0052="SERIES" -k 0020,000d=' + ListOfExamsUID[int(IDser)] + ' -k 0020,000e=' + ListOfSeriesUID[int(IDser)] + '\
        -aec ' + remote_aet + ' -aet ' + my_aet + ' -aem ' + my_aet + ' ' + remote_IP + ' ' + remote_port
        print cmd
            
        # Image transfer takes place over the C-STORE primitive (Storage Service Class). 
        # All of that is documented in detail in pa  rt 4 of the DICOM standard.
        p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
        p1.wait()
        
        # Go back - go to next 
        os.chdir(str(data_loc))    
        IDser += 1
        
    ########## END PULL #######################################
    return
    
def check_pacs(path_rootFolder, data_loc, hostID, clinical_aet, clinical_port, clinical_IP, local_port, PatientID, StudyID, AccessionN):
    
    os.chdir(path_rootFolder)
    
    # prepare directories        
    if not os.path.exists(path_rootFolder+os.sep+'querydata'):
        os.makedirs(path_rootFolder+os.sep+'querydata')
        
    print '\n--------- QUERY Suject (MRN): "' + PatientID + '" in "' + clinical_aet + '" from "'+ my_aet + '" ----------'

    cmd = 'findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
            -k 0008,0020="" -k 0008,0050='+AccessionN+' -k 0020,0011="" -k 0008,0052="SERIES" \
            -k 0020,000D="" -k 0020,000e="" -k 0020,1002="" -k 0008,0070="" -aet ' + my_aet + \
    ' -aec ' + clinical_aet + ' ' + clinical_IP + ' ' + clinical_port + ' >  querydata/'+PatientID+'_querydata_'+AccessionN+'.txt'     #142.76.62.102

            
    cmd = 'findscu -v -P -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="' + PatientID + 'SHSC*''"\
    -k 0008,1030="" -k 0008,0052="STUDY" -k 0008,0020="" -k 0020,0010="" -k 0008,0050="*" \
    -k 0008,0060="" -k 0020,0011="" -k 0020,000D= -k 0020,1002="" -aet ' + my_aet + \
    ' -aec ' + clinical_aet + ' ' + clinical_IP + ' ' + clinical_port + ' >  querydata/'+PatientID+'_querydata_'+AccessionN+'.txt'     #142.76.62.102

    print '\n---- Begin query with ' + clinical_aet + ' by PatientID ....' ;
    print "cmd -> " + cmd
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()

    readQueryFile1 = open( 'querydata/'+PatientID+'_querydata_'+AccessionN+'.txt', 'r')
    readQueryFile1.seek(0)
    line = readQueryFile1.readline()
    ListOfSeries = []
    while ( line ) : # readQueryFile1.readlines()):
        #print line
        if '(0008,0020) DA [' in line: #(0020,000d) UI
            lineStudyDate = line
            item = lineStudyDate
            pullStudyDate = item[item.find('[')+1:item.find(']')]

            nextline =  readQueryFile1.readline(),

            if '(0008,0050) SH' in nextline[0]:    # Filters by Modality MR
                item = nextline[0]
                newAccessionN = item[item.find('[')+1:item.find(']')]

            nextline =  readQueryFile1.readline(),
            while ( '(0008,1030) LO' not in nextline[0]) : #(0008,1030) LO
                nextline = readQueryFile1.readline(),

            item = nextline[0]
            pullExamsDescriptions = item[item.find('[')+1:item.find(']')]
            print 'MRStudyDate => ' + pullStudyDate
            print 'newAccessionNumber => ' + newAccessionN
            print 'pullExamsDescriptions => ' + pullExamsDescriptions

            '''---------------------------------------'''
            ListOfSeries.append([pullStudyDate, newAccessionN, pullExamsDescriptions])
            line = readQueryFile1.readline()
        else:
            line = readQueryFile1.readline()
            
    readQueryFile1.close()
    
    #################################################
    # Added: User input to pull specific Exam by Accession
    # Added by Cristina Gallego. April 26-2013
    #################################################
    iExamPair=[]
    flagfound = 1
    for iExamPair in ListOfSeries: # iExamID, iExamUID in ListOfExamsUID: #
        SelectedAccessionN = iExamPair[1]
        str_count = '';

        if SelectedAccessionN.strip() == AccessionN.strip():
            flagfound = 0

    if flagfound == 0:
        print "\n===============\n"
        print 'Accession number found in '+clinical_aet+'- Proceed with retrival'
        print "\n===============\n"
    else:
        print "\n===============\n"
        print 'Accession number Not found in '+clinical_aet+'- Abort'
        print "\n===============\n"
        fil=open('outcome/Errors_findscu_AS0SUNB.txt','a+')
        fil.write(PatientID+'\t'+StudyID+'\t'+str(AccessionN)+'\tAccession number found in '+clinical_aet+'\n')
        fil.close()
        sys.exit()

    return

def pull_pacs(path_rootFolder, data_loc, hostID, clinical_aet, clinical_port, clinical_IP, local_port, PatientID, StudyID, AccessionN):
        
    os.chdir(data_loc)
    print 'EXECUTE DICOM/Archive Commands ...'
    print 'Query,  Pull,  Anonymize, Push ...'

    print '\n--------- QUERY Suject (MRN): "' + PatientID + '" in "' + clinical_aet + '" from "'+ my_aet + '" ----------'

    cmd = 'findscu -v -P -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="' + PatientID + 'SHSC*''"\
    -k 0008,1030="" -k 0008,0052="STUDY" -k 0008,0020="" -k 0020,0010="" -k 0008,0050="*" \
    -k 0008,0060="" -k 0020,0011="" -k 0020,000D= -k 0020,1002="" -aet ' + my_aet + \
    ' -aec ' + clinical_aet + ' ' + clinical_IP + ' ' + clinical_port + ' > querydata/'+PatientID+'_querydata_'+AccessionN+'.txt'     #142.76.62.102

    print '\n---- Begin query with ' + clinical_aet + ' by PatientID ....' ;
    print "cmd -> " + cmd
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()

    readQueryFile1 = open( 'querydata/'+PatientID+'_querydata_'+AccessionN+'.txt', 'r')
    readQueryFile1.seek(0)
    line = readQueryFile1.readline()
    print '---------------------------------------'
    ListOfExams = []
    ListOfExamsUID = [] ;
    ListOfExamsID = []
    ListOfExamsDescriptions = []
    ListOfExamDates = []
    while ( line ) : # readQueryFile1.readlines()):
        # found instance of exam
        #print line
        if '(0008,0020) DA [' in line: #(0020,000d) UI
            lineStudyDate = line
            item = lineStudyDate
            pullStudyDate = item[item.find('[')+1:item.find(']')]

            nextline =  readQueryFile1.readline(),

            if '(0008,0050) SH' in nextline[0]:    # Filters by Modality MR
                item = nextline[0]
                newAccessionN = item[item.find('[')+1:item.find(']')]

        if '(0008,0060) CS [MR]' in line:    # Filters by Modality MR
            '''---------------------------------------'''
            nextline =  readQueryFile1.readline(),
            while ( 'StudyDescription' not in nextline[0]) : #(0008,1030) LO
                nextline = readQueryFile1.readline(),

            item = nextline[0]
            pullExamsDescriptions = item[item.find('[')+1:item.find(']')]
            print 'MRStudyDate => ' + pullStudyDate
            print 'newAccessionNumber => ' + newAccessionN
            print 'pullExamsDescriptions => ' + pullExamsDescriptions

            '''---------------------------------------'''
            nextline = readQueryFile1.readline(),
            while ( 'StudyInstanceUID' not in nextline[0]) : #(0020,000d) UI
                nextline = readQueryFile1.readline(),

            item = nextline[0]
            pullStudyUID = item[item.find('[')+1:item.find(']')]
            print 'pullStudyUID => ' + pullStudyUID
            print '\n'

            '''---------------------------------------'''
            ListOfExams.append([pullStudyDate, newAccessionN, pullExamsDescriptions, pullStudyUID])
            line = readQueryFile1.readline()
        else:
            line = readQueryFile1.readline()

    readQueryFile1.close()
    #print ListOfExams

    #################################################
    # Added: User input to pull specific Exam by Accession
    # Added by Cristina Gallego. April 26-2013
    #################################################
    iExamPair=[]
    flagfound = 1
    for iExamPair in ListOfExams: # iExamID, iExamUID in ListOfExamsUID: #
        SelectedAccessionN = iExamPair[1]
        SelectedExamUID = iExamPair[3]

        print AccessionN, SelectedAccessionN
        str_count = '';

        if SelectedAccessionN.strip() == AccessionN.strip():
            flagfound = 0
            for k in range(0,len(AccessionN.strip())):
                if SelectedAccessionN[k] == AccessionN[k]:
                    str_count = str_count+'1'

            print len(AccessionN)
            print len(str_count)
            if( len(AccessionN) == len(str_count)):
                print "\n===============\n SelectedAccessionN, SelectedExamUID"
                iAccessionN = SelectedAccessionN
                iExamUID = SelectedExamUID
                print iAccessionN, iExamUID
                print "\n===============\n"
                break
            
    if flagfound == 1:
        fil=open( 'outcome/Errors_pull_AS0SUNB.txt','a')
        fil.write(PatientID+'\t'+StudyID+'\t'+str(AccessionN)+'\tAccession number not found in AS0SUNB\n')
        fil.close()
        print "\n===============\n"
        sys.exit("Error. Accession number not found in AS0SUNB.")


    # Create fileout to print listStudy information
    # if StudyID folder doesn't exist create it
    if not os.path.exists(data_loc+os.sep+str(StudyID)):
        os.makedirs(data_loc+os.sep+str(StudyID))

    os.chdir(data_loc+os.sep+str(StudyID))

    # if AccessionN folder doesn't exist create it
    if not os.path.exists(str(AccessionN)):
        os.makedirs(str(AccessionN))

    os.chdir(str(data_loc))

    #################################################
    # 2nd-Part: # Required for pulling images.
    # Added by Cristina Gallego. July 2013
    #################################################
    writeRetrieveFile1 = open( 'outcome/oRetrieveExam.txt', 'w')
    readRetrieveFile1 = open( 'outcome/RetrieveExam.txt', 'r')
    print "Read original tags from RetrieveExam.txt. ......"
    readRetrieveFile1.seek(0)
    line = readRetrieveFile1.readline()
    outlines = ''

    while ( line ) : # readRetrieveFile1.readlines()):
        if '(0020,000d) UI' in line:    #StudyUID
            #print line,
            fakeStudyUID = line[line.find('[')+1:line.find(']')]
            print 'fakeStudyUID => ' + fakeStudyUID
            line = line.replace(fakeStudyUID, iExamUID)
            outlines = outlines + line
            line = readRetrieveFile1.readline()
        else:
            outlines = outlines + line
            line = readRetrieveFile1.readline()

    writeRetrieveFile1.writelines(outlines)
    writeRetrieveFile1.close()
    readRetrieveFile1.close()

    readRetrieveFile2 = open( 'outcome/oRetrieveExam.txt', 'r')
    print "Updated tags from oRetrieveExam.txt. ......"
    for line in readRetrieveFile2.readlines(): # failed to print out ????
        print line,
    readRetrieveFile2.close()

    print '---------------------------------------'
    print os.path.isfile('dump2dcm.exe')
    cmd = 'dump2dcm outcome/oRetrieveExam.txt outcome/RetrieveExam.dcm' #r'dump2dcm
    print 'cmd -> ' + cmd
    print 'Begin dump to dcm ....' ;
    os.system(cmd)
    print 'outcome/RetrieveExam.dcm is formed for pulling image from remote_aet.'
    

    # Now Create a subfolder : AccessionN to pull images .
    os.chdir(img_folder+os.sep+str(StudyID)+os.sep+str(AccessionN))

    ########## START PULL #######################################
    print 'Pulling images to cwd: ' + os.getcwd()
    cmd = data_loc+'/movescu -P +P ' + local_port + ' -aem ' + my_aet + ' -aet ' + my_aet + ' -aec ' + clinical_aet \
    + ' ' + clinical_IP + ' ' + clinical_port + ' ' + data_loc+'/outcome/RetrieveExam.dcm '

    print 'cmd -> ' + cmd
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()
    ########## END PULL #######################################

    print 'Next, to group "raw" image files into a hierarchical. ...'
    imagepath = img_folder+os.sep+str(StudyID)+os.sep+str(AccessionN) + '\\MR*.*'
    print 'imagepath: ', imagepath

    #################################################################
    # Anonymize/Modify images.
    # (0020,000D),StudyUID  (0020,000e),SeriesUID                   #
    # (0010,0010),PatientName/ID                                    #
    # (0012,0021),"BRCA1F"  (0012,0040),StudyNo                     #
    ###########################################
    os.chdir(str(data_loc))
    
    # Group all image files into a number of series for StudyUID/SeriesUID generation.
    cmd = 'dcmdump +f -L +F +P "0020,000e" +P "0020,0011" "' + imagepath + '" > outcome/pulledDicomFiles.txt'
    print 'cmd -> ' + cmd
    print 'Begin SortPulledDicom ....' ;
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()
    
    readPulledFiles = open('outcome/pulledDicomFiles.txt', 'r')
    
    cmd = 'dcmdump +f -L +F +P "0020,000e" +P "0008,103e" "' + imagepath + '" > outcome/descripPulledDicomFiles_'+str(StudyID)+'.txt'
    print 'cmd -> ' + cmd
    print 'Begin SortPulledDicom ....' ;
    p2 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p2.wait()
    
    print '---------------------------------------'
    ListOfSeriesGroup    = [] ; # [SeriesNo, SeriesUID] # SeriesNumber
    ListOfSeriesGroupRev = [] ; # [SeriesUID, SeriesNo]
    ListOfSeriesPairs    = [] ; # [imageFn, SeriesUID]
    #ListOfExamsID = []
    outlines = ""
    nextline = readPulledFiles.readline()
    while ( nextline ) : # readPulledFiles.readlines()):
        if 'dcmdump' in nextline:   #Modality
            item = nextline; #[0]
            imageFn = item[item.find(')')+2 : item.find('\n')]

            nextline = readPulledFiles.readline() # ( 'SeriesNumber' : #(0020,0011) IS
            item = nextline; #[0]
            SeriesNo = item[item.find('[')+1:item.find(']')]

            nextline =  readPulledFiles.readline() # ( 'SeriesInstanceUID' :    #(0020,000e) SH
            item = nextline; #[0]
            SeriesUID = item[item.find('[')+1:item.find(']')]

            '''---------------------------------------'''
            ListOfSeriesGroup.append([SeriesNo, SeriesUID])
            ListOfSeriesGroupRev.append([SeriesUID, SeriesNo])
            ListOfSeriesPairs.append([imageFn, SeriesUID])

            nextline = readPulledFiles.readline()
        else:
            nextline = readPulledFiles.readline()
    readPulledFiles.close()

    print "\n************************************************"
    #print 'ListOfSeriesGroup'
    #print ListOfSeriesGroup

    #print 'ListOfSeriesGroup'
    #ListOfSeriesGroupRev

    #print 'ListOfSeriesGroup'
    #ListOfSeriesPairs

    # Make a compact dictionary for {ListOfSeriesGroup}.
    ListOfSeriesGroupUnique = dict(ListOfSeriesGroup) #ListOfSeriesGroup:
    ListOfSeriesGroupUniqueRev = dict(ListOfSeriesGroupRev)

    # Make a compact dictionary\tuple for {ListOfSeriesPairs}.
    outlines = outlines + '------ListOfSeriesPairs---------'+ '\n'
    for SeriesPair in ListOfSeriesPairs:
        outlines = outlines + SeriesPair[0] + ', ' + SeriesPair[1] + '\n';

    outlines = outlines + 'Size: ' + str(len(ListOfSeriesPairs)) + '\n\n';
    outlines = outlines + '------ListOfSeriesGroup---------' + '\n'

    #for SeriesPair in ListOfSeriesGroup:
    #   outlines = outlines + SeriesPair[0] + ', ' + SeriesPair[1] + '\n';
    for k,v in ListOfSeriesGroupUnique.iteritems():
        outlines = outlines + k + ', \t\t' + v + '\n';
    outlines = outlines + 'Size: ' + str(len(ListOfSeriesGroupUnique)) + '\n\n';

    outlines = outlines + '------ListOfSeriesGroupRev---------' + '\n'

    #Calculate total number of the files of each series
    for k,v in ListOfSeriesGroupUniqueRev.iteritems():
        imagefList = []
        #print 'key -> ', v, # '\n'
        for SeriesPair in ListOfSeriesPairs:
            if SeriesPair[1] == k: # v:
                #print SeriesPair[1], '\t\t', v
                imagefList.append(SeriesPair[0])

        outlines = outlines + k + ', \t\t' + v + '\t\t' + str(len(imagefList)) + '\n';

    outlines = outlines + 'Size: ' + str(len(ListOfSeriesGroupUniqueRev)) + '\n\n';
    outlines = outlines + 'StudyInstanceUID: ' + str(iExamUID) + '\n';
    outlines = outlines + '\n\n------ListOfSeriesGroup::image files---------' + '\n'

    #List all files of each series
    for k,v in ListOfSeriesGroupUniqueRev.iteritems():
        imagefList = []
        for SeriesPair in ListOfSeriesPairs:
            if SeriesPair[1] == k: # v:
                imagefList.append(SeriesPair[0])
                #outlines = outlines + SeriesPair[0] + '\n';
        outlines = outlines + k + ', \t\t' + v + '\t\t' + str(len(imagefList)) + '\n\n';

    writeSortedPulledFile = open('outcome/sortedPulledDicomFiles.txt', 'w')
    try:
        writeSortedPulledFile.writelines(outlines)
    finally:
        writeSortedPulledFile.close()

    #################################################################
    # 3rd-Part: Anonymize/Modify images.                  #
    # (0020,000D),StudyUID  (0020,000e),SeriesUID                   #
    # (0010,0010),PatientName/ID                                    #
    # (0012,0021),"BRCA1F"  (0012,0040),StudyNo                     #
    #################################################################
    os.chdir(str(imagepath))
    print 'Anonymize images at cwd: ' + os.getcwd()

    # Make anonymized UID.
    print 'Check out system date/time to form StudyInstUID and SeriesInstUID ' # time.localtime()
    tt= time.time() # time(). e.g. '1335218455.013'(14), '1335218447.9189999'(18)
    shorttime = '%10.5f' % (tt)         # This only works for Python v2.5. You need change if newer versions.
    SRI_DCM_UID = '1.2.826.0.1.3680043.2.1009.'
    hostIDwidth = len(hostID)
    shostID = hostID[hostIDwidth-6:hostIDwidth] # Take the last 6 digits

    anonyStudyUID = SRI_DCM_UID + shorttime + '.' + hostID + str(AccessionN).strip() ;
    print 'anonyStudyUID->', anonyStudyUID, '\n'
    aPatientID = StudyID + 'CADPat'
    aPatientName = 'Patient ' + StudyID + 'Anon'

    #For Loop: every Series# with the Exam# in Anonymizing
    sIndex = 0
    ClinicTrialNo = StudyID.strip()
    print 'ClinicTrialNo: "' + ClinicTrialNo + '"'
    print 'Begin Modify ....' ;
    for k,v in ListOfSeriesGroupUniqueRev.iteritems():
        sIndex = sIndex + 1
        imagefList = []
        tt= time.time()
        shorttime = '%10.7f' % (tt)
        anonySeriesUID = SRI_DCM_UID + '' + shorttime + '' + shostID + v + '%#02d' % (sIndex)
        print 'key -> ', v, '\t', 'anonySeriesUID->', anonySeriesUID, # '\n' '\t\t\t', k

        for SeriesPair in ListOfSeriesPairs:
            print SeriesPair
            if SeriesPair[1] == k: # v:
                #print SeriesPair[1], '\t\t', v #, '\n' ###[0], '\t\t', k #, '\n'
                imagefList.append(SeriesPair[0])
                cmd = data_loc+'/dcmodify -gin -m "(0020,000D)=' + anonyStudyUID + '" -m "(0020,000e)=' + anonySeriesUID + '" \
                -m "(0010,0010)=' + aPatientName + '" -m "(0010,0020)=' + aPatientID +'" \
                -i "(0012,0021)=BRCA1F" -i "(0012,0040)=' + ClinicTrialNo + '" ' + SeriesPair[0] + ' > ' +data_loc+'/outcome/dcmodifiedPulledDicomFiles.txt'
                lines = os.system(cmd)

        print '(', len(imagefList), ' images are anonymized.)'

    print 'Total Series: ' + str(len(ListOfSeriesGroupUniqueRev)) + '\n';
    print 'cmd -> ' + cmd + '\n'

    ##########################################################################
    # Clean files

    bakimagepath = ('*.bak').strip() # (iExamID + '\\*.bak').strip()
    print 'Clean backup files (' + bakimagepath + ') ....' ;

    for fl in glob.glob(bakimagepath):
        #Do what you want with the file
        #print fl
        os.remove(fl)

    print 'Backed to cwd: ' + os.getcwd()

    ##########################################################################
    # 4-Part: Check anonymized Dicomd files resulted from modifing process.  #
    # This is used to compare with pulled Dicom Files.                       #
    # Finallly sort anonnimized files                                     #
    ##########################################################################
    print 'Next, to group "anonymized" image files into a hierarchical. ...'
    print 'imagepath: ', imagepath

    #########################################
    os.chdir(str(data_loc))

    # Group all image files into a number of series for StudyUID/SeriesUID generation.
    cmd = 'dcmdump +f -L +F +P "0020,000e" +P "0020,0011" "' + imagepath + '" > outcome/anonyPulledDicomFiles.txt'
    print 'cmd -> ' + cmd
    print 'Begin SortAnonyDicom ....' ;
    lines = os.system(cmd)

    ##########################################################################
    # 5-Part: Last part added when dealing with local pulls and NOT PUSHES.  #
    # This part will arrange individual images into folders by Series   #
    # Creates a folder for each series                                     #
    ##########################################################################
    readPulledSortedFiles = open('outcome/descripPulledDicomFiles_'+str(StudyID)+'.txt', 'r')
    
    #'---------------------------------------'
    os.chdir(imagepath)
    nextline = readPulledSortedFiles.readline()
    while ( nextline ) : # readPulledFiles.readlines()):
        if 'dcmdump' in nextline:   #Modality
            item = nextline; #[0]
            imageFn = item[item.find('MR.') : item.find('\n')]
            #print imageFn

            nextline = readPulledSortedFiles.readline() # ( 'SeriesNumber' : #(0020,0011) IS
            item = nextline; #[0]
            SeriesDes = item[item.find('[')+1:item.find(']')]
            #print SeriesDes
            ch = re.compile('/')
            SeriesDes = ch.sub('-', SeriesDes)

            nextline =  readPulledSortedFiles.readline() # ( 'SeriesInstanceUID' :    #(0020,000e) SH
            item = nextline; #[0]
            SeriesUID = item[item.find('[')+1:item.find(']')]
            
            #---------------------------------------
            if not(os.path.exists(imagepath+'/'+SeriesDes)):
                os.mkdir(imagepath+'/'+SeriesDes)
            
            mv_subp = subprocess.Popen(['mv', imageFn, SeriesDes], stdout=subprocess.PIPE)
            mv_subp.wait()
            #---------------------------------------
            nextline = readPulledSortedFiles.readline()
        else:
            nextline = readPulledSortedFiles.readline()
            
    readPulledSortedFiles.close()

    print "\n************************************************"
   
    return