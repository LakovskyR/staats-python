"""
STAATS Python - Core Data Structures
No BS, just clean types that work.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import pandas as pd


class QuestionType(Enum):
    """Question types - the DNA of survey data"""
    QUALI_UNIQUE = "QU"      # Single choice
    QUALI_MULTI = "QM"       # Multiple choice (stored as "1,2,3")
    NUMERIC = "N"            # Numeric value
    OPEN = "O"               # Open text
    
    @classmethod
    def from_string(cls, s: str) -> 'QuestionType':
        """Parse from STAATS notation"""
        mapping = {
            'QU': cls.QUALI_UNIQUE,
            'QM': cls.QUALI_MULTI,
            'N': cls.NUMERIC,
            'O': cls.OPEN,
            'QUALI UNIQUE': cls.QUALI_UNIQUE,
            'QUALI MULTIPLE': cls.QUALI_MULTI,
            'NUMERIC': cls.NUMERIC,
            'OPEN': cls.OPEN,
        }
        return mapping.get(s.upper(), cls.OPEN)


class RecodeType(Enum):
    """Recode transformation types"""
    QUALI_UNIQUE = "quali_unique"
    QUALI_MULTI = "quali_multi"
    NUMERIC = "numeric"
    NUMBER_OF_ANSWERS = "number_of_answers"
    COMBINATION = "combination"
    EXCEL_FORMULA = "excel_formula"
    WEIGHT = "weight"
    QUALI_MULTI_INI = "quali_multi_ini"  # Sub-totals


@dataclass
class Question:
    """
    A survey question definition
    This is what makes STAATS understand your data
    """
    name: str                          # e.g., "Q1"
    qtype: QuestionType               # Question type
    title: str                         # Question label
    codes: Dict[int, str] = field(default_factory=dict)  # {1: "Yes", 2: "No"}
    
    def validate_value(self, value: Any) -> bool:
        """Check if a value is valid for this question type"""
        if pd.isna(value):
            return True
            
        if self.qtype == QuestionType.NUMERIC:
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
                
        elif self.qtype == QuestionType.QUALI_UNIQUE:
            try:
                return int(value) in self.codes
            except (ValueError, TypeError):
                return False
                
        elif self.qtype == QuestionType.QUALI_MULTI:
            # Multi-choice stored as "1,2,3"
            if isinstance(value, str):
                try:
                    codes = [int(c.strip()) for c in value.split(',') if c.strip()]
                    return all(c in self.codes for c in codes)
                except ValueError:
                    return False
            return False
            
        return True  # OPEN type accepts anything
    
    def __repr__(self) -> str:
        return f"Question(name='{self.name}', type={self.qtype.name}, codes={len(self.codes)})"


@dataclass
class DataMap:
    """
    Complete question catalog - the schema of your survey
    This is the single source of truth
    """
    questions: Dict[str, Question] = field(default_factory=dict)
    
    def add_question(self, question: Question):
        """Add a question to the datamap"""
        self.questions[question.name] = question
        
    def get_question(self, name: str) -> Optional[Question]:
        """Get question by name"""
        return self.questions.get(name)
    
    def validate_dataframe(self, df: pd.DataFrame) -> List[str]:
        """
        Validate that DataFrame columns match the datamap
        Returns list of error messages (empty if valid)
        """
        errors = []
        
        # Check for missing columns
        missing = set(self.questions.keys()) - set(df.columns)
        if missing:
            errors.append(f"Missing columns in data: {missing}")
        
        # Check for unexpected columns (just warn)
        extra = set(df.columns) - set(self.questions.keys())
        if extra:
            errors.append(f"Extra columns in data (ignored): {extra}")
        
        # Validate data types for each question
        for name, question in self.questions.items():
            if name not in df.columns:
                continue
                
            # Sample validation on first 100 rows (full validation is slow)
            sample = df[name].head(100)
            invalid_count = sum(1 for val in sample if not question.validate_value(val))
            
            if invalid_count > 0:
                errors.append(
                    f"Column '{name}' has {invalid_count} invalid values "
                    f"(type: {question.qtype.name})"
                )
        
        return errors
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary (for JSON export)"""
        return {
            name: {
                'type': q.qtype.value,
                'title': q.title,
                'codes': q.codes
            }
            for name, q in self.questions.items()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DataMap':
        """Deserialize from dictionary (from JSON)"""
        dm = cls()
        for name, q_data in data.items():
            question = Question(
                name=name,
                qtype=QuestionType(q_data['type']),
                title=q_data['title'],
                codes={int(k): v for k, v in q_data.get('codes', {}).items()}
            )
            dm.add_question(question)
        return dm
    
    def __len__(self) -> int:
        return len(self.questions)
    
    def __repr__(self) -> str:
        return f"DataMap(questions={len(self.questions)})"


@dataclass 
class Filter:
    """
    A conditional filter for subsetting data
    """
    name: str
    formula: str
    with_na: bool = False
    
    def __repr__(self) -> str:
        return f"Filter(name='{self.name}', with_na={self.with_na})"


@dataclass
class Class:
    """
    Numeric binning definition
    Turns continuous numbers into categories
    """
    name: str
    bins: List[tuple[str, str]]  # [(formula, label), ...]
    option_na: bool = False
    
    def __repr__(self) -> str:
        return f"Class(name='{self.name}', bins={len(self.bins)})"


@dataclass
class TabDefinition:
    """
    A single cross-tabulation specification
    Row × Column with optional filters/weights
    """
    title: str
    row_var: str                        # Variable to analyze
    col_var: str                        # Split by this (must be quali)
    second_col_var: Optional[str] = None
    filter_name: Optional[str] = None   # Apply this filter
    weight_var: Optional[str] = None    # Weight by this variable
    class_name: Optional[str] = None    # For numeric row_var
    with_na: str = ""                   # "RowNA/ColNA/SecondcolNA/"
    display: str = "Both"               # Both/Vertical/Horizontal
    
    def has_row_na(self) -> bool:
        return "RowNA" in self.with_na
    
    def has_col_na(self) -> bool:
        return "ColNA" in self.with_na
        
    def has_second_col_na(self) -> bool:
        return "SecondcolNA" in self.with_na
    
    def __repr__(self) -> str:
        return f"TabDefinition('{self.title}': {self.row_var} × {self.col_var})"


@dataclass
class TabSpec:
    """
    A complete tabulation plan - can generate multiple files
    """
    name: str
    files: List[Dict[str, Any]] = field(default_factory=list)
    
    # Each file has:
    # - filename: str
    # - pdt_filter: Optional[str]  
    # - pdt_weight: Optional[str]
    # - tabs: List[TabDefinition]
    
    def __repr__(self) -> str:
        return f"TabSpec(name='{self.name}', files={len(self.files)})"


if __name__ == "__main__":
    # Quick test
    dm = DataMap()
    
    q1 = Question(
        name="Q1",
        qtype=QuestionType.QUALI_UNIQUE,
        title="Do you agree?",
        codes={1: "Yes", 2: "No", 3: "Don't know"}
    )
    
    q2 = Question(
        name="Q2",
        qtype=QuestionType.QUALI_MULTI,
        title="Which brands do you know?",
        codes={1: "Nike", 2: "Adidas", 3: "Puma", 4: "Reebok"}
    )
    
    q3 = Question(
        name="Age",
        qtype=QuestionType.NUMERIC,
        title="Your age"
    )
    
    dm.add_question(q1)
    dm.add_question(q2)
    dm.add_question(q3)
    
    print(dm)
    print(f"Q1: {q1}")
    print(f"Q2: {q2}")
    
    # Test validation
    test_data = pd.DataFrame({
        'Q1': [1, 2, 1, 3, None],
        'Q2': ['1,2', '3', '1,2,4', '2,3', None],
        'Age': [25, 30, 45, 22, 35]
    })
    
    errors = dm.validate_dataframe(test_data)
    print(f"\nValidation: {len(errors)} errors")
    for error in errors:
        print(f"  - {error}")
