# -*- coding: utf-8 -*-
"""
Created on Tue Apr 05 15:22:04 2016

@author: Cristina Gallego
"""
import sys, os
import string
import datetime
import numpy as np

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import MetaData, Table, Column, DateTime, Integer, String, Boolean, Float
from sqlalchemy.orm import mapper, sessionmaker, polymorphic_union

#import mydatabase
from base import localengine

# he Declarative base class also contains a catalog of all the Table objects that have been defined called MetaData
metadata = MetaData()
      
lesion = Table('lesion', metadata,
    Column('lesion_id', Integer, primary_key=True),
    Column('cad_pt_no_txt', String(50)),
    Column('anony_dob_datetime', DateTime),
    Column('latest_mutation', String(50)),
    Column('exam_dt_datetime', DateTime),
    Column('exam_a_number_txt', String(50)),
    Column('exam_img_dicom_txt', String(50)),
    Column('exam_tp_mri_int', String(50)),
    Column('exam_mri_cad_status_txt', String(50)),
    Column('comment_txt', String),
    Column('original_report', String),
    Column('BIRADS', String(50)),
    Column('mri_mass_yn', Boolean),
    Column('mri_nonmass_yn', Boolean),
    Column('mri_foci_yn', Boolean)
)

radiologyInfo = Table('radiologyInfo', metadata,
    Column('radio_id', Integer, primary_key=True),
    Column('lesion_id', ForeignKey('lesion.lesion_id', ondelete="CASCADE")),
    Column('cad_pt_no_txt', String(40)),
    Column('latest_mutation', String(40)),
    Column('exam_dt_datetime', DateTime),
    Column('mri_cad_status_txt', String(50)),
    Column('comment_txt', String),
    Column('original_report_txt', String),
    Column('sty_indicator_rout_screening_obsp_yn', Boolean),
    Column('sty_indicator_high_risk_yn', Boolean),
    Column('sty_indicator_high_risk_brca_1_yn', Boolean),
    Column('sty_indicator_high_risk_brca_2_yn', Boolean),
    Column('sty_indicator_high_risk_brca_1_or_2_yn', Boolean),
    Column('sty_indicator_high_risk_at_yn', Boolean),
    Column('sty_indicator_high_risk_other_gene_yn', Boolean),
    Column('sty_indicator_high_risk_prior_high_risk_marker_yn', Boolean),
    Column('sty_indicator_high_risk_prior_personal_can_hist_yn', Boolean),
    Column('sty_indicator_high_risk_hist_of_mantle_rad_yn', Boolean),
    Column('sty_indicator_add_eval_as_folup_yn', Boolean),
    Column('sty_indicator_folup_after_pre_exam_yn', Boolean),
    Column('sty_indicator_pre_operative_extent_of_dis_yn', Boolean),
    Column('sty_indicator_post_operative_margin_yn', Boolean),
    Column('sty_indicator_pre_neoadj_trtmnt_yn', Boolean),
    Column('sty_indicator_prob_solv_diff_img_yn', Boolean),
    Column('sty_indicator_scar_vs_recurr_yn', Boolean),
    Column('sty_indicator_folup_recommend_yn', Boolean),
    Column('sty_indicator_prior_2_prophy_mast_yn', Boolean)
)               
      

mass_lesion = Table('mass_lesion', metadata,
    Column('mass_id', Integer, primary_key=True),
    Column('lesion_id', ForeignKey('lesion.lesion_id', ondelete="CASCADE")),
    Column('woFsSeries_id', String(40)),
    Column('woFsSeries_desc', String(40)),
    Column('DynSeries_id', String(40)),
    Column('DynSeries_desc', String(40)),
    Column('L_T2Series_id', String(40)),
    Column('L_T2Series_desc', String(40)),
    Column('R_T2Series_id', String(40)),
    Column('R_T2Series_desc', String(40)),
    Column('BIRADS', String(40)),
    Column('side_int', String(40)),
    Column('size_x_double', String(40)),
    Column('size_y_double', String(40)),
    Column('size_z_double', String(40)),
    Column('mri_dce_init_enh_int', String(50)),
    Column('mri_dce_delay_enh_int', String(50)),
    Column('curve_int', String(50)),
    Column('mri_mass_margin_int', String(50)),
    Column('mammo_n_mri_mass_shape_int', String(50)),
    Column('t2_signal_int', String(50)),
    Column('mri_bk_enh_inten_int', String(50)),
    Column('mri_o_find_cysts_yn', Boolean),
    Column('start_image_no_int', String(20)),
    Column('finish_image_no_int', String(20))
)

