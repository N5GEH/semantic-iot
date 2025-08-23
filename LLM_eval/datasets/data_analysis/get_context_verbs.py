#!/usr/bin/env python3
"""
Script to read response files and count Bloom taxonomy values.
Processes markdown files containing evaluation data with bloom taxonomy classifications.
"""

import os
import re
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import json
import csv


def extract_bloom_values(file_path):
    """
    Extract bloom taxonomy values from a response file.
    
    Args:
        file_path (str): Path to the response file
        
    Returns:
        list: List of bloom taxonomy values found in the file
    """
    bloom_values = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Pattern to match bloom lines: "- bloom: <value> - <description> - <verb>"
        bloom_pattern = r'- bloom:\s*([^-]+)\s*-'
        matches = re.findall(bloom_pattern, content, re.MULTILINE | re.IGNORECASE)
        
        for match in matches:
            bloom_value = match.strip()
            if bloom_value:
                bloom_values.append(bloom_value)
                
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        
    return bloom_values


def extract_bloom_dim_verbs(file_path):
    """
    Extract bloom taxonomy values with their associated dim values and verbs.
    
    Args:
        file_path (str): Path to the response file
        
    Returns:
        list: List of tuples (bloom_value, dim_value, verb) found in the file
    """
    bloom_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Split content into evaluation blocks (each EVALUATION section)
        evaluation_blocks = re.split(r'EVALUATION:', content)
        
        for block in evaluation_blocks[1:]:  # Skip first empty split
            # Extract bloom value and first verb: "- bloom: <value> - <first_verb> <description> - <last_verb>"
            # This pattern captures the bloom level and the first word after the first dash
            bloom_match = re.search(r'- bloom:\s*([^-]+?)\s*-\s*(\w+)', block, re.MULTILINE | re.IGNORECASE)
            # Extract dim value: "- dim: <value> - <description>"
            dim_match = re.search(r'- dim:\s*([^-]+?)\s*-', block, re.MULTILINE | re.IGNORECASE)
            
            if bloom_match and dim_match:
                bloom_value = bloom_match.group(1).strip()
                verb = bloom_match.group(2).strip()  # This is now the first verb after the first dash
                dim_value = dim_match.group(1).strip()
                
                if bloom_value and dim_value and verb:
                    bloom_data.append((bloom_value, dim_value, verb))
                
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        
    return bloom_data


def find_response_files(directory):
    """
    Find all response.md files in the given directory and subdirectories.
    
    Args:
        directory (str): Root directory to search
        
    Returns:
        list: List of paths to response.md files
    """
    response_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == 'response.md':
                response_files.append(os.path.join(root, file))
                
    return response_files


def analyze_single_file(file_path, include_verbs=False):
    """
    Analyze a single response file and return bloom taxonomy counts.
    
    Args:
        file_path (str): Path to the response file
        include_verbs (bool): Whether to include verb analysis
        
    Returns:
        dict: Analysis results
    """
    if include_verbs:
        bloom_data = extract_bloom_dim_verbs(file_path)
        bloom_values = [item[0] for item in bloom_data]
        dim_values = [item[1] for item in bloom_data]
        verbs = [item[2] for item in bloom_data]
        bloom_dim_pairs = [(item[0], item[1]) for item in bloom_data]
        
        return {
            'file': file_path,
            'bloom_counts': Counter(bloom_values),
            'dim_counts': Counter(dim_values),
            'verb_counts': Counter(verbs),
            'bloom_dim_pairs': Counter(bloom_dim_pairs),
            'bloom_verb_pairs': Counter([(item[0], item[2]) for item in bloom_data]),
            'total_bloom_entries': len(bloom_values)
        }
    else:
        bloom_values = extract_bloom_values(file_path)
        
        return {
            'file': file_path,
            'bloom_counts': Counter(bloom_values),
            'total_bloom_entries': len(bloom_values)
        }


