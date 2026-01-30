# STAATS Python - Architecture Blueprint

## 🎯 Core Philosophy
Replace Excel VBA macros with clean, testable Python that runs anywhere - local, Google Colab, Cloud Functions, wherever.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    STAATS Engine                        │
├─────────────────────────────────────────────────────────┤
│  1. DataMapper    - Question definitions & types        │
│  2. RecodeEngine  - Variable transformations            │
│  3. FilterEngine  - Conditional logic                   │
│  4. ClassEngine   - Numeric binning                     │
│  5. TabEngine     - Cross-tabulation generator          │
│  6. SubBaseEngine - Patient/Product loop handler        │
└─────────────────────────────────────────────────────────┘
```

## 📦 Module Breakdown

### 1. **DataMapper** (`datamapper.py`)
**Purpose:** Define question structure - the DNA of your survey

```python
class Question:
    - name: str           # Variable name (e.g., "Q1")
    - type: QuestionType  # QUALI_UNIQUE, QUALI_MULTI, NUMERIC, OPEN
    - title: str          # Question label
    - codes: Dict[int, str]  # Code table {1: "Yes", 2: "No"}
    
class DataMap:
    - questions: Dict[str, Question]
    - validate() -> bool
    - from_sawtooth_print(text: str) -> DataMap
    - from_json(path: str) -> DataMap
```

**Key Logic:**
- Parse Sawtooth "Print Study" format
- Validate question types match data
- Generate schema for pandas DataFrames

---

### 2. **RecodeEngine** (`recode_engine.py`)
**Purpose:** Transform variables - the muscle of STAATS

```python
class Recode(ABC):
    name: str
    formula: str
    option_na: bool
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        pass

class QualiUniqueRecode(Recode):
    # ["S9"=1] -> creates single-choice variable
    
class QualiMultipleRecode(Recode):  
    # ["S7"C1] -> contains logic for multi-choice
    # C = Contains, NC = Not Contains
    # CO = Contains Only, NCO = Not Contains Only
    
class NumericRecode(Recode):
    # Arithmetic operations
    
class NumberOfAnswersRecode(Recode):
    # Count responses in quali-multiple
    
class CombinationRecode(Recode):
    # Multi -> Unique with combination codes
    
class WeightRecode(Recode):
    # Weighting/redressement
    
class RecodeEngine:
    recodes: List[Recode]
    
    def parse_formula(formula: str) -> Recode
    def validate() -> List[str]  # Returns errors
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame
```

**Critical Pattern:**
```python
# For Quali Multiple: use C/NC/CO/NCO operators
if variable_type == QUALI_MULTI:
    # ["Q23A"C1] means Q23A contains code 1
    # ["Q23A"CO1,2] means Q23A contains ONLY 1 and 2
    
# For Quali Unique: use = operator  
if variable_type == QUALI_UNIQUE:
    # ["S9"=1] means S9 equals 1
```

---

### 3. **FilterEngine** (`filter_engine.py`)
**Purpose:** Subset data based on conditions

```python
class Filter:
    name: str
    formula: str
    with_na: bool  # Include non-responses?
    
    def apply(self, df: pd.DataFrame) -> pd.Series[bool]:
        # Returns boolean mask
        
class FilterEngine:
    filters: Dict[str, Filter]
    
    def validate() -> List[str]
    def test(df: pd.DataFrame) -> pd.DataFrame
        # Returns df with filter columns appended
```

---

### 4. **ClassEngine** (`class_engine.py`)  
**Purpose:** Bin numeric variables into categories

```python
class Class:
    name: str
    option_na: bool
    bins: List[Tuple[str, str]]  # [(formula, label), ...]
    # Example: [("X>=1 and X<3", "Low"), ("X>=3 and X<6", "Med")]
    
    def apply(self, series: pd.Series) -> pd.Series:
        # Replace X with actual values, evaluate conditions
        
class ClassEngine:
    classes: Dict[str, Class]
    
    def validate() -> List[str]
