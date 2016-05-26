import os
import os.path
import sys
import string
import time
from sys import argv, stderr, exit
import shlex, subprocess
from numpy import *
from scipy.io import loadmat, savemat
import dicom
import Tix
from datetime import date
from operator import itemgetter, attrgetter
#from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
import pandas as pd


"""
Compilation of functions

usage:
======
import processDicoms
then on script use:
SUPPORT FUNCTIONS:
- processDicoms.FileCheck(argvs)
- processDicoms.is_number(argvs)
- processDicoms.get_immediate_subdirectories(argvs)
- processDicoms.get_only_linksindirectory(argvs)
- processDicoms.get_immediate_subdirectories(argvs)
- processDicoms.find(argvs)
- processDicoms.get_display_series(argvs)
- processDicoms.get_display(argvs)
- processDicoms.get_series(argvs)

PARSING DICOM SERIES:
- processDicoms.get_slices_at_all_locs(argvs)
- processDicoms.get_slices_for_volumes(argvs)

% Copyright (C) Cristina Gallego, University of Toronto, 2012
----------------------------------------------------------------------
"""
def ReadDicomfiles(abspath_PhaseID):
    """
    Reads dicom files located in Series folder on local machine, extracts total number 
    of images in series, process stacks by slice location and finds most left slice (marks origin).
    
    Inputs
    =======
    abspath_PhaseID: (string) path to files
    
    Output
    ========
    len_listSeries_files: (int)   # of images in series
    
    FileNms_slices_sorted_stack:  (DataFrame)    List of filenames amd slice location
    """
    slices = []
    FileNms_slices =  []
    
    listSeries_files = list(get_only_filesindirectory(str(abspath_PhaseID)))
    len_listSeries_files = len(listSeries_files)
                
    for n in range(len_listSeries_files):
        # Use all DICOM slices on series
        ''' EXTRACT DICOM SLICE LOCATION '''
        absp_fsID = str(abspath_PhaseID)+os.sep+listSeries_files[n]
        dInfo = dicom.read_file(absp_fsID, force=True )
        slices.append(dInfo.SliceLocation)
        FileNms_slices.append(listSeries_files[n])

    print "Total images in series: %d " % len_listSeries_files

    '''\nPROCESS STACKS BY SLICE LOCATIONS '''
    FileNms_slices_stack = pd.DataFrame({'slices': FileNms_slices,
                                         'location': slices})
    
    sorted_FileNms_slices_stack = FileNms_slices_stack.sort_values(by='location')        
    
    return len_listSeries_files, sorted_FileNms_slices_stack
    
    
# Function that checks whether file DICOMDIR.txt exits 
def FileCheck(filename):       
       try:
           fn=open(filename,"r") 
           fn.close()
           return True
       except IOError: 
           print "Error: DICOMDIR.txt doesn't exit, loading Series using vtkDICOMImageReader by setDirectoryName."
       return False

# Checks whether a number is float
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
        
# Gets immediate_subdirectories of folder mydir
def get_immediate_subdirectories(mydir):
    return [name for name in os.listdir(mydir) 
            if os.path.isdir(os.path.join(mydir, name))]

# Gets only_links in directory of folder mydir
def get_only_linksindirectory(mydir):
    return [name for name in os.listdir(mydir) 
            if os.path.islink(os.path.join(mydir, name))]

# Gets only_files in directory of folder mydir, excluding subdirectories folders
def get_only_filesindirectory(mydir):
     return [name for name in os.listdir(mydir) 
            if os.path.isfile(os.path.join(mydir, name))]

# Finds a substring within a string of chars
def find(strng, ch):
    index = 0
    while index < len(strng):
        if strng[index] == ch:
            return index
        index += 1                  
    return -1
     
