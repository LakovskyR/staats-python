"""
STAATS Python - Complete Working Demo
Shows the full pipeline in action with realistic survey data
"""

import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import DataMap, Question, QuestionType, Filter, Class
from formula_parser import FormulaParser
from recode_engine import (
    RecodeEngine, QualiUniqueRecode, QualiMultipleRecode,
    NumericRecode, NumberOfAnswersRecode, WeightRecode
)
from engines import FilterEngine, ClassEngine


def create_sample_data() -> pd.DataFrame:
    """
    Create realistic survey data for testing
    Simulates a healthcare professional survey
    """
    np.random.seed(42)
    n = 100
    
    data = {
        # Demographics
        'ID': range(1, n + 1),
        'Country': np.random.choice([1, 2, 3], n, p=[0.5, 0.3, 0.2]),  # 1=FR, 2=UK, 3=DE
        'Specialty': np.random.choice([1, 2, 3, 4], n, p=[0.4, 0.3, 0.2, 0.1]),  # Medical specialties
        'Age': np.random.randint(28, 68, n),
        'Experience': np.random.randint(1, 40, n),
        
        # Single choice questions
        'Q1_Satisfaction': np.random.choice([1, 2, 3, 4, 5], n),  # 1=Very dissatisfied, 5=Very satisfied
        'Q2_Recommend': np.random.choice([1, 2, 3], n),  # 1=Yes, 2=No, 3=Maybe
        
        # Multiple choice - stored as "1,2,3" format
        'Q3_Brands': [
            ','.join(map(str, sorted(np.random.choice([1, 2, 3, 4, 5], 
                         size=np.random.randint(0, 4), replace=False))))
            if np.random.rand() > 0.1 else None
            for _ in range(n)
        ],
        
        'Q4_Channels': [
            ','.join(map(str, sorted(np.random.choice([1, 2, 3, 4], 
                         size=np.random.randint(1, 3), replace=False))))
            for _ in range(n)
        ],
        
        # Numeric
        'Q5_Patients': np.random.randint(10, 200, n),
        'Q6_Score': np.random.randint(1, 11, n),  # 1-10 scale
    }
    
    return pd.DataFrame(data)


def setup_datamap() -> DataMap:
    """
    Define the data structure (paramétrage)
    """
    dm = DataMap()
    
    # Demographics
    dm.add_question(Question('ID', QuestionType.NUMERIC, 'Respondent ID'))
    dm.add_question(Question('Country', QuestionType.QUALI_UNIQUE, 'Country', {
        1: 'France', 2: 'UK', 3: 'Germany'
    }))
    dm.add_question(Question('Specialty', QuestionType.QUALI_UNIQUE, 'Medical Specialty', {
        1: 'Cardiology', 2: 'Dermatology', 3: 'Oncology', 4: 'Other'
    }))
    dm.add_question(Question('Age', QuestionType.NUMERIC, 'Age'))
    dm.add_question(Question('Experience', QuestionType.NUMERIC, 'Years of Experience'))
    
    # Questions
    dm.add_question(Question('Q1_Satisfaction', QuestionType.QUALI_UNIQUE, 'Overall Satisfaction', {
        1: 'Very dissatisfied', 2: 'Dissatisfied', 3: 'Neutral', 
        4: 'Satisfied', 5: 'Very satisfied'
    }))
    dm.add_question(Question('Q2_Recommend', QuestionType.QUALI_UNIQUE, 'Would Recommend', {
        1: 'Yes', 2: 'No', 3: 'Maybe'
    }))
    dm.add_question(Question('Q3_Brands', QuestionType.QUALI_MULTI, 'Brands Known', {
        1: 'Brand A', 2: 'Brand B', 3: 'Brand C', 4: 'Brand D', 5: 'Brand E'
    }))
    dm.add_question(Question('Q4_Channels', QuestionType.QUALI_MULTI, 'Information Channels', {
        1: 'Medical journals', 2: 'Conferences', 3: 'Online', 4: 'Colleagues'
    }))
    dm.add_question(Question('Q5_Patients', QuestionType.NUMERIC, 'Number of Patients per Month'))
    dm.add_question(Question('Q6_Score', QuestionType.NUMERIC, 'Product Score (1-10)'))
    
    return dm


