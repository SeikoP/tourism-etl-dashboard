#!/usr/bin/env python3
"""
Simple DAG structure validation without Airflow dependencies
"""

import ast
import sys
from pathlib import Path

def analyze_dag_file(file_path):
    """Analyze DAG file structure using AST"""
    
    print(f"INFO: Analyzing DAG file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        
        # Find function definitions
        functions = []
        classes = []
        imports = []
        assignments = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assignments.append(target.id)
        
        print("✓ DAG file parsed successfully")
        print(f"  - Functions found: {len(functions)}")
        for func in functions:
            print(f"    * {func}")
        
        print(f"  - Key imports: {len([i for i in imports if 'airflow' in i or 'dag' in i.lower()])}")
        for imp in imports:
            if 'airflow' in imp or 'dag' in imp.lower():
                print(f"    * {imp}")
        
        print(f"  - Variable assignments: {len([a for a in assignments if 'task' in a or a == 'dag'])}")
        for assign in assignments:
            if 'task' in assign or assign == 'dag':
                print(f"    * {assign}")
        
        # Check for common DAG patterns
        content_lower = content.lower()
        
        patterns_found = []
        if 'dag(' in content_lower:
            patterns_found.append("DAG instantiation")
        if 'pythonoperator' in content_lower:
            patterns_found.append("PythonOperator usage")
        if 'bashoperator' in content_lower:
            patterns_found.append("BashOperator usage")
        if '>>' in content:
            patterns_found.append("Task dependencies")
        
        print(f"  - DAG patterns found: {patterns_found}")
        
        # Check for potential issues
        issues = []
        if 'airflow.operators.python' in content and 'PythonOperator' in content:
            issues.append("Deprecated import: airflow.operators.python.PythonOperator")
        if 'airflow.operators.bash' in content and 'BashOperator' in content:
            issues.append("Deprecated import: airflow.operators.bash.BashOperator")
        if content.startswith('#!/usfrom'):
            issues.append("Invalid shebang line")
            
        if issues:
            print(f"  - Issues found: {len(issues)}")
            for issue in issues:
                print(f"    ! {issue}")
        else:
            print("  - No issues found!")
            
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error in DAG file: {e}")
        return False
    except Exception as e:
        print(f"✗ Error analyzing DAG file: {e}")
        return False

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    dag_file = project_root / "dags" / "vietnambooking_pipeline.py"
    
    if analyze_dag_file(dag_file):
        print("✓ DAG analysis completed successfully!")
    else:
        print("✗ DAG analysis failed!")
        sys.exit(1)