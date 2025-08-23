import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import numpy as np

# Define Bloom's taxonomy categories with associated verbs
bloom_categories = {
    'Knowledge': ['identify', 'relate', 'list', 'define', 'recall', 'memorize', 'repeat', 'record', 'name', 'recognize', 'acquire', 'retrieve', 'remember', 'access', 'get'],
    'Comprehension': ['restate', 'locate', 'report', 'recognize', 'explain', 'express', 'identify', 'discuss', 'describe', 'review', 'infer', 'illustrate', 'interpret', 'draw', 'represent', 'differentiate', 'conclude', 'understand', 'map', 'translate', 'process', 'parse'],
    'Application': ['relate', 'develop', 'translate', 'use', 'operate', 'organize', 'employ', 'restructure', 'interpret', 'demonstrate', 'illustrate', 'practice', 'calculate', 'show', 'exhibit', 'apply', 'implement', 'implementing', 'applying', 'configure', 'complete', 'update', 'increment', 'set', 'initialize', 'add', 'create', 'generate', 'write', 'advance', 'append', 'compile', 'load', 'fill', 'format', 'output', 'finalize'],
    'Analysis': ['compare', 'probe', 'inquire', 'examine', 'contrast', 'categorize', 'differentiate', 'contrast', 'investigate', 'detect', 'survey', 'classify', 'deduce', 'experiment', 'scrutinize', 'discover', 'inspect', 'dissect', 'discriminate', 'separate', 'extract', 'check', 'validate'],
    'Synthesis': ['compose', 'produce', 'design', 'assemble', 'create', 'prepare', 'predict', 'modify', 'tell', 'plan', 'invent', 'formulate', 'collect', 'set up', 'generalize', 'document', 'combine', 'relate', 'propose', 'develop', 'arrange', 'construct', 'organize', 'originate', 'derive', 'write', 'propose', 'composing', 'combining', 'establish', 'link', 'connect', 'declare', 'return'],
    'Evaluation': ['judge', 'evaluate', 'assess', 'compare', 'conclude', 'measure', 'deduce', 'argue', 'decide', 'choose', 'rate', 'select', 'estimate', 'validate', 'consider', 'appraise', 'value', 'criticize', 'infer', 'present']
}

# Create reverse mapping for quick lookup
verb_to_category = {}
for category, verbs in bloom_categories.items():
    for verb in verbs:
        verb_to_category[verb] = category

def categorize_verb(verb):
    """Categorize a verb according to Bloom's taxonomy"""
    verb_lower = verb.lower()
    return verb_to_category.get(verb_lower, 'Uncategorized')

# Raw data from scenarios
scenario_data = {
    'Scenario 1': {
        'bloom_objective': {
            'apply': 214, 'recall': 71, 'construct': 63, 'implement': 52, 'connect': 12, 
            'access': 9, 'compose': 9, 'identify': 9, 'map': 9, 'retrieve': 9, 'update': 9, 
            'translate': 8, 'create': 6, 'combine': 5, 'relate': 3, 'declare': 1, 
            'examine': 1, 'recognize': 1, 'remember': 1, 'set': 1
        },
        'description': {
            'create': 147, 'add': 110, 'increment': 44, 'retrieve': 44, 'declare': 40, 
            'process': 31, 'extract': 27, 'initialize': 14, 'link': 13, 'construct': 12, 
            'connect': 6, 'check': 1, 'format': 1, 'generate': 1, 'write': 1
        }
    },
    'Scenario 2': {
        'bloom_objective': {
            'implement': 166, 'apply': 98, 'implementing': 54, 'configure': 42, 'recall': 20, 
            'composing': 12, 'complete': 7, 'compose': 5, 'assess': 2, 'combine': 3, 
            'check': 1, 'declare': 1, 'identify': 1
        },
        'description': {
            'add': 165, 'create': 124, 'define': 90, 'complete': 13, 'increment': 12, 
            'declare': 3, 'initialize': 3, 'validate': 3, 'assemble': 1, 'finalize': 1, 
            'generate': 1, 'write': 1
        }
    },
    'Scenario 3': {
        'bloom_objective': {
            'apply': 144, 'recall': 60, 'use': 37, 'increment': 24, 'retrieve': 22, 
            'construct': 18, 'access': 12, 'get': 12, 'update': 12, 'create': 11, 
            'advance': 9, 'compose': 6, 'establish': 6, 'assemble': 5, 'combine': 4, 
            'append': 3, 'compile': 2, 'extract': 2, 'set': 2, 'initialize': 1, 
            'parse': 1, 'present': 1, 'recognize': 1, 'understand': 1
        },
        'description': {
            'update': 91, 'increment': 74, 'retrieve': 62, 'process': 40, 'initialize': 27, 
            'set': 24, 'create': 13, 'extract': 12, 'add': 10, 'get': 10, 'construct': 8, 
            'generate': 7, 'parse': 6, 'assemble': 3, 'map': 3, 'return': 3, 'compose': 2, 
            'load': 2, 'output': 2, 'compile': 1, 'fill': 1, 'format': 1
        }
    },
    'Context': {
        'bloom_objective': {
            'identify': 10,
            'examine': 10,
            'categorize': 5,
            'apply': 8,
            'relate': 4,
            'evaluate': 4,
            'match': 6,
            'recall': 4,
            'combine': 3,
            'understand': 3,
            'design': 2,
            'create': 3,
            'compare': 1,
            'list': 1,
            'derive': 1,
            'assemble': 1,
            'recognize': 1,
            'compose': 1
        }
    }
}

