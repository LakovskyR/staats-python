"""
STAATS Recode Engine
Transforms variables - the muscle of the system

Handles all recode types:
- Quali Unique: QM→QU, QU→QU, N→QU
- Quali Multiple: QM→QM, QU→QM
- Numeric: calculations
- Number of Answers: count multi-choice responses
- Combination: QM→QU with unique codes per combination
- Weight: redressement/weighting
- Quali Multi INI: sub-totals
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from core import DataMap, Question, QuestionType, RecodeType
from formula_parser import FormulaParser


@dataclass
class Recode(ABC):
    """Base class for all recode types"""
    name: str
    rtype: RecodeType
    title: str
    formula: str
    option_na: bool = False
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame, datamap: DataMap) -> pd.Series:
        """
        Calculate the recode on a DataFrame
        Returns: Series with recoded values
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', formula='{self.formula}')"


class QualiUniqueRecode(Recode):
    """
    Quali Unique recode - creates single-choice variable
    
    Examples:
    1. From QU: ["S9"=1]→1, ["S9"=2]→2
    2. From QM: ["Q23A"C1]→1, ["Q23A"C2,3]→2
    3. From N: ["Age">=18 and "Age"<30]→1, ["Age">=30]→2
    """
    
    codes: Dict[int, str]  # Code table
    
    def __init__(self, name: str, title: str, formula: str, codes: Dict[int, str], option_na: bool = False):
        super().__init__(name, RecodeType.QUALI_UNIQUE, title, formula, option_na)
        self.codes = codes
    
    def calculate(self, df: pd.DataFrame, datamap: DataMap) -> pd.Series:
        """
        Parse formula like:
        1: ["S9"=1]
        2: ["S9"=2] 
        3: ["S9"=3]
        
        Or:
        1: ["Q23A"C1]
        2: ["Q23A"C2,3]
        """
        result = pd.Series([None] * len(df), index=df.index, dtype='Int64')
        
        # Parse formula lines
        lines = [line.strip() for line in self.formula.split('\n') if line.strip()]
        
        for line in lines:
            # Format: "code: condition" or just "condition"
            if ':' in line:
                code_str, condition = line.split(':', 1)
                code = int(code_str.strip())
                condition = condition.strip()
            else:
                # Extract code from condition if possible
                # This is a fallback - proper format should have explicit codes
                continue
            
            # Evaluate condition
            try:
                mask = FormulaParser.evaluate_formula(df, condition, datamap)
                result.loc[mask] = code
            except Exception as e:
                raise ValueError(f"Error evaluating recode '{self.name}', line '{line}': {e}")
        
        return result


class QualiMultipleRecode(Recode):
    """
    Quali Multiple recode - creates multi-choice variable
    
    Examples:
    1. From QM: ["Q23A"C1]→1, ["Q23A"C2]→2 (can select both)
    2. From QU+N: ["Country"=1] and ["Sales">1000]→1
    
    Result stored as "1,2,3" format
    """
    
    codes: Dict[int, str]
    
    def __init__(self, name: str, title: str, formula: str, codes: Dict[int, str], option_na: bool = False):
        super().__init__(name, RecodeType.QUALI_MULTI, title, formula, option_na)
        self.codes = codes
    
    def calculate(self, df: pd.DataFrame, datamap: DataMap) -> pd.Series:
        """
        Each line represents one possible answer
        Multiple can be true simultaneously
        """
        # Track which codes apply to each row
        selections = {idx: [] for idx in df.index}
        
        # Parse formula lines
        lines = [line.strip() for line in self.formula.split('\n') if line.strip()]
        
        for line in lines:
            if ':' in line:
                code_str, condition = line.split(':', 1)
                code = int(code_str.strip())
                condition = condition.strip()
            else:
                continue
            
            try:
                mask = FormulaParser.evaluate_formula(df, condition, datamap)
                # Add this code to all matching rows
                for idx in df.index[mask]:
                    if code not in selections[idx]:
                        selections[idx].append(code)
            except Exception as e:
                raise ValueError(f"Error evaluating recode '{self.name}', line '{line}': {e}")
        
        # Convert to "1,2,3" format
        result = pd.Series([None] * len(df), index=df.index, dtype='object')
        for idx, codes in selections.items():
            if codes:
                result.loc[idx] = ','.join(map(str, sorted(codes)))
        
        return result