def setup_recodes(engine: RecodeEngine):
    """
    Define recoded variables
    """
    # Recode 1: Age groups from numeric Age
    engine.add_recode(QualiUniqueRecode(
        name='AgeGroup',
        title='Age Groups',
        formula='1: ["Age">=28] and ["Age"<40]\n2: ["Age">=40] and ["Age"<55]\n3: ["Age">=55]',
        codes={1: 'Under 40', 2: '40-54', 3: '55+'}
    ))
    
    # Recode 2: Experience levels
    engine.add_recode(QualiUniqueRecode(
        name='ExpLevel',
        title='Experience Level',
        formula='1: ["Experience"<5]\n2: ["Experience">=5] and ["Experience"<15]\n3: ["Experience">=15]',
        codes={1: 'Junior (<5y)', 2: 'Mid (5-15y)', 3: 'Senior (15y+)'}
    ))
    
    # Recode 3: Satisfaction top2box
    engine.add_recode(QualiUniqueRecode(
        name='Sat_Top2',
        title='Satisfaction Top 2 Box',
        formula='1: ["Q1_Satisfaction">=4]\n2: ["Q1_Satisfaction"<4]',
        codes={1: 'Satisfied (4-5)', 2: 'Not satisfied (1-3)'}
    ))
    
    # Recode 4: Count of brands known
    engine.add_recode(NumberOfAnswersRecode(
        name='Q3_BrandsCount',
        title='Number of Brands Known',
        formula='["Q3_Brands"]'
    ))
    
    # Recode 5: Brand awareness segments
    engine.add_recode(QualiUniqueRecode(
        name='BrandAwareness',
        title='Brand Awareness Level',
        formula='1: ["Q3_BrandsCount">=4]\n2: ["Q3_BrandsCount">=2] and ["Q3_BrandsCount"<4]\n3: ["Q3_BrandsCount"<2]',
        codes={1: 'High (4+ brands)', 2: 'Medium (2-3 brands)', 3: 'Low (0-1 brands)'}
    ))
    
    # Recode 6: Patient volume categories
    engine.add_recode(QualiUniqueRecode(
        name='PatientVolume',
        title='Patient Volume',
        formula='1: ["Q5_Patients"<50]\n2: ["Q5_Patients">=50] and ["Q5_Patients"<100]\n3: ["Q5_Patients">=100]',
        codes={1: 'Low (<50)', 2: 'Medium (50-99)', 3: 'High (100+)'}
    ))
    
    # Recode 7: Country weighting (fictional weights)
    engine.add_recode(WeightRecode(
        name='CountryWeight',
        title='Country Weighting',
        formula='',
        weights={
            '["Country"=1]': 1.0,   # France: no adjustment
            '["Country"=2]': 0.8,   # UK: down-weight
            '["Country"=3]': 1.2    # Germany: up-weight
        }
    ))


def setup_filters(engine: FilterEngine):
    """
    Define filters for analysis
    """
    engine.add_filter(Filter(
        name='France',
        formula='["Country"=1]',
        with_na=False
    ))
    
    engine.add_filter(Filter(
        name='Cardiologists',
        formula='["Specialty"=1]',
        with_na=False
    ))
    
    engine.add_filter(Filter(
        name='Senior',
        formula='["Experience">=15]',
        with_na=False
    ))
    
    engine.add_filter(Filter(
        name='HighSat',
        formula='["Q1_Satisfaction">=4]',
        with_na=False
    ))


def setup_classes(engine: ClassEngine):
    """
    Define classes for numeric binning
    """
    engine.add_class(Class(
        name='Score10to7',
        bins=[
            ('X>=1 and X<4', 'Low [1-3]'),
            ('X>=4 and X<7', 'Medium [4-6]'),
            ('X>=7 and X<9', 'Good [7-8]'),
            ('X>=9 and X<=10', 'Excellent [9-10]')
        ]
    ))
    
    engine.add_class(Class(
        name='PatientGroups',
        bins=[
            ('X<50', '<50'),
            ('X>=50 and X<100', '50-99'),
            ('X>=100 and X<150', '100-149'),
            ('X>=150', '150+')
        ]
    ))


