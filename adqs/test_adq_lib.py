from collections import namedtuple
import logging
import pandas as pd
from adq_lib import adq_per_quantity
from adq_lib import dose_from_name


def _apply_adq(d):
    with_rows = {}
    for k, v in d.items():
        with_rows[k] = [v]
    df = pd.DataFrame(with_rows)
    result = df.apply(adq_per_quantity, axis=1)[0]
    if result:
        result = round(result, 3)
    return result

## Non-blank ADQ denominators

def test_units_with_numerator_and_adq_in_g():
    subject = {
        'Practice_Code': 'P92635',
        'BNF_Code': '0102000A0BDAAAA',
        'BNF_Description': 'Audmonal_Cap 60mg',
        'Items': 1,
        'Quantity': 100,
        'ADQ_Usage': 33.33333,
        'bnf_code': '0102000A0BDAAAA',
        'name': 'Audmonal 60mg capsules',
        'vpid': 317148009,
        'form': 'Capsule',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'capsule',
        'unit_of_measure': 'capsule',
        'numerator': 0.06,
        'numerator_unit_of_measure': 'g',
        'denominator': None,
        'denominator_unit_of_measure': 'nan',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Audmonal_Cap 60mg',
        'adq_value': 0.18,
        'dose_multiplier': 1,
        'adq_denominator': 'g',
    }
    assert _apply_adq(subject) == 0.333

def test_units_with_numerator_and_adq_in_ml_and_no_denominator():
    subject = {
        'Practice_Code': 'C84017',
        'BNF_Description': 'Colomint_Cap G/R 0.2ml',
        'Items': 1,
        'Quantity': 100,
        'ADQ_Usage': 33.33333,
        'bnf_code': '0102000T0BJAAAA',
        'name': 'Colomint 0.2ml gastro-resistant capsules',
        'vpid': 14610311000001100,
        'form': 'Gastro-resistant capsule',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'capsule',
        'unit_of_measure': 'capsule',
        'numerator': 0.2,
        'numerator_unit_of_measure': 'ml',
        'denominator': None,
        'denominator_unit_of_measure': 'nan',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Colomint_Cap G/R 0.2ml',
        'adq_value': 0.6,
        'adq_denominator': 'ml',
        'dose_multiplier': 1,
    }
    assert _apply_adq(subject) == 0.333


def test_units_with_numerator_denominator_and_adq_in_ml():
    subject = {
        'Practice_Code': 'C84017',
        'BNF_Code': '0102000T0BJAAAA',
        'BNF_Description': 'Colomint_Cap G/R 0.2ml',
        'Items': 1,
        'Quantity': 100,
        'ADQ_Usage': 33.33333,
        'bnf_code': '0102000T0BJAAAA',
        'name': 'Colomint 0.2ml gastro-resistant capsules',
        'vpid': 14610311000001100,
        'form': 'Gastro-resistant capsule',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'capsule',
        'unit_of_measure': 'capsule',
        'numerator': 0.2,
        'numerator_unit_of_measure': 'ml',
        'denominator': None,
        'denominator_unit_of_measure': 'nan',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Colomint_Cap G/R 0.2ml',
        'adq_value': 0.6,
        'adq_denominator': 'ml',
        'dose_multiplier': 1,
        'computed_adq': 33.3333333333
    }
    assert _apply_adq(subject) == 0.333


def test_adq_in_unit_dose():
    subject = {
        'Practice_Code': 'Y03331',
        'BNF_Code': '0502030B0AAAXAX',
        'BNF_Description': 'Nystatin_Oral Susp 100,000u/ml S/F',
        'Items': 1,
        'Quantity': 30,
        'ADQ_Usage': 7.5,
        'bnf_code': '0502030B0AAAXAX',
        'name': 'Nystatin 100,000units/ml oral suspension sugar free',
        'vpid': 400576003,
        'form': 'Oral suspension',
        'form_indicator': 'Continuous',
        'form_size': None,
        'form_units': None,
        'unit_of_measure': None,
        'numerator': 100000.0,
        'numerator_unit_of_measure': 'unit',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'ml',
        'ingredient_count': 1.0,
        'squ': 'ml',
        'quantity_denominator': 'ml',
        'bnf_name': 'Nystatin_Oral Susp 100,000u/ml S/F',
        'adq_value': 400000.0,
        'adq_denominator': 'unit dose',
        'dose_multiplier': 1,
    }
    assert _apply_adq(subject) == 0.25