def analyze_directory(directory, include_verbs=False):
    """
    Analyze all response files in a directory and return aggregated results.
    
    Args:
        directory (str): Root directory to search
        include_verbs (bool): Whether to include verb analysis
        
    Returns:
        dict: Aggregated analysis results
    """
    response_files = find_response_files(directory)
    
    if not response_files:
        print(f"No response.md files found in {directory}")
        return None
        
    print(f"Found {len(response_files)} response.md files")
    
    # Aggregate counters
    total_bloom_counts = Counter()
    total_dim_counts = Counter() if include_verbs else None
    total_verb_counts = Counter() if include_verbs else None
    total_bloom_dim_pairs = Counter() if include_verbs else None
    total_bloom_verb_pairs = Counter() if include_verbs else None
    file_results = []
    
    for file_path in response_files:
        result = analyze_single_file(file_path, include_verbs)
        file_results.append(result)
        
        # Add to totals
        total_bloom_counts.update(result['bloom_counts'])
        if include_verbs:
            total_dim_counts.update(result['dim_counts'])
            total_verb_counts.update(result['verb_counts'])
            total_bloom_dim_pairs.update(result['bloom_dim_pairs'])
            total_bloom_verb_pairs.update(result['bloom_verb_pairs'])
    
    results = {
        'total_files': len(response_files),
        'total_bloom_counts': total_bloom_counts,
        'file_results': file_results,
        'total_bloom_entries': sum(total_bloom_counts.values())
    }
    
    if include_verbs:
        results['total_dim_counts'] = total_dim_counts
        results['total_verb_counts'] = total_verb_counts
        results['total_bloom_dim_pairs'] = total_bloom_dim_pairs
        results['total_bloom_verb_pairs'] = total_bloom_verb_pairs
    
    return results


def print_results(results, include_verbs=False):
    """
    Print analysis results in a formatted way.
    
    Args:
        results (dict): Analysis results
        include_verbs (bool): Whether to include verb analysis
    """
    print("\n" + "="*60)
    print("BLOOM TAXONOMY ANALYSIS RESULTS")
    print("="*60)
    
    print(f"\nTotal files analyzed: {results['total_files']}")
    print(f"Total bloom entries found: {results['total_bloom_entries']}")
    
    if include_verbs and 'total_bloom_dim_pairs' in results:
        print("\nBloom-Dim Combinations:")
        print("-" * 50)
        for (bloom_value, dim_value), count in results['total_bloom_dim_pairs'].most_common():
            percentage = (count / results['total_bloom_entries']) * 100
            print(f"{bloom_value} + {dim_value:<25}: {count:>3} ({percentage:>5.1f}%)")
        
        print("\nDim Counts:")
        print("-" * 30)
        for dim_value, count in results['total_dim_counts'].most_common():
            print(f"{dim_value:<30}: {count:>5}")
        
        print("\nVerb Counts:")
        print("-" * 30)
        for verb, count in results['total_verb_counts'].most_common():
            print(f"{verb:<20}: {count:>5}")
    else:
        print("\nBloom Taxonomy Counts:")
        print("-" * 30)
        for bloom_value, count in results['total_bloom_counts'].most_common():
            percentage = (count / results['total_bloom_entries']) * 100
            print(f"{bloom_value:<20}: {count:>5} ({percentage:>5.1f}%)")


