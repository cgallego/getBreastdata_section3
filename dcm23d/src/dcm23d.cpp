/*=========================================================================*/
/*Aim: reading 2D DICOM Series and Writing a Volume
*functions:
*	1. list patientID access#, series#:seriesDescrition
*	2. write all the series to 3D volume
*	3. write selected series, whose series description contains given keywords(case insensitive) to 3d volume
*	4. write converted files full path to convertedList.txt
*   5. support formats: mha(default),nii,nrrd,mhd,hdr
*author:YingLi Lu, yinglilu@gmail.com
*create date: 2015/06/23
*modified: 2015/07/08
*=========================================================================*/

#include "itkImage.h"
#include "itkGDCMImageIO.h"
#include "itkGDCMSeriesFileNames.h"
#include "itkImageSeriesReader.h"
#include "itkImageFileWriter.h"
#include "itkMetaDataObject.h"
#include "itksys/SystemTools.hxx"
#include <regex>
#include <map>
#include <ctime>
#include <iostream>
#include <fstream>

//path separator cross platform
#if defined(WIN32) || defined(_WIN32) 
#define PATH_SEP "\\" 
#else 
#define PATH_SEP "/" 
#endif 

using namespace std;

void PrintHelp(char *argv[])
{
	cerr << "Usage: " << argv[0] << " -i DicomDirectory [-o OutputDirectory] [-k SeriesDescriptionKeyword...] [-l ConvertedList.txt] [-f format]"<<endl;
	cerr << "        -i DicomDirectory, path contains DICOM files. This tool can search DicomDirectory recursively."<<endl;
	cerr << "        -o OutputDirectory, path to write the converted 3d volume file. The output filename is PatientID_StudyID_StudyDate_Access#_Series#_SeriesDescription.mha"<<endl;
	cerr << "        -k SeriesDescriptionKeyword..., convert only series whose series description contains the specified keyword."<<endl;
	cerr << "        	Multiple keywords can be used, for instance, \"-k keyword1 keyword2\" will write series whose series description contains keyword1 OR(NOT AND!) keyword2."<<endl;
	cerr << "			SeriesDescriptionKeywords are case insensitive"<<endl;
	cerr << "        -l ConvertedList.txt, record the converted filenames with ConvertedList.txt. "<<endl;
	cerr << "        -f format, specify the 3d volume format. Support formats: mha, nii, nrrd, mhd, hdr. mha is the default ouput format."<<endl;
	cerr << endl;
	cerr << "example 1: "<<argv[0] << " -i DicomDirectory"<<endl;  
	cerr <<	"        -list all the series under DicomDirectory WITHOUT converting 3D volume file"<<endl;
	cerr << "example 2: "<<argv[0] << " -i DicomDirectory -o OutPutDirectory"<<endl;
	cerr << "        -write all the series under DicomDirectory to 3D volume file in mha format."<<endl;
	cerr << "example 3: "<<argv[0] << " -i DicomDirectory -o OutPutDirectory -k sag \"wo fs\""<<endl;
	cerr << "        -write the series whose series description contains keyword \"sag\" OR \"wo fs\" to 3D volume file in mha format."<<endl;
	cerr << "example 4: "<<argv[0] << " -i DicomDirectory -o OutPutDirectory -f nii" <<endl;
	cerr << "        -write all the series to 3D volume file in nifti format."<<endl;
	cerr << "example 5: "<<argv[0] << " -i DicomDirectory -o OutPutDirectory -l converted.txt" <<endl;
	cerr << "        -write all the series to 3D volume file in mha format, record the converted filenames with converted.txt."<<endl;
	cerr << endl;
}