def test_mega_unit_dose_vials():
    subject = {
        'Practice_Code': 'P92639',
        'BNF_Code': '0501070I0BCAAAD',
        'BNF_Description': 'Promixin_Pdr For Neb 1mega u',
        'Items': 1,
        'Quantity': 60,
        'ADQ_Usage': 30.0,
        'bnf_code': '0501070I0BCAAAD',
        'name': 'Promixin 1million unit powder for nebuliser solution unit dose vials',
        'vpid': 4256011000001107,
        'form': 'Powder for nebuliser solution',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'unit dose',
        'unit_of_measure': 'unit dose',
        'numerator': 1000000.0,
        'numerator_unit_of_measure': 'unit',
        'denominator': None,
        'denominator_unit_of_measure': 'nan',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Promixin_Pdr For Neb 1mega u',
        'adq_value': 2.0,
        'adq_denominator': '',
        'dose_multiplier': 1,
    }
    assert _apply_adq(subject) == 0.5


def test_multiple_dose_presentation():
    subject = {
        'Practice_Code': 'M82028',
        'BNF_Code': '0105020D0AAACAC',
        'BNF_Description': 'Prednisolone_20mg/Applic Foam Enema(14D)',
        'Items': 1,
        'Quantity': 4,
        'ADQ_Usage': 56.0,
        'bnf_code': '0105020D0AAACAC',
        'name': 'Prednisolone 20mg/application foam enema',
        'vpid': 349392002,
        'form': 'Foam',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'application',
        'unit_of_measure': 'application',
        'numerator': 0.02,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'application',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Prednisolone_20mg/Applic Foam Enema(14D)',
        'adq_value': 0.02,
        'adq_denominator': 'g',
        'dose_multiplier': '14'}
    assert _apply_adq(subject) == 14.0


def test_adq_and_quantity_denominator_in_units_with_dose_multiplier():
    subject = {
        'Practice_Code': 'P92642',
        'BNF_Code': '0302000N0BCACAZ',
        'BNF_Description': 'Seretide 500_Accuhaler 500mcg/50mcg(60D)',
        'Items': 2,
        'Quantity': 1,
        'ADQ_Usage': 60.0,
        'bnf_code': '0302000N0BCACAZ',
        'name': 'Seretide 500 Accuhaler',
        'vpid': 320280004,
        'form': 'Inhalation powder',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'dose',
        'unit_of_measure': 'dose',
        'numerator': 5e-05,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'dose',
        'ingredient_count': 2.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Seretide 500_Accuhaler 500mcg/50mcg(60D)',
        'adq_value': 2.0,
        'adq_denominator': 'dose',
        'dose_multiplier': '60'
    }
    assert _apply_adq(subject) == 30.0


def xtest_unit_dose_spray_with_adq_in_grams():
    # There is no way of telling the unit dose contains 20mg from the data
    # But I think form_size is wrong
    subject = {
        'Practice_Code': 'P92029',
        'BNF_Description': 'Imigran_Nsl Spy 20mg/0.1ml Ud',
        'Items': 2,
        'Quantity': 6,
        'ADQ_Usage': 12.0,
        'bnf_code': '0407041T0BBAGAG',
        'name': 'Imigran 20mg nasal spray',
        'vpid': 322823002,
        'form': 'Spray',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'unit dose',
        'unit_of_measure': 'unit dose',
        'numerator': 0.2,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'ml',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Imigran_Nsl Spy 20mg/0.1ml Ud',
        'adq_value': 0.02,
        'adq_denominator': 'g',
        'dose_multiplier': 1.0,
        'adq_per_quantity': 10.0,
        'computed_adq': 120.0
    }
    assert _apply_adq(subject) == 1.0


def test_unit_dose_with_adq_in_grams():
    subject = {
        'bnf_code': '0301011R0AAAXAX',
        'name': 'Salbutamol 2.5mg/2.5ml nebuliser liquid unit dose vials',
        'vpid': 320177008,
        'form': 'Nebuliser liquid',
        'form_indicator': 'Discrete',
        'form_size': 2.5,
        'form_units': 'ml',
        'unit_of_measure': 'unit dose',
        'numerator': 0.001,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'ml',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Salbutamol_Inh Soln 2.5mg/2.5ml Ud',
        'adq_value': 0.01,
        'adq_denominator': 'g',
        'dose_multiplier': 1.0,
    }
    assert _apply_adq(subject) == 0.25