def main():
    """
    Run the complete STAATS pipeline
    """
    print("=" * 80)
    print("🚀 STAATS PYTHON - COMPLETE DEMO")
    print("=" * 80)
    
    # Step 1: Create data
    print("\n📊 Step 1: Creating sample survey data...")
    df = create_sample_data()
    print(f"   Created {len(df)} respondents")
    print(f"   Columns: {list(df.columns)}")
    
    # Step 2: Setup datamap
    print("\n🗺️  Step 2: Setting up datamap...")
    datamap = setup_datamap()
    print(f"   Defined {len(datamap)} variables")
    
    # Validate data against datamap
    print("\n✅ Step 3: Validating data...")
    errors = datamap.validate_dataframe(df)
    if errors:
        print(f"   ❌ Validation errors found:")
        for error in errors:
            print(f"      - {error}")
        return
    else:
        print("   ✅ Data validation passed!")
    
    # Step 4: Setup and calculate recodes
    print("\n🔄 Step 4: Setting up recodes...")
    recode_engine = RecodeEngine()
    setup_recodes(recode_engine)
    print(f"   Defined {len(recode_engine)} recodes")
    
    print("\n   Validating recodes...")
    errors = recode_engine.validate(datamap)
    if errors:
        print(f"   ❌ Recode validation errors:")
        for error in errors:
            print(f"      - {error}")
        return
    else:
        print("   ✅ Recode validation passed!")
    
    print("\n   Calculating recodes...")
    df = recode_engine.calculate_all(df, datamap)
    print(f"   ✅ Recodes calculated! DataFrame now has {len(df.columns)} columns")
    
    # Step 5: Setup filters
    print("\n🎯 Step 5: Setting up filters...")
    filter_engine = FilterEngine()
    setup_filters(filter_engine)
    print(f"   Defined {len(filter_engine)} filters")
    
    errors = filter_engine.validate(datamap)
    if errors:
        print(f"   ❌ Filter validation errors:")
        for error in errors:
            print(f"      - {error}")
    else:
        print("   ✅ Filter validation passed!")
    
    # Step 6: Setup classes
    print("\n📐 Step 6: Setting up classes...")
    class_engine = ClassEngine()
    setup_classes(class_engine)
    print(f"   Defined {len(class_engine)} classes")
    
    errors = class_engine.validate()
    if errors:
        print(f"   ❌ Class validation errors:")
        for error in errors:
            print(f"      - {error}")
    else:
        print("   ✅ Class validation passed!")
    
    # Step 7: Show results
    print("\n" + "=" * 80)
    print("📈 RESULTS PREVIEW")
    print("=" * 80)
    
    print("\n🔹 Sample of original + recoded data:")
    display_cols = ['Country', 'Age', 'AgeGroup', 'Experience', 'ExpLevel', 
                    'Q1_Satisfaction', 'Sat_Top2', 'Q3_Brands', 'Q3_BrandsCount', 'BrandAwareness']
    print(df[display_cols].head(10).to_string())
    
    print("\n🔹 Recoded variable summary:")
    print(f"   AgeGroup distribution:")
    print(df['AgeGroup'].value_counts().sort_index())
    
    print(f"\n   Brand Awareness distribution:")
    print(df['BrandAwareness'].value_counts().sort_index())
    
    print(f"\n   Satisfaction Top2 distribution:")
    print(df['Sat_Top2'].value_counts().sort_index())
    
    # Test filters
    print("\n🔹 Filter results:")
    france_mask = filter_engine.apply_filter(df, 'France', datamap)
    print(f"   France: {france_mask.sum()} respondents ({france_mask.sum()/len(df)*100:.1f}%)")
    
    cardio_mask = filter_engine.apply_filter(df, 'Cardiologists', datamap)
    print(f"   Cardiologists: {cardio_mask.sum()} respondents ({cardio_mask.sum()/len(df)*100:.1f}%)")
    
    # Test classes
    print("\n🔹 Class binning:")
    df['Q6_Binned'] = class_engine.apply_class(df['Q6_Score'], 'Score10to7')
    print("   Score binning distribution:")
    print(df['Q6_Binned'].value_counts())
    
    # Simple cross-tab example
    print("\n🔹 Simple cross-tabulation (Country × Satisfaction):")
    crosstab = pd.crosstab(
        df['Country'].map(datamap.get_question('Country').codes),
        df['Sat_Top2'].map(datamap.get_question('Sat_Top2').codes),
        margins=True,
        normalize='index'
    )
    print((crosstab * 100).round(1))
    
    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)
    print("\n🎯 What we demonstrated:")
    print("   ✓ Data loading and validation")
    print("   ✓ Datamap definition (paramétrage)")
    print("   ✓ Multiple recode types (quali unique, numeric, count, weight)")
    print("   ✓ Filter definition and application")
    print("   ✓ Class binning for numeric variables")
    print("   ✓ Basic cross-tabulation")
    print("\n🚀 Next steps:")
    print("   - Build Tab Engine for full cross-tab generation")
    print("   - Add Excel export with formatting")
    print("   - Add significance testing")
    print("   - Build sub-base handler")
    print("   - Create JSON config import/export")
    print()


if __name__ == "__main__":
    main()
