"""
STAATS Python - Complete End-to-End Pipeline Demo
Shows the FULL workflow from data → Excel output

This is production-ready code that processes survey data:
1. Load data (CSV/Excel)
2. Define/load configuration (datamap, recodes, filters, classes)
3. Validate data
4. Calculate recodes
5. Generate cross-tabulations
6. Export formatted Excel files
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List

from core import DataMap, Question, QuestionType, TabDefinition, Filter, Class
from formula_parser import FormulaParser
from recode_engine import (
    RecodeEngine, QualiUniqueRecode, NumericRecode,
    NumberOfAnswersRecode, WeightRecode
)
from engines import FilterEngine, ClassEngine
from tab_engine import TabEngine
from excel_export import ExcelExporter


class STAATSPipeline:
    """
    Complete STAATS processing pipeline
    Orchestrates all components
    """
    
    def __init__(self):
        self.datamap = None
        self.data = None
        self.recode_engine = RecodeEngine()
        self.filter_engine = FilterEngine()
        self.class_engine = ClassEngine()
        self.tab_engine = None
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        """Load survey data from CSV or Excel"""
        path = Path(filepath)
        
        if path.suffix == '.csv':
            self.data = pd.read_csv(filepath)
        elif path.suffix in ['.xlsx', '.xls']:
            self.data = pd.read_excel(filepath)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        print(f"✅ Loaded {len(self.data)} respondents from {filepath}")
        return self.data
    
    def set_datamap(self, datamap: DataMap):
        """Set the data structure definition"""
        self.datamap = datamap
        print(f"✅ Datamap set: {len(datamap)} questions defined")
    
    def validate_data(self) -> List[str]:
        """Validate data against datamap"""
        if self.data is None or self.datamap is None:
            raise ValueError("Data and datamap must be loaded first")
        
        errors = self.datamap.validate_dataframe(self.data)
        
        if errors:
            print(f"⚠️  Validation warnings:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✅ Data validation passed")
        
        return errors
    
    def setup_recodes(self, recodes: List):
        """Add recodes to the engine"""
        for recode in recodes:
            self.recode_engine.add_recode(recode)
        print(f"✅ {len(recodes)} recodes configured")
    
    def setup_filters(self, filters: List[Filter]):
        """Add filters to the engine"""
        for filt in filters:
            self.filter_engine.add_filter(filt)
        print(f"✅ {len(filters)} filters configured")
    
    def setup_classes(self, classes: List[Class]):
        """Add classes to the engine"""
        for cls in classes:
            self.class_engine.add_class(cls)
        print(f"✅ {len(classes)} classes configured")
    
    def calculate_recodes(self):
        """Execute all recodes"""
        if self.data is None or self.datamap is None:
            raise ValueError("Data and datamap must be loaded first")
        
        # Validate recodes first
        errors = self.recode_engine.validate(self.datamap)
        if errors:
            print(f"⚠️  Recode validation errors:")
            for error in errors:
                print(f"   - {error}")
            raise ValueError("Recode validation failed")
        
        # Calculate
        self.data = self.recode_engine.calculate_all(self.data, self.datamap)
        print(f"✅ Recodes calculated: DataFrame now has {len(self.data.columns)} columns")
    
    def generate_tabs(self, tab_specs: List[TabDefinition], output_filename: str):
        """Generate cross-tabulations and export to Excel"""
        if self.data is None or self.datamap is None:
            raise ValueError("Data and datamap must be loaded first")
        
        # Create tab engine
        self.tab_engine = TabEngine(
            self.datamap,
            self.filter_engine,
            self.class_engine
        )
        
        # Generate tabs
        print(f"🔄 Generating {len(tab_specs)} cross-tabulations...")
        results = self.tab_engine.generate_multiple_tabs(self.data, tab_specs)
        
        # Export to Excel
        exporter = ExcelExporter(output_dir="output")
        filepath = exporter.export_multiple_tabs(
            results,
            filename=output_filename,
            display_mode='Both',
            create_summary=True
        )
        
        print(f"✅ Excel file created: {filepath}")
        return filepath
    
    def run_full_pipeline(
        self,
        data_path: str,
        output_filename: str,
        datamap: DataMap,
        recodes: List = None,
        filters: List[Filter] = None,
        classes: List[Class] = None,
        tab_specs: List[TabDefinition] = None
    ):
        """
        Execute complete pipeline in one call
        """
        print("=" * 80)
        print("🚀 STAATS PYTHON - FULL PIPELINE EXECUTION")
        print("=" * 80)
        
        # Step 1: Load data
        print("\n📊 Step 1: Loading data...")
        self.load_data(data_path)
        
        # Step 2: Set datamap
        print("\n🗺️  Step 2: Setting datamap...")
        self.set_datamap(datamap)
        
        # Step 3: Validate
        print("\n✅ Step 3: Validating data...")
        self.validate_data()
        
        # Step 4: Setup recodes
        if recodes:
            print("\n🔄 Step 4: Setting up recodes...")
            self.setup_recodes(recodes)
            
            print("\n   Calculating recodes...")
            self.calculate_recodes()
        
        # Step 5: Setup filters
        if filters:
            print("\n🎯 Step 5: Setting up filters...")
            self.setup_filters(filters)
        
        # Step 6: Setup classes
        if classes:
            print("\n📐 Step 6: Setting up classes...")
            self.setup_classes(classes)
        
        # Step 7: Generate tabs
        if tab_specs:
            print("\n📊 Step 7: Generating tabulations...")
            filepath = self.generate_tabs(tab_specs, output_filename)
        
        print("\n" + "=" * 80)
        print("✅ PIPELINE COMPLETE!")
        print("=" * 80)
        
        return filepath


def create_complete_demo():
    """
    Complete working demonstration
    Creates realistic survey, defines everything, produces Excel output
    """
    
    # Create realistic survey data
    print("Creating sample healthcare professional survey...")
    np.random.seed(42)
    n = 300
    
    data = pd.DataFrame({
        'ID': range(1, n + 1),
        'Country': np.random.choice([1, 2, 3], n, p=[0.5, 0.3, 0.2]),
        'Specialty': np.random.choice([1, 2, 3, 4], n, p=[0.4, 0.3, 0.2, 0.1]),
        'Age': np.random.randint(28, 68, n),
        'Experience': np.random.randint(1, 40, n),
        'Q1_Satisfaction': np.random.choice([1, 2, 3, 4, 5], n),
        'Q2_Recommend': np.random.choice([1, 2, 3], n),
        'Q3_Brands': [
            ','.join(map(str, sorted(np.random.choice([1, 2, 3, 4, 5], 
                         size=np.random.randint(0, 4), replace=False))))
            if np.random.rand() > 0.1 else None
            for _ in range(n)
        ],
        'Q5_Patients': np.random.randint(10, 200, n),
        'Q6_Score': np.random.randint(1, 11, n),
    })
    
    # Save to CSV
    data.to_csv('output/sample_survey_data.csv', index=False)
    print(f"✅ Created {len(data)} survey responses → output/sample_survey_data.csv")
    
    # Define datamap
    dm = DataMap()
    dm.add_question(Question('ID', QuestionType.NUMERIC, 'Respondent ID'))
    dm.add_question(Question('Country', QuestionType.QUALI_UNIQUE, 'Country', {
        1: 'France', 2: 'UK', 3: 'Germany'
    }))
    dm.add_question(Question('Specialty', QuestionType.QUALI_UNIQUE, 'Medical Specialty', {
        1: 'Cardiology', 2: 'Dermatology', 3: 'Oncology', 4: 'Other'
    }))
    dm.add_question(Question('Age', QuestionType.NUMERIC, 'Age'))
    dm.add_question(Question('Experience', QuestionType.NUMERIC, 'Years of Experience'))
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
    dm.add_question(Question('Q5_Patients', QuestionType.NUMERIC, 'Number of Patients per Month'))
    dm.add_question(Question('Q6_Score', QuestionType.NUMERIC, 'Product Score (1-10)'))
    
    # Define recodes
    recodes = [
        QualiUniqueRecode(
            'AgeGroup', 'Age Groups',
            '1: ["Age">=28] and ["Age"<40]\n2: ["Age">=40] and ["Age"<55]\n3: ["Age">=55]',
            {1: 'Under 40', 2: '40-54', 3: '55+'}
        ),
        QualiUniqueRecode(
            'ExpLevel', 'Experience Level',
            '1: ["Experience"<5]\n2: ["Experience">=5] and ["Experience"<15]\n3: ["Experience">=15]',
            {1: 'Junior (<5y)', 2: 'Mid (5-15y)', 3: 'Senior (15y+)'}
        ),
        QualiUniqueRecode(
            'Sat_Top2', 'Satisfaction Top 2 Box',
            '1: ["Q1_Satisfaction">=4]\n2: ["Q1_Satisfaction"<4]',
            {1: 'Satisfied (4-5)', 2: 'Not satisfied (1-3)'}
        ),
        NumberOfAnswersRecode(
            'Q3_BrandsCount', 'Number of Brands Known', '["Q3_Brands"]'
        ),
        QualiUniqueRecode(
            'PatientVolume', 'Patient Volume',
            '1: ["Q5_Patients"<50]\n2: ["Q5_Patients">=50] and ["Q5_Patients"<100]\n3: ["Q5_Patients">=100]',
            {1: 'Low (<50)', 2: 'Medium (50-99)', 3: 'High (100+)'}
        ),
        WeightRecode(
            'CountryWeight', 'Country Weighting', '',
            {'["Country"=1]': 1.0, '["Country"=2]': 0.8, '["Country"=3]': 1.2}
        ),
    ]
    
    # Define filters
    filters = [
        Filter('France', '["Country"=1]'),
        Filter('Cardiologists', '["Specialty"=1]'),
        Filter('Senior', '["Experience">=15]'),
        Filter('HighSat', '["Q1_Satisfaction">=4]'),
    ]
    
    # Define classes
    classes = [
        Class('Score10', [
            ('X>=1 and X<4', 'Low [1-3]'),
            ('X>=4 and X<7', 'Medium [4-6]'),
            ('X>=7 and X<9', 'Good [7-8]'),
            ('X>=9 and X<=10', 'Excellent [9-10]')
        ]),
        Class('AgeGroups', [
            ('X>=28 and X<40', 'Under 40'),
            ('X>=40 and X<55', '40-54'),
            ('X>=55', '55+')
        ]),
    ]
    
    # Define tab specifications
    tab_specs = [
        TabDefinition('Q1: Satisfaction by Country', 'Q1_Satisfaction', 'Country'),
        TabDefinition('Q2: Recommend by Country', 'Q2_Recommend', 'Country'),
        TabDefinition('Age Groups by Country', 'Age', 'Country', class_name='AgeGroups'),
        TabDefinition('Satisfaction by Specialty', 'Q1_Satisfaction', 'Specialty'),
        TabDefinition('Patient Volume by Country', 'PatientVolume', 'Country'),
        TabDefinition('Product Score by Country', 'Q6_Score', 'Country', class_name='Score10'),
        TabDefinition('Sat Top2 by Specialty', 'Sat_Top2', 'Specialty'),
        TabDefinition('Experience Level by Country', 'ExpLevel', 'Country'),
    ]
    
    # Run pipeline
    pipeline = STAATSPipeline()
    
    filepath = pipeline.run_full_pipeline(
        data_path='output/sample_survey_data.csv',
        output_filename='healthcare_professional_survey.xlsx',
        datamap=dm,
        recodes=recodes,
        filters=filters,
        classes=classes,
        tab_specs=tab_specs
    )
    
    return filepath


if __name__ == "__main__":
    from pathlib import Path
    
    # Ensure output directory exists
    Path('output').mkdir(exist_ok=True)
    
    print("\n" + "=" * 80)
    print("STAATS PYTHON - COMPLETE END-TO-END DEMONSTRATION")
    print("=" * 80)
    print("\nThis demo will:")
    print("  1. Create 300 synthetic survey responses")
    print("  2. Define complete data structure (datamap)")
    print("  3. Create 6 recoded variables")
    print("  4. Define 4 filters and 2 classes")
    print("  5. Generate 8 cross-tabulations")
    print("  6. Export professionally formatted Excel file")
    print("\n" + "=" * 80 + "\n")
    
    try:
        filepath = create_complete_demo()
        
        print(f"\n🎉 SUCCESS! Professional survey analysis generated.")
        print(f"\n📁 Output file: {filepath}")
        print(f"\nOpen this file to see:")
        print(f"  • Summary sheet with table of contents")
        print(f"  • 8 cross-tabulation sheets")
        print(f"  • Professional formatting & styling")
        print(f"  • Significance testing markers")
        print(f"  • Base counts for each column")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