//compare patientID(string) access#(string) series#(string, convert to int, then compare)
bool comparator( const vector<string> & lhs, const vector<string> rhs )
{
	if ( lhs[0] < rhs[0] ) //patientID, string, lexicographical comparison
		return true;
	else if ( lhs[0] > rhs[0])
		return false;

	if ( lhs[1] < rhs[1] ) //access#, string , lexicographical comparison
		return true;
	else if ( lhs[1] > rhs[1])
		return false;

	if ( atoi(lhs[2].c_str()) < atoi(rhs[2].c_str()) ) //series#, string, convert to int, then compare. This is usual way most pacs system list/order the series.
		return true;
	else if ( atoi(lhs[2].c_str()) > atoi(rhs[2].c_str()) )
		return false;

	return false;
}

int main(int argc, char *argv[])
{
	//print help
	if( argc == 1 ) //argv[0]
	{
		PrintHelp(argv);
		return 1;
	}

	if( argc == 2 ) //argv[0] -h
	{
		if( argv[1] == string("-h") || argv[1] == string("-H") || argv[1] == string("-help") )
		{
			PrintHelp(argv);
			return 1;
		}
		else
		{
			cerr<< "For help: "<< argv[0] << " -h" <<endl;
			return 0;
		}
	}

	//tags used to name the converted 3d filename: PatientID_StudyID_StudyDate_Access#_Series#_SeriesDescription.mha
	vector<string> tags;
	tags.push_back("0010|0020");//patientID
	tags.push_back("0020|0010");//studyID
	tags.push_back("0008|0020");//studyDate
	tags.push_back("0008|0050");//access#
	tags.push_back("0020|0011");//series#
	tags.push_back("0008|103e");//series description

	//illegal filename chracters:  \ / : * ? " < > |   , which will be removed from tag value.
	string illegalChars = "\\/:?\"<>|"; 

	//accept output format, specified by -f 
	vector<string> acceptFormat;
	acceptFormat.push_back("mha"); 
	acceptFormat.push_back("nii");
	acceptFormat.push_back("mhd");
	acceptFormat.push_back("nrrd");
	acceptFormat.push_back("hdr");

	//timer start
	const clock_t begin_time = clock();

	//parse arguments
	string dicomDirectory; // -i
	string outputDirectory;// -o
	bool write3D = false; //will be set to true, if outputDirectory is good
	bool writeAllSeries = true; // default, if without -k
	string outputFormat = "mha"; //default, if without -f
	vector<string> seriesKeywords; //record series keywords specified by -f
	string convertedList; //-l
	bool writeConvertedList = false; 

	for (int ac = 1; ac < argc; ac++)
	{
		//-i
		if( argv[ac] == string("-i") || argv[ac] == string("-I"))
		{
			if ( ++ac >= argc ) 
			{
				cerr<< "missing argument for -i" <<endl;
				return 1;
			}
			dicomDirectory = argv[ac]; 
		}

		//-o
		if( argv[ac] == string("-o") || argv[ac] == string("-O") )
		{
			if ( ++ac >= argc ) 
			{
				cerr<< "missing argument for -o" <<endl;
				return 1;
			}
			outputDirectory = argv[ac]; 
		}

		//-f
		if( argv[ac] == string("-f") || argv[ac] == string("-F") )
		{
			if ( ++ac >= argc ) 
			{
				cerr<< "missing argument for -f" <<endl;
				return 1;
			}
			outputFormat = argv[ac]; 
			transform(outputFormat.begin(), outputFormat.end(),outputFormat.begin(), tolower); //to lower case
		}

		//-k
		if ( argv[ac] == string("-k") || argv[ac] == string("-K") ) 
		{
			if ( ++ac >= argc ) 
			{
				cerr<< "missing argument for -k" <<endl;
				return 1;
			}

			//add elements after -f to vector serieskeywords
			string seriesKeyword;
			for( int i=ac; i<argc; i++ )
			{
				seriesKeyword=argv[i];
				//push_back until next option
				if( seriesKeyword == string("-l") || seriesKeyword == string("-i") || seriesKeyword == string("-o") || seriesKeyword == string("-f") )
				{
					break;
				}
				transform(seriesKeyword.begin(), seriesKeyword.end(), seriesKeyword.begin(), tolower);//to lower case
				seriesKeyword = std::regex_replace(seriesKeyword, regex("^ +| +$|( ) +"), "$1");//remove leading,trailing and extra white space
				seriesKeywords.push_back(seriesKeyword);
			}

			if( seriesKeywords.size() > 0 )
			{
				writeAllSeries = false;
			}
		}

		//-l
		if( argv[ac] == string("-l") || argv[ac] == string("-L") )
		{
			if ( ++ac >= argc ) 
			{
				cerr<< "missing argument for -l" <<endl;
				return 1;
			}
			convertedList = argv[ac]; 
		}
	}	

	// Check if dicomDirectory is a directory and exist
	bool exist = itksys::SystemTools::FileExists(dicomDirectory.c_str());
	bool isDir = itksys::SystemTools::FileIsDirectory(dicomDirectory.c_str());
	if ( !(exist && isDir) )
	{
		cerr << "ERROR: " << dicomDirectory << " does not exist or is no directory." << endl;
		return 1;
	}

	//check if outputDirectory is good
	if ( !(outputDirectory.empty()) )
	{
		//check if outputDirectory is a file
		bool isFile = itksys::SystemTools::FileExists(outputDirectory.c_str(),true);
		if ( isFile )
		{
			cerr << "ERROR: " << outputDirectory << " should be a directory!" << endl;
			return 1;
		}
		// Check if outputDirectory exist 
		exist = itksys::SystemTools::FileExists( outputDirectory.c_str() );
		if( !exist ) //create directory is not exist
		{  
			try
			{
				itksys::SystemTools::MakeDirectory( outputDirectory.c_str() );
				cout << outputDirectory << " created." << endl;
			}
			catch (itk::ExceptionObject &ex)
			{
				cout << ex << std::endl;
				return 1;
			}
		}

		//set write3D to ture when outputDirectory is good.
		write3D = true;
	}

	//check if ouput format is accept
	if ( !(find(acceptFormat.begin(), acceptFormat.end(), outputFormat) != acceptFormat.end()) )
	{
		cerr<< "accepted output formats:mha, nii, mhd, nrrd, hdr" <<endl;
		return 1;
	}

	//open convertedList file specified by -l
	ofstream convertedListFile;
	if ( !convertedList.empty() )
	{
		convertedListFile.exceptions ( ofstream::failbit | ofstream::badbit );
		try 
		{
			convertedListFile.open( outputDirectory + string(PATH_SEP) + convertedList, ios::out | ios::app);
			writeConvertedList = true;
		}
		catch (std::ofstream::failure e) 
		{
			cerr << "Exception opening file."<<endl;
			return 1;
		}
	}

	cout<<"Analyzing "<<dicomDirectory<<endl;

	//image type to read 2d dicom image, used to get the dicom tags of patientID,studyId,etc...
	typedef itk::Image< signed short, 2 >  ImageType2D;
	typedef itk::ImageFileReader< ImageType2D >     ReaderType2D;
	ReaderType2D::Pointer reader2D = ReaderType2D::New();

	//image type to write 3d mha image
	typedef signed short    PixelType;
	const unsigned int      Dimension = 3;
	typedef itk::Image< PixelType, Dimension >         ImageType;
	typedef itk::ImageSeriesReader< ImageType >        ReaderType;
	typedef itk::GDCMSeriesFileNames NamesGeneratorType;
	NamesGeneratorType::Pointer nameGenerator = NamesGeneratorType::New();

	ReaderType::Pointer reader = ReaderType::New();
	typedef itk::GDCMImageIO       ImageIOType;
	ImageIOType::Pointer dicomIO = ImageIOType::New();

	nameGenerator->SetRecursive(true);
	nameGenerator->SetUseSeriesDetails(true);
	nameGenerator->AddSeriesRestriction("0008|0021");
	nameGenerator->SetDirectory(dicomDirectory);

	//get all the series (by series UID) under the input folder
	typedef std::vector< std::string >    SeriesIdContainer;
	const SeriesIdContainer & seriesUID = nameGenerator->GetSeriesUIDs();
	SeriesIdContainer::const_iterator seriesItr = seriesUID.begin();
	SeriesIdContainer::const_iterator seriesEnd = seriesUID.end();

	//get the correspondence between series UID and PatientID,studyId,studyDate,accessNumber,seriesNumber,seriesDescription
	//key is series UID, vector<string> is PatientID,studyID,studyDate,accessNumber,seriesNumber,seriesDescription
	map< string, vector<string> > seriesUidToOtherStuff; 
	seriesItr = seriesUID.begin();
	while (seriesItr != seriesUID.end())
	{
		string seriesIdentifier = seriesItr->c_str();
		//get file names belong to specific series
		vector< string > fileNames = nameGenerator->GetFileNames(seriesIdentifier);
		vector< string > otherStuff;

		//read tags(PatientID StudyID StudyDate Access# Series# SeriesDescription) value from the first file of each series
		if (!fileNames.empty())
		{
			reader2D->SetFileName(fileNames[0]);
			reader2D->SetImageIO(dicomIO);
			try
			{
				reader2D->UpdateLargestPossibleRegion(); //do not use reader->Update(),since image size is different across series.
			}
			catch (itk::ExceptionObject &ex)
			{
				cout << ex << endl; 
				return 1;
			}

			typedef itk::MetaDataDictionary   DictionaryType;
			const  DictionaryType & dictionary = dicomIO->GetMetaDataDictionary();
			typedef itk::MetaDataObject< std::string > MetaDataStringType;
			DictionaryType::ConstIterator itr = dictionary.Begin();
			DictionaryType::ConstIterator end = dictionary.End();

			for (int i = 0; i < tags.size(); i++)
			{
				string entryId = tags[i];
				DictionaryType::ConstIterator tagItr = dictionary.Find( entryId );
				if( tagItr != end )
				{
					MetaDataStringType::ConstPointer entryvalue =dynamic_cast<const MetaDataStringType *>(tagItr->second.GetPointer() );
					if( entryvalue )//entry found
					{
						string tagvalue = entryvalue->GetMetaDataObjectValue();
						tagvalue = regex_replace(tagvalue, regex("^ +| +$|( ) +"), "$1");//remove leading,trailing and extra white space
						otherStuff.push_back(tagvalue);
					}
					else
					{
						otherStuff.push_back("EntryNotFound");
					}
				}
			}//end for
		}//end if (!fileNames.empty())
		seriesUidToOtherStuff[seriesIdentifier] = otherStuff;
		seriesItr++;
	}//end while


	//list series number and description for each patient and access# 
	/*patientID, access#, series#, series descrition hierarchy:
	patientid
	access#
	series#:series description		
	series#:series description
	...
	access#
	series#:series description		
	series#:series description
	...
	patientid
	...
	...
	*/

	//create 2d vector for sorting
	vector<string> vs;
	vector< vector<string> > vvs;
	for( map< string,vector<string> >::iterator ii=seriesUidToOtherStuff.begin(); ii!=seriesUidToOtherStuff.end(); ++ii)
	{
		vector<string> vsNew;
		vs = (*ii).second;
		vsNew.push_back(vs[0]);//patientID
		vsNew.push_back(vs[3]);//access#
		vsNew.push_back(vs[4]);//series#
		vsNew.push_back(vs[5]);//series description
		vvs.push_back(vsNew);
	}

	//sort: patientID and access# by string lexicographical order, series# by integer
	sort(vvs.begin(),vvs.end(),comparator);

	//print series number and description for each patient and access# 
	string patientID;
	string accessNumber;
	vector<string> patientIDVector;
	vector<string> accessNumberVector;
	if ( vvs.size()>0 )
	{
		cout <<dicomDirectory<<" contains the following DICOM Series:"<<endl;
		for( int i = 0; i < vvs.size(); i++)
		{
			patientID = vvs[i][0];
			accessNumber = vvs[i][1];

			if (find(patientIDVector.begin(), patientIDVector.end(), patientID) == patientIDVector.end() ) // a new patientID
			{
				patientIDVector.push_back(patientID);
				cout<<"patient ID: "<<patientID<<endl;
			}
			if (find(accessNumberVector.begin(), accessNumberVector.end(), accessNumber) == accessNumberVector.end() ) // a new accessNumber
			{
				accessNumberVector.push_back(accessNumber);
				cout<<"   "<<"access#: "<<accessNumber<<endl;
			}
			cout<<"      "<<vvs[i][2]<<": "<<vvs[i][3]<<endl; //list series#:series description
		}
	}
	else
	{
		cout << "The directory: "<<dicomDirectory<<" contains no DICOM Series! InputDirectory correct?"<<endl;
		return 0;
	}

	//write 3D volume
	if (write3D)
	{
		typedef std::vector< std::string >   FileNamesContainer;
		FileNamesContainer fileNames; 

		typedef itk::ImageFileWriter< ImageType > WriterType;
		WriterType::Pointer writer = WriterType::New();
		string outFileName;

		seriesItr = seriesUID.begin();
		while (seriesItr != seriesUID.end())
		{
			string seriesIdentifier;
			if (writeAllSeries) //without -k option
			{
				seriesIdentifier = seriesItr->c_str();
			}
			else //with -k option
			{
				//get sereisDescription according to seriesUID
				string seriesDescription = seriesUidToOtherStuff[*seriesItr][5];
				transform(seriesDescription.begin(), seriesDescription.end(), seriesDescription.begin(), tolower);//to lower case

				//check if series Description contains the specified keyword (by -k)
				for( int i = 0; i < seriesKeywords.size(); i++)
				{
					if (seriesDescription.find(seriesKeywords[i]) != string::npos)
					{
						seriesIdentifier = seriesItr->c_str();
					}
				} 
			}//end if (writeAllSeries)

			if ( !seriesIdentifier.empty() )
			{
				//get file names belong to specific series
				fileNames = nameGenerator->GetFileNames(seriesIdentifier);
				reader->SetImageIO(dicomIO);
				reader->SetFileNames(fileNames);

				//get output file name:PatientID_StudyID_StudyDate_Access#_Series#_SeriesDescription
				vector<string> vs = seriesUidToOtherStuff[seriesIdentifier];
				string temp = vs[0]+"_"+vs[1]+"_"+vs[2]+"_"+vs[3]+"_"+vs[4]+"_"+vs[5];
				string tempNew;
				//remove illegal characters
				for (string::iterator it = temp.begin(); it < temp.end(); ++it)
				{
					bool found = illegalChars.find(*it) != string::npos;
					if(!found){
						tempNew=tempNew+(*it);
					}
				}
				//repace space with . . Many series descriptions come with spaces. But, filenames with spaces is not good.
				replace( tempNew.begin(), tempNew.end(), ' ', '.'); 
				//get full path file name
				outFileName = outputDirectory + string(PATH_SEP) + tempNew + "."+outputFormat;

				//write
				writer->SetFileName(outFileName);
				writer->UseCompressionOn();
				writer->SetInput(reader->GetOutput());
				cout << "Writing: " << outFileName << endl;
				try
				{
					writer->Update();
				}
				catch (itk::ExceptionObject &ex)
				{
					cout << ex << std::endl;
					continue;
				}

				//writing converted files full path to convertedList
				if ( writeConvertedList )
				{
					try
					{
						convertedListFile << outFileName <<endl;
					}
					catch (std::ofstream::failure e) 
					{
						cerr << "Exception writing file"<<endl;
					}
				}
			}
			seriesItr++;
		}//end while
	}//end if write3D

	//close convertedList file
	if (convertedListFile.is_open())
	{
		try
		{
			convertedListFile.close();
		}
		catch (std::ofstream::failure e) 
		{
			cerr << "Exception closing file"<<endl;
		}
	}

	//print elasped time
	cout << "Elapsed time: "<<float( clock () - begin_time )/CLOCKS_PER_SEC<<" Seconds";

	return 0;
}