class NumericRecode(Recode):
    """
    Numeric recode - arithmetic operations
    
    Examples:
    - ["Sales"] * 1.2 (increase by 20%)
    - ["Price1"] + ["Price2"]
    - ["Score"] / 10
    """
    
    def calculate(self, df: pd.DataFrame, datamap: DataMap) -> pd.Series:
        """
        Evaluate numeric expression
        """
        # Parse variable references
        formula = self.formula
        
        # Replace variable references with df column access
        # ["VarName"] → df['VarName']
        var_pattern = re.compile(r'\["([^"]+)"\]')
        
        for match in var_pattern.finditer(formula):
            var_name = match.group(1)
            if var_name not in df.columns:
                raise ValueError(f"Variable '{var_name}' not found in data")
        
        # Build safe eval expression
        formula_eval = var_pattern.sub(lambda m: f"df['{m.group(1)}']", formula)
        
        try:
            # Use pandas eval for safety and performance
            result = pd.eval(formula_eval, local_dict={'df': df})
            return pd.Series(result, index=df.index)
        except Exception as e:
            raise ValueError(f"Error evaluating numeric recode '{self.name}': {e}")


class NumberOfAnswersRecode(Recode):
    """
    Count number of responses in a quali multiple variable
    
    Example:
    Formula: ["Q23A"]
    Result: Q23A="1,2,3" → 3, Q23A="1" → 1, Q23A=None → 0
    """
    
    def __init__(self, name: str, title: str, formula: str, option_na: bool = False):
        super().__init__(name, RecodeType.NUMBER_OF_ANSWERS, title, formula, option_na)
    
    def calculate(self, df: pd.DataFrame, datamap: DataMap) -> pd.Series:
        """
        Count comma-separated codes
        """
        import re
        
        # Extract variable name from formula
        var_pattern = re.compile(r'\["([^"]+)"\]')
        match = var_pattern.search(self.formula)
        
        if not match:
            raise ValueError(f"Could not parse variable from formula: {self.formula}")
        
        var_name = match.group(1)
        
        if var_name not in df.columns:
            raise ValueError(f"Variable '{var_name}' not found in data")
        
        def count_answers(value):
            if pd.isna(value):
                return 0
            if isinstance(value, str):
                codes = [c.strip() for c in value.split(',') if c.strip()]
                return len(codes)
            return 0 if pd.isna(value) else 1
        
        return df[var_name].apply(count_answers)


class CombinationRecode(Recode):
    """
    Transform QM→QU by creating unique code for each combination
    
    Example:
    Q23A="1" → 1
    Q23A="2" → 2
    Q23A="1,2" → 3
    Q23A="1,3" → 4
    etc.
    
    Codes are assigned dynamically based on observed combinations
    """
    
    def __init__(self, name: str, title: str, formula: str, option_na: bool = False):
        super().__init__(name, RecodeType.COMBINATION, title, formula, option_na)
    
    def calculate(self, df: pd.DataFrame, datamap: DataMap) -> pd.Series:
        """
        Assign unique code to each unique combination
        """
        import re
        
        # Extract variable name
        var_pattern = re.compile(r'\["([^"]+)"\]')
        match = var_pattern.search(self.formula)
        
        if not match:
            raise ValueError(f"Could not parse variable from formula: {self.formula}")
        
        var_name = match.group(1)
        
        if var_name not in df.columns:
            raise ValueError(f"Variable '{var_name}' not found in data")
        
        col = df[var_name]
        
        # Find unique combinations
        unique_combos = col.dropna().unique()
        
        # Create mapping: combination → code
        combo_to_code = {combo: idx + 1 for idx, combo in enumerate(sorted(unique_combos))}
        
        # Apply mapping
        result = col.map(combo_to_code)
        
        # Store the mapping for reference (useful for labeling)
        self.combo_codes = combo_to_code
        
        return result


