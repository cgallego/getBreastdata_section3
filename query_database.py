# -*- coding: utf-8 -*-
"""
Created on Wed Apr 09 15:53:42 2014

@ author (C) Cristina Gallego, University of Toronto
"""

import sys, os
import string
import datetime
from numpy import *

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

import database_atExam
import database_atlinkPatho
from base import Base, engine
import pandas as pd

#!/usr/bin/env python
class Query(object):
    """
    USAGE:
    =============
    database = Query()
    """
    def __call__(self):       
        """ Turn Class into a callable object """
        Query()
        
        
    def __init__(self): 
        """ initialize QueryDatabase """
        self.QueryPatient = []
        self.is_mass = []
        self.is_nonmass = []
    
    def queryRadiolinfo(self, fStudyID, redateID):
        """
        run : Query by StudyID/AccesionN pair study to local folder NO GRAPICAL INTERFACE. default print to output

        Inputs
        ======
        fStudyID : (int)    CAD fStudyID
        redateID : (int)  CAD StudyID Data of exam (format yyyy-mm-dd)

        Output
        ======
        """
        # Create the ORMâ€™s â€œhandleâ€ to the database_atExam: the Session. 
        self.Session = sessionmaker()
        self.Session.configure(bind=engine)  # once engine is available
        session = self.Session() #instantiate a Session
        
        datainfo = [];

        for cad, exam, in session.query(database_atExam.Cad_record, database_atExam.Exam_record).\
                    filter(database_atExam.Cad_record.pt_id==database_atExam.Exam_record.pt_id).\
                    filter(database_atExam.Cad_record.cad_pt_no_txt == str(fStudyID)).\
                    filter(database_atExam.Exam_record.exam_dt_datetime == redateID).all():
      
            # print results
            if not cad:
                print "cad is empty"
            if not exam:
                print "exam is empty"

            datainfo.append( [([cad.cad_pt_no_txt, cad.latest_mutation_status_int,
                                    exam.exam_dt_datetime, exam.mri_cad_status_txt, exam.comment_txt,
                                    exam.original_report_txt,
                                    exam.sty_indicator_rout_screening_obsp_yn,
                                    exam.sty_indicator_high_risk_yn,
                                    exam.sty_indicator_high_risk_brca_1_yn,
                                    exam.sty_indicator_high_risk_brca_2_yn,
                                    exam.sty_indicator_high_risk_brca_1_or_2_yn,
                                    exam.sty_indicator_high_risk_at_yn,
                                    exam.sty_indicator_high_risk_other_gene_yn,
                                    exam.sty_indicator_high_risk_prior_high_risk_marker_yn,
                                    exam.sty_indicator_high_risk_prior_personal_can_hist_yn,
                                    exam.sty_indicator_high_risk_hist_of_mantle_rad_yn,
                                    exam.sty_indicator_high_risk_fam_hist_yn,
                                    exam.sty_indicator_add_eval_as_folup_yn,
                                    exam.sty_indicator_folup_after_pre_exam_yn,
                                    exam.sty_indicator_pre_operative_extent_of_dis_yn,
                                    exam.sty_indicator_post_operative_margin_yn,
                                    exam.sty_indicator_pre_neoadj_trtmnt_yn,
                                    exam.sty_indicator_prob_solv_diff_img_yn,
                                    exam.sty_indicator_scar_vs_recurr_yn,
                                    exam.sty_indicator_folup_recommend_yn,
                                    exam.sty_indicator_prior_2_prophy_mast_yn])] )

        ################### Send to table display
        # add main CAD record table
        colLabels = ("cad.cad_pt_no_txt", "cad.latest_mutation", "exam.exam_dt_datetime", "exam.mri_cad_status_txt", "exam.comment_txt",
                     "exam.original_report_txt",
                     "exam.sty_indicator_rout_screening_obsp_yn",
                     "exam.sty_indicator_high_risk_yn",
                     "exam.sty_indicator_high_risk_brca_1_yn",
                     "exam.sty_indicator_high_risk_brca_2_yn",
                     "exam.sty_indicator_high_risk_brca_1_or_2_yn",
                     "exam.sty_indicator_high_risk_at_yn",
                     "exam.sty_indicator_high_risk_other_gene_yn",
                     "exam.sty_indicator_high_risk_prior_high_risk_marker_yn",
                     "exam.sty_indicator_high_risk_prior_personal_can_hist_yn",
                     "exam.sty_indicator_high_risk_hist_of_mantle_rad_yn",
                     "exam.sty_indicator_high_risk_fam_hist_yn",
                     "exam.sty_indicator_add_eval_as_folup_yn",
                     "exam.sty_indicator_folup_after_pre_exam_yn",
                     "exam.sty_indicator_pre_operative_extent_of_dis_yn",
                     "exam.sty_indicator_post_operative_margin_yn",
                     "exam.sty_indicator_pre_neoadj_trtmnt_yn",
                     "exam.sty_indicator_prob_solv_diff_img_yn",
                     "exam.sty_indicator_scar_vs_recurr_yn",
                     "exam.sty_indicator_folup_recommend_yn",
                     "exam.sty_indicator_prior_2_prophy_mast_yn")

        # write output query to pandas frame.
        print len(datainfo)
        dinfo = pd.DataFrame(data=datainfo[0], columns=colLabels)
        print(dinfo['exam.original_report_txt'][0])

        return dinfo
        
        
    def queryExamFindings(self, fStudyID, redateID):
        """
        run : Query by StudyID/AccesionN pair study to local folder
        
        Inputs
        ======
        StudyID : (int)    CAD StudyID
        redateID : (int)  CAD StudyID Data of exam (format yyyy-mm-dd)
        
        Output
        ======
        """               
        # Create the database: the Session. 
        self.Session = sessionmaker()
        self.Session.configure(bind=engine)  # once engine is available
        session = self.Session() #instantiate a Session
        
        #for cad_case in session.query(Cad_record).order_by(Cad_record.pt_id): 
        #    print cad_case.pt_id, cad_case.cad_pt_no_txt, cad_case.latest_mutation_status_int    
        
        datainfo = []; is_mass=[];  is_nonmass=[]; is_foci=[]; 
        for pt, cad, exam, finding, in session.query(database_atExam.Pt_record, database_atExam.Cad_record, database_atExam.Exam_record, database_atExam.Exam_Finding).\
                     filter(database_atExam.Pt_record.pt_id==database_atExam.Cad_record.pt_id).\
                     filter(database_atExam.Cad_record.pt_id==database_atExam.Exam_record.pt_id).\
                     filter(database_atExam.Exam_record.pt_exam_id==database_atExam.Exam_Finding.pt_exam_id).\
                     filter(database_atExam.Cad_record.cad_pt_no_txt == str(fStudyID)).\
                     filter(database_atExam.Exam_record.exam_dt_datetime == redateID).\
                     filter(database_atExam.Exam_Finding.mri_nonmass_yn == True).all():   
                         
           # print results
           if not cad:
               print "cad is empty"
           if not exam:
               print "exam is empty"
           if not finding:
               print "finding is empty"
                   
           datainfo.append([cad.cad_pt_no_txt, pt.anony_dob_datetime, cad.latest_mutation_status_int,
              exam.exam_dt_datetime, exam.a_number_txt, exam.exam_img_dicom_txt, exam.exam_tp_mri_int, exam.mri_cad_status_txt, exam.comment_txt, exam.original_report_txt,
              finding.all_birads_scr_int,
              finding.mri_mass_yn, finding.mri_nonmass_yn, finding.mri_foci_yn])
          
           
           # Find if it's mass or non-mass and process
           if (finding.mri_mass_yn):
               is_mass.append([finding.all_birads_scr_int, finding.side_int, finding.size_x_double, finding.size_y_double, finding.size_z_double, finding.mri_dce_init_enh_int, finding.mri_dce_delay_enh_int, finding.curve_int, finding.mri_mass_margin_int, finding.mammo_n_mri_mass_shape_int, finding.t2_signal_int, finding.mri_bk_enh_inten_int, finding.mri_o_find_cysts_yn, finding.lesion_mri_start_image_no_int,  finding.lesion_mri_finish_image_no_int])
               # add mass lesion record table
               colLabelsmass = ("finding.all_birads_scr_int","finding.side_int", "finding.size_x_double", "finding.size_y_double", "finding.size_z_double", "finding.mri_dce_init_enh_int", "finding.mri_dce_delay_enh_int", "finding.curve_int", "finding.mri_mass_margin_int", "finding.mammo_n_mri_mass_shape_int", "finding.t2_signal_int", "finding.mri_bk_enh_inten_int", "finding.mri_o_find_cysts_yn", "finding.start_image_no_int",  "finding.finish_image_no_int")
               self.massreport = pd.DataFrame(data=array(is_mass), columns=list(colLabelsmass))
               
               
           # Find if it's mass or non-mass and process
           if (finding.mri_nonmass_yn):
               is_nonmass.append([finding.all_birads_scr_int, finding.side_int, finding.size_x_double, finding.size_y_double, finding.size_z_double, finding.mri_dce_init_enh_int, finding.mri_dce_delay_enh_int, finding.curve_int, finding.mri_nonmass_dist_int, finding.mri_nonmass_int_enh_int, finding.t2_signal_int, finding.mri_bk_enh_inten_int, finding.mri_o_find_cysts_yn, finding.lesion_mri_start_image_no_int,  finding.lesion_mri_finish_image_no_int ])
               # add non-mass lesion record table
               colLabelsnonmass = ("finding.all_birads_scr_int","finding.side_int", "finding.size_x_double", "finding.size_y_double", "finding.size_z_double", "finding.mri_dce_init_enh_int", "finding.mri_dce_delay_enh_int", "finding.curve_int", "finding.mri_nonmass_dist_int", "finding.mri_nonmass_int_enh_int", "finding.t2_signal_int", "finding.mri_bk_enh_inten_int", "finding.mri_o_find_cysts_yn", "finding.start_image_no_int",  "finding.finish_image_no_int")
               self.nonmassreport = pd.DataFrame(data=array(is_nonmass), columns=list(colLabelsnonmass))


           # Find if it's mass or non-mass and process
           if (finding.mri_foci_yn):
               is_foci.append([finding.all_birads_scr_int, finding.side_int, finding.size_x_double, finding.size_y_double, finding.size_z_double, finding.mri_dce_init_enh_int, finding.mri_dce_delay_enh_int, finding.curve_int, finding.mri_foci_distr_int, finding.t2_signal_int, finding.mri_bk_enh_inten_int, finding.mri_o_find_cysts_yn, finding.lesion_mri_start_image_no_int,  finding.lesion_mri_finish_image_no_int])
               # add foci lesion record table
               colLabelsfoci = ("finding.all_birads_scr_int","finding.side_int", "finding.size_x_double", "finding.size_y_double", "finding.size_z_double", "finding.mri_dce_init_enh_int", "finding.mri_dce_delay_enh_int", "finding.curve_int", "finding.mri_foci_distr_int", "finding.t2_signal_int", "finding.mri_bk_enh_inten_int", "finding.mri_o_find_cysts_yn", "finding.start_image_no_int",  "finding.finish_image_no_int")
               self.focireport = pd.DataFrame(data=array(is_foci), columns=list(colLabelsfoci))

          
        ####### finish finding masses and non-mass or foci
        # add main CAD record        
        colLabels = ("cad.cad_pt_no_txt", "pt.anony_dob_datetime", "cad.latest_mutation", "exam.exam_dt_datetime","exam.a_number_txt","exam.exam_img_dicom_txt","exam.exam_tp_mri_int","exam.mri_cad_status_txt","exam.comment_txt","exam.original_report", "finding.all_birads_scr_int", "finding.mri_mass_yn", "finding.mri_nonmass_yn", "finding.mri_foci_yn")
        self.findreport = pd.DataFrame(data=array(datainfo), columns=list(colLabels))
    
        colLabelsmass = ("finding.all_birads_scr_int","finding.side_int", "finding.size_x_double", "finding.size_y_double", "finding.size_z_double", "finding.mri_dce_init_enh_int", "finding.mri_dce_delay_enh_int", "finding.curve_int", "finding.mri_mass_margin_int", "finding.mammo_n_mri_mass_shape_int", "finding.t2_signal_int", "finding.mri_bk_enh_inten_int", "finding.mri_o_find_cysts_yn")
        colLabelsnonmass = ("finding.all_birads_scr_int","finding.side_int", "finding.size_x_double", "finding.size_y_double", "finding.size_z_double", "finding.mri_dce_init_enh_int", "finding.mri_dce_delay_enh_int", "finding.curve_int", "finding.mri_nonmass_dist_int", "finding.mri_nonmass_int_enh_int", "finding.t2_signal_int", "finding.mri_bk_enh_inten_int", "finding.mri_o_find_cysts_yn")
        colLabelsfoci = ("finding.all_birads_scr_int","finding.side_int", "finding.size_x_double", "finding.size_y_double", "finding.size_z_double", "finding.mri_dce_init_enh_int", "finding.mri_dce_delay_enh_int", "finding.curve_int", "finding.mri_foci_distr_int", "finding.t2_signal_int", "finding.mri_bk_enh_inten_int", "finding.mri_o_find_cysts_yn")
        
        return is_mass, colLabelsmass, is_nonmass, colLabelsnonmass, is_foci, colLabelsfoci
        

    def queryifProcedure(self, fStudyID, redateID):
        """
        run : Query by StudyID/AccesionN pair study to local folder
        
        Inputs
        ======
        StudyID : (int)    CAD StudyID
        redateID : (int)  CAD StudyID Data of exam (format yyyy-mm-dd)
        
        Output
        ======
        """
        # Create the ORMâ€™s â€œhandleâ€ to the database: the Session. 
        self.Session = sessionmaker()
        self.Session.configure(bind=engine)  # once engine is available
        session = self.Session() #instantiate a Session
        
        gtpathology=[]; self.gtpathology=[]; 
        for cad, exam, finding, proc, patho in session.query(database_atExam.Cad_record, database_atExam.Exam_record, database_atExam.Exam_Finding, database_atlinkPatho.Procedure, database_atlinkPatho.Pathology).\
                     filter(database_atExam.Cad_record.pt_id==database_atExam.Exam_record.pt_id).\
                     filter(database_atExam.Exam_record.pt_exam_id==database_atExam.Exam_Finding.pt_exam_id).\
                     filter(database_atExam.Exam_record.pt_id==database_atlinkPatho.Procedure.pt_id).\
                     filter(database_atlinkPatho.Procedure.pt_procedure_id==database_atlinkPatho.Pathology.pt_procedure_id).\
                     filter(database_atExam.Cad_record.cad_pt_no_txt == str(fStudyID)).\
                     filter(database_atExam.Exam_record.exam_dt_datetime == str(redateID)).\
                     filter(database_atExam.Exam_Finding.mri_nonmass_yn == True).all():
            
           # print results
           if not proc:
               print "proc is empty"
           if not patho:
               print "patho is empty"
                   
           gtpathology.append([proc.pt_procedure_id, proc.proc_dt_datetime, proc.proc_side_int, proc.proc_source_int, proc.proc_guid_int, proc.proc_tp_int, proc.original_report_txt,
                               patho.pt_path_id, patho.histop_core_biopsy_benign_yn, patho.histop_other_txt, patho.histop_benign_bst_parenchyma_yn,
                               patho.histop_tp_isc_ductal_yn, patho.histop_tp_isc_other_txt, patho.in_situ_nucl_grade_int,
                               patho.histop_tp_ic_yn, patho.histop_tp_ic_other_txt, patho.histop_other_2_txt])
           
           gtpathologyLabels = ("proc.pt_procedure_id",  "proc.proc_dt_datetime",  "proc.proc_side_int",  "proc.proc_source_int",  "proc.proc_guid_int",  "proc.proc_tp_int",  "proc.original_report_txt", 
                               "patho.pt_path_id",  "patho.histop_core_biopsy_benign_yn",  "patho.histop_other_txt",  "patho.histop_benign_bst_parenchyma_yn", 
                               "patho.histop_tp_isc_ductal_yn",  "patho.histop_tp_isc_other_txt",  "patho.in_situ_nucl_grade_int", 
                               "patho.histop_tp_ic_yn",  "patho.histop_tp_ic_other_txt",  "patho.histop_other_2_txt")
           self.gtpathology = pd.DataFrame(data=array(gtpathology), columns=list(gtpathologyLabels))
    
        return 
        
        
    