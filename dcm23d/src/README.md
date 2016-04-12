aim: Reading 2D DICOM Series and Writing a Volume

functions:
	1. list patientID access#, series#:seriesDescrition
	2. write all the series to 3D volume
	3. write selected series, whose series description contains given keywords(case insensitive) to 3d volume
	4. write converted files full path to convertedList.txt
    5. support formats: mha(default),nii,nrrd,mhd,hdr

Usage: dcm23d.exe -i DicomDirectory [-o OutputDirectory] [-k SeriesDescriptionKeyword...] [-l ConvertedList.txt] [-f format]
        -i DicomDirectory, path contains DICOM files. This tool can search DicomDirectory recursively.
        -o OutputDirectory, path to write the converted 3d volume file. The output filename is PatientID_StudyID_StudyDate_Access#_Series#_SeriesDescription.mha
        -k SeriesDescriptionKeyword..., convert only series whose series description contains the specified keyword.
                Multiple keywords can be used, for instance, "-k keyword1 keyword2" will write series whose series description contains keyword1 OR(NOT AND!) keyword2.
                        SeriesDescriptionKeywords are case insensitive
        -l ConvertedList.txt, record the converted filenames with ConvertedList.txt.
        -f format, specify the 3d volume format. Support formats: mha, nii, nrrd, mhd, hdr. mha is the default ouput format.

example 1: dcm23d.exe -i DicomDirectory
        -list all the series under DicomDirectory WITHOUT converting 3D volume file
example 2: dcm23d.exe -i DicomDirectory -o OutPutDirectory
        -write all the series under DicomDirectory to 3D volume file in mha format.
example 3: dcm23d.exe -i DicomDirectory -o OutPutDirectory -k sag "wo fs"
        -write the series whose series description contains keyword "sag" OR "wo fs" to 3D volume file in mha format.
example 4: dcm23d.exe -i DicomDirectory -o OutPutDirectory -f nii
        -write all the series to 3D volume file in nifti format.
example 5: dcm23d.exe -i DicomDirectory -o OutPutDirectory -l converted.txt
        -write all the series to 3D volume file in mha format, record the converted filenames with converted.txt.

note:  need ITK 4.5 dlls run!
suggestion: put all the dlls in one folder and add it to the path.

How to build on Windows:
	0. Building dcm23d from source requires to first build the ITK. Currently we rely on ITK4.5, available at http://www.itk.org/ITK/resources/software.html
    1. Create a 'bin' directory at the same level as the 'src' directory
    2. Run cmake, set the source directory to dcm23d/src and the binary directory to dcm23d/bin, press configure, press generate.
    3. Open bin/dcm23.sln, and start the build. Note: The visual studio solution configuration(debug/release) should be correspond with the ITK_DIR specified in the CMakeLists.txt.
	