def get_display_series(abspath_SeriesID):
    """
    Lists and displays the summary of DICOM Series available for display
    
    Inputs
    =======
    abspath_SeriesID: (string) path to files in a SeriesID
    
    Output
    ========
    arranged_folders: (dict)   immediate_subdirectories of folder abspath_SeriesID
    """
    arranged_folders = get_immediate_subdirectories(abspath_SeriesID);

    # Initialize series count
    s=0;
    print "Total number of series: %d" % len(arranged_folders)
    print " "
    print "%s     %s        %s     %s " % ('n', 'Series#', '#Images', 'SeriesDescription')
            
    # Iterate for each series in ExamID
    for arrangedF in arranged_folders:
        path_arrangedF_ID = abspath_SeriesID+os.sep+arrangedF
        #print path_SeriesID
        
        # Get total number of files
        listSeries_files = get_only_filesindirectory(path_arrangedF_ID)
                    
        # Use only the first slice one file and get DICOM DICTIONARY
        if(listSeries_files != []):
            path_filenameID = abspath_SeriesID+os.sep+arrangedF+os.sep+listSeries_files[0]
            
            NumberOfVolumes = 1 # default
            
            # iterate number of slices and get full volume (#slices, each slice loc)
            slices = []
            num_images=0;
            for filename in listSeries_files:
                num_images = num_images+1
                    
            # Print series info                        
            print "%d    %d        %s" % (s, num_images, arrangedF) 
            # increment series number
            s=s+1;    
        else:
            print "%d    %s        %d        %s" % (s, "NONE", 0, "NULL") 
            # increment series number
            s=s+1;    
        
    # Go back to rootfolder
    os.chdir(path_rootFolder)
    
    return arranged_folders

def get_display(abspath_SeriesID):
    """
    Finds all dicoms Series in sudyfolder abspath_SeriesID and Iterates
    
    Inputs
    =======
    abspath_SeriesID: (string) path to files in a SeriesID
    
    Output
    ========
    arranged_folders: (dict)   immediate_subdirectories of folder abspath_SeriesID
    """
    arranged_folders = get_immediate_subdirectories(abspath_SeriesID);
    
    # Initialize series count
    s=0;
    print " "
    print "%s \t %s \t\t %s " % ('n', 'Series#', '#Images')
    
    # Find all dicoms Series in sudyfolder (will go into including subfolders)
    # Iterate
    for arrangedF in arranged_folders:
        #print "arrangedFolder: %s" % arrangedF
        path_arrangedF_ID = abspath_SeriesID+os.sep+arrangedF
        #print path_arrangedF_ID
        
        # Enter Studyfolder to process all Dicom Series of ExamID
        path_arrangedF_images = get_only_filesindirectory(path_arrangedF_ID);
        #print path_arrangedF_images

        print "%s \t %s \t\t %s " % (s, arrangedF, len(path_arrangedF_images))
        
        # increment series number
        s=s+1;    
        
    # Go back to rootfolder
    os.chdir(path_rootFolder)
    
    return arranged_folders            
    
    
