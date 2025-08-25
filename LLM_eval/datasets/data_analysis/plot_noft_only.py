import matplotlib.pyplot as plt
import numpy as np

# Data from the table
tasks = ['Find API Endpoint', 'Analyze JSON keys', 'Map Entities', 'Map Properties', 'Check Entity Classes', 'Map Supp. Entities', 'Find Connection Property',
         'Generate Root RDF', 'Generate Entity RDF', 'Generate Device RDF', 'Generate Supp. Entity RDF']

# Separate task lists for different contexts
context_tasks = ['Find API Endpoint', 'Analyze JSON keys', 'Map Entities', 'Map Properties', 'Check Entity Classes', 'Map Supp. Entities', 'Find Connection Property']
approach_tasks = ['Generate Root RDF', 'Generate Entity RDF', 'Generate Device RDF', 'Generate Supp. Entity RDF']

# NofT (Number of Thoughts) data
approach1_noft = [None, None, None, None, None, None, None, 3, 4, 5, 3.5]
approach2_noft = [None, None, None, None, None, None, None, 3, 4, 5, 5]
approach3_noft = [None, None, None, None, None, None, None, 2, 3, 3.5, 4.5]
approach4_noft = [1, 2, 2, 3, 1, 2, 1, None, None, None, None]

# NofT error data (standard deviations)
approach1_noft_std = [None, None, None, None, None, None, None, 0, 1.06, 1.33, 0.97]
approach2_noft_std = [None, None, None, None, None, None, None, 0, 1.49, 2.27, 1.07]
approach3_noft_std = [None, None, None, None, None, None, None, 0.55, 0.99, 2.13, 0.52]
approach4_noft_std = [0, 0.45, 0, 0.45, 0, 0, 0, None, None, None, None]

# Create figure with 1x2 subplots (horizontal layout)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), gridspec_kw={'width_ratios': [7, 8]}, sharey=True)

# X positions for tasks
x_positions = np.arange(len(tasks))
context_x_positions = np.arange(len(context_tasks))
approach_x_positions = np.arange(len(approach_tasks))

# Colors for each approach (reordered to put Context first)
colors = ['#612158', '#F6A800', '#0098A1', '#BDCD00']
approach_labels = ['Kontext', 'KG manuell', 'RML manuell', 'SIoT']

# Get the maximum NofT value for consistent scaling
max_noft = max([x for sublist in [approach1_noft, approach2_noft, approach3_noft, approach4_noft] for x in sublist if x is not None]) * 1.1

# LEFT SUBPLOT: Context (Dataset VI) - Number of Thoughts
approach4_noft_clean = [x for x in approach4_noft if x is not None]
approach4_noft_std_clean = [std for std in approach4_noft_std if std is not None]
x_positions_approach4_noft = [i for i, x in enumerate(approach4_noft) if x is not None]

line1, = ax1.plot(x_positions_approach4_noft, approach4_noft_clean, color=colors[0], linewidth=4, alpha=0.99)
ax1.errorbar(x_positions_approach4_noft, approach4_noft_clean, yerr=approach4_noft_std_clean, 
           fmt='o', color=colors[0], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[0])

# RIGHT SUBPLOT: Approaches I-III - Number of Thoughts
# Plot Approach I
approach1_noft_clean = [x for x in approach1_noft if x is not None]
approach1_noft_std_clean = [std for std in approach1_noft_std if std is not None]
x_positions_approach1_noft = [i-7 for i, x in enumerate(approach1_noft) if x is not None]  # Adjust for approach tasks starting at index 7

line2, = ax2.plot(x_positions_approach1_noft, approach1_noft_clean, color=colors[1], linewidth=4, alpha=0.99)
ax2.errorbar(x_positions_approach1_noft, approach1_noft_clean, yerr=approach1_noft_std_clean, 
           fmt='s', color=colors[1], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[1])

# Plot Approach II
approach2_noft_clean = [x for x in approach2_noft if x is not None]
approach2_noft_std_clean = [std for std in approach2_noft_std if std is not None]
x_positions_approach2_noft = [i-7 for i, x in enumerate(approach2_noft) if x is not None]  # Adjust for approach tasks starting at index 7

line3, = ax2.plot(x_positions_approach2_noft, approach2_noft_clean, color=colors[2], linewidth=4, alpha=0.99, linestyle='--')
ax2.errorbar(x_positions_approach2_noft, approach2_noft_clean, yerr=approach2_noft_std_clean, 
           fmt='d', color=colors[2], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[2])

# Plot Approach III
approach3_noft_clean = [x for x in approach3_noft if x is not None]
approach3_noft_std_clean = [std for std in approach3_noft_std if std is not None]
x_positions_approach3_noft = [i-7 for i, x in enumerate(approach3_noft) if x is not None]  # Adjust for approach tasks starting at index 7

line4, = ax2.plot(x_positions_approach3_noft, approach3_noft_clean, color=colors[3], linewidth=4, alpha=0.99)
ax2.errorbar(x_positions_approach3_noft, approach3_noft_clean, yerr=approach3_noft_std_clean, 
           fmt='^', color=colors[3], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[3])

# Customize the subplots
# LEFT: Context NofT
ax1.set_xticks(context_x_positions)
ax1.set_xticklabels(context_tasks, fontsize=18, rotation=20, ha='right')
# ax1.set_title('Number of Thoughts (NofT) Comparison', fontsize=18, fontweight='bold')
# ax1.set_ylabel('Repr. Number of Thoughts (NofT)', fontsize=16, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='both')
ax1.legend([line1], [approach_labels[0]], loc='upper right', fontsize=18)
ax1.set_ylim(0, max_noft)
ax1.tick_params(axis='y', labelsize=14)

# RIGHT: Approaches I-III NofT
ax2.set_xticks(approach_x_positions)
ax2.set_xticklabels(approach_tasks, fontsize=18, rotation=20, ha='right')
ax2.grid(True, alpha=0.3, axis='both')
ax2.legend([line2, line3, line4], approach_labels[1:4], loc='upper left', fontsize=18)
ax2.set_ylim(0, 8)
ax2.tick_params(axis='y', labelsize=14)

# Adjust layout to prevent label cutoff
plt.tight_layout()
plt.subplots_adjust(wspace=0.05)

# Display the plot
plt.savefig(r"C:\\Users\\56xsl\\Downloads\\noft_only_comparison.png", format="png")

plt.show()

# Optional: Save the plot as PNG
# plt.savefig('noft_only_comparison.png', dpi=300, bbox_inches='tight')