```

---

### 5. **TabEngine** (`tab_engine.py`)
**Purpose:** Generate cross-tabulations - the core output

```python
class TabSpec:
    filename: str
    pdt_filter: Optional[str]  # Plan-level filter
    pdt_weight: Optional[str]  # Plan-level weight
    tabs: List[TabDefinition]
    
class TabDefinition:
    title: str
    row_var: str              # Variable to analyze
    col_var: str              # Main cross-var (must be quali)
    second_col_var: Optional[str]
    filter: Optional[str]     # Row-level filter
    weighting: Optional[str]  # Row-level weight
    classes: Optional[str]    # For numeric row_var
    with_na: str              # "RowNA/ColNA/SecondcolNA/"
    
class TabEngine:
    datamap: DataMap
    filters: FilterEngine
    classes: ClassEngine
    
    def generate_tab(
        df: pd.DataFrame,
        spec: TabDefinition
    ) -> pd.DataFrame:
        # Returns formatted cross-tab with percentages
        
    def calculate_signif(
        tab: pd.DataFrame,
        col_var: str
    ) -> pd.DataFrame:
        # Chi-square or z-tests between columns
        
    def export_to_excel(
        tabs: List[pd.DataFrame],
        filename: str
    ):
        # Formatted Excel with conditional formatting
```

**Key Logic:**
- Row variable = what you're analyzing
- Column variable = how you're splitting it (MUST be qualitative)
- Second column = additional split
- Significance testing between column categories

---

### 6. **SubBaseEngine** (`subbase_engine.py`)
**Purpose:** Handle patient/product loops - 1 row per MD → multiple rows

```python
class SubBase:
    name: str
    parent_df: pd.DataFrame
    loop_var: str  # e.g., "Patient", "Product"
    
    def expand(self) -> pd.DataFrame:
        # Transform: 1 row/MD → N rows (MD × Patient/Product)
        
class SubBaseEngine:
    sub_bases: Dict[str, SubBase]
    
    def create_subbase(
        df: pd.DataFrame,
        loop_vars: List[str]
    ) -> pd.DataFrame
```

---

## 🔧 Utility Modules

### `formula_parser.py`
```python
class FormulaParser:
    """
    Parse STAATS formulas:
    - ["S9"=1] 
    - ["Q23A"C1,2,3]
    - X>=1 and X<3
    """
    
    @staticmethod
    def parse_variable_condition(formula: str) -> Tuple[str, str, Any]:
        # Returns (variable, operator, value)
        
    @staticmethod  
    def parse_class_formula(formula: str) -> Callable:
        # Returns lambda function for X
```

### `excel_io.py`
```python
class ExcelReader:
    def read_datamap(path: str) -> DataMap
    def read_recodes(path: str) -> List[Recode]
    def read_filters(path: str) -> FilterEngine
    def read_classes(path: str) -> ClassEngine
    def read_tabspecs(path: str) -> List[TabSpec]
    
class ExcelWriter:
    def write_tabs(tabs: List[pd.DataFrame], path: str)
    def apply_formatting(worksheet, datamap: DataMap)
```

### `validators.py`
```python
class Validator:
    @staticmethod
    def check_datamap(datamap: DataMap, df: pd.DataFrame) -> List[str]
    
    @staticmethod
    def check_recodes(recodes: List[Recode]) -> List[str]
    
    @staticmethod
    def check_filters(filters: FilterEngine) -> List[str]
    
    @staticmethod
    def check_tabspecs(specs: List[TabSpec], datamap: DataMap) -> List[str]