def get_series(StudyID,img_folder):
    """
    Obtains subdires in the StudyID directory, correspond to ExamsID 
    Checks for one in subdirectory tree, (e.g Mass or NonMass) 
    
    Inputs
    =======
    StudyID: (str) StudyID or CAD patient id
    
    img_folder: (str)   Path to images subdirectory tree (either Mass or NonMass) 
    
    Outputs
    ========
    abspath_ExamID: (str)    Path to path_ExamID = img_folder/StudyID/eID
    eID (str):   Chosen series id in sequence number (1 to n)
    SeriesID, studyFolder (str):    Other series info
    dicomInfo (pydicom dict): Available dicom info
    """
    global abspath_SeriesID
    
    path_studyID = img_folder+StudyID
    studyFolder = os.path.abspath(path_studyID)
    print studyFolder
    
    ExamsID = get_immediate_subdirectories(path_studyID);
    #print ExamsID
    c = 0
    if(len(ExamsID)>1):
        
        print "%s     %s    " % ('n', 'Series#')
        for iexam in ExamsID:
            print "%d    %s " % (c, str(iexam)) 
            c=c+1
                    
        choseSerie = raw_input('Enter n Series to load (0-n), or x to exit: ')
        if(choseSerie != 'x'):
            c = 0
            for iexam in ExamsID:
                if(int(choseSerie) == c):
                    eID = iexam
                c=c+1    
        else:
            return '', 0, '', studyFolder
            
        
        print "ExamID: %s" % eID
        path_ExamID = img_folder+StudyID+os.sep+eID
        abspath_ExamID = os.path.abspath(path_ExamID)
        print abspath_ExamID
        
        # Enter Studyfolder to process all Dicom Series of ExamID
        SeriesID = get_immediate_subdirectories(path_ExamID);
        #print SeriesID
        
        # Initialize series count
        s=0;
        print "Total number of series: %d" % len(SeriesID)
        print " "
        print "%s     %s        %s     %s " % ('n', 'Series#', '#Images', 'SeriesDescription')
                
        # Iterate for each series in ExamID
        for sID in SeriesID:

            path_SeriesID = img_folder+StudyID+os.sep+eID+os.sep+sID
                            
            abspath_SeriesID = os.path.abspath(path_SeriesID)
            
            # Get total number of files
            listSeries_files = get_only_filesindirectory(abspath_SeriesID)
            
            #initialize
            PatientID=''
            SeriesNumber=''
            SeriesDescription=''
            MinSliceLocation=''
            ImageOrientationPatient=''
            
            # Use only the first slice one file and get DICOM DICTIONARY
            if(listSeries_files != []):
                path_filenameID = img_folder+StudyID+os.sep+eID+os.sep+sID+os.sep+listSeries_files[0]
                try:
                    dicomInfo = dicom.read_file(os.path.abspath(path_filenameID), force=True)
                except ValueError:
                    dicomInfo = []
                    
                # Get the main dataset (they are in fact two separate datasets in the DICOM standard). 
                # That dicom dataset is now stored in the file_meta attribute of the dataset
                                                
                # Get structure of study (all files in directory consistent with studyID and patientID
                studyTree = []
                FileNames=listSeries_files;
                if("PatientID" in dicomInfo):
                    PatientID = dicomInfo.PatientID#
                else:    PatientID=''
                if("SeriesNumber" in dicomInfo):
                    SeriesNumber = dicomInfo.SeriesNumber#
                else:    SeriesNumber=''
                if("SeriesDescription" in dicomInfo):
                    SeriesDescription = dicomInfo.SeriesDescription; #
                else:    SeriesDescription=''
                if("SliceLocation" in dicomInfo):
                    MinSliceLocation = dicomInfo.SliceLocation; # Infos to identify number of slices/volumes
                else:    MinSliceLocation=''
                if('ImageOrientationPatient' in dicomInfo):
                    ImageOrientationPatient = dicomInfo.ImageOrientationPatient; # Infos to identify number of slices/volumes
                else:    ImageOrientationPatient=''
                
                NumberOfVolumes = 1 # default
                
            # iterate number of slices and get full volume (#slices, each slice loc)
            slices = []
            num_images=0;
            for filename in listSeries_files:
                num_images = num_images+1
                    
            # Print series info                        
            print "%d    %s        %d        %s" % (s, SeriesNumber, num_images, SeriesDescription) 
            # increment series number
            s=s+1;    
            
            # Go back to rootfolder
            chdirname='Z:/Cristina/MassNonmass/'
            os.chdir(chdirname)  
            #print os.getcwd()
    else:    
        studyFolder = os.path.abspath(path_studyID)
        #print studyFolder
        
        # Find all dicoms Series in sudyfolder (will go into including subfolders)
        # Iterate
        for eID in ExamsID:
            print "ExamID: %s" % eID
            path_ExamID = img_folder+StudyID+os.sep+eID
            abspath_ExamID = os.path.abspath(path_ExamID)
            print abspath_ExamID
            
            # Enter Studyfolder to process all Dicom Series of ExamID
            SeriesID = get_immediate_subdirectories(path_ExamID);
            #print SeriesID
            
            # Initialize series count
            s=0;
            print "Total number of series: %d" % len(SeriesID)
            print " "
            print "%s     %s        %s     %s " % ('n', 'Series#', '#Images', 'SeriesDescription')
                    
            # Iterate for each series in ExamID
            for sID in SeriesID:
    
                path_SeriesID = img_folder+StudyID+os.sep+eID+os.sep+sID
                
                abspath_SeriesID = os.path.abspath(path_SeriesID)
                #print abspath_SeriesID
                
                # Get total number of files
                listSeries_files = get_only_filesindirectory(abspath_SeriesID)
            
                # Use only the first slice one file and get DICOM DICTIONARY
                if(listSeries_files != []):
                    path_filenameID = img_folder+StudyID+os.sep+eID+os.sep+sID+os.sep+listSeries_files[0]
                    try:
                        dicomInfo = dicom.read_file(os.path.abspath(path_filenameID), force=True) 
                    except ValueError:
                        dicomInfo = []
                                        
                    # Get the main dataset (they are in fact two separate datasets in the DICOM standard). 
                    # That dicom dataset is now stored in the file_meta attribute of the dataset
                        
                    # Get structure of study (all files in directory consistent with studyID and patientID
                    studyTree = []
                    FileNames=listSeries_files;
                    
                    if("PatientID" in dicomInfo):
                        PatientID = dicomInfo.PatientID#
                    else:    PatientID=''
                    if("SeriesNumber" in dicomInfo):
                        SeriesNumber = dicomInfo.SeriesNumber#
                    else:    SeriesNumber=''
                    if("SeriesNumber" in dicomInfo):
                        SeriesNumber = dicomInfo.SeriesNumber
                    else:    SeriesNumber=''
                    if("SeriesDescription" in dicomInfo):
                        SeriesDescription = dicomInfo.SeriesDescription;
                    else:    SeriesDescription=''
                    if("SliceLocation" in dicomInfo):
                        MinSliceLocation = dicomInfo.SliceLocation; # Infos to identify number of slices/volumes
                    else:    MinSliceLocation=''
                    if('ImageOrientationPatient' in dicomInfo):
                        ImageOrientationPatient = dicomInfo.ImageOrientationPatient; # Infos to identify number of slices/volumes
                    else:    ImageOrientationPatient=''
                    
                    NumberOfVolumes = 1 # default
                    
                    # iterate number of slices and get full volume (#slices, each slice loc)
                    slices = []
                    num_images=0;
                    for filename in listSeries_files:
                        num_images = num_images+1
                            
                    # Print series info                        
                    print "%d    %s        %d        %s" % (s, SeriesNumber, num_images, SeriesDescription) 
                    # increment series number
                    s=s+1;    
                else:
                    print "%d    %s        %d        %s" % (s, "NONE", 0, "NULL") 
                    # increment series number
                    s=s+1;    
                
        # Go back to rootfolder
        #os.chdir(path_rootFolder)    
                
    return abspath_ExamID, eID, SeriesID, studyFolder, dicomInfo

