"""
STAATS Python - Web Application
Point-and-click interface for survey data processing

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import json
import io

from core import DataMap, Question, QuestionType, TabDefinition, Filter, Class
from recode_engine import (
    RecodeEngine, QualiUniqueRecode, QualiMultipleRecode,
    NumericRecode, NumberOfAnswersRecode, WeightRecode
)
from engines import FilterEngine, ClassEngine
from tab_engine import TabEngine
from excel_export import ExcelExporter
from complete_demo import STAATSPipeline

# Page config
st.set_page_config(
    page_title="STAATS Python - aplusa",
    page_icon="assets/aplusa_logo.jpg",
    layout="wide"
)

# Initialize session state
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = STAATSPipeline()
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'config_loaded' not in st.session_state:
    st.session_state.config_loaded = False

# Sidebar with logo
try:
    st.sidebar.image("assets/aplusa_logo.jpg", use_column_width=True)
except:
    st.sidebar.title("STAATS Python")
st.sidebar.markdown("**Healthcare Market Research - Worldwide**")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Load Data", "Configure", "Recodes", "Analyze", "Export"]
)

# Main content
if page == "Home":
    st.title("STAATS Python - Professional Survey Data Processing")
    st.markdown("### For aplusa Healthcare Market Research")
    
    st.markdown("""
    **STAATS Python** replaces Excel VBA macros with modern Python - faster, more reliable, and cloud-ready.
    
    #### Quick Start:
    1. **Load Data** - Upload your survey CSV or Excel file
    2. **Configure** - Define questions (datamap) or load from STAATS.xlsm
    3. **Recodes** - Create recoded variables
    4. **Analyze** - Generate cross-tabulations
    5. **Export** - Download formatted Excel files
    
    #### Features:
    - Process unlimited rows (no more Excel crashes)
    - 100x faster than Excel VBA
    - Significance testing built-in
    - Professional formatting
    - Cloud-ready deployment
    """)
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Data Loaded", "Yes" if st.session_state.data_loaded else "No")
    with col2:
        st.metric("Config Ready", "Yes" if st.session_state.config_loaded else "No")
    with col3:
        if st.session_state.data_loaded:
            st.metric("Respondents", len(st.session_state.pipeline.data))

elif page == "Load Data":
    st.title("Load Survey Data")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload survey data (CSV or Excel)",
        type=['csv', 'xlsx', 'xls']
    )
    
    if uploaded_file:
        try:
            # Read file based on type
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.session_state.pipeline.data = df
            st.session_state.data_loaded = True
            
            st.success(f"Loaded {len(df)} respondents with {len(df.columns)} columns")
            
            # Preview
            st.markdown("### Data Preview")
            st.dataframe(df.head(20))
            
            # Basic stats
            st.markdown("### Column Info")
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.astype(str),
                'Non-Null': df.count(),
                'Null': df.isnull().sum()
            })
            st.dataframe(col_info)
            
        except Exception as e:
            st.error(f"Error loading file: {e}")
    
    # Or use sample data
    st.markdown("---")
    st.markdown("**Test with Sample Data**")
    if st.button("Load Sample Healthcare Survey (demo data)"):
        # Create sample data
        np.random.seed(42)
        n = 300  # Sample size for demo
        df = pd.DataFrame({
            'ID': range(1, n + 1),
            'Country': np.random.choice([1, 2, 3], n, p=[0.5, 0.3, 0.2]),
            'Age': np.random.randint(28, 68, n),
            'Satisfaction': np.random.choice([1, 2, 3, 4, 5], n),
            'Recommend': np.random.choice([1, 2, 3], n),
        })
        
        st.session_state.pipeline.data = df
        st.session_state.data_loaded = True
        st.success("Sample data loaded successfully!")
        st.rerun()

elif page == "Configure":
    st.title("Data Configuration (Datamap)")
    
    if not st.session_state.data_loaded:
        st.warning("Please load data first")
        st.stop()
    
    tab1, tab2 = st.tabs(["Manual Setup", "Import Config"])
    
    with tab1:
        st.markdown("### Define Questions")
        
        df = st.session_state.pipeline.data
        
        if 'datamap' not in st.session_state:
            st.session_state.datamap = DataMap()
        
        # Quick auto-detect
        if st.button("Auto-Detect Question Types"):
            dm = DataMap()
            for col in df.columns:
                # Simple heuristic
                unique_count = df[col].nunique()
                
                if unique_count <= 10 and df[col].dtype in ['int64', 'float64']:
                    qtype = QuestionType.QUALI_UNIQUE
                    codes = {int(val): f"Code {int(val)}" 
                            for val in df[col].dropna().unique() if pd.notna(val)}
                elif df[col].dtype == 'object':
                    # Check if multi-choice format
                    if df[col].astype(str).str.contains(',').any():
                        qtype = QuestionType.QUALI_MULTI
                        codes = {}
                    else:
                        qtype = QuestionType.OPEN
                        codes = {}
                else:
                    qtype = QuestionType.NUMERIC
                    codes = {}
                
                dm.add_question(Question(col, qtype, col, codes))
            
            st.session_state.datamap = dm
            st.success(f"Auto-detected {len(dm)} questions")
            st.rerun()
        
        # Show current datamap
        if len(st.session_state.datamap) > 0:
            st.markdown("### Current Configuration")
            
            config_data = []
            for name, q in st.session_state.datamap.questions.items():
                config_data.append({
                    'Variable': name,
                    'Type': q.qtype.name,
                    'Label': q.title,
                    'Codes': len(q.codes)
                })
            
            st.dataframe(pd.DataFrame(config_data))
            
            if st.button("Save Configuration"):
                st.session_state.pipeline.datamap = st.session_state.datamap
                st.session_state.config_loaded = True
                st.success("Configuration saved!")
        
    with tab2:
        st.markdown("### Import from STAATS.xlsm")
        
        config_file = st.file_uploader(
            "Upload STAATS configuration file",
            type=['xlsm', 'xlsx']
        )
        
        if config_file:
            try:
                # Save temporarily
                temp_path = Path("temp_config.xlsm")
                with open(temp_path, 'wb') as f:
                    f.write(config_file.read())
                
                # Import
                from excel_config_reader import ExcelConfigReader
                reader = ExcelConfigReader(str(temp_path))
                
                datamap, recode_engine, filter_engine, class_engine = reader.read_all()
                
                st.session_state.pipeline.datamap = datamap
                st.session_state.pipeline.recode_engine = recode_engine
                st.session_state.pipeline.filter_engine = filter_engine
                st.session_state.pipeline.class_engine = class_engine
                st.session_state.config_loaded = True
                
                st.success(f"""
                Configuration imported!
                - Questions: {len(datamap)}
                - Recodes: {len(recode_engine)}
                - Filters: {len(filter_engine)}
                - Classes: {len(class_engine)}
                """)
                
                # Cleanup
                temp_path.unlink()
                
            except Exception as e:
                st.error(f"Error importing config: {e}")

elif page == "Recodes":
    st.title("Recoded Variables")
    
    if not st.session_state.config_loaded:
        st.warning("Please configure data first")
        st.stop()
    
    st.markdown("### Create Recodes")
    
    # Simple recode builder
    with st.expander("Add New Recode"):
        recode_name = st.text_input("Recode Name", "MyRecode")
        recode_type = st.selectbox(
            "Recode Type",
            ["Quali Unique", "Numeric", "Number of Answers", "Weight"]
        )
        
        if recode_type == "Quali Unique":
            st.markdown("**Formula (one condition per line):**")
            formula = st.text_area(
                "Formula",
                '1: ["SourceVar"=1]\n2: ["SourceVar"=2]',
                height=150
            )
            
            code1 = st.text_input("Code 1 Label", "Label 1")
            code2 = st.text_input("Code 2 Label", "Label 2")
            
            if st.button("Add Recode"):
                try:
                    recode = QualiUniqueRecode(
                        recode_name,
                        recode_name,
                        formula,
                        {1: code1, 2: code2}
                    )
                    st.session_state.pipeline.recode_engine.add_recode(recode)
                    st.success(f"Recode '{recode_name}' added")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Show existing recodes
    if len(st.session_state.pipeline.recode_engine) > 0:
        st.markdown("### Configured Recodes")
        
        recode_list = []
        for recode in st.session_state.pipeline.recode_engine.recodes:
            recode_list.append({
                'Name': recode.name,
                'Type': recode.rtype.name,
                'Title': recode.title
            })
        
        st.dataframe(pd.DataFrame(recode_list))
        
        if st.button("Calculate All Recodes"):
            with st.spinner("Calculating recodes..."):
                try:
                    st.session_state.pipeline.calculate_recodes()
                    st.success(f"Recodes calculated! Data now has {len(st.session_state.pipeline.data.columns)} columns")
                except Exception as e:
                    st.error(f"Error: {e}")

elif page == "Analyze":
    st.title("Cross-Tabulation Analysis")
    
    if not st.session_state.config_loaded:
        st.warning("Please configure data first")
        st.stop()
    
    st.markdown("### Create Cross-Tabulations")
    
    # Get available variables
    if st.session_state.pipeline.datamap:
        vars_list = list(st.session_state.pipeline.datamap.questions.keys())
    else:
        vars_list = []
    
    # Tab builder
    with st.expander("Add Cross-Tab"):
        tab_title = st.text_input("Tab Title", "My Cross-Tab")
        
        col1, col2 = st.columns(2)
        with col1:
            row_var = st.selectbox("Row Variable (analyze)", vars_list)
        with col2:
            col_var = st.selectbox("Column Variable (cross by)", vars_list)
        
        if 'tab_specs' not in st.session_state:
            st.session_state.tab_specs = []
        
        if st.button("Add to Analysis"):
            spec = TabDefinition(tab_title, row_var, col_var)
            st.session_state.tab_specs.append(spec)
            st.success(f"Added '{tab_title}'")
    
    # Show tab specs
    if 'tab_specs' in st.session_state and len(st.session_state.tab_specs) > 0:
        st.markdown(f"### Tabs to Generate ({len(st.session_state.tab_specs)})")
        
        for i, spec in enumerate(st.session_state.tab_specs):
            st.markdown(f"{i+1}. **{spec.title}**: {spec.row_var} × {spec.col_var}")
        
        if st.button("Generate Analysis"):
            with st.spinner("Generating cross-tabulations..."):
                try:
                    # Create tab engine
                    tab_engine = TabEngine(
                        st.session_state.pipeline.datamap,
                        st.session_state.pipeline.filter_engine,
                        st.session_state.pipeline.class_engine
                    )
                    
                    # Generate tabs
                    results = tab_engine.generate_multiple_tabs(
                        st.session_state.pipeline.data,
                        st.session_state.tab_specs
                    )
                    
                    st.session_state.tab_results = results
                    st.success(f"Generated {len(results)} cross-tabulations")
                    
                    # Preview first tab
                    if results:
                        st.markdown("### Preview: " + results[0].title)
                        st.dataframe(results[0].col_pct.round(1))
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())

elif page == "Export":
    st.title("Export Results")
    
    if 'tab_results' not in st.session_state:
        st.warning("Please generate analysis first")
        st.stop()
    
    st.markdown("### Download Excel File")
    
    filename = st.text_input("Filename", "survey_analysis.xlsx")
    
    if st.button("Generate Excel File"):
        with st.spinner("Creating Excel file..."):
            try:
                # Create exporter
                exporter = ExcelExporter(output_dir="temp")
                
                # Export
                filepath = exporter.export_multiple_tabs(
                    st.session_state.tab_results,
                    filename=filename,
                    display_mode='Both',
                    create_summary=True
                )
                
                # Read file for download
                with open(filepath, 'rb') as f:
                    excel_data = f.read()
                
                st.download_button(
                    label="Download Excel File",
                    data=excel_data,
                    file_name=filename,
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
                st.success("Excel file ready for download!")
                
            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**STAATS Python v1.0**")
st.sidebar.markdown("Built for aplusa")
