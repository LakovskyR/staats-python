#!/usr/bin/env python3
"""
STAATS Python - Command Line Interface
For automation and power users

Usage:
    staats process data.csv config.json -o output.xlsx
    staats validate data.csv config.json
    staats convert config.xlsm config.json
"""

import argparse
import json
import sys
from pathlib import Path
import pandas as pd

from core import DataMap, Question, QuestionType, TabDefinition, Filter, Class
from recode_engine import (
    RecodeEngine, QualiUniqueRecode, NumericRecode,
    NumberOfAnswersRecode, WeightRecode
)
from engines import FilterEngine, ClassEngine
from complete_demo import STAATSPipeline
from excel_config_reader import ExcelConfigReader


def load_json_config(config_path: str):
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Reconstruct datamap
    dm = DataMap.from_dict(config['datamap'])
    
    # Reconstruct other engines
    # TODO: Full JSON deserialization
    recode_engine = RecodeEngine()
    filter_engine = FilterEngine()
    class_engine = ClassEngine()
    
    return dm, recode_engine, filter_engine, class_engine


def cmd_process(args):
    """Process survey data end-to-end"""
    print(f"🚀 Processing {args.data}")
    
    pipeline = STAATSPipeline()
    
    # Load data
    pipeline.load_data(args.data)
    
    # Load config
    if args.config.endswith('.json'):
        dm, recode_engine, filter_engine, class_engine = load_json_config(args.config)
        pipeline.datamap = dm
        pipeline.recode_engine = recode_engine
        pipeline.filter_engine = filter_engine
        pipeline.class_engine = class_engine
    elif args.config.endswith(('.xlsm', '.xlsx')):
        reader = ExcelConfigReader(args.config)
        dm, recode_engine, filter_engine, class_engine = reader.read_all()
        pipeline.datamap = dm
        pipeline.recode_engine = recode_engine
        pipeline.filter_engine = filter_engine
        pipeline.class_engine = class_engine
    else:
        print(f"❌ Unsupported config format: {args.config}")
        sys.exit(1)
    
    # Validate
    print("✅ Validating data...")
    errors = pipeline.validate_data()
    if errors:
        print("⚠️ Validation warnings found (continuing anyway)")
    
    # Calculate recodes
    if len(pipeline.recode_engine) > 0:
        print(f"🔄 Calculating {len(pipeline.recode_engine)} recodes...")
        pipeline.calculate_recodes()
    
    # Generate tabs (if specified in config)
    # For now, create basic tabs
    from core import TabDefinition
    
    # Auto-generate tabs for all quali variables
    tab_specs = []
    if pipeline.datamap:
        quali_vars = [name for name, q in pipeline.datamap.questions.items() 
                     if q.qtype in [QuestionType.QUALI_UNIQUE, QuestionType.QUALI_MULTI]]
        
        if len(quali_vars) >= 2:
            # Create tabs: each var by first quali var
            col_var = quali_vars[0]
            for row_var in quali_vars[1:6]:  # First 5
                tab_specs.append(TabDefinition(
                    f"{row_var} by {col_var}",
                    row_var,
                    col_var
                ))
    
    # Generate
    if tab_specs:
        print(f"📊 Generating {len(tab_specs)} cross-tabulations...")
        output_file = args.output or "output.xlsx"
        pipeline.generate_tabs(tab_specs, output_file)
        print(f"✅ Results saved to {output_file}")
    else:
        print("⚠️ No tabs generated (no quali variables found)")
    
    print("✅ Processing complete!")


def cmd_validate(args):
    """Validate data against configuration"""
    print(f"🔍 Validating {args.data}")
    
    # Load data
    if args.data.endswith('.csv'):
        df = pd.read_csv(args.data)
    else:
        df = pd.read_excel(args.data)
    
    # Load config
    if args.config.endswith('.json'):
        dm, _, _, _ = load_json_config(args.config)
    else:
        reader = ExcelConfigReader(args.config)
        dm, _, _, _ = reader.read_all()
    
    # Validate
    errors = dm.validate_dataframe(df)
    
    if errors:
        print(f"❌ Validation failed with {len(errors)} errors:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    else:
        print("✅ Validation passed!")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {len(df.columns)}")
        print(f"   Questions: {len(dm)}")


def cmd_convert(args):
    """Convert STAATS.xlsm to JSON config"""
    print(f"🔄 Converting {args.input} to JSON...")
    
    reader = ExcelConfigReader(args.input)
    dm, recode_engine, filter_engine, class_engine = reader.read_all()
    
    # Serialize to JSON
    config = {
        'datamap': dm.to_dict(),
        'recodes': [
            {
                'name': r.name,
                'type': r.rtype.value,
                'title': r.title,
                'formula': r.formula,
                'option_na': r.option_na
            }
            for r in recode_engine.recodes
        ],
        'filters': {
            name: {
                'formula': f.formula,
                'with_na': f.with_na
            }
            for name, f in filter_engine.filters.items()
        },
        'classes': {
            name: {
                'bins': c.bins,
                'option_na': c.option_na
            }
            for name, c in class_engine.classes.items()
        }
    }
    
    output_path = args.output or args.input.replace('.xlsm', '.json')
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Converted to {output_path}")
    print(f"   Questions: {len(dm)}")
    print(f"   Recodes: {len(recode_engine)}")
    print(f"   Filters: {len(filter_engine)}")
    print(f"   Classes: {len(class_engine)}")


def main():
    parser = argparse.ArgumentParser(
        description='STAATS Python - Survey Data Processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process data with JSON config
  staats process survey.csv config.json -o results.xlsx
  
  # Process data with Excel config
  staats process survey.csv STAATS.xlsm -o results.xlsx
  
  # Validate data
  staats validate survey.csv config.json
  
  # Convert Excel config to JSON
  staats convert STAATS.xlsm -o config.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process survey data')
    process_parser.add_argument('data', help='Survey data file (CSV or Excel)')
    process_parser.add_argument('config', help='Configuration file (JSON or XLSM)')
    process_parser.add_argument('-o', '--output', help='Output Excel file')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate data')
    validate_parser.add_argument('data', help='Survey data file')
    validate_parser.add_argument('config', help='Configuration file')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert Excel config to JSON')
    convert_parser.add_argument('input', help='Input STAATS.xlsm file')
    convert_parser.add_argument('-o', '--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'process':
            cmd_process(args)
        elif args.command == 'validate':
            cmd_validate(args)
        elif args.command == 'convert':
            cmd_convert(args)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
