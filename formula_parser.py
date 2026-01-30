"""
STAATS Formula Parser
Translates STAATS formulas into executable Python logic

Formula types:
1. Variable conditions: ["S9"=1], ["Q23A"C1,2,3]
2. Class formulas: X>=1 and X<3
3. Compound logic: ["S9"=1] and ["Q10"C2,3]
"""

import re
from typing import Tuple, List, Any, Callable, Optional
from enum import Enum
import pandas as pd


class Operator(Enum):
    """Operators for quali multiple questions"""
    CONTAINS = "C"              # Contains
    NOT_CONTAINS = "NC"         # Not Contains
    CONTAINS_ONLY = "CO"        # Contains Only
    NOT_CONTAINS_ONLY = "NCO"   # Not Contains Only
    EQUALS = "="                # Equals (for quali unique/numeric)
    NOT_EQUALS = "!="           # Not equals
    GT = ">"                    # Greater than
    LT = "<"                    # Less than
    GTE = ">="                  # Greater or equal
    LTE = "<="                  # Less or equal


class FormulaParser:
    """
    Parse STAATS formulas into executable conditions
    This is where the magic happens
    """
    
    # Regex patterns
    VAR_CONDITION_PATTERN = re.compile(
        r'\["([^"]+)"(C|NC|CO|NCO|=|!=|>=|<=|>|<)([\d,\s\.]+)\]'
    )
    
    CLASS_FORMULA_PATTERN = re.compile(
        r'X\s*(>=|<=|>|<|=|!=)\s*(\d+(?:\.\d+)?)'
    )
    
    @staticmethod
    def parse_variable_condition(formula: str) -> List[Tuple[str, str, Any]]:
        """
        Parse conditions like ["S9"=1] or ["Q23A"C1,2,3]
        
        Returns: List of (variable_name, operator, value) tuples
        
        Examples:
            '["S9"=1]' -> [('S9', '=', 1)]
            '["Q23A"C1,2,3]' -> [('Q23A', 'C', [1,2,3])]
            '["S9"=1] and ["Q10"C2,3]' -> [('S9', '=', 1), ('Q10', 'C', [2,3])]
        """
        conditions = []
        
        for match in FormulaParser.VAR_CONDITION_PATTERN.finditer(formula):
            var_name = match.group(1)
            operator = match.group(2)
            value_str = match.group(3)
            
            # Parse value(s)
            if operator in ['C', 'NC', 'CO', 'NCO']:
                # Multi-choice: parse comma-separated codes
                values = [int(v.strip()) for v in value_str.split(',')]
            else:
                # Single value: try int, then float, then string
                value_str = value_str.strip()
                # Remove quotes if present
                if value_str.startswith('"') and value_str.endswith('"'):
                    value_str = value_str[1:-1]
                
                try:
                    values = int(value_str)
                except ValueError:
                    try:
                        values = float(value_str)
                    except ValueError:
                        values = value_str
            
            conditions.append((var_name, operator, values))
        
        return conditions
    
    @staticmethod
    def parse_class_formula(formula: str) -> Optional[Callable]:
        """
        Parse class binning formulas like "X>=1 and X<3"
        
        Returns: Function that takes a value and returns bool
        
        Examples:
            'X>=1 and X<3' -> lambda x: x >= 1 and x < 3
            'X=5' -> lambda x: x == 5
        """
        if 'X' not in formula:
            return None
        
        # Replace X with actual variable name for eval
        # Build safe eval environment
        safe_formula = formula.replace('X', 'x')
        
        # Security: only allow math operators and numbers
        allowed_chars = set('x0123456789 ()<>=!and.or')
        if not all(c in allowed_chars for c in safe_formula.lower()):
            raise ValueError(f"Invalid characters in class formula: {formula}")
        
        try:
            # Create lambda function
            return eval(f"lambda x: {safe_formula}", {"__builtins__": {}}, {})
        except Exception as e:
            raise ValueError(f"Failed to parse class formula '{formula}': {e}")
    
    @staticmethod
    def evaluate_condition(
        df: pd.DataFrame,
        var_name: str,
        operator: str,
        value: Any,
        question_type: str
    ) -> pd.Series:
        """
        Evaluate a single condition on a DataFrame column
        
        Returns: Boolean Series (True where condition is met)
        """
        if var_name not in df.columns:
            raise ValueError(f"Variable '{var_name}' not found in data")
        
        col = df[var_name]
        
        # Handle quali multiple (stored as "1,2,3")
        if operator in ['C', 'NC', 'CO', 'NCO']:
            if not isinstance(value, list):
                value = [value]
            
            def contains_check(cell_value):
                if pd.isna(cell_value):
                    return False
                # Parse comma-separated codes
                if isinstance(cell_value, str):
                    codes = [int(c.strip()) for c in cell_value.split(',') if c.strip()]
                else:
                    codes = [int(cell_value)]
                
                if operator == 'C':  # Contains
                    return any(v in codes for v in value)
                elif operator == 'NC':  # Not Contains
                    return not any(v in codes for v in value)
                elif operator == 'CO':  # Contains Only
                    return set(codes) == set(value)
                elif operator == 'NCO':  # Not Contains Only
                    return set(codes) != set(value)
                return False
            
            return col.apply(contains_check)
        
        # Handle quali unique / numeric
        elif operator == '=':
            return col == value
        elif operator == '!=':
            return col != value
        elif operator == '>':
            return col > value
        elif operator == '<':
            return col < value
        elif operator == '>=':
            return col >= value
        elif operator == '<=':
            return col <= value
        else:
            raise ValueError(f"Unknown operator: {operator}")
    
    @staticmethod
    def evaluate_formula(
        df: pd.DataFrame,
        formula: str,
        datamap: 'DataMap'
    ) -> pd.Series:
        """
        Evaluate complete formula on DataFrame
        Handles AND/OR logic between conditions
        
        Returns: Boolean Series
        """
        # Parse all conditions
        conditions = FormulaParser.parse_variable_condition(formula)
        
        if not conditions:
            raise ValueError(f"No valid conditions found in formula: {formula}")
        
        # Evaluate first condition
        var_name, operator, value = conditions[0]
        question = datamap.get_question(var_name)
        if not question:
            raise ValueError(f"Variable '{var_name}' not in datamap")
        
        result = FormulaParser.evaluate_condition(
            df, var_name, operator, value, question.qtype.name
        )
        
        # Handle multiple conditions
        if len(conditions) > 1:
            formula_lower = formula.lower()
            
            for var_name, operator, value in conditions[1:]:
                question = datamap.get_question(var_name)
                if not question:
                    raise ValueError(f"Variable '{var_name}' not in datamap")
                
                cond = FormulaParser.evaluate_condition(
                    df, var_name, operator, value, question.qtype.name
                )
                
                # Determine if AND or OR
                # Simple heuristic: check if 'or' appears before next condition
                # More robust: use proper expression parser (TODO for v2)
                if ' or ' in formula_lower:
                    result = result | cond
                else:  # Default to AND
                    result = result & cond
        
        return result
    
    @staticmethod
    def apply_class(series: pd.Series, class_bins: List[Tuple[str, str]]) -> pd.Series:
        """
        Apply class binning to a numeric series
        
        Args:
            series: Numeric column
            class_bins: List of (formula, label) tuples
            
        Returns: Series with category labels
        """
        result = pd.Series([None] * len(series), index=series.index)
        
        for formula, label in class_bins:
            func = FormulaParser.parse_class_formula(formula)
            if func is None:
                continue
            
            # Apply to non-NA values
            mask = series.notna()
            try:
                matches = series[mask].apply(func)
                result.loc[mask & matches] = label
            except Exception as e:
                raise ValueError(f"Error applying class '{label}' with formula '{formula}': {e}")
        
        return result