def save_results_to_csv(results, output_file, include_verbs=False):
    """
    Save analysis results to CSV file.
    
    Args:
        results (dict): Analysis results
        output_file (str): Path to output CSV file
        include_verbs (bool): Whether to include verb analysis
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        if include_verbs and 'total_bloom_dim_pairs' in results:
            # Write bloom-dim combinations
            writer.writerow(['Bloom Taxonomy', 'Dim', 'Count', 'Percentage'])
            total = results['total_bloom_entries']
            for (bloom_value, dim_value), count in results['total_bloom_dim_pairs'].most_common():
                percentage = (count / total) * 100
                writer.writerow([bloom_value, dim_value, count, f"{percentage:.1f}%"])
            
            writer.writerow([])  # Empty row
            writer.writerow(['Dim', 'Count'])
            for dim_value, count in results['total_dim_counts'].most_common():
                writer.writerow([dim_value, count])
            
            writer.writerow([])  # Empty row
            writer.writerow(['Verb', 'Count'])
            for verb, count in results['total_verb_counts'].most_common():
                writer.writerow([verb, count])
        else:
            # Write bloom taxonomy counts
            writer.writerow(['Bloom Taxonomy', 'Count', 'Percentage'])
            total = results['total_bloom_entries']
            for bloom_value, count in results['total_bloom_counts'].most_common():
                percentage = (count / total) * 100
                writer.writerow([bloom_value, count, f"{percentage:.1f}%"])


def save_results_to_json(results, output_file):
    """
    Save analysis results to JSON file.
    
    Args:
        results (dict): Analysis results
        output_file (str): Path to output JSON file
    """
    # Convert Counter objects to regular dicts for JSON serialization
    json_results = {
        'total_files': results['total_files'],
        'total_bloom_entries': results['total_bloom_entries'],
        'total_bloom_counts': dict(results['total_bloom_counts']),
    }
    
    if 'total_dim_counts' in results:
        json_results['total_dim_counts'] = dict(results['total_dim_counts'])
        json_results['total_verb_counts'] = dict(results['total_verb_counts'])
        json_results['total_bloom_dim_pairs'] = {f"{k[0]}_{k[1]}": v for k, v in results['total_bloom_dim_pairs'].items()}
        json_results['total_bloom_verb_pairs'] = {f"{k[0]}_{k[1]}": v for k, v in results['total_bloom_verb_pairs'].items()}
    
    # Add file-level results
    json_results['file_results'] = []
    for file_result in results['file_results']:
        file_data = {
            'file': file_result['file'],
            'total_bloom_entries': file_result['total_bloom_entries'],
            'bloom_counts': dict(file_result['bloom_counts'])
        }
        if 'dim_counts' in file_result:
            file_data['dim_counts'] = dict(file_result['dim_counts'])
            file_data['verb_counts'] = dict(file_result['verb_counts'])
            file_data['bloom_dim_pairs'] = {f"{k[0]}_{k[1]}": v for k, v in file_result['bloom_dim_pairs'].items()}
            file_data['bloom_verb_pairs'] = {f"{k[0]}_{k[1]}": v for k, v in file_result['bloom_verb_pairs'].items()}
        json_results['file_results'].append(file_data)
    
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(json_results, jsonfile, indent=2, ensure_ascii=False)


def main():
    """Main function to handle command line arguments and run analysis."""
    parser = argparse.ArgumentParser(description='Analyze Bloom taxonomy values in response files')
    parser.add_argument('input', help='Input file or directory path')
    parser.add_argument('--verbs', '-v', action='store_true', help='Include verb analysis')
    parser.add_argument('--output-csv', '-c', help='Output CSV file path')
    parser.add_argument('--output-json', '-j', help='Output JSON file path')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    input_path = args.input
    
    if os.path.isfile(input_path):
        # Analyze single file
        result = analyze_single_file(input_path, args.verbs)
        
        if not args.quiet:
            print(f"\nAnalyzing file: {input_path}")
            print(f"Total bloom entries: {result['total_bloom_entries']}")
            
            if args.verbs and 'bloom_dim_pairs' in result:
                print("\nBloom-Dim Combinations:")
                for (bloom_value, dim_value), count in result['bloom_dim_pairs'].most_common():
                    print(f"{bloom_value} + {dim_value:<25}: {count}")
                
                print("\nDim Counts:")
                for dim_value, count in result['dim_counts'].most_common():
                    print(f"{dim_value:<30}: {count}")
                
                print("\nVerb Counts:")
                for verb, count in result['verb_counts'].most_common():
                    print(f"{verb:<20}: {count}")
            else:
                print("\nBloom Taxonomy Counts:")
                for bloom_value, count in result['bloom_counts'].most_common():
                    print(f"{bloom_value:<20}: {count}")
        
        # For single file, wrap in directory-style structure for output functions
        results = {
            'total_files': 1,
            'total_bloom_entries': result['total_bloom_entries'],
            'total_bloom_counts': result['bloom_counts'],
            'file_results': [result]
        }
        if args.verbs:
            results['total_dim_counts'] = result['dim_counts']
            results['total_verb_counts'] = result['verb_counts']
            results['total_bloom_dim_pairs'] = result['bloom_dim_pairs']
            results['total_bloom_verb_pairs'] = result['bloom_verb_pairs']
            
    elif os.path.isdir(input_path):
        # Analyze directory
        results = analyze_directory(input_path, args.verbs)
        
        if results is None:
            return
            
        if not args.quiet:
            print_results(results, args.verbs)
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        return
    
    # Save to output files if requested
    if args.output_csv:
        save_results_to_csv(results, args.output_csv, args.verbs)
        if not args.quiet:
            print(f"\nResults saved to CSV: {args.output_csv}")
    
    if args.output_json:
        save_results_to_json(results, args.output_json)
        if not args.quiet:
            print(f"Results saved to JSON: {args.output_json}")


if __name__ == "__main__":
    main()



