# -*- coding: utf-8 -*-
"""
USAGE: 
=============
from add_records import *
record = AddRecords()
record.lesion_2DB(image, image_pos_pat, image_ori_pat)
record.addSegment(lesion3D)
record.subImage(Images2Sub, timep)                  
record.visualize(images, image_pos_pat, image_ori_pat, sub, postS, interact)

Class Methods:
=============
dicomTransform(image, image_pos_pat, image_ori_pat)
addSegment(lesion3D)
subImage(Images2Sub, timep)                  
visualize(images, image_pos_pat, image_ori_pat, sub, postS, interact)

Class Instance Attributes:
===============

Created on Tue Apr 05 15:22:04 2016

@ author (C) Cristina Gallego, University of Toronto
--------------------------------------------------------------------
 """
import os, os.path
import sys
import string
from sys import argv, stderr, exit
import vtk
from numpy import *
import pandas as pd

from sqlalchemy.orm import sessionmaker
from base import localengine
import mylocaldatabase

class AddNewRecords(object):
    """
    USAGE:
    =============
    record = AddNewRecords()
    """
    def __init__(self): 
        """ initialize database session """           
        #  create a top level Session configuration which can then be used throughout
        # Create the Session
        self.Session = sessionmaker()
        self.Session.configure(bind=localengine)  # once engine is available
        
    def __call__(self):       
        """ Turn Class into a callable object """
        AddNewRecords() 

    def lesion_2DB(self, findreport):

        [cad_id, anony_dob, mutation, exam_date, accession_no, dicom_no, type_mri,
                 cad_status, lesion_comments, original_report, BIRADS, mass_yn, nonmass_yn, foci_yn] = findreport         
        
        self.session = self.Session() #instantiate a Session
        # Send to database lesion info
        lesion_info = mylocaldatabase.Lesion_record(cad_id, anony_dob, mutation, exam_date, accession_no, dicom_no, type_mri, 
                                                   cad_status, lesion_comments, original_report, BIRADS,  mass_yn, nonmass_yn, foci_yn)
        self.session.add(lesion_info)
        
        # Finally send records to database
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()
            
        return
        
    def mass_2DB(self, lesion_id, massreport, Sids, Sdesc):   
        
        Seriesdf = pd.DataFrame({'Desc' : Sdesc,'ids' : Sids})
        
        L_T2Series_id = Seriesdf.iloc[0]['ids']
        L_T2Series_desc = Seriesdf.iloc[0]['Desc']
        R_T2Series_id = Seriesdf.iloc[1]['ids']
        R_T2Series_desc = Seriesdf.iloc[1]['Desc']
        woFsSeries_id = Seriesdf.iloc[2]['ids']
        woFsSeries_desc = Seriesdf.iloc[2]['Desc']
        DynSeries_id = Seriesdf.iloc[3]['ids']
        DynSeries_desc = Seriesdf.iloc[3]['Desc']
         
        [BIRADS, side_int, size_x_double, size_y_double, size_z_double, 
                 mri_dce_init_enh_int, mri_dce_delay_enh_int, curve_int, mri_mass_margin, mri_mass_shape,
                 t2_signal_int, mri_bk_enh_inten_int, mri_o_find_cysts_yn,
                 start_image_no_int, finish_image_no_int] = massreport
                 
                
        self.session = self.Session() #instantiate a Session
        # Send to database lesion info
        mass_record = mylocaldatabase.Mass_record(lesion_id, woFsSeries_id, woFsSeries_desc, DynSeries_id, DynSeries_desc,
                L_T2Series_id, L_T2Series_desc, R_T2Series_id, R_T2Series_desc,
                BIRADS, side_int, size_x_double, size_y_double, size_z_double, 
                mri_dce_init_enh_int, mri_dce_delay_enh_int, curve_int, 
                mri_mass_margin, mri_mass_shape,
                t2_signal_int, mri_bk_enh_inten_int, mri_o_find_cysts_yn,
                start_image_no_int, finish_image_no_int)
                     
        self.session.add(mass_record)
        
        # Finally send records to database
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()
            
        return        
            
    def nonmass_2DB(self, lesion_id, nonmassreport, Sids, Sdesc):   
        
        Seriesdf = pd.DataFrame({'Desc' : Sdesc,'ids' : Sids})
        
        L_T2Series_id = Seriesdf.iloc[0]['ids']
        L_T2Series_desc = Seriesdf.iloc[0]['Desc']
        R_T2Series_id = Seriesdf.iloc[1]['ids']
        R_T2Series_desc = Seriesdf.iloc[1]['Desc']
        woFsSeries_id = Seriesdf.iloc[2]['ids']
        woFsSeries_desc = Seriesdf.iloc[2]['Desc']
        DynSeries_id = Seriesdf.iloc[3]['ids']
        DynSeries_desc = Seriesdf.iloc[3]['Desc']

        [BIRADS, side_int, size_x_double, size_y_double, size_z_double, 
                 mri_dce_init_enh_int, mri_dce_delay_enh_int, curve_int, mri_nonmass_dist_int, mri_nonmass_int_enh_int,
                 t2_signal_int, mri_bk_enh_inten_int, mri_o_find_cysts_yn,
                 start_image_no_int, finish_image_no_int] = nonmassreport
        
        self.session = self.Session() #instantiate a Session
        # Send to database lesion info
        nonmass_record = mylocaldatabase.Nonmass_record(lesion_id, woFsSeries_id, woFsSeries_desc, DynSeries_id, DynSeries_desc,
                L_T2Series_id, L_T2Series_desc, R_T2Series_id, R_T2Series_desc,
                BIRADS, side_int, str(size_x_double), str(size_y_double), str(size_z_double), 
                mri_dce_init_enh_int, mri_dce_delay_enh_int, curve_int, 
                mri_nonmass_dist_int, mri_nonmass_int_enh_int,
                str(t2_signal_int), mri_bk_enh_inten_int, mri_o_find_cysts_yn,
                str(start_image_no_int), str(finish_image_no_int) )
                 
        self.session.add(nonmass_record)
        
        # Finally send records to database
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()
            
        return
    
    
    def foci_2DB(self, focireport):        
        
        Seriesdf = pd.DataFrame({'Desc' : Sdesc,'ids' : Sids})
        
        L_T2Series_id = Seriesdf.iloc[0]['ids']
        L_T2Series_desc = Seriesdf.iloc[0]['Desc']
        R_T2Series_id = Seriesdf.iloc[1]['ids']
        R_T2Series_desc = Seriesdf.iloc[1]['Desc']
        woFsSeries_id = Seriesdf.iloc[2]['ids']
        woFsSeries_desc = Seriesdf.iloc[2]['Desc']
        DynSeries_id = Seriesdf.iloc[3]['ids']
        DynSeries_desc = Seriesdf.iloc[3]['Desc']
         
        [BIRADS, side_int, size_x_double, size_y_double, size_z_double, 
                 mri_dce_init_enh_int, mri_dce_delay_enh_int, curve_int, mri_foci_distr,
                 t2_signal_int, mri_bk_enh_inten_int, mri_o_find_cysts_yn,
                 start_image_no_int, finish_image_no_int] = focireport
                 
        self.session = self.Session() #instantiate a Session
        # Send to database lesion info
        foci_record = mylocaldatabase.Foci_record(lesion_id, woFsSeries_id, woFsSeries_desc, DynSeries_id, DynSeries_desc,
                L_T2Series_id, L_T2Series_desc, R_T2Series_id, R_T2Series_desc,
                BIRADS, side_int, size_x_double, size_y_double, size_z_double, 
                mri_dce_init_enh_int, mri_dce_delay_enh_int, curve_int, 
                mri_foci_distr,
                t2_signal_int, mri_bk_enh_inten_int, mri_o_find_cysts_yn,
                start_image_no_int, finish_image_no_int)
                
        self.session.add(foci_record)
        
        # Finally send records to database
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()
            
        return        
        
           
    def radiology_2DB(self, lesion_id, radioinfo):        
        
        [cad_pt_no_txt, latest_mutation, exam_dt_datetime, mri_cad_status_txt, comment_txt, original_report_txt,
                sty_indicator_rout_screening_obsp_yn, 
                sty_indicator_high_risk_yn, sty_indicator_high_risk_brca_1_yn, sty_indicator_high_risk_brca_2_yn, sty_indicator_high_risk_brca_1_or_2_yn, 
                sty_indicator_high_risk_at_yn, sty_indicator_high_risk_other_gene_yn,
                sty_indicator_high_risk_prior_high_risk_marker_yn, sty_indicator_high_risk_prior_personal_can_hist_yn, sty_indicator_high_risk_hist_of_mantle_rad_yn,
                sty_indicator_high_risk_fam_hist_yn, sty_indicator_add_eval_as_folup_yn, sty_indicator_folup_after_pre_exam_yn, 
                sty_indicator_pre_operative_extent_of_dis_yn, sty_indicator_post_operative_margin_yn, sty_indicator_pre_neoadj_trtmnt_yn,
                sty_indicator_prob_solv_diff_img_yn, sty_indicator_scar_vs_recurr_yn, sty_indicator_folup_recommend_yn, 
                sty_indicator_prior_2_prophy_mast_yn] = radioinfo
        
        self.session = self.Session() #instantiate a Session
        # Send to database lesion info
        rad_records = mylocaldatabase.Radiology_record(lesion_id, cad_pt_no_txt, latest_mutation, exam_dt_datetime, mri_cad_status_txt, 
                comment_txt, str(original_report_txt),
                sty_indicator_rout_screening_obsp_yn, 
                sty_indicator_high_risk_yn, sty_indicator_high_risk_brca_1_yn, sty_indicator_high_risk_brca_2_yn, sty_indicator_high_risk_brca_1_or_2_yn, 
                sty_indicator_high_risk_at_yn, sty_indicator_high_risk_other_gene_yn,
                sty_indicator_high_risk_prior_high_risk_marker_yn, sty_indicator_high_risk_prior_personal_can_hist_yn, sty_indicator_high_risk_hist_of_mantle_rad_yn,
                sty_indicator_high_risk_fam_hist_yn, sty_indicator_add_eval_as_folup_yn, sty_indicator_folup_after_pre_exam_yn, 
                sty_indicator_pre_operative_extent_of_dis_yn, sty_indicator_post_operative_margin_yn, sty_indicator_pre_neoadj_trtmnt_yn,
                sty_indicator_prob_solv_diff_img_yn, sty_indicator_scar_vs_recurr_yn, sty_indicator_folup_recommend_yn, 
                sty_indicator_prior_2_prophy_mast_yn)
                        
        self.session.add(rad_records)
        
        # Finally send records to database
        try:
            self.session.commit()  
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()
            
        return
        
        
    def gtpathology_2DB(self, lesion_id, gtpathology):        
        
        [pt_procedure_id, proc_dt_datetime, proc_side_int,
                 proc_source_int, proc_guid_int, proc_tp_int, original_report_txt, pt_path_id, histop_core_biopsy_benign_yn, histop_other_txt,
                 histop_benign_bst_parenchyma_yn, histop_tp_isc_ductal_yn, histop_tp_isc_other_txt, in_situ_nucl_grade_int,
                 histop_tp_ic_yn, histop_tp_ic_other_txt, histop_other_2_txt] = gtpathology
        
        self.session = self.Session() #instantiate a Session
        # Send to database lesion info
        gtpatho_records = mylocaldatabase.gtPathology_record(lesion_id, pt_procedure_id, proc_dt_datetime, proc_side_int,
                 proc_source_int, proc_guid_int, proc_tp_int, original_report_txt, pt_path_id, histop_core_biopsy_benign_yn, histop_other_txt,
                 histop_benign_bst_parenchyma_yn, histop_tp_isc_ductal_yn, histop_tp_isc_other_txt, in_situ_nucl_grade_int,
                 histop_tp_ic_yn, histop_tp_ic_other_txt, histop_other_2_txt)
                        
        self.session.add(gtpatho_records)
        
        # Finally send records to database
        try:
            self.session.commit()  
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()
            
        return