class WeightRecode(Recode):
    """
    Weighting/Redressement variable
    
    Example:
    ["Country"=1] → 0.62
    ["Country"=2] → 1.36
    ["Country"=3] → 1.54
    """
    
    weights: Dict[str, float]  # condition → weight
    
    def __init__(self, name: str, title: str, formula: str, weights: Dict[str, float], option_na: bool = False):
        super().__init__(name, RecodeType.WEIGHT, title, formula, option_na)
        self.weights = weights
    
    def calculate(self, df: pd.DataFrame, datamap: DataMap) -> pd.Series:
        """
        Apply weights based on conditions
        """
        result = pd.Series([1.0] * len(df), index=df.index, dtype=float)
        
        for condition, weight in self.weights.items():
            try:
                mask = FormulaParser.evaluate_formula(df, condition, datamap)
                result.loc[mask] = weight
            except Exception as e:
                raise ValueError(f"Error applying weight condition '{condition}': {e}")
        
        return result


class QualiMultiINIRecode(Recode):
    """
    Quali Multiple with sub-totals (INI = initialization)
    
    Example:
    Formula includes original variable codes PLUS sub-total definitions
    
    Q23A original codes: 1,2,3,4,5
    Sub-totals:
    - ST1 (codes 1,2) → 101
    - ST2 (codes 3,4,5) → 102
    
    Result can include: 1,2,101 (codes 1,2 AND their sub-total)
    """
    
    codes: Dict[int, str]
    subtotals: Dict[int, List[int]]  # ST code → list of original codes
    
    def __init__(self, name: str, title: str, formula: str, codes: Dict[int, str], 
                 subtotals: Dict[int, List[int]], option_na: bool = False):
        super().__init__(name, RecodeType.QUALI_MULTI_INI, title, formula, option_na)
        self.codes = codes
        self.subtotals = subtotals
    
    def calculate(self, df: pd.DataFrame, datamap: DataMap) -> pd.Series:
        """
        Add sub-total codes to existing responses
        """
        import re
        
        # Extract source variable
        var_pattern = re.compile(r'\["([^"]+)"\]')
        match = var_pattern.search(self.formula)
        
        if not match:
            raise ValueError(f"Could not parse variable from formula: {self.formula}")
        
        var_name = match.group(1)
        
        if var_name not in df.columns:
            raise ValueError(f"Variable '{var_name}' not found in data")
        
        def add_subtotals(value):
            if pd.isna(value):
                return None
            
            # Parse existing codes
            if isinstance(value, str):
                codes = [int(c.strip()) for c in value.split(',') if c.strip()]
            else:
                codes = [int(value)]
            
            result_codes = codes.copy()
            
            # Add applicable sub-totals
            for st_code, st_members in self.subtotals.items():
                # If any member of ST is selected, add ST code
                if any(c in codes for c in st_members):
                    if st_code not in result_codes:
                        result_codes.append(st_code)
            
            return ','.join(map(str, sorted(result_codes)))
        
        return df[var_name].apply(add_subtotals)


