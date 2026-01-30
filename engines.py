"""
STAATS Filter & Class Engines
Filter: Subset data based on conditions
Class: Bin numeric variables into categories
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd

from core import DataMap, Filter, Class
from formula_parser import FormulaParser


class FilterEngine:
    """
    Manages filters for subsetting data
    Filters are reusable conditions that can be applied in tabulations
    """
    
    def __init__(self):
        self.filters: Dict[str, Filter] = {}
    
    def add_filter(self, filter_obj: Filter):
        """Add a filter"""
        self.filters[filter_obj.name] = filter_obj
    
    def get_filter(self, name: str) -> Optional[Filter]:
        """Get filter by name"""
        return self.filters.get(name)
    
    def apply_filter(
        self,
        df: pd.DataFrame,
        filter_name: str,
        datamap: DataMap
    ) -> pd.Series:
        """
        Apply a filter to DataFrame
        Returns: Boolean Series (True for rows that pass filter)
        """
        if filter_name not in self.filters:
            raise ValueError(f"Filter '{filter_name}' not found")
        
        filter_obj = self.filters[filter_name]
        
        try:
            return FormulaParser.evaluate_formula(df, filter_obj.formula, datamap)
        except Exception as e:
            raise ValueError(f"Error applying filter '{filter_name}': {e}")
    
    def validate(self, datamap: DataMap) -> List[str]:
        """
        Validate all filters
        Returns: List of error messages
        """
        errors = []
        
        for name, filter_obj in self.filters.items():
            # Try to parse formula
            try:
                FormulaParser.parse_variable_condition(filter_obj.formula)
            except Exception as e:
                errors.append(f"Filter '{name}': {e}")
        
        return errors
    
    def test(self, df: pd.DataFrame, datamap: DataMap) -> pd.DataFrame:
        """
        Test all filters on DataFrame
        Returns: DataFrame with filter results as columns
        """
        result = df.copy()
        
        for name, filter_obj in self.filters.items():
            try:
                result[f'FILTER_{name}'] = self.apply_filter(df, name, datamap)
            except Exception as e:
                result[f'FILTER_{name}'] = None
                print(f"Error testing filter '{name}': {e}")
        
        return result
    
    def __len__(self) -> int:
        return len(self.filters)
    
    def __repr__(self) -> str:
        return f"FilterEngine(filters={len(self.filters)})"


class ClassEngine:
    """
    Manages classes for binning numeric variables
    Classes define how to group continuous numbers into categories
    """
    
    def __init__(self):
        self.classes: Dict[str, Class] = {}
    
    def add_class(self, class_obj: Class):
        """Add a class"""
        self.classes[class_obj.name] = class_obj
    
    def get_class(self, name: str) -> Optional[Class]:
        """Get class by name"""
        return self.classes.get(name)
    
    def apply_class(
        self,
        series: pd.Series,
        class_name: str
    ) -> pd.Series:
        """
        Apply class binning to a numeric series
        Returns: Series with category labels
        """
        if class_name not in self.classes:
            raise ValueError(f"Class '{class_name}' not found")
        
        class_obj = self.classes[class_name]
        
        try:
            return FormulaParser.apply_class(series, class_obj.bins)
        except Exception as e:
            raise ValueError(f"Error applying class '{class_name}': {e}")
    
    def validate(self) -> List[str]:
        """
        Validate all classes
        Returns: List of error messages
        """
        errors = []
        
        for name, class_obj in self.classes.items():
            # Test that formulas can be parsed
            for formula, label in class_obj.bins:
                try:
                    FormulaParser.parse_class_formula(formula)
                except Exception as e:
                    errors.append(f"Class '{name}', bin '{label}': {e}")
        
        return errors
    
    def __len__(self) -> int:
        return len(self.classes)
    
    def __repr__(self) -> str:
        return f"ClassEngine(classes={len(self.classes)})"


# Example usage
if __name__ == "__main__":
    from core import DataMap, Question, QuestionType
    import pandas as pd
    
    print("🧪 Testing Filter & Class Engines\n")
    
    # Setup
    df = pd.DataFrame({
        'S9': [1, 2, 1, 3, 1, 2],
        'Age': [25, 35, 45, 28, 52, 19],
        'Country': [1, 2, 1, 3, 2, 1]
    })
    
    dm = DataMap()
    dm.add_question(Question('S9', QuestionType.QUALI_UNIQUE, 'Q9', {1: 'A', 2: 'B', 3: 'C'}))
    dm.add_question(Question('Age', QuestionType.NUMERIC, 'Age'))
    dm.add_question(Question('Country', QuestionType.QUALI_UNIQUE, 'Country', {1: 'FR', 2: 'UK', 3: 'DE'}))
    
    # Test FilterEngine
    print("=" * 60)
    print("FILTER ENGINE TEST")
    print("=" * 60)
    
    fe = FilterEngine()
    
    fe.add_filter(Filter(
        name='Young',
        formula='["Age"<30]',
        with_na=False
    ))
    
    fe.add_filter(Filter(
        name='France',
        formula='["Country"=1]',
        with_na=False
    ))
    
    fe.add_filter(Filter(
        name='YoungFrance',
        formula='["Age"<30] and ["Country"=1]',
        with_na=False
    ))
    
    print(f"Filters defined: {len(fe)}")
    
    # Validate
    errors = fe.validate(dm)
    if errors:
        print(f"❌ Validation errors: {errors}")
    else:
        print("✅ Filters validated")
    
    # Test filters
    print("\nTesting filters:")
    test_result = fe.test(df, dm)
    print(test_result[['Age', 'Country', 'FILTER_Young', 'FILTER_France', 'FILTER_YoungFrance']])
    
    # Test ClassEngine
    print("\n" + "=" * 60)
    print("CLASS ENGINE TEST")
    print("=" * 60)
    
    ce = ClassEngine()
    
    ce.add_class(Class(
        name='AgeGroups',
        bins=[
            ('X>=18 and X<30', '18-29'),
            ('X>=30 and X<50', '30-49'),
            ('X>=50', '50+')
        ],
        option_na=False
    ))
    
    ce.add_class(Class(
        name='AgeSimple',
        bins=[
            ('X<30', 'Young'),
            ('X>=30', 'Old')
        ],
        option_na=False
    ))
    
    print(f"Classes defined: {len(ce)}")
    
    # Validate
    errors = ce.validate()
    if errors:
        print(f"❌ Validation errors: {errors}")
    else:
        print("✅ Classes validated")
    
    # Apply classes
    print("\nApplying classes to Age:")
    df['Age_Group'] = ce.apply_class(df['Age'], 'AgeGroups')
    df['Age_Simple'] = ce.apply_class(df['Age'], 'AgeSimple')
    
    print(df[['Age', 'Age_Group', 'Age_Simple']])
    
    print("\n✅ All tests passed!")
