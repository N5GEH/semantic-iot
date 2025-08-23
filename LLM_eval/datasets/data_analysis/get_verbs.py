import json
import pandas as pd
from collections import defaultdict, Counter
import os

def analyze_bloom_dim_pairs_by_steps(json_file_path):
    """
    Analyze the frequency of bloom-dim pairs for each KG element by count of steps.
    Steps are defined by the number of unique evaluation_keys in the same source_file.
    """
    
    # Load the aggregated evaluations data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Dictionary to store results: {kg_element: {step_count: {bloom_dim_pair: count}}}
    results = defaultdict(lambda: defaultdict(Counter))
    
    # First, we need to count steps per source file for each KG element
    # Structure: {kg_element: {source_file: set_of_evaluation_keys}}
    kg_element_file_steps = defaultdict(lambda: defaultdict(set))
    
    # Collect all evaluation keys per source file for each KG element
    for kg_element, kg_data in data['kg_elements'].items():
        print(f"Processing KG element: {kg_element}")
        
        for evaluation in kg_data['evaluations']:
            source_file = evaluation['source_file']
            evaluation_key = evaluation['evaluation_key']
            
            kg_element_file_steps[kg_element][source_file].add(evaluation_key)
    
    # Now count bloom-dim pairs by step count for each KG element
    for kg_element, kg_data in data['kg_elements'].items():
        print(f"Analyzing bloom-dim pairs for KG element: {kg_element}")
        
        for evaluation in kg_data['evaluations']:
            source_file = evaluation['source_file']
            bloom = evaluation['data'].get('bloom', 'unknown')
            dim = evaluation['data'].get('dim', 'unknown')
            
            # Create the bloom-dim pair string
            bloom_dim_pair = f"{bloom}x{dim}"
            
            # Count the number of steps (unique evaluation keys) for this source file
            step_count = len(kg_element_file_steps[kg_element][source_file])
            
            # Increment the counter for this bloom-dim pair
            results[kg_element][step_count][bloom_dim_pair] += 1
    
    return results

def create_analysis_tables(results):
    """
    Create tables showing bloom-dim pair frequencies for each KG element and step count.
    """
    
    all_tables = {}
    
    for kg_element, step_data in results.items():
        print(f"\n=== Analysis for KG Element: {kg_element} ===")
        
        kg_tables = {}
        
        for step_count, pair_counts in step_data.items():
            print(f"\nStep Count: {step_count}")
            
            # Create a DataFrame for this step count
            pair_df = pd.DataFrame([
                {'bloom_dim_pair': pair, 'frequency': count}
                for pair, count in pair_counts.most_common()
            ])
            
            if not pair_df.empty:
                # Add percentage
                pair_df['percentage'] = (pair_df['frequency'] / pair_df['frequency'].sum() * 100).round(2)
                
                print(pair_df.to_string(index=False))
                kg_tables[step_count] = pair_df
            else:
                print("No data available")
        
        all_tables[kg_element] = kg_tables
    
    return all_tables

def save_results_to_csv(results, output_dir="bloom_dim_analysis"):
    """
    Save the analysis results to CSV files.
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a comprehensive table with all data
    comprehensive_data = []
    
    for kg_element, step_data in results.items():
        for step_count, pair_counts in step_data.items():
            total_evaluations = sum(pair_counts.values())
            
            for pair, count in pair_counts.items():
                percentage = (count / total_evaluations * 100) if total_evaluations > 0 else 0
                
                comprehensive_data.append({
                    'kg_element': kg_element,
                    'step_count': step_count,
                    'bloom_dim_pair': pair,
                    'frequency': count,
                    'percentage': round(percentage, 2),
                    'total_evaluations_for_step_count': total_evaluations
                })
    
    # Save comprehensive table
    comprehensive_df = pd.DataFrame(comprehensive_data)
    comprehensive_path = os.path.join(output_dir, 'comprehensive_bloom_dim_analysis.csv')
    comprehensive_df.to_csv(comprehensive_path, index=False, encoding='utf-8')
    print(f"\nComprehensive analysis saved to: {comprehensive_path}")
    
    # Save individual tables for each KG element
    for kg_element, step_data in results.items():
        kg_element_safe = kg_element.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
        
        kg_data = []
        for step_count, pair_counts in step_data.items():
            total_evaluations = sum(pair_counts.values())
            
            for pair, count in pair_counts.items():
                percentage = (count / total_evaluations * 100) if total_evaluations > 0 else 0
                
                kg_data.append({
                    'step_count': step_count,
                    'bloom_dim_pair': pair,
                    'frequency': count,
                    'percentage': round(percentage, 2),
                    'total_evaluations_for_step_count': total_evaluations
                })
        
        if kg_data:
            kg_df = pd.DataFrame(kg_data)
            kg_path = os.path.join(output_dir, f'{kg_element_safe}_bloom_dim_analysis.csv')
            kg_df.to_csv(kg_path, index=False, encoding='utf-8')
            print(f"Analysis for '{kg_element}' saved to: {kg_path}")

def create_summary_statistics(results):
    """
    Create summary statistics across all KG elements and step counts.
    """
    
    print("\n" + "="*50)
    print("SUMMARY STATISTICS")
    print("="*50)
    
    # Overall statistics
    all_pairs = Counter()
    all_step_counts = Counter()
    kg_element_counts = Counter()
    
    for kg_element, step_data in results.items():
        kg_element_counts[kg_element] = 0
        
        for step_count, pair_counts in step_data.items():
            all_step_counts[step_count] += sum(pair_counts.values())
            
            for pair, count in pair_counts.items():
                all_pairs[pair] += count
                kg_element_counts[kg_element] += count
    
    print(f"\nTotal KG Elements: {len(results)}")
    print(f"Total Evaluations: {sum(all_pairs.values())}")
    
    print(f"\nMost Common Bloom-Dim Pairs (overall):")
    for pair, count in all_pairs.most_common(10):
        percentage = (count / sum(all_pairs.values()) * 100)
        print(f"  {pair}: {count} ({percentage:.1f}%)")
    
    print(f"\nStep Count Distribution:")
    for step_count, count in sorted(all_step_counts.items()):
        percentage = (count / sum(all_step_counts.values()) * 100)
        print(f"  {step_count} steps: {count} evaluations ({percentage:.1f}%)")
    
    print(f"\nMost Evaluated KG Elements:")
    for kg_element, count in kg_element_counts.most_common(10):
        percentage = (count / sum(kg_element_counts.values()) * 100)
        print(f"  {kg_element}: {count} evaluations ({percentage:.1f}%)")

def main(json_file_path):
    """
    Main function to run the analysis.
    """
    
    print("Starting bloom-dim pair analysis by step count...")
    print(f"Input file: {json_file_path}")
    
    # Perform the analysis
    results = analyze_bloom_dim_pairs_by_steps(json_file_path)
    
    # Create and display analysis tables
    tables = create_analysis_tables(results)
    
    # Save results to CSV files
    save_results_to_csv(results)
    
    # Create summary statistics
    create_summary_statistics(results)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    # Path to the aggregated evaluations file
    json_file_path = "LLM_eval/datasets/fiware_v1_hotel/run_250703_10reps/scenario_I/aggregated_evaluations.json"

    main(json_file_path)