```

---

## 📊 Data Flow

```
1. Load data (CSV/Excel) → pd.DataFrame
2. Load DataMap → validate against data
3. Calculate Recodes → append to DataFrame
4. Define Filters → ready for application
5. Define Classes → ready for numeric binning
6. Generate Tabs → apply filters, weights, classes
7. Export → formatted Excel files
```

---

## 🎮 Main Controller

```python
class STAATSEngine:
    """The orchestrator - brings it all together"""
    
    def __init__(self):
        self.datamap: Optional[DataMap] = None
        self.data: Optional[pd.DataFrame] = None
        self.recode_engine = RecodeEngine()
        self.filter_engine = FilterEngine()
        self.class_engine = ClassEngine()
        self.tab_engine = TabEngine()
        self.subbase_engine = SubBaseEngine()
        
    def load_config_from_excel(self, path: str):
        """Load all config from STAATS Excel file"""
        
    def load_config_from_json(self, config_dir: str):
        """Load from JSON files (Google-friendly)"""
        
    def load_data(self, path: str):
        """Load survey data"""
        
    def validate_all(self) -> Dict[str, List[str]]:
        """Run all validators, return errors by category"""
        
    def calculate_recodes(self):
        """Execute all recodes, update self.data"""
        
    def generate_all_tabs(self, output_dir: str):
        """Generate all tab specs, export to Excel"""
        
    def run_pipeline(self, config_path: str, data_path: str, output_dir: str):
        """Full execution: load → validate → recode → tab"""
```

---

## 🚀 Usage Examples

### Basic Usage
```python
from staats import STAATSEngine

engine = STAATSEngine()

# Option 1: Load from Excel (backward compatible)
engine.load_config_from_excel("STAATS_config.xlsm")
engine.load_data("survey_data.csv")

# Validate
errors = engine.validate_all()
if errors:
    print("Errors found:", errors)
    exit(1)

# Execute
engine.calculate_recodes()
engine.generate_all_tabs("output/")
```

### Google Colab / Cloud
```python
# Store config as JSON instead of Excel
{
  "datamap": {...},
  "recodes": [...],
  "filters": {...},
  "classes": {...},
  "tabspecs": [...]
}

engine = STAATSEngine()
engine.load_config_from_json("config/")
engine.load_data("gs://bucket/survey_data.csv")
engine.run_pipeline()
```

---

## 🧪 Testing Strategy

```python
tests/
├── test_datamapper.py      # Question type validation
├── test_recode_engine.py   # All recode types
├── test_filter_engine.py   # Filter logic
├── test_class_engine.py    # Binning accuracy
├── test_tab_engine.py      # Cross-tab calculations
├── test_formula_parser.py  # Formula parsing edge cases
└── integration/
    └── test_full_pipeline.py
```

---

## 📁 Project Structure

```
staats-python/
├── staats/
│   ├── __init__.py
│   ├── engine.py              # Main STAATSEngine
│   ├── datamapper.py
│   ├── recode_engine.py
│   ├── filter_engine.py
│   ├── class_engine.py
│   ├── tab_engine.py
│   ├── subbase_engine.py
│   └── utils/
│       ├── formula_parser.py
│       ├── excel_io.py
│       └── validators.py
├── tests/
├── examples/
│   ├── basic_usage.py
│   └── google_colab_example.ipynb
├── requirements.txt
├── setup.py
└── README.md
```

---

## 🔥 Key Technical Decisions

1. **Pandas over raw lists** - Industry standard, vectorized ops
2. **Abstract base classes for Recodes** - Clean polymorphism
3. **Formula strings, not code injection** - Security first
4. **JSON config option** - Cloud-native, version control friendly
5. **Comprehensive validation** - Catch errors before execution
6. **Modular design** - Each engine is independent

---

## 🎯 Next Steps

1. **Phase 1:** Core data structures (DataMap, Question types)
2. **Phase 2:** Recode engine (most complex part)
3. **Phase 3:** Filter & Class engines
4. **Phase 4:** Tab engine with significance testing
5. **Phase 5:** Excel I/O and formatting
6. **Phase 6:** Sub-base handling
7. **Phase 7:** Testing & documentation

---

## ⚡ Performance Considerations

- Use `pd.eval()` for formula parsing (safe + fast)
- Vectorize operations (no Python loops on data)
- Lazy loading for large datasets
- Chunk processing for massive files
- Cache filter results when used multiple times

---

**Bottom line:** This isn't just a port - it's a complete modernization. Excel macros are dead weight. Python + pandas is the championship belt.
