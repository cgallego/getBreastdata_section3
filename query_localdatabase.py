# -*- coding: utf-8 -*-
"""
Created on Tue Apr 12 13:12:41 2016

@ author (C) Cristina Gallego, University of Toronto
"""

import sys, os
import string
import datetime
from numpy import *
import pandas as pd

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

from base import Base, localengine
import mylocaldatabase
from sqlalchemy.sql import select


#!/usr/bin/env python
class Querylocal(object):
    """
    USAGE:
    =============
    database = Querylocal()
    """
    def __call__(self):       
        """ Turn Class into a callable object """
        Querylocal()
        
        
    def __init__(self): 
        """ initialize QueryDatabase """
        self.lesion = []
    
    def queryby_lesionid(self, lesion_id):
        """
        run : Query by Lesion_id on local database

        Inputs
        ======
        lesion_id : (int)    My CADStudy lesion_id

        Output
        lesion record
        ======
        """
        # Create the database: the Session.
        self.Session = sessionmaker()
        self.Session.configure(bind=localengine)  # once engine is available
        session = self.Session() #instantiate a Session

        # for cad_case in session.query(Cad_record).order_by(Cad_record.pt_id):
        #     print cad_case.pt_id, cad_case.cad_pt_no_txt, cad_case.latest_mutation_status_int
        for lesion in session.query(mylocaldatabase.Lesion_record,mylocaldatabase.Nonmass_record).\
            filter(mylocaldatabase.Nonmass_record.lesion_id==mylocaldatabase.Lesion_record.lesion_id).\
            filter(mylocaldatabase.Lesion_record.lesion_id == str(lesion_id)):
            # print results
            if not lesion:
                print "lesion is empty"

        return lesion
        
    def queryby_lesionidwpatch(self, lesion_id):
        """
        run : Query by Lesion_id on local database

        Inputs
        ======
        lesion_id : (int)    My CADStudy lesion_id

        Output
        lesion record
        ======
        """
        # Create the database: the Session.
        self.Session = sessionmaker()
        self.Session.configure(bind=localengine)  # once engine is available
        session = self.Session() #instantiate a Session

        # for cad_case in session.query(Cad_record).order_by(Cad_record.pt_id):
        #     print cad_case.pt_id, cad_case.cad_pt_no_txt, cad_case.latest_mutation_status_int
        try:
            for lesion in session.query(mylocaldatabase.Lesion_record,mylocaldatabase.Nonmass_record, mylocaldatabase.lesion_patch).\
                filter(mylocaldatabase.Nonmass_record.lesion_id==mylocaldatabase.Lesion_record.lesion_id).\
                filter(mylocaldatabase.lesion_patch.lesion_id==mylocaldatabase.Lesion_record.lesion_id).\
                filter(mylocaldatabase.Lesion_record.lesion_id == str(lesion_id)):
                    #print lesion
                    return lesion
                    
        except exc.SQLAlchemyError, e:
            print e
            return False

        
        
    def deleteby_lesionid(self, lesion_id):
        """
        run : Delete whole records by Lesion_id on local database

        Inputs
        ======
        lesion_id : (int)    My CADStudy lesion_id

        Output
        lesion record
        ======
        """
        # Create the database: the Session.
        self.Session = sessionmaker()
        self.Session.configure(bind=localengine)  # once engine is available
        session = self.Session() #instantiate a Session

        ## delete with query (supported one table at a time)
        session.query(mylocaldatabase.Lesion_record).\
        filter(mylocaldatabase.Lesion_record.lesion_id == str(lesion_id)).\
             delete(synchronize_session='evaluate')
             
        session.query(mylocaldatabase.Radiology_record).\
        filter(mylocaldatabase.Radiology_record.lesion_id == lesion_id).\
             delete(synchronize_session=False)             
             
        session.query(mylocaldatabase.Segment_record).\
        filter(mylocaldatabase.Segment_record.lesion_id == lesion_id).\
             delete(synchronize_session=False) 

        session.query(mylocaldatabase.Stage1_record).\
        filter(mylocaldatabase.Stage1_record.lesion_id == lesion_id).\
             delete(synchronize_session=False) 

        session.query(mylocaldatabase.Mass_record).\
        filter(mylocaldatabase.Mass_record.lesion_id == lesion_id).\
             delete(synchronize_session=False) 

        session.query(mylocaldatabase.Nonmass_record).\
        filter(mylocaldatabase.Nonmass_record.lesion_id == lesion_id).\
             delete(synchronize_session=False) 

        session.query(mylocaldatabase.Foci_record).\
        filter(mylocaldatabase.Foci_record.lesion_id == lesion_id).\
             delete(synchronize_session=False) 
             
        session.query(mylocaldatabase.Dynamic_features).\
        filter(mylocaldatabase.Dynamic_features.lesion_id == lesion_id).\
             delete(synchronize_session=False)      
             
        session.query(mylocaldatabase.Morpho_features).\
        filter(mylocaldatabase.Morpho_features.lesion_id == lesion_id).\
             delete(synchronize_session=False)

        session.query(mylocaldatabase.Texture_features).\
        filter(mylocaldatabase.Texture_features.lesion_id == lesion_id).\
             delete(synchronize_session=False)             
             
        session.query(mylocaldatabase.T2_features).\
        filter(mylocaldatabase.T2_features.lesion_id == lesion_id).\
             delete(synchronize_session=False)             
             
        print "Deleting lesion records...."
        
        # Finally send records to database
        try:
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

        return
        
    def query_allpatches(self):
        
        sel_patches = select([mylocaldatabase.lesion_patch.lesion_id, mylocaldatabase.lesion_patch.patch_size])

        # get all the results in a list of tuples
        self.conn = localengine.connect()
        res = self.conn.execute(sel_patches)
        fetchall = res.fetchall()
        
        # Build a DataFrame with the results
        dfallpatches = pd.DataFrame(fetchall)
        
        return dfallpatches