def get_slices_at_all_locs(img_folder, abspath_SeriesID, len_listSeries_files, StudyID, eID, SeriesID, choseSerie, listSeries_files, abspath_ExamID):
    # enter folder of Series selection /examID/S_XXX 
    print "entering folder abspath_SeriesID"
    os.chdir(abspath_SeriesID)
    print abspath_SeriesID
                
    # Obtain all datasets in current series
    # iterate number of slices and get full volume (#slices, each slice loc)
    slices = []
    FileNms_slices =  []
                
    for n in range(len_listSeries_files):
        # Use all DICOM slices on series
        ''' EXTRACT DICOM SLICE LOCATION '''
        absp_fsID = 'Z:/Cristina/MassNonMass/'+img_folder+StudyID+'/'+eID+'/'+SeriesID[int(choseSerie)]+'/'+listSeries_files[n]
                            
        dInfo = dicom.read_file(absp_fsID)
        slices.append(dInfo.SliceLocation)
        FileNms_slices.append(listSeries_files[n])
        FileNms_slices.append(dInfo.SliceLocation)
        
    print '''\nPROCESS STACKS BY SLICE LOCATIONS '''
    FileNms_slices_stack = reshape(FileNms_slices, [len_listSeries_files,2])
    
    FileNms_slices_sorted = sorted(FileNms_slices_stack, key=itemgetter(1))
    #print FileNms_slices_sorted
    #time.sleep(5) #will sleep for 5 seconds
    
    FileNms_slices_sorted_stack = reshape(FileNms_slices_sorted, [len_listSeries_files,2])
    #print FileNms_slices_sorted_stack
    #time.sleep(5) #will sleep for 5 seconds
    
    current_slice = FileNms_slices_sorted_stack[0,1]
    print current_slice
    stack_byLocation = []
    name_byLocation = []
    scount = 0
    
    
    for sliceS in FileNms_slices_sorted_stack:
        # Get the num_series = 5 name_byLocations for a given Location
        if( current_slice == sliceS[1]):
            print "Name: %s" % sliceS[0]
            #print "Slice_loc: %s" % sliceS[1]
            stack_byLocation.append(sliceS[1])
            name_byLocation.append(sliceS[0])
            scount = scount+1
    
        # Finish getting all series for a given Location
        else:
            print scount
            '''-----\t NOW HAVE ALL SLICES IN A stack_byLocation '''
            # Get the new Location folder
            # To verify "Above lengths should be = num_series + 1" len(stack_byLocation) len(name_byLocation)'''                
            current_loc = stack_byLocation[0]
                                    
            # Makedir of current loc
            # if current loc folder doesn't exist create it        
            if not os.path.exists(str(current_loc)):
                os.makedirs(str(current_loc))
                            
            # Get inside location directory
            os.chdir(str(current_loc))
            #print os.getcwd()
            
            # Now link slices at location to folder
            filename = str(name_byLocation[0])
            filename = filename[0:-10]
            file_ending = '.MR.dcm'
            
            # Save the file list to read as series later
            filename_series = 'DIRCONTENTS.txt'
            file_series = open(filename_series, 'a')
                        
            for j in range(scount):
                # list to read as series later
                link_to = '../'+name_byLocation[j]
                name4link_to = filename+'00'+str(j)+file_ending
                print "linking file: %s to: %s" % (link_to, name4link_to)
                ln_subp = subprocess.Popen(['ln', link_to, name4link_to], stdout=subprocess.PIPE)
                ln_subp.wait()
                file_series.write(str(name4link_to)+'\n')
                
            file_series.close()
                
            # Get back inside the  Series directory
            os.chdir(abspath_SeriesID)
            
            print '''\n-----\tchdir out GET NEXT LOCATIONS SLICES'''
            current_slice = sliceS[1]
            scount = 0
            stack_byLocation = []
            name_byLocation = []
            print current_slice
            
            print "Name: %s" % sliceS[0]
            #print "Slice_loc: %s" % sliceS[1]
            stack_byLocation.append(sliceS[1])
            name_byLocation.append(sliceS[0])
            scount = scount+1
    
    # finalize the last location move
    if( current_slice ==  FileNms_slices_sorted_stack[-1,1]):
        print scount
        print '''-----\t NOW HAVE ALL SLICES IN A stack_byLocation '''
        # Get the new Location folder
        # To verify "Above lengths should be = num_series + 1" len(stack_byLocation) len(name_byLocation)'''                
        current_loc = stack_byLocation[0]
                                
        # Makedir of current loc
        # if current loc folder doesn't exist create it        
        if not os.path.exists(str(current_loc)):
            os.makedirs(str(current_loc))
        
        # Get inside location directory
        os.chdir(str(current_loc))
        #print os.getcwd()
        
        # Now link slices at location to folder
        filename = str(name_byLocation[0])
        filename = filename[0:-10]
        file_ending = '.MR.dcm'
        
        # Save the file list to read as series later
        filename_series = 'DIRCONTENTS.txt'
        file_series = open(filename_series, 'w')
        
        for j in range(scount):
            # list to read as series later
            link_to = '../'+name_byLocation[j]
            name4link_to = filename+'00'+str(j)+file_ending
            print "linking file: %s to: %s" % (link_to, name4link_to)
            ln_subp = subprocess.Popen(['ln', link_to, name4link_to], stdout=subprocess.PIPE)
            ln_subp.wait()
            file_series.write(str(name4link_to)+'\n')
            
        file_series.close()
            
        # Get back inside the  Series directory
        os.chdir(abspath_SeriesID)
    
    print "\n------------------------------------------------------------------"                        
    print '''FINISH get_slices_at_all_locs \n'''    
    os.chdir(abspath_ExamID)
    
    return scount