def create_categorized_dataset(data, data_type, scenario_name):
    """Create a dataset with Bloom's taxonomy categorization"""
    categorized_data = []
    
    for verb, count in data.items():
        category = categorize_verb(verb)
        categorized_data.append({
            'scenario': scenario_name,
            'data_type': data_type,
            'verb': verb,
            'count': count,
            'bloom_category': category
        })
    
    return categorized_data

# Create datasets
all_data = []

# Dataset 1: Bloom Objective only
bloom_objective_data = []
for scenario, data in scenario_data.items():
    if 'bloom_objective' in data:
        bloom_objective_data.extend(create_categorized_dataset(data['bloom_objective'], 'bloom_objective', scenario))

# Dataset 2: Description only
description_data = []
for scenario, data in scenario_data.items():
    if 'description' in data:
        description_data.extend(create_categorized_dataset(data['description'], 'description', scenario))

# Dataset 3: Combined
combined_data = bloom_objective_data + description_data

# Convert to DataFrames
df_bloom_objective = pd.DataFrame(bloom_objective_data)
df_description = pd.DataFrame(description_data)
df_combined = pd.DataFrame(combined_data)

print("=== BLOOM'S TAXONOMY ANALYSIS ===\n")

# Define the correct Bloom's taxonomy order
bloom_order = ['Knowledge', 'Comprehension', 'Application', 'Analysis', 'Synthesis', 'Evaluation', 'Uncategorized']

def sort_by_bloom_order(category_counts):
    """Sort categories according to Bloom's taxonomy order"""
    ordered_data = []
    for category in bloom_order:
        if category in category_counts.index:
            ordered_data.append((category, category_counts[category]))
    return pd.Series(dict(ordered_data))

# Analysis functions
def analyze_dataset(df, dataset_name):
    """Comprehensive analysis of a dataset"""
    print(f"\n--- {dataset_name} Analysis ---")
    
    # Category distribution with proper ordering
    category_counts = df.groupby('bloom_category')['count'].sum()
    category_counts_ordered = sort_by_bloom_order(category_counts)
    
    print(f"\nBloom's Taxonomy Distribution:")
    total_count = category_counts_ordered.sum()
    for category, count in category_counts_ordered.items():
        percentage = (count / total_count) * 100
        print(f"  {category}: {count} ({percentage:.1f}%)")
    
    # Scenario breakdown
    print(f"\nScenario Distribution:")
    scenario_counts = df.groupby('scenario')['count'].sum().sort_values(ascending=False)
    for scenario, count in scenario_counts.items():
        percentage = (count / scenario_counts.sum()) * 100
        print(f"  {scenario}: {count} ({percentage:.1f}%)")
    
    # Top verbs by category (ordered by Bloom's taxonomy)
    print(f"\nTop 5 Verbs by Category:")
    for category in category_counts_ordered.index:  # Use ordered categories
        if category in df['bloom_category'].values:
            top_verbs = df[df['bloom_category'] == category].nlargest(5, 'count')
            print(f"  {category}:")
            for _, row in top_verbs.iterrows():
                print(f"    {row['verb']}: {row['count']}")
    
    return category_counts_ordered, scenario_counts

# Analyze each dataset
bloom_obj_cat, bloom_obj_scen = analyze_dataset(df_bloom_objective, "BLOOM OBJECTIVE")
desc_cat, desc_scen = analyze_dataset(df_description, "DESCRIPTION")
combined_cat, combined_scen = analyze_dataset(df_combined, "COMBINED")

