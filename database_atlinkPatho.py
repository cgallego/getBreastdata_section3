# -*- coding: utf-8 -*-
"""
Created on Fri Mar 14 12:36:36 2014

@author: Cristina Gallego
"""
import sys, os
import string
import datetime
import numpy as np

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

from base import Base



#  created a Procedure mapping                              
class Procedure(Base):
    """Base for Procedure class using Declarative. """
    __tablename__ = 'tbl_pt_procedure'
    __table_args__ = {'autoload':True}
    pt_procedure_id = Column(Integer, primary_key=True)
    
    # class introduces the ForeignKey construct, which is a directive applied to Column that indicates that values in this column should be constrained to be values present in the named remote column.
    pt_id = Column(Integer, ForeignKey('tbl_pt_mri_cad_record.pt_id'))
    
    def __repr__(self):
        return "Procedure: proc_dt_datetime=%s, proc_side_int=%s, proc_source_int=%s, proc_guid_int=%s, proc_tp_int=%s, original_report_txt=%s" % (self.proc_dt_datetime, self.proc_side_int, self.proc_source_int, self.proc_guid_int, self.proc_tp_int, self.original_report_txt)
  
 
#  created a Pathology mapping                              
class Pathology(Base):
    """Base for Pathology class using Declarative. """
    __tablename__ = 'tbl_pt_pathology'
    __table_args__ = {'autoload':True}
    pt_path_id = Column(Integer, primary_key=True)
    
    # class introduces the ForeignKey construct, which is a directive applied to Column that indicates that values in this column should be constrained to be values present in the named remote column.
    pt_procedure_id = Column(Integer, ForeignKey('tbl_pt_procedure.pt_procedure_id'))
    #pathology_record = relationship("Pathology",  primaryjoin="Pathology.pt_procedure_id==Procedure.pt_procedure_id")
    
    def __repr__(self):
        return "Pathology: cytology_int=%s, biopsy_benign_yn=%s, biopsy_high_risk_yn=%s, insitu_carcinoma=%s, invasive_carcinoma=%s, " % (self.cytology_int, self.histop_core_biopsy_benign_yn, self.histop_core_biopsy_high_risk_yn, self.histop_tp_isc_yn, self.histop_tp_ic_yn)

  
#  created exam_finding_lesion_link  
class Path_Exam_Finding_link(Base):
    """Base for Finding_Lesion_link class using Declarative. """
    __tablename__ = 'tbl_pt_path_exam_find_link'
    __table_args__ = {'autoload':True}
    pt_path_exam_find_link_id = Column(Integer, primary_key=True)
    
    # class introduces the ForeignKey construct, which is a directive applied to Column that indicates that values in this column should be constrained to be values present in the named remote column.
    pt_path_id = Column(Integer, ForeignKey('tbl_pt_pathology.pt_path_id'))
    pt_exam_finding_id = Column(Integer, ForeignKey('tbl_pt_exam_finding.pt_exam_finding_id'))
    
    def __repr__(self):
        return
        
