#!/usr/bin/python 

import sys, os
import string
import shutil
import itertools
import glob ##Unix style pathname pattern expansion
import time
import shlex, subprocess
from dictionaries import my_aet, my_port, hostID, local_port, remote_aet, remote_IP, remote_port

"""
-----------------------------------------------------------
Runs batch Exam list to get Dicom Exams on a local folder based on list of 
Exam_list.txt(list of MRN StudyIDs DicomExam# )

Run on master folder: Z:\Cristina\Pipeline4Archive
where Z: amartel_data(\\srlabs)

usage:     python Get_Anonymized_DicomExam.py Exam_list.txt
    [INPUTS]    
        Exam_list.txt (required) sys.argv[1] 

% Copyright (C) Cristina Gallego, University of Toronto, 2012 - 2013
% April 26/13 - Created first version that queries StudyId based on the AccessionNumber instead of DicomExamNo
% Sept 18/12 -     Added additional options for retrieving only specific sequences (e.g T1 or T2)
% Mar
-----------------------------------------------------------
"""
def get_only_filesindirectory(mydir):
    """List and get only files inside a directory mydir"""
    return [name for name in os.listdir(mydir) 
        if os.path.isfile(os.path.join(mydir, name))]

def check_pacs(path_rootFolder, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN):
    """
    Checks for the existance of a given accession number in remote_aet,
    if not present, proceed to pull from pacs, if present, stops and writes case to checkdata\Errors_check.txt
    """
    print '\n--------- QUERY Suject: "' + PatientID + '" in "' + remote_aet + '" from "'+ my_aet + '" ----------'
    print "First: Checking whether wanted exam is archived on 'MRI_MARTEL'.\n"
    
    cmd=path_rootFolder+os.sep+'findscu -v -S -k 0008,0020="" -k 0010,0010="" -k 0010,0020="" -k 0008,0018="" -k 0008,103e="" -k 0020,000e="" '+\
            '-k 0008,0050='+AccessionN+' -k 0008,0052="SERIES" \
        -aet '+my_aet+' -aec '+remote_aet+' '+remote_IP+' '+remote_port+' > '+ 'checkdata'+os.sep+'checkdata_'+AccessionN+'.txt' 
        
    print '\n---- Begin query with ' + remote_aet + ' by PatientID ....' ;
    print "cmd -> " + cmd
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()
    
    #################################################
    # Check mthat accession exists
    readQueryFile1 = open('checkdata'+os.sep+'checkdata_'+AccessionN+'.txt' , 'r')
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
            while ( '(0008,103e) LO' not in nextline[0]) : #(0008,1030) LO 
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
        
    if flagfound == 1:
        print "\n===============\n"
        os.chdir(path_rootFolder)
        fil=open('checkdata'+os.sep+'Errors_check.txt','a')
        fil.write(PatientID+'\t'+StudyID+'\t'+str(AccessionN)+'\tAccession number found in '+remote_aet+'\n')
        fil.close()
        print "\n===============\n"
        sys.exit('Accession number not found in '+remote_aet)    
    else:
        print "\n===============\n"
        print 'Accession number found in '+remote_aet +' - Proceed with retrival'
        print "\n===============\n"
        
    return

            
def pull_pacs(path_rootFolder, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN, countImages):
    """
    Checks for the existance of a given accession number in remote_aet,
    if not present, proceed to pull from research pacs, if present, stops and writes case to checkdata\Errors_check.txt
    """
    current_loc = os.getcwd() #'Z:'+os.sep+'Cristina'+os.sep+'Pipeline4Archive' 

    cmd='findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
            -k 0008,0020="" -k 0008,0050='+AccessionN+' -k 0020,0011="" -k 0008,0052="SERIES" \
            -k 0020,000D="" -k 0020,000e="" -k 0020,1002="" -k 0008,0070="" \
            -aet '+my_aet+' -aec '+remote_aet+' '+remote_IP+' '+remote_port+' > '+ 'outcome'+os.sep+'findscu_'+AccessionN+'_SERIES.txt' 
              
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
    seriesout =  path_rootFolder+os.sep+str(StudyID)+os.sep+str(AccessionN)+'_seriesStudy.txt'
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
        
        elif '(0020,1002) IS [' in line:    #images_in_series
            item = line
            images_in_series = item[item.find('[')+1:item.find(']')]        
            #print 'images_in_series => ' + images_in_series
            line = readQueryFile1.readline()
        
        elif( (line.rstrip() == '--------') and (match == 1) ):
            if (images_in_series == 0 & countImages==True): # some servers don't return 0020,1002, so count the series
                cmd = path_rootFolder+os.sep+'findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
                -k 0010,0020="" -k 0008,1030="" -k 0008,0020="" -k 0008,0050='+AccessionN+' -k 0020,0011="" -k 0008,0052="IMAGE" \
                -k 0020,000D="" -k 0020,000e='+series_uid+' -k 0020,0013="" -k 0020,0020="" -k 0008,0023="" -k 0008,0033="" -k 00028,0102="" \
                -aet ' + my_aet + ' -aec ' + remote_aet + ' ' + remote_IP + ' ' + remote_port + ' > outcome'+os.sep+'findscu_'+AccessionN+'_IMAGE.txt'
                
                #lines = os.system(cmd) 
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
                 # ------------ FInish obtaining SERIES info 
                readQueryFile2.close()
            else:
                print ' series %2d: %3d %4s' % (int(count), int(series_number), series_description)
                print >> sout, ' series %2d: %3d %4s' % (int(count), int(series_number), series_description)
                 # ------------ FInish obtaining SERIES info without images
                
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
                
        # Anno Patient personal information such as "PatientName"
        for sfiles in listSeries_files:
            cmd = path_rootFolder+os.sep+'dcmodify -ma "(0010,0010)=AnonName" '+sfiles
            p1 = subprocess.Popen(cmd, shell=False)
            p1.wait()
            try:
                p2 = subprocess.Popen(['rm', sfiles+'.bak'], shell=True, stdin=subprocess.PIPE)
                p2.wait()
            except ValueError:
                break

        # Go back - go to next 
        os.chdir(str(path_rootFolder))    
        IDser += 1
        
    ########## END PULL #######################################
        
    return