nonmass_lesion = Table('nonmass_lesion', metadata,
    Column('nonmass_id', Integer, primary_key=True),
    Column('lesion_id', ForeignKey('lesion.lesion_id', ondelete="CASCADE")),
    Column('woFsSeries_id', String(40)),
    Column('woFsSeries_desc', String(40)),
    Column('DynSeries_id', String(40)),
    Column('DynSeries_desc', String(40)),
    Column('L_T2Series_id', String(40)),
    Column('L_T2Series_desc', String(40)),
    Column('R_T2Series_id', String(40)),
    Column('R_T2Series_desc', String(40)),
    Column('BIRADS', String(40)),
    Column('side_int', String(40)),
    Column('size_x_double', String(40)),
    Column('size_y_double', String(40)),
    Column('size_z_double', String(40)),
    Column('mri_dce_init_enh_int', String(50)),
    Column('mri_dce_delay_enh_int', String(50)),
    Column('curve_int', String(50)),
    Column('mri_nonmass_dist_int', String(50)),
    Column('mri_nonmass_int_enh_int', String(50)),
    Column('t2_signal_int', String(50)),
    Column('mri_bk_enh_inten_int', String(50)),
    Column('mri_o_find_cysts_yn', Boolean),
    Column('start_image_no_int', String(20)),
    Column('finish_image_no_int', String(20))
)


foci_lesion = Table('foci_lesion', metadata,
    Column('foci_id', Integer, primary_key=True),
    Column('lesion_id', ForeignKey('lesion.lesion_id', ondelete="CASCADE")),
    Column('woFsSeries_id', String(40)),
    Column('woFsSeries_desc', String(40)),
    Column('DynSeries_id', String(40)),
    Column('DynSeries_desc', String(40)),
    Column('L_T2Series_id', String(40)),
    Column('L_T2Series_desc', String(40)),
    Column('R_T2Series_id', String(40)),
    Column('R_T2Series_desc', String(40)),
    Column('BIRADS', String(40)),
    Column('side_int', String(40)),
    Column('size_x_double', String(40)),
    Column('size_y_double', String(40)),
    Column('size_z_double', String(40)),
    Column('mri_dce_init_enh_int', String(50)),
    Column('mri_dce_delay_enh_int', String(50)),
    Column('curve_int', String(50)),
    Column('mri_foci_distr_int', String(50)),
    Column('t2_signal_int', String(50)),
    Column('mri_bk_enh_inten_int', String(50)),
    Column('mri_o_find_cysts_yn', Boolean),
    Column('start_image_no_int', String(20)),
    Column('finish_image_no_int', String(20))
)


gtpathology = Table('gtpathology', metadata,
    Column('gthisto_id', Integer, primary_key=True),
    Column('lesion_id', ForeignKey('lesion.lesion_id', ondelete="CASCADE")),
    Column('pt_procedure_id', String(40)),
    Column('proc_dt_datetime', DateTime),
    Column('proc_side_int', String(40)),
    Column('proc_source_int', String(40)),
    Column('proc_guid_int', String(40)),
    Column('proc_tp_int', String(50)),
    Column('original_report_txt', String ),
    Column('pt_path_id', String(50)),
    Column('histop_core_biopsy_benign_yn', String(50)),
    Column('histop_other_txt', String ),
    Column('histop_benign_bst_parenchyma_yn', String(50)),
    Column('histop_tp_isc_ductal_yn', String(50)),
    Column('histop_tp_isc_other_txt', String),
    Column('in_situ_nucl_grade_int', String(50)),
    Column('histop_tp_ic_yn', String(50)),
    Column('histop_tp_ic_other_txt', String),
    Column('histop_other_2_txt', String)
)



# configure myengine and create tables with desired options
metadata.create_all(localengine)