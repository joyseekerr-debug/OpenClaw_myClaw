# -*- coding: utf-8 -*-
"""
Stock Price Prediction System - Simple Test
Basic syntax and import check
"""

import sys
import os
import ast

print("=" * 60)
print("Stock Price Prediction System - Simple Test")
print("=" * 60)

# Test 1: Python version
print("\n[Test 1] Python Version Check")
print(f"  Python Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
print(f"  Path: {sys.executable}")

# Test 2: Basic dependencies
print("\n[Test 2] Dependencies Check")
dependencies = ['pandas', 'numpy']
for dep in dependencies:
    try:
        __import__(dep)
        print(f"  [OK] {dep}")
    except ImportError:
        print(f"  [FAIL] {dep} (not installed)")

# Test 3: Syntax check
print("\n[Test 3] Code Syntax Check")
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')

syntax_errors = []

if os.path.exists(src_path):
    for root, dirs, files in os.walk(src_path):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        code = f.read()
                    ast.parse(code)
                    print(f"  [OK] {file}")
                except SyntaxError as e:
                    print(f"  [ERROR] {file}: Syntax Error - {e}")
                    syntax_errors.append((file, str(e)))
                except Exception as e:
                    print(f"  [WARN] {file}: Read Error - {e}")
else:
    print(f"  [WARN] src directory not found: {src_path}")

# Test 4: Module import check
print("\n[Test 4] Module Import Check")
sys.path.insert(0, src_path)

test_modules = [
    ('data.data_loader', 'Data Loader'),
    ('data.data_processor', 'Data Processor'),
    ('features.feature_engineering', 'Feature Engineering'),
    ('features.support_resistance', 'Support Resistance'),
    ('features.chart_patterns', 'Chart Patterns'),
]

for module_name, desc in test_modules:
    try:
        __import__(module_name)
        print(f"  [OK] {desc}")
    except Exception as e:
        print(f"  [FAIL] {desc}: {type(e).__name__}")

# Summary
print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)

if syntax_errors:
    print(f"\nFound {len(syntax_errors)} syntax errors:")
    for file, error in syntax_errors:
        print(f"  - {file}: {error}")
else:
    print("\n[PASS] All files have correct syntax")

print("\nTest Completed")