def get_slices_for_volumes(scount, img_folder, abspath_SeriesID, len_listSeries_files, StudyID, eID, SeriesID, choseSerie, listSeries_files, abspath_ExamID ):
    global num_locs_per_Vol
    
    print "entering folder abspath_SeriesID"
    os.chdir(abspath_SeriesID)
    print abspath_SeriesID
                
    # Obtain all datasets in current series
    # iterate number of slices and get full volume (#slices, each slice loc)
    slices = []
    FileNms_slices =  []
        
    for n in range(len_listSeries_files):
        # Use all DICOM slices on series
        ''' EXTRACT DICOM SLICE LOCATION '''
        absp_fsID = 'Z:/Cristina/MassNonMass/'+img_folder+StudyID+'/'+eID+'/'+SeriesID[int(choseSerie)]+'/'+listSeries_files[n]
                            
        dInfo = dicom.read_file(listSeries_files[n])
        slices.append(dInfo.SliceLocation)
        FileNms_slices.append(listSeries_files[n])
        FileNms_slices.append(dInfo.SliceLocation)
    
    print '''\nPROCESS STACKS BY SLICE LOCATIONS '''
    print "Total number of locations found: %d" % scount
    FileNms_slices_stack = reshape(FileNms_slices, [len_listSeries_files,2])
    #print FileNms_slices_stack
    FileNms_slices_sorted = sorted(FileNms_slices_stack, key=itemgetter(0))
    FileNms_slices_sorted_stack = reshape(FileNms_slices_sorted, [len_listSeries_files,2])
    print   FileNms_slices_sorted_stack

    stack_byLocation = []
    name_byLocation = []
    
    # Extracting the number of slices per bilateral 3D volumes based on num_series for 280/5 = 56
    num_locs_per_Vol = int(float(len_listSeries_files)/float(scount))
    scount = int(scount)
    
    print "------\tNumber of Dynamic Volumes (series time points: including pre-contrast): %d" % scount 
    print "------\tNumber of Locations per Bilateral Volume: %d " % num_locs_per_Vol
    stack_byBilatVol = []
        
    k=0
    # Get the folder names based on num_series
    for numlocs in range(scount):
        if ( numlocs == 0):    
            stack_byBilatVol.append('pre-Contrast')
        else:# Now link slices at location to folder
            stack_byBilatVol.append('post_Contrast-'+str(k))
        k=k+1
            
    # Initialized BilatVol
    print stack_byBilatVol
    slice_i = 0
    
    for Vol_i in range(scount):    
        print'''-----\t NOW HAVE ALL SLICES IN A bilateral vol '''
        # Get the new Location folder
        print "bit vol %d" % Vol_i
        current_vol = stack_byBilatVol[Vol_i]
                                
        # Makedir of current loc
        # if current loc folder doesn't exist create it        
        if not os.path.exists(str(current_vol)):
            os.makedirs(str(current_vol))
        
        # Get inside location directory
        os.chdir(str(current_vol))
        print os.getcwd()
        
        #FileNms_slices_sorted_stack[slice_i,0]
        # Now link slices at location to folder
        filename = str(FileNms_slices_sorted_stack[slice_i,0])
        filename = filename[0:-10]
        file_ending = '.MR.dcm'
        
        # Save the file list to read as series later
        filename_series = 'DIRCONTENTS.txt'
        file_series = open(filename_series, 'a')
        
        for j in range(num_locs_per_Vol):
            link_to = '../'+FileNms_slices_sorted_stack[slice_i,0]
            if ( j < 9):
                name4link_to = filename+'00'+str(j+1)+file_ending
            else:
                name4link_to = filename+'0'+str(j+1)+file_ending
            print "linking file: %s to: %s" % (link_to, name4link_to)
            ln_subp = subprocess.Popen(['ln', link_to, name4link_to], stdout=subprocess.PIPE)
            ln_subp.wait()
            file_series.write(str(name4link_to)+'\n')
            slice_i = slice_i+1
            
        file_series.close()
            
        # Get back inside the  Series directory
        os.chdir(abspath_SeriesID)
                        
    print "\n------------------------------------------------------------------"                        
    print '''FINISH get_slices_for_volumes \n'''    
    os.chdir(abspath_ExamID)
    
    return scount

