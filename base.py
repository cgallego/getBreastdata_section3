# -*- coding: utf-8 -*-
"""
Created on Fri Apr 11 09:46:09 2014

@ author (C) Cristina Gallego, University of Toronto
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# configure Session class with desired options
Session = sessionmaker()
engine = create_engine("postgresql+psycopg2://biomatrix_ruser_mri_cad:bi0matrix4mricadSTUDY@142.76.29.187/biomatrixdb_raccess_mri_cad")

localengine = create_engine('sqlite:///C:\\Users\\windows\\Documents\\repoCode-local\\Section3\\getBreastdata\\miningBreastMRIdata.db', echo=False) # when querying local data

# later, we create the engine
Base = declarative_base(engine)