def test_unit_ampoules_with_form_size_greater_than_one():
    subject = {
        'Practice_Code': 'B81092',
        'BNF_Description': 'Salipraneb_Neb Soln 0.5/2.5mg/2.5ml Amp',
        'Items': 1,
        'Quantity': 60,
        'ADQ_Usage': 30.0,
        'bnf_code': '0301040R0BEAAAC',
        'name': 'Salipraneb 0.5mg/2.5mg nebuliser solution 2.5ml ampoules',
        'vpid': 15534911000001100,
        'form': 'Nebuliser liquid',
        'form_indicator': 'Discrete',
        'form_size': 2.5,
        'form_units': 'ml',
        'unit_of_measure': 'ampoule',
        'numerator': 0.001,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'ml',
        'ingredient_count': 2.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Salipraneb_Neb Soln 0.5/2.5mg/2.5ml Amp',
        'adq_value': 2.0,
        'adq_denominator': '',
        'dose_multiplier': 1,
    }
    assert _apply_adq(subject) == 0.5


def x_test_units_with_numerator_in_ml_and_adq_in_g():
    # does not exist!
    pass

def x_test_units_with_numerator_in_g_and_adq_in_ml():
    # does not exist!
    pass

def x_test_continuous_liquid_with_numerator_in_ml_and_adq_in_g():
    # does not exist
    pass

def test_continuous_liquid_with_numerator_in_g_and_adq_in_g():
    subject = {
        'Practice_Code': 'D82044',
        'BNF_Code': '0105010E0AAALAL',
        'BNF_Description': 'Sulfasalazine_Liq Spec 200mg/5ml',
        'Items': 1,
        'Quantity': 1000,
        'ADQ_Usage': 20.0,
        'bnf_code': '0105010E0AAALAL',
        'name': 'Sulfasalazine 200mg/5ml oral suspension',
        'vpid': 13395811000001106,
        'form': 'Oral suspension',
        'form_indicator': 'Continuous',
        'form_size': None,
        'form_units': None,
        'unit_of_measure': None,
        'numerator': 0.04,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'ml',
        'ingredient_count': 1.0,
        'squ': 'ml',
        'quantity_denominator': 'ml',
        'bnf_name': 'Sulfasalazine_Liq Spec 200mg/5ml',
        'adq_value': 2.0,
        'adq_denominator': 'g',
        'dose_multiplier': 1,
        'adq_per_quantity': 0.02,
        'computed_adq': 20.0
    }
    assert _apply_adq(subject) == 0.02


def test_continuous_liquid_with_numerator_in_ml_and_adq_in_ml():
    subject = {
        'Practice_Code': 'J81056',
        'BNF_Code': '0106030P0AAABAB',
        'BNF_Description': 'Liq Paraf_Liq',
        'Items': 1,
        'Quantity': 650,
        'ADQ_Usage': 65.0,
        'bnf_code': '0106030P0AAABAB',
        'name': 'Liquid paraffin liquid',
        'vpid': 4072011000001101,
        'form': 'Liquid',
        'form_indicator': 'Continuous',
        'form_size': None,
        'form_units': None,
        'unit_of_measure': None,
        'numerator': 1.0,
        'numerator_unit_of_measure': 'ml',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'ml',
        'ingredient_count': 1.0,
        'squ': 'ml',
        'quantity_denominator': 'ml',
        'bnf_name': 'Liq Paraf_Liq',
        'adq_value': 10.0,
        'adq_denominator': 'ml',
        'dose_multiplier': 1,
    }
    assert _apply_adq(subject) == 0.1


def test_continuous_liquid_with_numerator_in_g_and_adq_in_ml():
    subject = {
        'Practice_Code': 'G83037',
        'BNF_Description': 'Kaolin & Morph_Mix',
        'Items': 1,
        'Quantity': 200,
        'ADQ_Usage': 5.0,
        'bnf_code': '0104020N0AAABAB',
        'name': 'Kaolin and Morphine mixture',
        'vpid': 14610811000001109,
        'form': 'Oral suspension',
        'form_indicator': 'Continuous',
        'form_size': None,
        'form_units': None,
        'unit_of_measure': None,
        'numerator': 50.0,
        'numerator_unit_of_measure': 'g',
        'denominator': 1000.0,
        'denominator_unit_of_measure': 'ml',
        'ingredient_count': 4.0,
        'squ': 'ml',
        'quantity_denominator': 'ml',
        'bnf_name': 'Kaolin & Morph_Mix',
        'adq_value': 40.0,
        'adq_denominator': 'ml',
        'dose_multiplier': 1,
    }
    assert _apply_adq(subject) == 0.025


