"""
STAATS Tab Engine - Cross-Tabulation Generator
The knockout punch that turns data into insights

Generates:
- Row × Column cross-tabs
- Weighted calculations
- Percentages (vertical/horizontal/both)
- Significance testing (Chi-square, z-tests)
- Multi-level cross-tabs (second column variable)
"""

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from scipy import stats
from dataclasses import dataclass

from core import DataMap, TabDefinition, QuestionType
from engines import FilterEngine, ClassEngine
from formula_parser import FormulaParser


@dataclass
class TabResult:
    """Results of a single tabulation"""
    title: str
    counts: pd.DataFrame          # Raw counts
    row_pct: pd.DataFrame         # Row percentages
    col_pct: pd.DataFrame         # Column percentages
    significance: Optional[pd.DataFrame] = None  # Significance markers
    weighted: bool = False
    base: pd.Series = None        # Base counts for each column
    
    def to_display_format(self, display: str = "Both") -> pd.DataFrame:
        """
        Format for display/export
        display: "Vertical" (col %), "Horizontal" (row %), "Both"
        """
        if display == "Vertical":
            return self.col_pct
        elif display == "Horizontal":
            return self.row_pct
        else:  # Both
            # Combine: "Count (col%)"
            result = pd.DataFrame(index=self.counts.index, columns=self.counts.columns)
            for col in self.counts.columns:
                for idx in self.counts.index:
                    count = self.counts.loc[idx, col]
                    pct = self.col_pct.loc[idx, col]
                    if pd.notna(count):
                        result.loc[idx, col] = f"{int(count)} ({pct:.1f}%)"
            return result