class RecodeEngine:
    """
    Orchestrates all recodes
    Validates, calculates, and manages the recode pipeline
    """
    
    def __init__(self):
        self.recodes: List[Recode] = []
    
    def add_recode(self, recode: Recode):
        """Add a recode to the engine"""
        self.recodes.append(recode)
    
    def validate(self, datamap: DataMap) -> List[str]:
        """
        Validate all recodes
        Returns: List of error messages
        """
        errors = []
        
        # Check for duplicate names
        names = [r.name for r in self.recodes]
        duplicates = [name for name in names if names.count(name) > 1]
        if duplicates:
            errors.append(f"Duplicate recode names: {set(duplicates)}")
        
        # Check that formulas reference valid variables
        for recode in self.recodes:
            # Extract variable references from formula
            import re
            var_pattern = re.compile(r'\["([^"]+)"\]')
            variables = var_pattern.findall(recode.formula)
            
            for var in variables:
                if not datamap.get_question(var):
                    errors.append(
                        f"Recode '{recode.name}': variable '{var}' not in datamap"
                    )
        
        return errors
    
    def calculate_all(self, df: pd.DataFrame, datamap: DataMap) -> pd.DataFrame:
        """
        Calculate all recodes and append to DataFrame
        
        IMPORTANT: Recodes are calculated in order and added sequentially
        Later recodes can reference earlier recodes
        """
        result_df = df.copy()
        
        for recode in self.recodes:
            try:
                # Calculate recode
                recode_values = recode.calculate(result_df, datamap)
                
                # Add to dataframe
                result_df[recode.name] = recode_values
                
                # Add to datamap
                if isinstance(recode, QualiUniqueRecode):
                    qtype = QuestionType.QUALI_UNIQUE
                    codes = recode.codes
                elif isinstance(recode, QualiMultipleRecode) or isinstance(recode, QualiMultiINIRecode):
                    qtype = QuestionType.QUALI_MULTI
                    codes = recode.codes
                elif isinstance(recode, NumericRecode) or isinstance(recode, NumberOfAnswersRecode) or isinstance(recode, WeightRecode):
                    qtype = QuestionType.NUMERIC
                    codes = {}
                else:
                    qtype = QuestionType.NUMERIC
                    codes = {}
                
                datamap.add_question(Question(
                    name=recode.name,
                    qtype=qtype,
                    title=recode.title,
                    codes=codes
                ))
                
            except Exception as e:
                raise ValueError(f"Error calculating recode '{recode.name}': {e}")
        
        return result_df
    
    def __len__(self) -> int:
        return len(self.recodes)
    
    def __repr__(self) -> str:
        return f"RecodeEngine(recodes={len(self.recodes)})"


# Example usage
if __name__ == "__main__":
    import re
    from core import DataMap, Question, QuestionType
    
    print("🧪 Testing Recode Engine\n")
    
    # Setup test data
    df = pd.DataFrame({
        'S9': [1, 2, 1, 3, 1, 2],
        'Q23A': ['1,2', '3', '1,2,4', '2,3', None, '1'],
        'Age': [25, 35, 45, 28, 52, 19],
        'Country': [1, 2, 1, 3, 2, 1]
    })
    
    dm = DataMap()
    dm.add_question(Question('S9', QuestionType.QUALI_UNIQUE, 'Q9', {1: 'A', 2: 'B', 3: 'C'}))
    dm.add_question(Question('Q23A', QuestionType.QUALI_MULTI, 'Q23', {1: 'Brand1', 2: 'Brand2', 3: 'Brand3', 4: 'Brand4'}))
    dm.add_question(Question('Age', QuestionType.NUMERIC, 'Age'))
    dm.add_question(Question('Country', QuestionType.QUALI_UNIQUE, 'Country', {1: 'FR', 2: 'UK', 3: 'DE'}))
    
    engine = RecodeEngine()
    
    # Test 1: Number of Answers
    print("Test 1: Number of Answers")
    recode1 = NumberOfAnswersRecode(
        name='Q23A_Count',
        title='Number of brands selected',
        formula='["Q23A"]'
    )
    engine.add_recode(recode1)
    
    # Test 2: Age groups
    print("\nTest 2: Quali Unique from Numeric")
    recode2 = QualiUniqueRecode(
        name='AgeGroup',
        title='Age groups',
        formula='1: ["Age">=18] and ["Age"<30]\n2: ["Age">=30] and ["Age"<50]\n3: ["Age">=50]',
        codes={1: '18-29', 2: '30-49', 3: '50+'}
    )
    engine.add_recode(recode2)
    
    # Test 3: Weight
    print("\nTest 3: Weighting")
    recode3 = WeightRecode(
        name='CountryWeight',
        title='Country weighting',
        formula='',
        weights={
            '["Country"=1]': 0.62,
            '["Country"=2]': 1.36,
            '["Country"=3]': 1.54
        }
    )
    engine.add_recode(recode3)
    
    # Validate
    print("\n📋 Validating...")
    errors = engine.validate(dm)
    if errors:
        print(f"❌ Validation errors: {errors}")
    else:
        print("✅ Validation passed")
    
    # Calculate
    print("\n🔄 Calculating recodes...")
    result = engine.calculate_all(df, dm)
    
    print("\n📊 Results:")
    print(result[['Q23A', 'Q23A_Count', 'Age', 'AgeGroup', 'Country', 'CountryWeight']])
    
    print("\n✅ Recode Engine test complete!")