## blank ADQ denominators

def test_patch_with_blank_adq_denominator():
    subject = {
        'Practice_Code': 'P92021',
        'BNF_Code': '0407020A0BBAJAF',
        'BNF_Description': 'Durogesic DTrans_T/Derm Patch 50mcg',
        'Items': 2,
        'Quantity': 10,
        'ADQ_Usage': 66.66666,
        'bnf_code': '0407020A0BBAJAF',
        'name': 'Durogesic DTrans 50micrograms transdermal patches',
        'vpid': 333920004,
        'form': 'Transdermal patch',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'patch',
        'unit_of_measure': 'patch',
        'numerator': 5e-05,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'hour',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Durogesic DTrans_T/Derm Patch 50mcg',
        'adq_value': 0.3,
        'adq_denominator': '',
        'dose_multiplier': 1
    }
    assert _apply_adq(subject) == 3.333


def test_mass_per_liquid_with_blank_adq_denominator():
    subject = {
        'Practice_Code': 'P92642',
        'BNF_Description': 'Co-Danthramer_Susp 25mg/200mg/5ml S/F',
        'Items': 1,
        'Quantity': 300,
        'ADQ_Usage': 30.0,
        'bnf_code': '0106020B0AAAAAA',
        'name': 'Co-danthramer 25mg/200mg/5ml oral suspension sugar free',
        'vpid': 317519008,
        'form': 'Oral suspension',
        'form_indicator': 'Discrete',
        'form_size': 5.0,
        'form_units': 'ml',
        'unit_of_measure': 'spoonful',
        'numerator': 0.04,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'ml',
        'ingredient_count': 2.0,
        'squ': 'ml',
        'quantity_denominator': 'ml',
        'bnf_name': 'Co-Danthramer_Susp 25mg/200mg/5ml S/F',
        'adq_value': 10.0,
        'adq_denominator': '',
        'dose_multiplier': 1,
    }
    assert _apply_adq(subject) == 0.1


def test_unit_dose_simple_liquid_with_blank_adq_denominator():
    subject = {
        'Practice_Code': 'C81062',
        'BNF_Description': 'Arach Oil_Enem 130ml',
        'Items': 1,
        'Quantity': 1,
        'ADQ_Usage': 1.0,
        'bnf_code': '0106030A0AAAAAA',
        'name': 'Arachis oil 130ml enema',
        'vpid': 317635009,
        'form': 'Enema',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'enema',
        'unit_of_measure': 'enema',
        'numerator': 1.0,
        'numerator_unit_of_measure': 'ml',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'ml',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Arach Oil_Enem 130ml',
        'adq_value': 1.0,
        'adq_denominator': '',
        'dose_multiplier': 1,
    }
    assert _apply_adq(subject) == 1.0


def test_unit_with_blank_adq_denominator():
    subject = {
        'Practice_Code': 'P92637',
        'BNF_Description': 'CosmoCol_Half Oral Pdr Sach 6.9g',
        'Items': 2,
        'Quantity': 60,
        'ADQ_Usage': 60.0,
        'bnf_code': '0106040M0BGAEAB',
        'name': 'CosmoCol Half oral powder 6.9g sachets',
        'vpid': 4052411000001107,
        'form': 'Powder',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'sachet',
        'unit_of_measure': 'sachet',
        'numerator': 5.4,
        'numerator_unit_of_measure': 'mmol',
        'denominator': 1000.0,
        'denominator_unit_of_measure': 'ml',
        'ingredient_count': 5.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'CosmoCol_Half Oral Pdr Sach 6.9g',
        'adq_value': 2.0,
        'adq_denominator': '',
        'dose_multiplier': 1,
    }
    assert _apply_adq(subject) == 0.5


def xtest_num_and_denom_match_adq_form():
    subject = {
        "Practice_Code": "P92017",
        "BNF_Description": "Normacol_Gran 62%",
        "Items": 2,
        "Quantity": 500,
        "ADQ_Usage": 62,
        "bnf_code": "0106010N0BBAAAA",
        "name": "Normacol granules",
        "vpid": 3505711000001104,
        "form": "Granules",
        "form_indicator": "Continuous",
        "form_size": None,
        "form_units": None,
        "unit_of_measure": None,
        "numerator": 0.62,
        "numerator_unit_of_measure": "g",
        "denominator": 1,
        "denominator_unit_of_measure": "g",
        "ingredient_count": 1,
        "squ": "g",
        "quantity_denominator": "g",
        "bnf_name": "Normacol_Gran 62%",
        "adq_value": 10,
        'dose_multiplier': 1,
        "adq_denominator": "g",
    }
    assert _apply_adq(subject) == 0.6