# Cross-scenario comparison
print(f"\n--- CROSS-SCENARIO COMPARISON ---")

def compare_scenarios(df, data_type):
    """Compare Bloom's taxonomy distribution across scenarios"""
    print(f"\n{data_type} - Bloom's Categories by Scenario:")
    
    pivot_df = df.pivot_table(values='count', index='bloom_category', columns='scenario', fill_value=0)
    
    # Reorder according to Bloom's taxonomy
    pivot_df_ordered = pivot_df.reindex([cat for cat in bloom_order if cat in pivot_df.index])
    
    # Calculate percentages
    pivot_percent = pivot_df_ordered.div(pivot_df_ordered.sum(axis=0), axis=1) * 100
    
    print(pivot_percent.round(1))
    
    return pivot_df_ordered, pivot_percent

bloom_obj_pivot, bloom_obj_percent = compare_scenarios(df_bloom_objective, "BLOOM OBJECTIVE")
desc_pivot, desc_percent = compare_scenarios(df_description, "DESCRIPTION")

# Summary insights
print(f"\n--- KEY INSIGHTS ---")

print(f"\n1. Dominant Categories:")
print(f"   - Bloom Objective: {bloom_obj_cat.index[0]} ({bloom_obj_cat.iloc[0]} occurrences)")
print(f"   - Description: {desc_cat.index[0]} ({desc_cat.iloc[0]} occurrences)")
print(f"   - Combined: {combined_cat.index[0]} ({combined_cat.iloc[0]} occurrences)")

print(f"\n2. Category Coverage:")
categories_bloom = set(df_bloom_objective['bloom_category'].unique())
categories_desc = set(df_description['bloom_category'].unique())
print(f"   - Bloom Objective covers: {len(categories_bloom)} categories")
print(f"   - Description covers: {len(categories_desc)} categories")
print(f"   - Common categories: {len(categories_bloom & categories_desc)}")
print(f"   - Unique to Bloom Objective: {categories_bloom - categories_desc}")
print(f"   - Unique to Description: {categories_desc - categories_bloom}")

print(f"\n3. Scenario Patterns:")
for scenario in ['Scenario 1', 'Scenario 2', 'Scenario 3', 'Context']:
    bloom_total = df_bloom_objective[df_bloom_objective['scenario'] == scenario]['count'].sum()
    desc_total = df_description[df_description['scenario'] == scenario]['count'].sum()
    if desc_total > 0:
        print(f"   - {scenario}: Bloom Objective ({bloom_total}) vs Description ({desc_total})")
    else:
        print(f"   - {scenario}: Bloom Objective ({bloom_total}) vs Description (No data)")

# Visualization preparation
print(f"\n--- CREATING VISUALIZATIONS ---")

# Set up the plotting style with muted colors
plt.style.use('default')
muted_colors = ['#8B9DC3', '#DEB887', '#B0C4B1', '#D4A5A5', '#C8AD7F', '#A8A8A8']  # Muted color palette

# Define Bloom's taxonomy colors - more intense for higher cognitive levels
# Using gradient from #DAE9F8 (light) to #00549F (dark)
bloom_colors = {
    'Knowledge': '#DAE9F8',      # Very light - lowest level (your light blue)
    'Comprehension': '#B8D4F0',  # Light blue
    'Application': '#8FBFE7',    # Medium-light blue
    'Analysis': '#5FA0D8',       # Medium blue
    'Synthesis': '#3581C9',      # Medium-dark blue
    'Evaluation': '#00549F',     # Very intense - highest level (your dark blue)
    'Uncategorized': '#F0F0F0'   # Very unintense gray
}

# Create ordered color list for plots
def get_bloom_colors_ordered(categories):
    """Get colors for categories in the order they appear"""
    return [bloom_colors.get(cat, '#A8A8A8') for cat in categories]

# Create comprehensive visualizations
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('Bloom\'s Taxonomy Analysis Across Scenarios', fontsize=16, fontweight='bold')

# Convert counts to percentages for all visualizations
bloom_obj_cat_pct = (bloom_obj_cat / bloom_obj_cat.sum()) * 100
desc_cat_pct = (desc_cat / desc_cat.sum()) * 100
combined_cat_pct = (combined_cat / combined_cat.sum()) * 100

bloom_obj_scen_pct = (bloom_obj_scen / bloom_obj_scen.sum()) * 100
desc_scen_pct = (desc_scen / desc_scen.sum()) * 100
combined_scen_pct = (combined_scen / combined_scen.sum()) * 100