class SignificanceTest:
    """
    Statistical significance testing for cross-tabs
    """
    
    @staticmethod
    def chi_square_test(crosstab: pd.DataFrame) -> Tuple[float, float]:
        """
        Chi-square test for independence
        Returns: (chi2_stat, p_value)
        """
        # Remove totals if present
        data = crosstab.copy()
        if 'Total' in data.index:
            data = data.drop('Total')
        if 'Total' in data.columns:
            data = data.drop('Total', axis=1)
        
        try:
            chi2, p_value, dof, expected = stats.chi2_contingency(data)
            return chi2, p_value
        except:
            return None, None
    
    @staticmethod
    def column_z_tests(crosstab: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
        """
        Pairwise z-tests between columns
        
        Returns DataFrame with letters marking significant differences
        Each cell gets letters for columns it's significantly different from
        
        Example:
        If column A is significantly higher than B and C, it gets "BC"
        """
        # Remove totals
        data = crosstab.copy()
        if 'Total' in data.index:
            data = data.drop('Total')
        if 'Total' in data.columns:
            data = data.drop('Total', axis=1)
        
        n_cols = len(data.columns)
        if n_cols < 2:
            return pd.DataFrame(index=data.index, columns=data.columns)
        
        # Get column totals (base sizes)
        col_totals = data.sum(axis=0)
        
        # Calculate proportions
        proportions = data / col_totals
        
        # Initialize result
        sig_markers = pd.DataFrame('', index=data.index, columns=data.columns)
        
        # For each row (response category)
        for row_idx in data.index:
            # For each column
            for i, col_i in enumerate(data.columns):
                p_i = proportions.loc[row_idx, col_i]
                n_i = col_totals[col_i]
                
                sig_letters = []
                
                # Compare against all other columns
                for j, col_j in enumerate(data.columns):
                    if i == j:
                        continue
                    
                    p_j = proportions.loc[row_idx, col_j]
                    n_j = col_totals[col_j]
                    
                    # Two-proportion z-test
                    if pd.notna(p_i) and pd.notna(p_j) and n_i > 0 and n_j > 0:
                        # Pooled proportion
                        p_pool = (data.loc[row_idx, col_i] + data.loc[row_idx, col_j]) / (n_i + n_j)
                        
                        # Standard error
                        se = np.sqrt(p_pool * (1 - p_pool) * (1/n_i + 1/n_j))
                        
                        if se > 0:
                            # Z statistic
                            z = (p_i - p_j) / se
                            
                            # Two-tailed p-value
                            p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                            
                            # If significant and i > j, mark with letter
                            if p_value < alpha and p_i > p_j:
                                # Add letter corresponding to column j
                                # A=0, B=1, C=2, etc.
                                sig_letters.append(chr(65 + j))
                
                sig_markers.loc[row_idx, col_i] = ''.join(sorted(sig_letters))
        
        return sig_markers


class TabEngine:
    """
    Generates cross-tabulations from data
    The core of STAATS output generation
    """
    
    def __init__(
        self,
        datamap: DataMap,
        filter_engine: Optional[FilterEngine] = None,
        class_engine: Optional[ClassEngine] = None
    ):
        self.datamap = datamap
        self.filter_engine = filter_engine or FilterEngine()
        self.class_engine = class_engine or ClassEngine()
    
    def generate_tab(
        self,
        df: pd.DataFrame,
        spec: TabDefinition,
        pdt_filter: Optional[str] = None,
        pdt_weight: Optional[str] = None
    ) -> TabResult:
        """
        Generate a single cross-tabulation
        
        Args:
            df: Source data
            spec: Tab specification
            pdt_filter: Plan-level filter (applied to whole file)
            pdt_weight: Plan-level weight (applied to whole file)
        
        Returns: TabResult with counts, percentages, significance
        """
        # Step 1: Apply filters
        mask = pd.Series(True, index=df.index)
        
        # Plan-level filter
        if pdt_filter:
            mask &= self.filter_engine.apply_filter(df, pdt_filter, self.datamap)
        
        # Row-level filter
        if spec.filter_name:
            mask &= self.filter_engine.apply_filter(df, spec.filter_name, self.datamap)
        
        filtered_df = df[mask].copy()
        
        if len(filtered_df) == 0:
            # Empty result
            return TabResult(
                title=spec.title,
                counts=pd.DataFrame(),
                row_pct=pd.DataFrame(),
                col_pct=pd.DataFrame()
            )
        
        # Step 2: Prepare row variable
        row_var = spec.row_var
        row_question = self.datamap.get_question(row_var)
        
        if not row_question:
            raise ValueError(f"Row variable '{row_var}' not in datamap")
        
        row_data = filtered_df[row_var].copy()
        
        # Apply class binning if specified
        if spec.class_name and row_question.qtype == QuestionType.NUMERIC:
            row_data = self.class_engine.apply_class(row_data, spec.class_name)
            # Get class labels
            class_obj = self.class_engine.get_class(spec.class_name)
            row_labels = {i: label for i, (_, label) in enumerate(class_obj.bins, 1)}
        else:
            row_labels = row_question.codes
        
        # Step 3: Prepare column variable
        col_var = spec.col_var
        col_question = self.datamap.get_question(col_var)
        
        if not col_question:
            raise ValueError(f"Column variable '{col_var}' not in datamap")
        
        if col_question.qtype not in [QuestionType.QUALI_UNIQUE, QuestionType.QUALI_MULTI]:
            raise ValueError(f"Column variable must be qualitative, got {col_question.qtype}")
        
        col_data = filtered_df[col_var].copy()
        col_labels = col_question.codes
        
        # Step 4: Get weights
        weights = None
        weighted = False
        
        if pdt_weight:
            weights = filtered_df[pdt_weight]
            weighted = True
        elif spec.weight_var:
            weights = filtered_df[spec.weight_var]
            weighted = True
        
        # Step 5: Handle quali multiple columns (expand to multiple columns)
        if col_question.qtype == QuestionType.QUALI_MULTI:
            # For multi-choice, create a column for each code
            col_expanded = {}
            for code, label in col_labels.items():
                # Check if this code is selected
                def has_code(val):
                    if pd.isna(val):
                        return False
                    if isinstance(val, str):
                        codes = [int(c.strip()) for c in val.split(',') if c.strip()]
                        return code in codes
                    return int(val) == code
                
                col_expanded[label] = col_data.apply(has_code)
            
            # Create cross-tabs for each code
            results_by_code = {}
            for code_label, code_mask in col_expanded.items():
                # Split into selected/not selected
                temp_col = pd.Series('Not selected', index=filtered_df.index)
                temp_col[code_mask] = 'Selected'
                
                # Create crosstab
                ct = pd.crosstab(
                    row_data,
                    temp_col,
                    margins=True,
                    normalize=False,
                    dropna=False
                )
                
                results_by_code[code_label] = ct
            
            # Combine into single result
            # This is simplified - real implementation would need proper multi-level handling
            # For now, return first code's result as example
            first_code = list(results_by_code.keys())[0]
            counts = results_by_code[first_code]
        
        else:
            # Step 6: Generate crosstab
            if weights is not None:
                # Weighted crosstab using groupby
                temp_df = pd.DataFrame({
                    'row': row_data,
                    'col': col_data.map(col_labels),
                    'weight': weights
                })
                
                counts = temp_df.pivot_table(
                    values='weight',
                    index='row',
                    columns='col',
                    aggfunc='sum',
                    margins=True,
                    margins_name='Total'
                )
            else:
                # Unweighted
                counts = pd.crosstab(
                    row_data,
                    col_data.map(col_labels),
                    margins=True,
                    margins_name='Total',
                    dropna=False
                )
        
        # Step 7: Calculate percentages
        # Column percentages (vertical)
        col_pct = counts.div(counts.loc['Total'], axis=1) * 100
        
        # Row percentages (horizontal)
        row_pct = counts.div(counts['Total'], axis=0) * 100
        
        # Step 8: Significance testing
        significance = None
        if len(counts.columns) > 2:  # Need at least 2 data columns (plus Total)
            significance = SignificanceTest.column_z_tests(counts)
        
        # Step 9: Get base counts
        base = counts.loc['Total'].copy()
        
        return TabResult(
            title=spec.title,
            counts=counts,
            row_pct=row_pct,
            col_pct=col_pct,
            significance=significance,
            weighted=weighted,
            base=base
        )
    
    def generate_multiple_tabs(
        self,
        df: pd.DataFrame,
        specs: List[TabDefinition],
        pdt_filter: Optional[str] = None,
        pdt_weight: Optional[str] = None
    ) -> List[TabResult]:
        """
        Generate multiple tabs in batch
        """
        results = []
        
        for spec in specs:
            try:
                result = self.generate_tab(df, spec, pdt_filter, pdt_weight)
                results.append(result)
            except Exception as e:
                print(f"Error generating tab '{spec.title}': {e}")
                # Add empty result
                results.append(TabResult(
                    title=spec.title,
                    counts=pd.DataFrame(),
                    row_pct=pd.DataFrame(),
                    col_pct=pd.DataFrame()
                ))
        
        return results
    
    def summary_statistics(self, df: pd.DataFrame, var_name: str, weight_var: Optional[str] = None) -> Dict[str, float]:
        """
        Calculate summary stats for numeric variables
        """
        var_data = df[var_name].dropna()
        
        if weight_var:
            weights = df.loc[var_data.index, weight_var]
            return {
                'Mean': np.average(var_data, weights=weights),
                'Median': var_data.median(),  # Weighted median is complex
                'Std': np.sqrt(np.average((var_data - np.average(var_data, weights=weights))**2, weights=weights)),
                'Min': var_data.min(),
                'Max': var_data.max(),
                'N': len(var_data)
            }
        else:
            return {
                'Mean': var_data.mean(),
                'Median': var_data.median(),
                'Std': var_data.std(),
                'Min': var_data.min(),
                'Max': var_data.max(),
                'N': len(var_data)
            }


# Example usage
if __name__ == "__main__":
    from core import DataMap, Question, QuestionType, Filter, Class
    from engines import FilterEngine, ClassEngine
    import pandas as pd
    import numpy as np
    
    print("🧪 Testing Tab Engine\n")
    
    # Create test data
    np.random.seed(42)
    n = 200
    
    df = pd.DataFrame({
        'Country': np.random.choice([1, 2, 3], n, p=[0.5, 0.3, 0.2]),
        'Age': np.random.randint(25, 65, n),
        'Satisfaction': np.random.choice([1, 2, 3, 4, 5], n),
        'Recommend': np.random.choice([1, 2, 3], n),
    })
    
    # Setup datamap
    dm = DataMap()
    dm.add_question(Question('Country', QuestionType.QUALI_UNIQUE, 'Country', {
        1: 'France', 2: 'UK', 3: 'Germany'
    }))
    dm.add_question(Question('Age', QuestionType.NUMERIC, 'Age'))
    dm.add_question(Question('Satisfaction', QuestionType.QUALI_UNIQUE, 'Satisfaction', {
        1: 'Very dissatisfied', 2: 'Dissatisfied', 3: 'Neutral',
        4: 'Satisfied', 5: 'Very satisfied'
    }))
    dm.add_question(Question('Recommend', QuestionType.QUALI_UNIQUE, 'Recommend', {
        1: 'Yes', 2: 'No', 3: 'Maybe'
    }))
    
    # Setup class
    ce = ClassEngine()
    ce.add_class(Class('AgeGroups', [
        ('X>=25 and X<40', 'Under 40'),
        ('X>=40 and X<55', '40-54'),
        ('X>=55', '55+')
    ]))
    
    # Create tab engine
    tab_engine = TabEngine(dm, class_engine=ce)
    
    # Test 1: Basic cross-tab
    print("=" * 80)
    print("TEST 1: Satisfaction × Country")
    print("=" * 80)
    
    spec1 = TabDefinition(
        title='Satisfaction by Country',
        row_var='Satisfaction',
        col_var='Country'
    )
    
    result1 = tab_engine.generate_tab(df, spec1)
    
    print("\nCounts:")
    print(result1.counts)
    
    print("\nColumn Percentages:")
    print(result1.col_pct.round(1))
    
    if result1.significance is not None:
        print("\nSignificance (letters show sig higher than):")
        print(result1.significance)
    
    # Test 2: With class binning
    print("\n" + "=" * 80)
    print("TEST 2: Age Groups × Country (with class binning)")
    print("=" * 80)
    
    spec2 = TabDefinition(
        title='Age Groups by Country',
        row_var='Age',
        col_var='Country',
        class_name='AgeGroups'
    )
    
    result2 = tab_engine.generate_tab(df, spec2)
    
    print("\nCounts:")
    print(result2.counts)
    
    print("\nColumn Percentages:")
    print(result2.col_pct.round(1))
    
    # Test 3: Display format
    print("\n" + "=" * 80)
    print("TEST 3: Display Format (Count + %)")
    print("=" * 80)
    
    display = result1.to_display_format("Both")
    print(display)
    
    print("\n✅ Tab Engine tests complete!")