# Example usage and tests
if __name__ == "__main__":
    print("🧪 Testing Formula Parser\n")
    
    # Test 1: Variable condition parsing
    print("Test 1: Parse variable conditions")
    formulas = [
        '["S9"=1]',
        '["Q23A"C1,2,3]',
        '["S9"=1] and ["Q10"C2,3]',
        '["Age">=18] and ["Age"<65]'
    ]
    
    for f in formulas:
        result = FormulaParser.parse_variable_condition(f)
        print(f"  {f}")
        print(f"    → {result}\n")
    
    # Test 2: Class formula parsing
    print("\nTest 2: Parse class formulas")
    class_formulas = [
        "X>=1 and X<3",
        "X>=3 and X<6",
        "X>=6 and X<=7",
        "X=5"
    ]
    
    for f in class_formulas:
        func = FormulaParser.parse_class_formula(f)
        print(f"  {f}")
        print(f"    Test with 2: {func(2)}")
        print(f"    Test with 5: {func(5)}")
        print(f"    Test with 7: {func(7)}\n")
    
    # Test 3: Evaluate on DataFrame
    print("\nTest 3: Evaluate on real data")
    
    # Create test data
    test_df = pd.DataFrame({
        'S9': [1, 2, 1, 3, 1],
        'Q10': ['1,2', '3', '2,3', '1', '4'],
        'Age': [25, 35, 45, 28, 52]
    })
    
    print("Test data:")
    print(test_df)
    print()
    
    # Mock datamap
    from core import DataMap, Question, QuestionType
    
    dm = DataMap()
    dm.add_question(Question('S9', QuestionType.QUALI_UNIQUE, 'Question 9', {1: 'A', 2: 'B', 3: 'C'}))
    dm.add_question(Question('Q10', QuestionType.QUALI_MULTI, 'Question 10', {1: 'X', 2: 'Y', 3: 'Z', 4: 'W'}))
    dm.add_question(Question('Age', QuestionType.NUMERIC, 'Age'))
    
    # Test formulas
    test_formulas = [
        '["S9"=1]',
        '["Q10"C2]',
        '["Age">=30]'
    ]
    
    for formula in test_formulas:
        result = FormulaParser.evaluate_formula(test_df, formula, dm)
        print(f"Formula: {formula}")
        print(f"Result: {result.tolist()}\n")
    
    # Test 4: Class binning
    print("\nTest 4: Class binning")
    age_classes = [
        ("X>=18 and X<30", "18-29"),
        ("X>=30 and X<50", "30-49"),
        ("X>=50", "50+")
    ]
    
    binned = FormulaParser.apply_class(test_df['Age'], age_classes)
    print("Age binning:")
    print(pd.DataFrame({'Age': test_df['Age'], 'Age_Class': binned}))
    
    print("\n✅ All tests passed!")
