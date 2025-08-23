
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Set global font size for all plot elements
plt.rcParams.update({'font.size': 16})

# Data from the previous evaluation (old results)
old_data = {
    'Context': {'Knowledge': 19, 'Comprehension': 6, 'Application': 22, 'Analysis': 38, 'Synthesis': 14},
    'Approach I': {'Knowledge': 19, 'Comprehension': 4, 'Application': 69, 'Synthesis': 8},
    'Approach II': {'Knowledge': 5, 'Application': 86, 'Synthesis': 8, 'Evaluation': 1},
    'Approach III': {'Knowledge': 38, 'Application': 57, 'Synthesis': 4}
}

# Data from the new evaluation (current results)
new_data = {
    'C': {'Knowledge': 22.73, 'Comprehension': 15.91, 'Application': 13.64, 'Analysis': 18.18, 'Synthesis': 17.05, 'Evaluation': 5.68, 'Uncategorized': 6.8},
    'A. I': {'Knowledge': 22.3, 'Comprehension': 6.3, 'Application': 56.4, 'Analysis': 1.0, 'Synthesis': 14.0, 'Evaluation': 0.0, 'Uncategorized': 0.0},
    'A. II': {'Knowledge': 20.1, 'Comprehension': 1.1, 'Application': 68.4, 'Analysis': 1.1, 'Synthesis': 4.7, 'Evaluation': 2.2, 'Uncategorized': 2.2},
    'A. III': {'Knowledge': 40.9, 'Comprehension': 1.5, 'Application': 40.1, 'Analysis': 3.1, 'Synthesis': 12.9, 'Evaluation': 1.5, 'Uncategorized': 0.0}
}

# All possible bloom categories
all_categories = ['Knowledge', 'Comprehension', 'Application', 'Analysis', 'Synthesis', 'Evaluation', 'Uncategorized']

def prepare_data_for_scenario(scenario_name, old_scenario_data, new_scenario_data):
    """Prepare data for a specific scenario comparison"""
    old_values = [old_scenario_data.get(cat, 0) for cat in all_categories]
    new_values = [new_scenario_data.get(cat, 0) for cat in all_categories]
    return old_values, new_values

fig, axes = plt.subplots(4, 1, figsize=(10, 11))


# Add a figure title above the plot
fig.suptitle('Frequencies of Cognitive Processes', fontsize=20, y=0.96, x=0.35)

# Add a single y-axis description vertically centered, closer to the axis
# fig.text(0.13, 0.5, 'Frequency', ha='center', va='center', fontsize=20, rotation=90)

# Refined Classification of Cognitive Processes Through Action Verb Classification

# Approach mappings
scenario_mappings = [
    ('Context', 'C'),
    ('Approach I', 'A. I'),
    ('Approach II', 'A. II'),
    ('Approach III', 'A. III')
]

# Colors for the bars
colors_old = '#00549F'  # Light blue
colors_new = "#a11035"  # Dark blue

# Create plots for each scenario
for idx, (old_key, new_key) in enumerate(scenario_mappings):
    ax = axes[idx]

    # Get data for this scenario
    old_scenario_data = old_data.get(old_key, {})
    new_scenario_data = new_data.get(new_key, {})

    old_values, new_values = prepare_data_for_scenario(new_key, old_scenario_data, new_scenario_data)

    # Create bar positions
    x_pos = np.arange(len(all_categories))
    width = 0.35

    # Create bars
    bars1 = ax.bar(x_pos - width/2, old_values, width, label='MCQ-Scoring', color=colors_old, alpha=0.8)
    bars2 = ax.bar(x_pos + width/2, new_values, width, label='Post-hoc Classification', color=colors_new, alpha=0.8)

    # Set common y-axis scale for all subplots
    ax.set_ylim(0, 100)

    # Customize the plot
    ax.set_ylabel(f'{new_key}', fontsize=18, fontweight='bold', rotation=0, labelpad=30, va='center')
    ax.grid(True, alpha=0.3, axis='y')

    # Format y-axis tick labels as percent
    yticks = ax.get_yticks()
    # ax.set_yticklabels([f'{int(y)}%' if y == int(y) else f'{y:.1f}%' for y in yticks], fontsize=16)
    ax.set_yticklabels([])

    # Only show x-labels and tick labels on the bottom subplot
    if idx == len(scenario_mappings) - 1:
        ax.set_xlabel('Cognitive Processes', fontsize=18)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(all_categories, rotation=20, ha='right', fontsize=18)
    else:
        ax.set_xlabel("")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(["" for _ in all_categories])

    # Draw vertical lines between cognitive processes
    for xpos in x_pos[:-1]:
        ax.axvline(x=xpos + 0.5, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    # Add value labels on bars
    def add_value_labels(bars, values):
        for bar, value in zip(bars, values):
            if value > 0:  # Only show labels for non-zero values
                height = bar.get_height()
                rounded_value = int(round(value))
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{rounded_value}%',
                       ha='center', va='bottom', fontsize=13)

    add_value_labels(bars1, old_values)
    add_value_labels(bars2, new_values)


# Add a single legend for the entire figure beside the x-axis label (right side)
handles, labels = axes[-1].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper right', ncol=1, fontsize=15, frameon=False, bbox_to_anchor=(0.98, 0.98))

plt.tight_layout()
plt.savefig(r"C:\\Users\\56xsl\\Downloads\\bloom_category_comparison.pdf", format="pdf")
plt.show()

# Create a summary comparison table
print("\n" + "="*80)
print("SUMMARY COMPARISON TABLE")
print("="*80)

summary_df = pd.DataFrame({
    'Approach': [],
    'Dataset': [],
    'Knowledge': [],
    'Comprehension': [],
    'Application': [],
    'Analysis': [],
    'Synthesis': [],
    'Evaluation': [],
    'Uncategorized': []
})

# Add data to summary table
rows = []
for old_key, new_key in scenario_mappings:
    old_scenario_data = old_data.get(old_key, {})
    new_scenario_data = new_data.get(new_key, {})
    
    # Old data row
    old_row = [new_key, 'Previous']
    for cat in all_categories:
        old_row.append(old_scenario_data.get(cat, 0))
    rows.append(old_row)
    
    # New data row
    new_row = [new_key, 'New']
    for cat in all_categories:
        new_row.append(new_scenario_data.get(cat, 0))
    rows.append(new_row)

summary_df = pd.DataFrame(rows, columns=['Approach', 'Dataset'] + all_categories)
print(summary_df.to_string(index=False))

# Calculate and display key insights
print("\n" + "="*80)
print("KEY INSIGHTS")
print("="*80)

for old_key, new_key in scenario_mappings:
    old_scenario_data = old_data.get(old_key, {})
    new_scenario_data = new_data.get(new_key, {})
    
    print(f"\n{new_key}:")
    
    # Calculate major changes
    for category in ['Knowledge', 'Comprehension', 'Application', 'Analysis', 'Synthesis']:
        old_val = old_scenario_data.get(category, 0)
        new_val = new_scenario_data.get(category, 0)
        
        if old_val > 0 and new_val > 0:
            change = new_val - old_val
            if abs(change) > 5:  # Only show significant changes
                direction = "increased" if change > 0 else "decreased"
                print(f"  - {category}: {direction} by {abs(change):.1f}% (from {old_val}% to {new_val:.1f}%)")
        elif old_val == 0 and new_val > 0:
            print(f"  - {category}: newly appeared with {new_val:.1f}%")
        elif old_val > 0 and new_val == 0:
            print(f"  - {category}: disappeared (was {old_val}%)")

