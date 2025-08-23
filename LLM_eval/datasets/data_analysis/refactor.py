import json
import os
import glob
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Any

def group_evaluations_by_kg_element(json_file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Group all evaluations by their kg_element.
    
    Args:
        json_file_path: Path to the JSON file containing evaluation data
        
    Returns:
        Dictionary with kg_element as key and value containing:
        - evaluations: list of evaluations for that kg_element
        - total_human_effort: sum of human_effort for all evaluations
        - total_evaluations: count of evaluations for that kg_element
    """
    # Load the JSON data
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Initialize the result dictionary
    grouped_data = defaultdict(lambda: {
        'evaluations': [],
        'total_human_effort': 0,
        'total_evaluations': 0,
        'bloom_verbs': []
    })
    
    # Process each evaluation
    for evaluation_key, evaluation_data in data.items():
        # Skip non-evaluation entries (like COMPUTED)
        if not evaluation_key.startswith('EVALUATION_'):
            continue
            
        # Get the kg_element, skip if not present
        kg_element = evaluation_data.get('kg_element')
        if not kg_element:
            continue
            
        # Add the evaluation to the appropriate group
        grouped_data[kg_element]['evaluations'].append({
            'evaluation_key': evaluation_key,
            'data': evaluation_data
        })
        
        # Collect bloom_verb if present
        bloom_verb = evaluation_data.get('bloom_verb')
        if bloom_verb:
            grouped_data[kg_element]['bloom_verbs'].append(bloom_verb)
        
        # Add to total human effort (convert to int, default to 0 if not present/invalid)
        try:
            human_effort = int(evaluation_data.get('human_effort', 0))
            grouped_data[kg_element]['total_human_effort'] += human_effort
        except (ValueError, TypeError):
            pass  # Skip invalid human_effort values
            
        # Increment evaluation count
        grouped_data[kg_element]['total_evaluations'] += 1
    
    # Convert defaultdict to regular dict
    return dict(grouped_data)

def print_grouped_summary(grouped_data: Dict[str, Dict[str, Any]]) -> None:
    """Print a summary of the grouped evaluation data."""
    print(f"{'KG Element':<40} {'Evaluations':<12} {'Total Effort':<12}")
    print("-" * 64)
    
    total_evaluations = 0
    total_effort = 0
    
    for kg_element, data in sorted(grouped_data.items()):
        # Skip KG elements with '(decision point)' or '(lookup)'
        if '(decision point)' in kg_element or '(lookup)' in kg_element:
            continue
            
        evaluations_count = data['total_evaluations']
        effort = data['total_human_effort']
        
        print(f"{kg_element:<40} {evaluations_count:<12} {effort:<12}")
        
        total_evaluations += evaluations_count
        total_effort += effort
    
    print("-" * 64)
    print(f"{'TOTAL':<40} {total_evaluations:<12} {total_effort:<12}")

def find_evaluation_data_files(folder_path: str) -> List[str]:
    """
    Find all evaluation_data JSON files in the given folder and its subdirectories.
    
    Args:
        folder_path: Path to the folder to search in
        
    Returns:
        List of paths to evaluation_data JSON files
    """
    # Search pattern for evaluation_data files
    pattern = os.path.join(folder_path, "**/evaluation_data*.json")
    evaluation_files = glob.glob(pattern, recursive=True)
    
    return evaluation_files

def process_multiple_evaluation_files(folder_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Process all evaluation_data files in a folder and aggregate the results by kg_element.
    
    Args:
        folder_path: Path to the folder containing evaluation_data files
        
    Returns:
        Aggregated dictionary with kg_element as key and combined statistics
    """
    evaluation_files = find_evaluation_data_files(folder_path)
    
    if not evaluation_files:
        print(f"No evaluation_data files found in {folder_path}")
        return {}
    
    print(f"Found {len(evaluation_files)} evaluation_data files:")
    for file_path in evaluation_files:
        print(f"  - {os.path.relpath(file_path, folder_path)}")
    print()
    
    # Initialize aggregated data
    aggregated_data = defaultdict(lambda: {
        'evaluations': [],
        'total_human_effort': 0,
        'total_evaluations': 0,
        'files_processed': [],
        'avg_human_effort': 0.0,
        'bloom_verbs': []
    })
    
    # Process each file
    for file_path in evaluation_files:
        try:
            file_data = group_evaluations_by_kg_element(file_path)
            relative_path = os.path.relpath(file_path, folder_path)
            
            # Aggregate data for each kg_element
            for kg_element, data in file_data.items():
                # Skip KG elements with '(decision point)' or '(lookup)'
                if '(decision point)' in kg_element or '(lookup)' in kg_element:
                    continue
                    
                # Add evaluations with file info
                for eval_item in data['evaluations']:
                    eval_item['source_file'] = relative_path
                    aggregated_data[kg_element]['evaluations'].append(eval_item)
                
                # Add to totals
                aggregated_data[kg_element]['total_human_effort'] += data['total_human_effort']
                aggregated_data[kg_element]['total_evaluations'] += data['total_evaluations']
                
                # Aggregate bloom_verbs
                aggregated_data[kg_element]['bloom_verbs'].extend(data['bloom_verbs'])
                
                # Track which files contributed to this kg_element
                if relative_path not in aggregated_data[kg_element]['files_processed']:
                    aggregated_data[kg_element]['files_processed'].append(relative_path)
                    
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    # Calculate average human effort for each kg_element
    for kg_element, data in aggregated_data.items():
        if data['total_evaluations'] > 0:
            data['avg_human_effort'] = data['total_human_effort'] / data['total_evaluations']
    
    return dict(aggregated_data)

def print_aggregated_summary(aggregated_data: Dict[str, Dict[str, Any]]) -> None:
    """Print a summary of the aggregated evaluation data from multiple files."""
    print(f"{'KG Element':<40} {'Evaluations':<12} {'Total Effort':<12} {'Avg Effort':<12} {'Files':<6} {'Bloom Verbs':<30}")
    print("-" * 118)
    
    total_evaluations = 0
    total_effort = 0
    
    # Filter out KG elements with '(decision point)' or '(lookup)' and sort by total effort (descending)
    filtered_items = {k: v for k, v in aggregated_data.items() 
                     if '(decision point)' not in k and '(lookup)' not in k}
    sorted_items = sorted(filtered_items.items(), key=lambda x: x[1]['total_human_effort'], reverse=True)
    
    for kg_element, data in sorted_items:
        evaluations_count = data['total_evaluations']
        effort = data['total_human_effort']
        avg_effort = data['avg_human_effort']
        files_count = len(data['files_processed'])
        
        # Get unique bloom verbs for this kg_element
        unique_bloom_verbs = list(set(data.get('bloom_verbs', [])))
        bloom_verbs_str = ', '.join(unique_bloom_verbs[:5])  # Show first 5 unique verbs
        if len(unique_bloom_verbs) > 5:
            bloom_verbs_str += f" (+{len(unique_bloom_verbs)-5} more)"
        
        print(f"{kg_element:<40} {evaluations_count:<12} {effort:<12} {avg_effort:<12.1f} {files_count:<6} {bloom_verbs_str:<30}")
        
        total_evaluations += evaluations_count
        total_effort += effort
    
    print("-" * 118)
    avg_total = total_effort / total_evaluations if total_evaluations > 0 else 0
    print(f"{'TOTAL':<40} {total_evaluations:<12} {total_effort:<12} {avg_total:<12.1f}")
    
    # Print additional bloom verb statistics
    print(f"\n=== BLOOM VERB ANALYSIS ===")
    all_bloom_verbs = []
    for data in filtered_items.values():
        all_bloom_verbs.extend(data.get('bloom_verbs', []))
    
    if all_bloom_verbs:
        verb_counts = Counter(all_bloom_verbs)
        print(f"Most common bloom verbs across all KG elements:")
        for verb, count in verb_counts.most_common(10):
            print(f"  {verb}: {count} occurrences")
    else:
        print("No bloom verb data found.")

def save_aggregated_results(aggregated_data: Dict[str, Dict[str, Any]], output_file: str) -> None:
    """Save aggregated results to JSON file with additional metadata."""
    # Create summary metadata
    summary = {
        'metadata': {
            'total_kg_elements': len(aggregated_data),
            'total_evaluations': sum(data['total_evaluations'] for data in aggregated_data.values()),
            'total_human_effort': sum(data['total_human_effort'] for data in aggregated_data.values()),
            'files_processed': len(set(file for data in aggregated_data.values() for file in data['files_processed']))
        },
        'kg_elements': aggregated_data
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

def extract_run_identifier(file_path: str) -> str:
    """
    Extract a meaningful run identifier from the file path.
    
    Args:
        file_path: Path to the evaluation file
        
    Returns:
        String identifier for the run
    """
    # Extract the directory structure to create a meaningful run ID
    path_parts = file_path.replace('\\', '/').split('/')
    
    # Find scenario and run information
    run_id_parts = []
    for i, part in enumerate(path_parts):
        if 'scenario' in part.lower():
            run_id_parts.append(part)
            # Also add the next part if it contains date/time info
            if i + 1 < len(path_parts) and ('250703' in path_parts[i + 1] or 'run' in path_parts[i + 1]):
                run_id_parts.append(path_parts[i + 1])
            break
    
    if not run_id_parts:
        # Fallback: use the parent directory name
        run_id_parts = [path_parts[-3] if len(path_parts) >= 3 else path_parts[-2]]
    
    return '/'.join(run_id_parts)

def create_detailed_kg_table(folder_path: str) -> pd.DataFrame:
    """
    Create a detailed table showing KG elements across runs with variance analysis.
    
    Args:
        folder_path: Path to the folder containing evaluation_data files
        
    Returns:
        DataFrame with KG elements as rows, runs as columns, plus statistics
    """
    evaluation_files = find_evaluation_data_files(folder_path)
    
    if not evaluation_files:
        print(f"No evaluation_data files found in {folder_path}")
        return pd.DataFrame()
    
    # Process each file and collect data by run
    run_data = {}  # run_id -> {kg_element -> {effort, count, bloom_verbs}}
    all_kg_elements = set()
    
    for file_path in evaluation_files:
        try:
            file_data = group_evaluations_by_kg_element(file_path)
            run_id = extract_run_identifier(os.path.relpath(file_path, folder_path))
            
            run_data[run_id] = {}
            for kg_element, data in file_data.items():
                # Skip KG elements with '(decision point)' or '(lookup)'
                if '(decision point)' in kg_element or '(lookup)' in kg_element:
                    continue
                    
                effort = data['total_human_effort']
                count = data['total_evaluations']  # Number of occurrences/evaluations
                bloom_verbs = data.get('bloom_verbs', [])
                run_data[run_id][kg_element] = {
                    'effort': effort,
                    'count': count,
                    'bloom_verbs': bloom_verbs
                }
                all_kg_elements.add(kg_element)
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    # Create DataFrame
    df_data = []
    for kg_element in sorted(all_kg_elements):
        # Skip KG elements with '(decision point)' or '(lookup)'
        if '(decision point)' in kg_element or '(lookup)' in kg_element:
            continue
            
        row = {'KG_Element': kg_element}
        
        # Add effort values and counts for each run
        efforts = []
        counts = []
        all_bloom_verbs = []
        
        for run_id in sorted(run_data.keys()):
            run_kg_data = run_data[run_id].get(kg_element, {'effort': 0, 'count': 0, 'bloom_verbs': []})
            effort = run_kg_data['effort']
            count = run_kg_data['count']
            bloom_verbs = run_kg_data.get('bloom_verbs', [])
            
            row[f"{run_id}_effort"] = effort
            row[f"{run_id}_count"] = count
            row[f"{run_id}_bloom_verbs"] = ', '.join(bloom_verbs) if bloom_verbs else ''
            
            if effort > 0:  # Only include non-zero values for statistics
                efforts.append(effort)
            if count > 0:
                counts.append(count)
            all_bloom_verbs.extend(bloom_verbs)
        
        # Calculate statistics for effort
        if efforts:
            row['Total_Effort'] = sum(efforts)
            row['Avg_Effort'] = np.mean(efforts)
            row['Effort_Variance'] = np.var(efforts, ddof=1) if len(efforts) > 1 else 0
            row['Effort_Std_Dev'] = np.std(efforts, ddof=1) if len(efforts) > 1 else 0
        else:
            row['Total_Effort'] = 0
            row['Avg_Effort'] = 0
            row['Effort_Variance'] = 0
            row['Effort_Std_Dev'] = 0
            
        # Calculate statistics for counts
        if counts:
            row['Total_Count'] = sum(counts)
            row['Avg_Count'] = np.mean(counts)
            row['Count_Variance'] = np.var(counts, ddof=1) if len(counts) > 1 else 0
            row['Count_Std_Dev'] = np.std(counts, ddof=1) if len(counts) > 1 else 0
            row['Runs_Present'] = len(counts)
        else:
            row['Total_Count'] = 0
            row['Avg_Count'] = 0
            row['Count_Variance'] = 0
            row['Count_Std_Dev'] = 0
            row['Runs_Present'] = 0
        
        # Add bloom verb statistics
        unique_bloom_verbs = list(set(all_bloom_verbs))
        row['Unique_Bloom_Verbs'] = ', '.join(unique_bloom_verbs[:10])  # Show first 10 unique verbs
        row['Bloom_Verb_Count'] = len(unique_bloom_verbs)
        
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # Sort by total effort (descending)
    df = df.sort_values('Total_Effort', ascending=False)
    
    return df

def print_detailed_kg_table(df: pd.DataFrame, max_runs_display: int = 5) -> None:
    """
    Print a formatted version of the detailed KG table.
    
    Args:
        df: DataFrame with KG element analysis
        max_runs_display: Maximum number of run columns to display
    """
    if df.empty:
        print("No data to display.")
        return
    
    # Get run columns (exclude metadata columns)
    metadata_cols = ['KG_Element', 'Total_Effort', 'Avg_Effort', 'Effort_Variance', 'Effort_Std_Dev', 
                     'Total_Count', 'Avg_Count', 'Count_Variance', 'Count_Std_Dev', 'Runs_Present',
                     'Unique_Bloom_Verbs', 'Bloom_Verb_Count']
    run_cols = [col for col in df.columns if col not in metadata_cols]
    
    # Get unique run names (removing _effort, _count, and _bloom_verbs suffixes)
    run_names = sorted(list(set(col.replace('_effort', '').replace('_count', '').replace('_bloom_verbs', '') for col in run_cols)))
    
    # Limit run columns if too many
    if len(run_names) > max_runs_display:
        display_runs = run_names[:max_runs_display]
        print(f"Note: Showing first {max_runs_display} of {len(run_names)} runs. Full data saved to CSV.")
    else:
        display_runs = run_names
    
    # Format for better display
    print(f"\n{'='*140}")
    print("DETAILED KG ELEMENT ANALYSIS BY RUN (Effort/Count)")
    print(f"{'='*140}")
    
    # Print header
    header = f"{'KG Element':<30}"
    for run in display_runs:
        header += f"{run[:12]:<15}"  # Effort/Count pairs
    header += f"{'T.Eff':<8}{'A.Eff':<8}{'T.Cnt':<8}{'A.Cnt':<8}{'Runs':<6}"
    print(header)
    print("-" * len(header))
    
    # Print data rows
    for _, row in df.head(20).iterrows():  # Show top 20 KG elements
        kg_element = row['KG_Element']
        
        # Skip KG elements with '(decision point)' or '(lookup)'
        if '(decision point)' in kg_element or '(lookup)' in kg_element:
            continue
        
        line = f"{kg_element[:29]:<30}"
        for run in display_runs:
            effort_col = f"{run}_effort"
            count_col = f"{run}_count"
            effort = row[effort_col] if effort_col in row and pd.notna(row[effort_col]) else 0
            count = row[count_col] if count_col in row and pd.notna(row[count_col]) else 0
            
            if effort > 0 or count > 0:
                line += f"{int(effort)}/{int(count):<12}"  # Format as effort/count
            else:
                line += f"{'.':<15}"
                
        line += f"{int(row['Total_Effort']):<8}"
        line += f"{row['Avg_Effort']:<8.1f}"
        line += f"{int(row['Total_Count']):<8}"
        line += f"{row['Avg_Count']:<8.1f}"
        line += f"{int(row['Runs_Present']):<6}"
        print(line)
    
    if len(df) > 20:
        print(f"... and {len(df)-20} more KG elements (see CSV file for complete data)")
    
    print(f"\nSummary: {len(df)} unique KG elements across {len(display_runs)} runs")
    print("Format: effort/count per run")
    print("T.Eff=Total Effort, A.Eff=Average Effort, T.Cnt=Total Count, A.Cnt=Average Count")

def print_occurrence_summary(df: pd.DataFrame) -> None:
    """
    Print a summary focused on occurrence counts of KG elements.
    
    Args:
        df: DataFrame with KG element analysis including count information
    """
    if df.empty:
        print("No data to display.")
        return
    
    print(f"\n{'='*80}")
    print("KG ELEMENT OCCURRENCE SUMMARY")
    print(f"{'='*80}")
    print(f"{'KG Element':<40} {'Total Occur.':<12} {'Avg Occur.':<12} {'Count Var.':<12} {'Runs':<6}")
    print("-" * 80)
    
    # Sort by total count (descending)
    sorted_df = df.sort_values('Total_Count', ascending=False)
    
    for _, row in sorted_df.head(25).iterrows():  # Show top 25 by occurrence
        kg_element = row['KG_Element']
        
        # Skip KG elements with '(decision point)' or '(lookup)'
        if '(decision point)' in kg_element or '(lookup)' in kg_element:
            continue
            
        kg_element_display = kg_element[:39]  # Truncate if too long
        total_count = int(row['Total_Count'])
        avg_count = row['Avg_Count']
        count_var = row['Count_Variance']
        runs_present = int(row['Runs_Present'])
        
        print(f"{kg_element_display:<40} {total_count:<12} {avg_count:<12.1f} {count_var:<12.1f} {runs_present:<6}")
    
    if len(df) > 25:
        print(f"... and {len(df)-25} more KG elements")
    
    print(f"\nTotal unique KG elements: {len(df)}")
    print(f"Total occurrences across all runs: {int(df['Total_Count'].sum())}")
    print(f"Average occurrences per KG element: {df['Total_Count'].mean():.1f}")

def create_kg_element_runs_table(folder_path: str) -> pd.DataFrame:
    """
    Create a table showing KG elements with number of steps and sum of human effort across runs.
    Format matches the table structure with runs as columns and metrics as sub-columns.
    
    Args:
        folder_path: Path to the folder containing evaluation_data files
        
    Returns:
        DataFrame with KG elements as rows, runs and metrics as hierarchical columns
    """
    evaluation_files = find_evaluation_data_files(folder_path)
    
    if not evaluation_files:
        print(f"No evaluation_data files found in {folder_path}")
        return pd.DataFrame()
    
    # Process each file and collect data by run
    run_data = {}  # run_id -> {kg_element -> {'steps': count, 'effort': total_effort, 'bloom_verbs': list}}
    all_kg_elements = set()
    
    for file_path in evaluation_files:
        try:
            file_data = group_evaluations_by_kg_element(file_path)
            run_id = extract_run_identifier(os.path.relpath(file_path, folder_path))
            
            run_data[run_id] = {}
            for kg_element, data in file_data.items():
                # Skip KG elements with '(decision point)' or '(lookup)'
                if '(decision point)' in kg_element or '(lookup)' in kg_element:
                    continue
                    
                effort = data['total_human_effort']
                steps = data['total_evaluations']  # Number of evaluation steps
                bloom_verbs = data.get('bloom_verbs', [])
                run_data[run_id][kg_element] = {
                    'steps': steps,
                    'effort': effort,
                    'bloom_verbs': bloom_verbs
                }
                all_kg_elements.add(kg_element)
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    # Create DataFrame with hierarchical structure
    df_data = []
    run_ids = sorted(run_data.keys())
    
    for kg_element in sorted(all_kg_elements):
        # Skip KG elements with '(decision point)' or '(lookup)'
        if '(decision point)' in kg_element or '(lookup)' in kg_element:
            continue
            
        row = {'KG_Element': kg_element}
        
        # Collect data for statistics
        steps_values = []
        effort_values = []
        all_bloom_verbs = []
        
        # Add data for each run
        for run_id in run_ids:
            run_kg_data = run_data[run_id].get(kg_element, {'steps': 0, 'effort': 0, 'bloom_verbs': []})
            steps = run_kg_data['steps']
            effort = run_kg_data['effort']
            bloom_verbs = run_kg_data.get('bloom_verbs', [])
            
            row[f"{run_id}_steps"] = steps
            row[f"{run_id}_effort"] = effort
            row[f"{run_id}_bloom_verbs"] = ', '.join(bloom_verbs) if bloom_verbs else ''
            
            if steps > 0:
                steps_values.append(steps)
            if effort > 0:
                effort_values.append(effort)
            all_bloom_verbs.extend(bloom_verbs)
        
        # Calculate statistics for steps
        if steps_values:
            row['steps_median'] = np.median(steps_values)
            row['steps_std'] = np.std(steps_values, ddof=1) if len(steps_values) > 1 else 0
        else:
            row['steps_median'] = 0
            row['steps_std'] = 0
            
        # Calculate statistics for effort
        if effort_values:
            row['effort_median'] = np.median(effort_values)
            row['effort_std'] = np.std(effort_values, ddof=1) if len(effort_values) > 1 else 0
        else:
            row['effort_median'] = 0
            row['effort_std'] = 0
        
        # Mark if this element is present in runs
        row['runs_present'] = len([r for r in run_ids if kg_element in run_data[r]])
        
        # Add bloom verb statistics
        unique_bloom_verbs = list(set(all_bloom_verbs))
        row['unique_bloom_verbs'] = ', '.join(unique_bloom_verbs[:10])  # Show first 10 unique verbs
        row['bloom_verb_count'] = len(unique_bloom_verbs)
        
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # Sort by total effort (sum across all runs)
    effort_cols = [col for col in df.columns if col.endswith('_effort')]
    df['total_effort_all_runs'] = df[effort_cols].sum(axis=1)
    df = df.sort_values('total_effort_all_runs', ascending=False)
    
    return df

def print_kg_element_runs_table(df: pd.DataFrame, max_runs_display: int = 5) -> None:
    """
    Print the KG element runs table in the format shown in the image.
    
    Args:
        df: DataFrame with KG element runs data
        max_runs_display: Maximum number of runs to display
    """
    if df.empty:
        print("No data to display.")
        return
    
    # Get run columns
    all_cols = df.columns.tolist()
    run_cols = [col for col in all_cols if '_steps' in col or '_effort' in col]
    
    # Extract unique run names
    run_names = sorted(list(set(col.replace('_steps', '').replace('_effort', '') for col in run_cols)))
    
    # Limit displayed runs if too many
    if len(run_names) > max_runs_display:
        display_runs = run_names[:max_runs_display]
        print(f"Note: Showing first {max_runs_display} of {len(run_names)} runs")
    else:
        display_runs = run_names
    
    print(f"\n{'='*120}")
    print("KG ELEMENT PERFORMANCE TABLE")
    print(f"{'='*120}")
    
    # Print table for each KG element (similar to the image format)
    for idx, (_, row) in enumerate(df.head(10).iterrows()):  # Show top 10 KG elements
        kg_element = row['KG_Element']
        
        # Skip KG elements with '(decision point)' or '(lookup)'
        if '(decision point)' in kg_element or '(lookup)' in kg_element:
            continue
        
        print(f"\n{kg_element} (extra node)")
        print("-" * 80)
        
        # Header row
        header = f"{'file':<15}"
        for run in display_runs:
            run_short = run[-1] if len(run) > 0 else run  # Use last character as file identifier
            header += f"{run_short:<12}"
        header += f"{'...':<8}{'median':<10}{'Standard Deviation':<18}"
        print(header)
        
        # Number of steps row
        steps_row = f"{'number of steps':<15}"
        steps_values = []
        for run in display_runs:
            steps_col = f"{run}_steps"
            steps = int(row[steps_col]) if steps_col in row and pd.notna(row[steps_col]) and row[steps_col] > 0 else ""
            steps_row += f"{steps:<12}"
            if steps != "":
                steps_values.append(int(steps))
        
        steps_row += f"{'...':<8}"
        steps_row += f"{int(row['steps_median']):<10}" if row['steps_median'] > 0 else f"{'0':<10}"
        steps_row += f"{row['steps_std']:<18.1f}" if row['steps_std'] > 0 else f"{'0':<18}"
        print(steps_row)
        
        # Sum of human effort row
        effort_row = f"{'sum of human effort':<15}"
        effort_values = []
        for run in display_runs:
            effort_col = f"{run}_effort"
            effort = int(row[effort_col]) if effort_col in row and pd.notna(row[effort_col]) and row[effort_col] > 0 else ""
            effort_row += f"{effort:<12}"
            if effort != "":
                effort_values.append(int(effort))
        
        effort_row += f"{'...':<8}"
        effort_row += f"{int(row['effort_median']):<10}" if row['effort_median'] > 0 else f"{'0':<10}"
        effort_row += f"{row['effort_std']:<18.1f}" if row['effort_std'] > 0 else f"{'0':<18}"
        print(effort_row)
        
        if idx < 9:  # Add separator between KG elements except for the last one
            print()
    
    if len(df) > 10:
        print(f"\n... and {len(df)-10} more KG elements")
    
    print(f"\nTotal KG elements: {len(df)}")
    print(f"Runs analyzed: {len(run_names)}")

def print_kg_element_runs_table_with_bloom_verbs(df: pd.DataFrame, max_runs_display: int = 5) -> None:
    """
    Print the KG element runs table with bloom verbs included.
    
    Args:
        df: DataFrame with KG element runs data including bloom verbs
        max_runs_display: Maximum number of runs to display
    """
    if df.empty:
        print("No data to display.")
        return
    
    # Get run columns
    all_cols = df.columns.tolist()
    run_cols = [col for col in all_cols if '_steps' in col or '_effort' in col or '_bloom_verbs' in col]
    
    # Extract unique run names
    run_names = sorted(list(set(col.replace('_steps', '').replace('_effort', '').replace('_bloom_verbs', '') for col in run_cols)))
    
    # Limit displayed runs if too many
    if len(run_names) > max_runs_display:
        display_runs = run_names[:max_runs_display]
        print(f"Note: Showing first {max_runs_display} of {len(run_names)} runs")
    else:
        display_runs = run_names
    
    print(f"\n{'='*140}")
    print("KG ELEMENT PERFORMANCE TABLE WITH BLOOM VERBS")
    print(f"{'='*140}")
    
    # Print table for each KG element
    for idx, (_, row) in enumerate(df.head(10).iterrows()):  # Show top 10 KG elements
        kg_element = row['KG_Element']
        
        # Skip KG elements with '(decision point)' or '(lookup)'
        if '(decision point)' in kg_element or '(lookup)' in kg_element:
            continue
        
        print(f"\n{kg_element} (extra node)")
        print("-" * 100)
        
        # Header row
        header = f"{'metric':<20}"
        for run in display_runs:
            run_short = run.split('/')[-1][-8:] if '/' in run else run[-8:]  # Use last 8 chars as identifier
            header += f"{run_short:<15}"
        header += f"{'...':<8}{'median':<10}{'Std Dev':<10}{'Unique Verbs':<25}"
        print(header)
        
        # Number of steps row
        steps_row = f"{'number of steps':<20}"
        steps_values = []
        for run in display_runs:
            steps_col = f"{run}_steps"
            steps = int(row[steps_col]) if steps_col in row and pd.notna(row[steps_col]) and row[steps_col] > 0 else ""
            steps_row += f"{steps:<15}"
            if steps != "":
                steps_values.append(int(steps))
        
        steps_row += f"{'...':<8}"
        steps_row += f"{int(row['steps_median']):<10}" if row['steps_median'] > 0 else f"{'0':<10}"
        steps_row += f"{row['steps_std']:<10.1f}" if row['steps_std'] > 0 else f"{'0':<10}"
        steps_row += f"{'':<25}"  # No verbs for steps row
        print(steps_row)
        
        # Sum of human effort row
        effort_row = f"{'sum of human effort':<20}"
        effort_values = []
        for run in display_runs:
            effort_col = f"{run}_effort"
            effort = int(row[effort_col]) if effort_col in row and pd.notna(row[effort_col]) and row[effort_col] > 0 else ""
            effort_row += f"{effort:<15}"
            if effort != "":
                effort_values.append(int(effort))
        
        effort_row += f"{'...':<8}"
        effort_row += f"{int(row['effort_median']):<10}" if row['effort_median'] > 0 else f"{'0':<10}"
        effort_row += f"{row['effort_std']:<10.1f}" if row['effort_std'] > 0 else f"{'0':<10}"
        unique_verbs = row.get('unique_bloom_verbs', '')
        unique_verbs_display = unique_verbs[:22] + "..." if len(str(unique_verbs)) > 22 else str(unique_verbs)
        effort_row += f"{unique_verbs_display:<25}"
        print(effort_row)
        
        # Bloom verbs row for each run
        bloom_verbs_row = f"{'bloom verbs':<20}"
        for run in display_runs:
            bloom_verbs_col = f"{run}_bloom_verbs"
            bloom_verbs = row[bloom_verbs_col] if bloom_verbs_col in row and pd.notna(row[bloom_verbs_col]) else ""
            bloom_verbs_display = bloom_verbs[:12] + "..." if len(str(bloom_verbs)) > 12 else str(bloom_verbs)
            bloom_verbs_row += f"{bloom_verbs_display:<15}"
        
        bloom_verbs_row += f"{'...':<8}"
        bloom_verbs_row += f"{'N/A':<10}"  # No median for bloom verbs
        bloom_verbs_row += f"{'N/A':<10}"  # No std dev for bloom verbs
        verb_count = row.get('bloom_verb_count', 0)
        bloom_verbs_row += f"{'(' + str(verb_count) + ' unique)':<25}"
        print(bloom_verbs_row)
        
        if idx < 9:  # Add separator between KG elements except for the last one
            print()
    
    if len(df) > 10:
        print(f"\n... and {len(df)-10} more KG elements")
    
    print(f"\nTotal KG elements: {len(df)}")
    print(f"Runs analyzed: {len(run_names)}")

def create_bloom_verb_frequency_by_steps_table(folder_path: str) -> pd.DataFrame:
    """
    Create a table showing bloom verbs and their frequency, grouped by the count of steps per KG element.
    
    Args:
        folder_path: Path to the folder containing evaluation_data files
        
    Returns:
        DataFrame with KG elements, their step counts, and bloom verb frequencies
    """
    evaluation_files = find_evaluation_data_files(folder_path)
    
    if not evaluation_files:
        print(f"No evaluation_data files found in {folder_path}")
        return pd.DataFrame()
    
    # Collect data from all files
    kg_element_data = {}  # kg_element -> {'total_steps': int, 'bloom_verbs': list}
    
    for file_path in evaluation_files:
        try:
            file_data = group_evaluations_by_kg_element(file_path)
            
            for kg_element, data in file_data.items():
                # Skip KG elements with '(decision point)' or '(lookup)'
                if '(decision point)' in kg_element or '(lookup)' in kg_element:
                    continue
                
                if kg_element not in kg_element_data:
                    kg_element_data[kg_element] = {'total_steps': 0, 'bloom_verbs': []}
                
                kg_element_data[kg_element]['total_steps'] += data['total_evaluations']
                kg_element_data[kg_element]['bloom_verbs'].extend(data.get('bloom_verbs', []))
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    if not kg_element_data:
        return pd.DataFrame()
    
    # Create DataFrame
    df_data = []
    
    for kg_element, data in kg_element_data.items():
        total_steps = data['total_steps']
        bloom_verbs = data['bloom_verbs']
        
        if not bloom_verbs:  # Skip KG elements with no bloom verbs
            continue
        
        # Count frequency of each bloom verb for this KG element
        verb_counts = Counter(bloom_verbs)
        
        # Create a row for each unique bloom verb
        for bloom_verb, frequency in verb_counts.items():
            df_data.append({
                'KG_Element': kg_element,
                'Total_Steps': total_steps,
                'Bloom_Verb': bloom_verb,
                'Frequency': frequency,
                'Relative_Frequency': frequency / len(bloom_verbs) if bloom_verbs else 0,
                'Steps_Per_Verb_Occurrence': total_steps / frequency if frequency > 0 else 0
            })
    
    df = pd.DataFrame(df_data)
    
    if df.empty:
        return df
    
    # Sort by Total_Steps (descending), then by Frequency (descending)
    df = df.sort_values(['Total_Steps', 'Frequency'], ascending=[False, False])
    
    return df

def print_bloom_verb_frequency_by_steps_table(df: pd.DataFrame, max_kg_elements: int = 20) -> None:
    """
    Print the bloom verb frequency table grouped by steps per KG element.
    
    Args:
        df: DataFrame with bloom verb frequency data
        max_kg_elements: Maximum number of KG elements to display
    """
    if df.empty:
        print("No bloom verb data to display.")
        return
    
    print(f"\n{'='*140}")
    print("BLOOM VERB FREQUENCY BY STEPS PER KG ELEMENT")
    print(f"{'='*140}")
    
    # Get unique KG elements and their step counts
    kg_elements_steps = df[['KG_Element', 'Total_Steps']].drop_duplicates().sort_values('Total_Steps', ascending=False)
    
    displayed_count = 0
    
    for _, kg_row in kg_elements_steps.iterrows():
        if displayed_count >= max_kg_elements:
            break
            
        kg_element = kg_row['KG_Element']
        total_steps = kg_row['Total_Steps']
        
        # Get all bloom verbs for this KG element
        kg_verbs = df[df['KG_Element'] == kg_element].sort_values('Frequency', ascending=False)
        
        print(f"\n{kg_element} (Total Steps: {total_steps})")
        print("-" * 100)
        print(f"{'Bloom Verb':<20} {'Frequency':<12} {'Rel. Freq.':<12} {'Steps/Occurrence':<18}")
        print("-" * 100)
        
        for _, verb_row in kg_verbs.iterrows():
            bloom_verb = verb_row['Bloom_Verb']
            frequency = verb_row['Frequency']
            rel_frequency = verb_row['Relative_Frequency']
            steps_per_occurrence = verb_row['Steps_Per_Verb_Occurrence']
            
            print(f"{bloom_verb:<20} {frequency:<12} {rel_frequency:<12.2%} {steps_per_occurrence:<18.1f}")
        
        displayed_count += 1
        
        if displayed_count < max_kg_elements and displayed_count < len(kg_elements_steps):
            print()  # Add separator between KG elements
    
    if len(kg_elements_steps) > max_kg_elements:
        print(f"\n... and {len(kg_elements_steps) - max_kg_elements} more KG elements")
    
    print(f"\nTotal KG elements with bloom verbs: {len(kg_elements_steps)}")
    print(f"Total unique bloom verbs: {df['Bloom_Verb'].nunique()}")

def print_bloom_verb_summary_by_steps(df: pd.DataFrame) -> None:
    """
    Print a summary of bloom verbs grouped by step count ranges.
    
    Args:
        df: DataFrame with bloom verb frequency data
    """
    if df.empty:
        print("No bloom verb data to display.")
        return
    
    print(f"\n{'='*120}")
    print("BLOOM VERB SUMMARY BY STEP COUNT RANGES")
    print(f"{'='*120}")
    
    # Create step count ranges
    step_ranges = [
        (1, 10, "1-10 steps"),
        (11, 50, "11-50 steps"),
        (51, 100, "51-100 steps"),
        (101, 200, "101-200 steps"),
        (201, float('inf'), "200+ steps")
    ]
    
    for min_steps, max_steps, range_label in step_ranges:
        # Filter KG elements in this step range
        if max_steps == float('inf'):
            range_df = df[df['Total_Steps'] >= min_steps]
        else:
            range_df = df[(df['Total_Steps'] >= min_steps) & (df['Total_Steps'] <= max_steps)]
        
        if range_df.empty:
            continue
        
        print(f"\n{range_label}:")
        print("-" * 60)
        
        # Count bloom verbs in this range
        verb_frequency = Counter()
        total_occurrences = 0
        
        for _, row in range_df.iterrows():
            verb_frequency[row['Bloom_Verb']] += row['Frequency']
            total_occurrences += row['Frequency']
        
        # Show top 10 bloom verbs in this range
        print(f"{'Bloom Verb':<20} {'Total Freq.':<12} {'Percentage':<12} {'KG Elements':<12}")
        print("-" * 60)
        
        for bloom_verb, total_freq in verb_frequency.most_common(10):
            kg_count = len(range_df[range_df['Bloom_Verb'] == bloom_verb]['KG_Element'].unique())
            percentage = (total_freq / total_occurrences) * 100 if total_occurrences > 0 else 0
            print(f"{bloom_verb:<20} {total_freq:<12} {percentage:<12.1f}% {kg_count:<12}")
        
        print(f"\nKG elements in range: {range_df['KG_Element'].nunique()}")
        print(f"Total bloom verb occurrences: {total_occurrences}")

def save_bloom_verb_frequency_table_to_csv(df: pd.DataFrame, filename: str = "bloom_verb_frequency_by_steps.csv") -> None:
    """
    Save the bloom verb frequency table to CSV.
    
    Args:
        df: DataFrame with bloom verb frequency data
        filename: Output CSV filename
    """
    if df.empty:
        print("No data to export.")
        return
    
    df.to_csv(filename, index=False)
    print(f"Bloom verb frequency table exported to {filename}")

def save_kg_element_runs_table_to_csv(df: pd.DataFrame, filename: str = "kg_element_runs_table.csv") -> None:
    """
    Export the KG element runs table to CSV with proper formatting.
    
    Args:
        df: DataFrame with KG element runs data
        filename: Output CSV filename
    """
    if df.empty:
        print("No data to export.")
        return
    
    # Create a more readable export format
    export_df = df.copy()
    
    # Drop the total effort column used for sorting
    if 'total_effort_all_runs' in export_df.columns:
        export_df = export_df.drop('total_effort_all_runs', axis=1)
    
    # Reorder columns for better readability
    kg_col = ['KG_Element']
    run_cols = [col for col in export_df.columns if '_steps' in col or '_effort' in col or '_bloom_verbs' in col]
    stat_cols = [col for col in export_df.columns if col.endswith('_median') or col.endswith('_std') or 
                 col in ['runs_present', 'unique_bloom_verbs', 'bloom_verb_count']]
    
    # Sort run columns
    run_cols = sorted(run_cols)
    
    new_order = kg_col + run_cols + stat_cols
    export_df = export_df[new_order]
    
    export_df.to_csv(filename, index=False)
    print(f"KG element runs table exported to {filename}")

def get_all_kg_elements(folder_path: str) -> List[str]:
    """
    Get a list of all unique KG elements across all evaluation files.
    
    Args:
        folder_path: Path to the folder containing evaluation_data files
        
    Returns:
        Sorted list of unique KG elements (excluding decision points and lookups)
    """
    evaluation_files = find_evaluation_data_files(folder_path)
    
    if not evaluation_files:
        print(f"No evaluation_data files found in {folder_path}")
        return []
    
    all_kg_elements = set()
    
    for file_path in evaluation_files:
        try:
            file_data = group_evaluations_by_kg_element(file_path)
            for kg_element in file_data.keys():
                # Skip KG elements with '(decision point)' or '(lookup)'
                if '(decision point)' not in kg_element and '(lookup)' not in kg_element:
                    all_kg_elements.add(kg_element)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    return sorted(list(all_kg_elements))

def check_kg_element_presence(folder_path: str, selected_kg_element: str) -> Dict[str, bool]:
    """
    Check if the selected KG element is present in all evaluation files.
    
    Args:
        folder_path: Path to the folder containing evaluation_data files
        selected_kg_element: The KG element to check for
        
    Returns:
        Dictionary mapping file paths to presence boolean
    """
    evaluation_files = find_evaluation_data_files(folder_path)
    presence_map = {}
    
    for file_path in evaluation_files:
        try:
            file_data = group_evaluations_by_kg_element(file_path)
            presence_map[file_path] = selected_kg_element in file_data
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            presence_map[file_path] = False
    
    return presence_map

def create_kg_element_detailed_table(folder_path: str, selected_kg_element: str) -> pd.DataFrame:
    """
    Create a detailed table for a specific KG element showing steps and effort across runs.
    
    Args:
        folder_path: Path to the folder containing evaluation_data files
        selected_kg_element: The specific KG element to analyze
        
    Returns:
        DataFrame with the selected KG element's data across runs
    """
    evaluation_files = find_evaluation_data_files(folder_path)
    
    if not evaluation_files:
        print(f"No evaluation_data files found in {folder_path}")
        return pd.DataFrame()
    
    # Check if KG element is present in all files
    presence_map = check_kg_element_presence(folder_path, selected_kg_element)
    missing_files = [file_path for file_path, present in presence_map.items() if not present]
    
    if missing_files:
        print(f"ERROR: KG element '{selected_kg_element}' is not present in all files!")
        print("Missing from the following files:")
        for file_path in missing_files:
            print(f"  - {os.path.relpath(file_path, folder_path)}")
        return pd.DataFrame()
    
    # Process each file and collect data
    run_data = {}  # run_id -> {'steps': count, 'effort': total_effort, 'bloom_verbs': list}
    
    for file_path in evaluation_files:
        try:
            file_data = group_evaluations_by_kg_element(file_path)
            run_id = extract_run_identifier(os.path.relpath(file_path, folder_path))
            
            if selected_kg_element in file_data:
                data = file_data[selected_kg_element]
                run_data[run_id] = {
                    'steps': data['total_evaluations'],
                    'effort': data['total_human_effort'],
                    'bloom_verbs': data.get('bloom_verbs', [])
                }
            else:
                # This shouldn't happen due to the check above, but just in case
                run_data[run_id] = {'steps': 0, 'effort': 0, 'bloom_verbs': []}
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    # Create DataFrame in the format matching the table structure
    if not run_data:
        return pd.DataFrame()
    
    # Sort run IDs for consistent ordering
    sorted_runs = sorted(run_data.keys())
    
    # Create the table data
    table_data = []
    
    # Steps row
    steps_row = {'metric': 'number of steps'}
    effort_row = {'metric': 'sum of human effort'}
    bloom_verbs_row = {'metric': 'bloom verbs'}
    
    for run_id in sorted_runs:
        steps_row[run_id] = run_data[run_id]['steps']
        effort_row[run_id] = run_data[run_id]['effort']
        bloom_verbs_row[run_id] = ', '.join(run_data[run_id]['bloom_verbs']) if run_data[run_id]['bloom_verbs'] else ''
    
    # Calculate statistics
    steps_values = [run_data[run_id]['steps'] for run_id in sorted_runs]
    effort_values = [run_data[run_id]['effort'] for run_id in sorted_runs]
    all_bloom_verbs = [verb for run_id in sorted_runs for verb in run_data[run_id]['bloom_verbs']]
    
    steps_row['median'] = np.median(steps_values)
    steps_row['std_dev'] = np.std(steps_values, ddof=1) if len(steps_values) > 1 else 0
    
    effort_row['median'] = np.median(effort_values)
    effort_row['std_dev'] = np.std(effort_values, ddof=1) if len(effort_values) > 1 else 0
    
    # For bloom verbs, show unique verbs and count
    unique_bloom_verbs = list(set(all_bloom_verbs))
    bloom_verbs_row['median'] = ', '.join(unique_bloom_verbs[:5]) + (f" (+{len(unique_bloom_verbs)-5} more)" if len(unique_bloom_verbs) > 5 else "")
    bloom_verbs_row['std_dev'] = f"{len(unique_bloom_verbs)} unique"
    
    table_data.append(steps_row)
    table_data.append(effort_row)
    table_data.append(bloom_verbs_row)
    
    df = pd.DataFrame(table_data)
    return df

def print_kg_element_detailed_table(df: pd.DataFrame, kg_element: str) -> None:
    """
    Print a detailed table for a specific KG element in the format shown in the image.
    
    Args:
        df: DataFrame with the KG element's data
        kg_element: The name of the KG element
    """
    if df.empty:
        print("No data to display.")
        return
    
    print(f"\n{'='*120}")
    print(f"{kg_element} (extra node)")
    print(f"{'='*120}")
    
    # Get run columns (exclude metric, median, std_dev)
    run_cols = [col for col in df.columns if col not in ['metric', 'median', 'std_dev']]
    
    # Create header
    header = f"{'file':<20}"
    for run_col in run_cols:
        # Use just the last part of the run identifier for display
        col_display = run_col.split('/')[-1] if '/' in run_col else run_col
        header += f"{col_display[:10]:<12}"
    header += f"{'...':<8}{'median':<10}{'Standard Deviation':<18}"
    print(header)
    print("-" * len(header))
    
    # Print each row
    for _, row in df.iterrows():
        metric = row['metric']
        line = f"{metric:<20}"
        
        for run_col in run_cols:
            value = row[run_col]
            if pd.notna(value) and value > 0:
                line += f"{int(value):<12}"
            else:
                line += f"{'':>12}"
        
        line += f"{'...':<8}"
        line += f"{int(row['median']):<10}" if pd.notna(row['median']) else f"{'0':<10}"
        line += f"{row['std_dev']:<18.1f}" if pd.notna(row['std_dev']) else f"{'0':<18}"
        print(line)
    
    print(f"\nRuns analyzed: {len(run_cols)}")

def interactive_kg_element_selection(folder_path: str) -> None:
    """
    Interactive function to let user select a KG element and display its detailed table.
    
    Args:
        folder_path: Path to the folder containing evaluation_data files
    """
    # Get all KG elements
    kg_elements = get_all_kg_elements(folder_path)
    
    if not kg_elements:
        print("No KG elements found in the evaluation files.")
        return
    
    print(f"\nFound {len(kg_elements)} unique KG elements:")
    print("="*60)
    
    # Display numbered list
    for i, kg_element in enumerate(kg_elements, 1):
        print(f"{i:3d}. {kg_element}")
    
    print("="*60)
    
    # Get user selection
    try:
        selection = input(f"\nEnter the number of the KG element you want to analyze (1-{len(kg_elements)}): ").strip()
        
        if not selection:
            print("No selection made. Exiting.")
            return
            
        selection_num = int(selection)
        
        if selection_num < 1 or selection_num > len(kg_elements):
            print(f"Invalid selection. Please enter a number between 1 and {len(kg_elements)}.")
            return
            
        selected_kg_element = kg_elements[selection_num - 1]
        
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return
    
    print(f"\nSelected KG element: {selected_kg_element}")
    print("Creating detailed table...")
    
    # Create and display the detailed table
    detailed_table = create_kg_element_detailed_table(folder_path, selected_kg_element)
    
    if not detailed_table.empty:
        print_kg_element_detailed_table(detailed_table, selected_kg_element)
    else:
        print("No data available for the selected KG element.")

def print_bloom_verb_analysis(df: pd.DataFrame, max_runs_display: int = 5) -> None:
    """
    Print a detailed analysis of bloom verbs for each KG element across runs.
    
    Args:
        df: DataFrame with KG element analysis including bloom verb data
        max_runs_display: Maximum number of runs to display
    """
    if df.empty:
        print("No data to display.")
        return
    
    # Get run columns with bloom_verbs data
    bloom_verb_cols = [col for col in df.columns if col.endswith('_bloom_verbs')]
    run_names = sorted([col.replace('_bloom_verbs', '') for col in bloom_verb_cols])
    
    # Limit displayed runs if too many
    if len(run_names) > max_runs_display:
        display_runs = run_names[:max_runs_display]
        print(f"Note: Showing first {max_runs_display} of {len(run_names)} runs")
    else:
        display_runs = run_names
    
    print(f"\n{'='*150}")
    print("BLOOM VERB ANALYSIS BY KG ELEMENT AND RUN")
    print(f"{'='*150}")
    
    # Print header
    header = f"{'KG Element':<35}"
    for run in display_runs:
        header += f"{run[:20]:<25}"
    header += f"{'Unique Verbs':<20}"
    print(header)
    print("-" * len(header))
    
    # Print data rows for top KG elements
    for _, row in df.head(15).iterrows():  # Show top 15 KG elements
        kg_element = row['KG_Element']
        
        # Skip KG elements with '(decision point)' or '(lookup)'
        if '(decision point)' in kg_element or '(lookup)' in kg_element:
            continue
        
        line = f"{kg_element[:34]:<35}"
        
        for run in display_runs:
            bloom_verbs_col = f"{run}_bloom_verbs"
            if bloom_verbs_col in row:
                bloom_verbs = row[bloom_verbs_col]
                if pd.notna(bloom_verbs) and bloom_verbs:
                    # Truncate if too long
                    bloom_verbs_display = bloom_verbs[:22] + "..." if len(bloom_verbs) > 22 else bloom_verbs
                    line += f"{bloom_verbs_display:<25}"
                else:
                    line += f"{'.':<25}"
            else:
                line += f"{'.':<25}"
        
        # Add unique verbs summary
        unique_verbs = row.get('Unique_Bloom_Verbs', '')
        if pd.notna(unique_verbs) and unique_verbs:
            unique_verbs_display = unique_verbs[:18] + "..." if len(unique_verbs) > 18 else unique_verbs
            line += f"{unique_verbs_display:<20}"
        else:
            line += f"{'.':<20}"
            
        print(line)
    
    if len(df) > 15:
        print(f"... and {len(df)-15} more KG elements")
    
    print(f"\nShowing bloom verbs for top {min(15, len(df))} KG elements across {len(display_runs)} runs")

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        # Default path or prompt user
        folder_path = input("Enter the path to the folder containing evaluation_data files: ").strip()
        if not folder_path:
            print("No folder path provided. Exiting.")
            sys.exit(1)
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        sys.exit(1)
    
    print(f"Analyzing evaluation data in: {folder_path}")
    interactive_kg_element_selection(folder_path)
    # Path to the JSON file or folder
    path = r"LLM_eval/datasets/fiware_v1_hotel/run_250703_10reps/scenario_III/"  # Process entire fiware_v1_hotel folder
    
    # Check if the path is a file or a directory
    if os.path.isfile(path):
        # Process single file
        json_file_path = path
        try:
            # Group the evaluations
            grouped_evaluations = group_evaluations_by_kg_element(json_file_path)
            
            # Print summary
            print_grouped_summary(grouped_evaluations)
            
            # Optionally save the grouped data to a new JSON file
            output_file = "grouped_evaluations.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(grouped_evaluations, f, indent=2, ensure_ascii=False)
            print(f"\nGrouped data saved to {output_file}")
            
            # Example: Access specific kg_element data
            print(f"\nExample - Details for 'counter' kg_element:")
            if 'counter' in grouped_evaluations:
                counter_data = grouped_evaluations['counter']
                print(f"  Total evaluations: {counter_data['total_evaluations']}")
                print(f"  Total human effort: {counter_data['total_human_effort']}")
                print(f"  Evaluations: {[eval_data['evaluation_key'] for eval_data in counter_data['evaluations']]}")
                
        except FileNotFoundError:
            print(f"Error: Could not find file {json_file_path}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {json_file_path}")
        except Exception as e:
            print(f"Error: {e}")
    
    elif os.path.isdir(path):
        # Process all evaluation_data files in the folder
        folder_path = path
        try:
            print("Processing all evaluation_data files in folder...")
            
            # Ask user what they want to do
            print("\nChoose an option:")
            print("1. View all KG elements analysis")
            print("2. Select specific KG element for detailed analysis")
            print("3. Interactive KG element selection")
            print("4. Bloom verb frequency analysis by steps")
            
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == "2" or choice == "3":
                # Interactive KG element selection
                interactive_kg_element_selection(folder_path)
                
            elif choice == "4":
                # Bloom verb frequency analysis by steps
                print("\n" + "="*120)
                print("BLOOM VERB FREQUENCY ANALYSIS BY STEPS PER KG ELEMENT")
                print("="*120)
                
                bloom_verb_freq_df = create_bloom_verb_frequency_by_steps_table(folder_path)
                
                if not bloom_verb_freq_df.empty:
                    # Print the detailed table
                    print_bloom_verb_frequency_by_steps_table(bloom_verb_freq_df)
                    
                    # Print summary by step ranges
                    print_bloom_verb_summary_by_steps(bloom_verb_freq_df)
                    
                    # Save to CSV
                    save_bloom_verb_frequency_table_to_csv(bloom_verb_freq_df, "bloom_verb_frequency_by_steps.csv")
                else:
                    print("No bloom verb data found in the evaluation files.")
            
            elif choice == "1":
                # Default behavior - show all analysis
                # Create detailed KG table with run-by-run analysis
                print("\n" + "="*120)
                print("CREATING DETAILED KG ELEMENT TABLE WITH VARIANCE ANALYSIS")
                print("="*120)
                
                kg_table = create_detailed_kg_table(folder_path)
                
                if not kg_table.empty:
                    # Print the detailed table
                    print_detailed_kg_table(kg_table)
                    
                    # Print occurrence summary
                    print_occurrence_summary(kg_table)
                    
                    # Create and display the KG element runs table (matching the image format)
                    print("\n" + "="*120)
                    print("KG ELEMENT RUNS TABLE (Format: Steps/Effort per Run)")
                    print("="*120)
                    
                    kg_runs_table = create_kg_element_runs_table(folder_path)
                    if not kg_runs_table.empty:
                        print_kg_element_runs_table(kg_runs_table)
                        
                        # Also display with bloom verbs
                        print("\n" + "="*120)
                        print("KG ELEMENT RUNS TABLE WITH BLOOM VERBS")
                        print("="*120)
                        print_kg_element_runs_table_with_bloom_verbs(kg_runs_table)
                        
                        # Export to CSV
                        save_kg_element_runs_table_to_csv(kg_runs_table, "kg_element_runs_table.csv")
                    else:
                        print("No data available for KG element runs table.")
                    
                    # Print bloom verb analysis
                    print_bloom_verb_analysis(kg_table)
                    
                    # Save detailed table to CSV
                    csv_file = "detailed_kg_analysis.csv"
                    kg_table.to_csv(csv_file, index=False)
                    print(f"\nDetailed KG analysis saved to {csv_file}")
                    
                    # Also create the aggregated analysis for comparison
                    print("\n" + "="*120)
                    print("AGGREGATED ANALYSIS (for comparison)")
                    print("="*120)
                    
                    aggregated_evaluations = process_multiple_evaluation_files(folder_path)
                    
                    if aggregated_evaluations:
                        # Print aggregated summary
                        print_aggregated_summary(aggregated_evaluations)
                        
                        # Save aggregated results to a JSON file
                        output_file = "aggregated_evaluations.json"
                        save_aggregated_results(aggregated_evaluations, output_file)
                        print(f"\nAggregated results saved to {output_file}")
                        
                        # Show variance insights
                        print(f"\n=== VARIANCE INSIGHTS ===")
                        high_variance_elements = kg_table[
                            (kg_table['Effort_Variance'] > 50) & 
                            (~kg_table['KG_Element'].str.contains(r'\(decision point\)|\(lookup\)', regex=True))
                        ].sort_values('Effort_Variance', ascending=False)
                        if not high_variance_elements.empty:
                            print("KG elements with high effort variance (>50):")
                            for _, row in high_variance_elements.head(10).iterrows():
                                print(f"  {row['KG_Element']}: effort_var={row['Effort_Variance']:.1f}, count_var={row['Count_Variance']:.1f}, avg_effort={row['Avg_Effort']:.1f}, avg_count={row['Avg_Count']:.1f}")
                        else:
                            print("No KG elements with high effort variance found.")
                        
                        # Show high count variance
                        high_count_variance = kg_table[
                            (kg_table['Count_Variance'] > 5) & 
                            (~kg_table['KG_Element'].str.contains(r'\(decision point\)|\(lookup\)', regex=True))
                        ].sort_values('Count_Variance', ascending=False)
                        if not high_count_variance.empty:
                            print(f"\nKG elements with high count variance (>5):")
                            for _, row in high_count_variance.head(10).iterrows():
                                print(f"  {row['KG_Element']}: count_var={row['Count_Variance']:.1f}, effort_var={row['Effort_Variance']:.1f}, avg_count={row['Avg_Count']:.1f}")
                        
                        # Show consistency insights
                        consistent_elements = kg_table[
                            (kg_table['Effort_Variance'] < 10) & 
                            (kg_table['Count_Variance'] < 2) & 
                            (kg_table['Runs_Present'] > 3) &
                            (~kg_table['KG_Element'].str.contains(r'\(decision point\)|\(lookup\)', regex=True))
                        ].sort_values('Total_Effort', ascending=False)
                        if not consistent_elements.empty:
                            print(f"\nMost consistent KG elements (low variance in both effort and count, appears in >3 runs):")
                            for _, row in consistent_elements.head(5).iterrows():
                                print(f"  {row['KG_Element']}: effort_var={row['Effort_Variance']:.1f}, count_var={row['Count_Variance']:.1f}, avg_effort={row['Avg_Effort']:.1f}, avg_count={row['Avg_Count']:.1f}")
                        
                        # Show elements with consistent count but varying effort
                        consistent_count_varying_effort = kg_table[
                            (kg_table['Count_Variance'] < 1) & 
                            (kg_table['Effort_Variance'] > 20) & 
                            (kg_table['Runs_Present'] > 3) &
                            (~kg_table['KG_Element'].str.contains(r'\(decision point\)|\(lookup\)', regex=True))
                        ].sort_values('Effort_Variance', ascending=False)
                        if not consistent_count_varying_effort.empty:
                            print(f"\nKG elements with consistent occurrence count but varying effort:")
                            for _, row in consistent_count_varying_effort.head(5).iterrows():
                                print(f"  {row['KG_Element']}: count_var={row['Count_Variance']:.1f}, effort_var={row['Effort_Variance']:.1f}, avg_count={row['Avg_Count']:.1f}, avg_effort={row['Avg_Effort']:.1f}")
                else:
                    print("No evaluation data found to process.")
            
            else:
                print("Invalid choice. Please choose 1, 2, 3, or 4.")
                
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Error: The path {path} is neither a file nor a directory.")