## Compound drugs

def test_compound_unit_dose_item():
    subject = {
        'Practice_Code': 'P92042',
        'BNF_Description': 'Fluticasone/Salmeterol_Inh 250/25mcg120D',
        'Items': 1,
        'Quantity': 1,
        'ADQ_Usage': 30.0,
        'bnf_code': '0302000N0AABGBG',
        'name': 'Fluticasone 250micrograms/dose / Salmeterol 25micrograms/dose inhaler CFC free',
        'vpid': 320276009,
        'form': 'Pressurised inhalation',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'dose',
        'unit_of_measure': 'dose',
        'numerator': 2.5e-05,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'dose',
        'ingredient_count': 2.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Fluticasone/Salmeterol_Inh 250/25mcg120D',
        'adq_value': 4.0,
        'adq_denominator': '',
        'dose_multiplier': 120.0,
    }
    assert _apply_adq(subject) == 30.0


def test_compound_unit_dose_item_with_adq_in_g():
    subject = {
        'Practice_Code': 'G81047',
        'BNF_Description': 'Maxepa_Cap 1g',
        'Items': 1,
        'Quantity': 100,
        'ADQ_Usage': 10.0,
        'bnf_code': '0212000V0BBABAB',
        'name': 'MaxEPA 1g capsules',
        'vpid': 319978009,
        'form': 'Capsule',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'capsule',
        'unit_of_measure': 'capsule',
        'numerator': 0.115,
        'numerator_unit_of_measure': 'g',
        'denominator': None,
        'denominator_unit_of_measure': 'nan',
        'ingredient_count': 2.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Maxepa_Cap 1g',
        'adq_value': 10.0,
        'adq_denominator': 'g',
        'dose_multiplier': 1.0}
    assert _apply_adq(subject) == 0.1


def test_patch():
    subject = {
        'Practice_Code': 'C84094',
        'BNF_Description': 'Mezolar Matrix_TransdermalPatch 25mcg/hr',
        'Items': 5,
        'Quantity': 10,
        'ADQ_Usage': 166.66665,
        'bnf_code': '0407020A0BFABAE',
        'name': 'Mezolar Matrix 25micrograms/hour transdermal patches',
        'vpid': 333919005,
        'form': 'Transdermal patch',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'patch',
        'unit_of_measure': 'patch',
        'numerator': 2.5e-05,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'hour',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Mezolar Matrix_TransdermalPatch 25mcg/hr',
        'adq_value': 0.3,
        'adq_denominator': '',
        'dose_multiplier': 1.0,
    }
    assert _apply_adq(subject) == 3.333

def xxx_test_patch_with_adq_in_grammes():
    # See notes.md -- no idea what the right thing to do here is
    subject = {
        'Practice_Code': 'P92642',
        'BNF_Description': 'Buprenorphine_Patch 10mcg/hr (7day)',
        'Items': 1,
        'Quantity': 16,
        'ADQ_Usage': 48.0,
        'bnf_code': '0407020B0AAAIAI',
        'name': 'Buprenorphine 10micrograms/hour transdermal patches',
        'vpid': 9567411000001100,
        'form': 'Transdermal patch',
        'form_indicator': 'Discrete',
        'form_size': 1.0,
        'form_units': 'patch',
        'unit_of_measure': 'patch',
        'numerator': 1e-05,
        'numerator_unit_of_measure': 'g',
        'denominator': 1.0,
        'denominator_unit_of_measure': 'hour',
        'ingredient_count': 1.0,
        'squ': 'unit',
        'quantity_denominator': 'unit',
        'bnf_name': 'Buprenorphine_Patch 10mcg/hr (7day)',
        'adq_value': 0.00056,
        'adq_denominator': 'g',
        'dose_multiplier': 1.0,
        'adq_per_quantity': 0.4285714286,
        'computed_adq': 6.8571428571}
    assert _apply_adq(subject) == 4.0

def test_dose_from_name():
    assert dose_from_name("Fluticasone/Salmeterol_Inh 250/25mcg120D") == 120.0
    assert dose_from_name("Mesalazine_Foam Aero Enem 1g/D 14g") == 14.0
    assert dose_from_name("Seretide 500_Accuhaler 500mcg/50mcg(60D)") == 60.0