# 1. Bloom Objective Category Distribution
bloom_obj_colors = get_bloom_colors_ordered(bloom_obj_cat_pct.index)
bloom_obj_cat_pct.plot(kind='bar', ax=axes[0,0], color=bloom_obj_colors)
axes[0,0].set_title('Bloom Objective - Category Distribution')
axes[0,0].set_xlabel('Bloom\'s Category')
axes[0,0].set_ylabel('Percentage (%)')
axes[0,0].tick_params(axis='x', rotation=45)

# 2. Description Category Distribution  
desc_colors = get_bloom_colors_ordered(desc_cat_pct.index)
desc_cat_pct.plot(kind='bar', ax=axes[0,1], color=desc_colors)
axes[0,1].set_title('Description - Category Distribution')
axes[0,1].set_xlabel('Bloom\'s Category')
axes[0,1].set_ylabel('Percentage (%)')
axes[0,1].tick_params(axis='x', rotation=45)

# 3. Combined Category Distribution
combined_colors = get_bloom_colors_ordered(combined_cat_pct.index)
combined_cat_pct.plot(kind='bar', ax=axes[0,2], color=combined_colors)
axes[0,2].set_title('Combined - Category Distribution')
axes[0,2].set_xlabel('Bloom\'s Category')
axes[0,2].set_ylabel('Percentage (%)')
axes[0,2].tick_params(axis='x', rotation=45)

# 4. Bloom Objective by Scenario
bloom_obj_scen_pct.plot(kind='bar', ax=axes[1,0], color=muted_colors[3])
axes[1,0].set_title('Bloom Objective - Scenario Distribution')
axes[1,0].set_xlabel('Scenario')
axes[1,0].set_ylabel('Percentage (%)')
axes[1,0].tick_params(axis='x', rotation=45)

# 5. Description by Scenario
desc_scen_pct.plot(kind='bar', ax=axes[1,1], color=muted_colors[4])
axes[1,1].set_title('Description - Scenario Distribution')
axes[1,1].set_xlabel('Scenario')
axes[1,1].set_ylabel('Percentage (%)')
axes[1,1].tick_params(axis='x', rotation=45)

# 6. Combined by Scenario
combined_scen_pct.plot(kind='bar', ax=axes[1,2], color=muted_colors[5])
axes[1,2].set_title('Combined - Scenario Distribution')
axes[1,2].set_xlabel('Scenario')
axes[1,2].set_ylabel('Percentage (%)')
axes[1,2].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()

# Create stacked bar charts for cross-scenario comparison
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Cross-Scenario Comparison - Bloom\'s Categories (%)', fontsize=14, fontweight='bold')

# Convert to percentages for stacked bar charts
bloom_obj_percent_ordered = bloom_obj_percent.T
desc_percent_ordered = desc_percent.T

# Create ordered color list for stacked charts
bloom_stacked_colors = [bloom_colors.get(cat, '#A8A8A8') for cat in bloom_order if cat in bloom_obj_percent_ordered.columns]

# Bloom Objective Stacked Bar Chart (using percentages)
bloom_obj_percent_ordered.plot(kind='bar', stacked=True, ax=axes[0], 
                              color=bloom_stacked_colors)
axes[0].set_title('Bloom Objective - Categories by Scenario (%)')
axes[0].set_xlabel('Scenario')
axes[0].set_ylabel('Percentage (%)')
axes[0].tick_params(axis='x', rotation=45)
axes[0].legend(title='Bloom\'s Category', bbox_to_anchor=(1.05, 1), loc='upper left')

# Description Stacked Bar Chart (using percentages) 
desc_stacked_colors = [bloom_colors.get(cat, '#A8A8A8') for cat in bloom_order if cat in desc_percent_ordered.columns]
desc_percent_ordered.plot(kind='bar', stacked=True, ax=axes[1], 
                         color=desc_stacked_colors)
axes[1].set_title('Description - Categories by Scenario (%)')
axes[1].set_xlabel('Scenario')
axes[1].set_ylabel('Percentage (%)')
axes[1].tick_params(axis='x', rotation=45)
axes[1].legend(title='Bloom\'s Category', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.show()

# Save datasets to CSV
print(f"\n--- SAVING DATASETS ---")
df_bloom_objective.to_csv('bloom_objective_categorized.csv', index=False)
df_description.to_csv('description_categorized.csv', index=False)
df_combined.to_csv('combined_categorized.csv', index=False)

print("Datasets saved:")
print("- bloom_objective_categorized.csv")
print("- description_categorized.csv") 
print("- combined_categorized.csv")

print(f"\n=== ANALYSIS COMPLETE ===")