def get_LorR_from_bilateral(DicomDirectory, DynSeries_id, T2Series_id):
    '''
    This function takes a root directory with a bilateral scan and returns two subdirectories 
    nested inside abspath_PhaseID, one for LEFT breast and other for Right breast only
    '''
    # procees Dynamic
    abspath_PhaseID = DicomDirectory+os.sep+DynSeries_id
    # read and sort by location
    [len_listSeries_files, sorted_FileNms_slices_stack] = ReadDicomfiles(abspath_PhaseID) 
    # simple separation between L and R
    Left_slices = sorted_FileNms_slices_stack.iloc[:int(len_listSeries_files/2)]
    Rigth_slices = sorted_FileNms_slices_stack.iloc[int(len_listSeries_files/2+1):]
    
    os.chdir(abspath_PhaseID)
    # preccess Left
    os.mkdir(abspath_PhaseID+os.sep+'Left')
    for i in range(len(Left_slices)):
        dcmtomove = Left_slices.iloc[i,1]
        proc = subprocess.Popen(['cp', dcmtomove, 'Left'+os.sep], stdout=subprocess.PIPE)
        proc.wait()
        
    # process Right        
    os.mkdir(abspath_PhaseID+os.sep+'Right')
    for i in range(len(Rigth_slices)):
        dcmtomove = Rigth_slices.iloc[i,1]
        proc = subprocess.Popen(['cp', dcmtomove, 'Right'+os.sep], stdout=subprocess.PIPE)
        proc.wait()
        
    # extract left most slice position for each subvolume
    # for left
    [Leftlen_listSeries_files, Leftsorted_FileNms_slices_stack] = ReadDicomfiles(abspath_PhaseID+os.sep+'Left') 
    print Leftsorted_FileNms_slices_stack.values
    Leftmostleft_slice = Leftsorted_FileNms_slices_stack.iloc[0]['slices']  
    dicomInfo_Left = dicom.read_file(abspath_PhaseID+os.sep+'Left'+os.sep+str(Leftmostleft_slice))     
    # Image Position (0020,0032): specifies the x, y, and z coordinates of the upper left hand corner of the image. 
    # his tag specifies the coordinates of the the first voxel transmitted.
    Left_pos_pat = list(dicomInfo_Left[0x0020,0x0032].value)
    # Image Orientation (0020,0037): specifies the direction cosines 
    Left_ori_pat = list(dicomInfo_Left[0x0020,0x0037].value)
    print "Left DCE image_pos_pat: %s" % Left_pos_pat
    
    # for Right
    [Rightlen_listSeries_files, Rightsorted_FileNms_slices_stack] = ReadDicomfiles(abspath_PhaseID+os.sep+'Right') 
    print Rightsorted_FileNms_slices_stack.values
    Rightmostleft_slice = Rightsorted_FileNms_slices_stack.iloc[0]['slices']  
    dicomInfo_Right = dicom.read_file(abspath_PhaseID+os.sep+'Right'+os.sep+str(Rightmostleft_slice))     
    # Image Position (0020,0032): specifies the x, y, and z coordinates of the upper left hand corner of the image. 
    # his tag specifies the coordinates of the the first voxel transmitted.
    Right_pos_pat = list(dicomInfo_Right[0x0020,0x0032].value)
    # Image Orientation (0020,0037): specifies the direction cosines 
    Right_ori_pat = list(dicomInfo_Right[0x0020,0x0037].value)
    print "Right DCE image_pos_pat: %s" % Right_pos_pat
    
    return Left_pos_pat, Left_ori_pat, Right_pos_pat, Right_ori_pat
    
    
def get_T2_pos_ori(DicomDirectory, T2Series_id):
    # for T2
    path_T2Series = DicomDirectory+os.sep+T2Series_id
    [T2len_listSeries_files, T2sorted_FileNms_slices_stack] = ReadDicomfiles(path_T2Series) 
    print T2sorted_FileNms_slices_stack.values
    
    T2mostleft_slice = T2sorted_FileNms_slices_stack.iloc[0]['slices']  
    dicomInfo_T2 = dicom.read_file(path_T2Series+os.sep+str(T2mostleft_slice)) 
    # Image Position (0020,0032): specifies the x, y, and z coordinates of the upper left hand corner of the image. 
    # his tag specifies the coordinates of the the first voxel transmitted.
    T2_pos_pat = list(dicomInfo_T2[0x0020,0x0032].value)
    # Image Orientation (0020,0037): specifies the direction cosines 
    T2_ori_pat = list(dicomInfo_T2[0x0020,0x0037].value)
    print "T2 image_pos_pat: %s" % T2_pos_pat    
    
    T2fatsat = str(dicomInfo_T2[0x0018,0x0022].value)
    print "T2fatsat scan options: %s" % T2fatsat    
            
    return T2_pos_pat, T2_ori_pat, T2fatsat
    
## END

