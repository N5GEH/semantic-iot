import matplotlib.pyplot as plt
import numpy as np

# Data from the table
tasks = ['Find API Endpoint', 'Analyze JSON keys', 'Map Entities', 'Map Properties', 'Check Entity Classes', 'Map Supp. Entities', 'Find Connection Property',
         'Generate Root RDF', 'Generate Entity RDF', 'Generate Sensor RDF', 'Generate Supp. Entity RDF']

# Separate task lists for different contexts
context_tasks = ['Find API Endpoint', 'Analyze JSON keys', 'Map Entities', 'Map Properties', 'Check Entity Classes', 'Map Supp. Entities', 'Find Connection Property']
approach_tasks = ['Generate Root RDF', 'Generate Entity RDF', 'Generate Sensor RDF', 'Generate Supp. Entity RDF']

# Approach I data (extended with None for new tasks)
approach1_he = [None, None, None, None, None, None, None, 32, 47, 66.5, 85.5]
approach1_std = [None, None, None, None, None, None, None, 15, 20, 26, 36]  # std dev values

# Approach II data (extended with None for new tasks)
approach2_he = [None, None, None, None, None, None, None, 80, 125, 135, 155]
approach2_std = [None, None, None, None, None, None, None, 28, 41, 65, 56]

# Approach III data (extended with None for new tasks)
approach3_he = [None, None, None, None, None, None, None, 20, 40, 45, 69]
approach3_std = [None, None, None, None, None, None, None, 6, 9, 12, 24]

# Approach IV data (new dataset)
approach4_he = [15, 35, 57, 45.5, 30, 75, 25, None, None, None, None]
approach4_std = [0, 11, 14, 10, 2, 14, 4, None, None, None, None]

# Create figure with 2x1 subplots (vertical layout)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [7, 8]})

# Y positions for tasks
y_positions = np.arange(len(tasks))
context_y_positions = np.arange(len(context_tasks))
approach_y_positions = np.arange(len(approach_tasks))

# Colors for each approach (reordered to put Context first)
colors = ['#612158', '#F6A800', '#0098A1', '#BDCD00']
approach_labels = ['Context', 'Approach I', 'Approach II', 'Approach III']

# Get the maximum HE value for consistent scaling
max_he = max(max([x for x in approach1_he if x is not None]), 
             max([x for x in approach2_he if x is not None]), 
             max([x for x in approach3_he if x is not None]),
             max([x for x in approach4_he if x is not None])) * 1.1

# TOP SUBPLOT: Context (Dataset VI) - Human Effort
approach4_he_clean = [he for he in approach4_he if he is not None]
approach4_std_clean = [std for std in approach4_std if std is not None]
y_positions_approach4 = [i for i, he in enumerate(approach4_he) if he is not None]

line1, = ax1.plot(approach4_he_clean, y_positions_approach4, color=colors[0], linewidth=4, alpha=0.99)
ax1.errorbar(approach4_he_clean, y_positions_approach4, xerr=approach4_std_clean, 
           fmt='o', color=colors[0], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[0])

# BOTTOM SUBPLOT: Approaches I-III - Human Effort
# Plot Approach I
approach1_he_clean = [he for he in approach1_he if he is not None]
approach1_std_clean = [std for std in approach1_std if std is not None]
y_positions_approach1 = [i-7 for i, he in enumerate(approach1_he) if he is not None]  # Adjust for approach tasks starting at index 7

line2, = ax2.plot(approach1_he_clean, y_positions_approach1, color=colors[1], linewidth=4, alpha=0.99)
ax2.errorbar(approach1_he_clean, y_positions_approach1, xerr=approach1_std_clean, 
           fmt='s', color=colors[1], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[1])

# Plot Approach II
approach2_he_clean = [he for he in approach2_he if he is not None]
approach2_std_clean = [std for std in approach2_std if std is not None]
y_positions_approach2 = [i-7 for i, he in enumerate(approach2_he) if he is not None]  # Adjust for approach tasks starting at index 7

line3, = ax2.plot(approach2_he_clean, y_positions_approach2, color=colors[2], linewidth=4, alpha=0.99)
ax2.errorbar(approach2_he_clean, y_positions_approach2, xerr=approach2_std_clean, 
           fmt='d', color=colors[2], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[2])

# Plot Approach III
approach3_he_clean = [he for he in approach3_he if he is not None]
approach3_std_clean = [std for std in approach3_std if std is not None]
y_positions_approach3 = [i-7 for i, he in enumerate(approach3_he) if he is not None]  # Adjust for approach tasks starting at index 7

line4, = ax2.plot(approach3_he_clean, y_positions_approach3, color=colors[3], linewidth=4, alpha=0.99)
ax2.errorbar(approach3_he_clean, y_positions_approach3, xerr=approach3_std_clean, 
           fmt='^', color=colors[3], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[3])

# Customize the subplots
# TOP: Context HE
ax1.set_yticks(context_y_positions)
ax1.set_yticklabels(context_tasks, fontsize=14)
# ax1.set_title('Human Effort (HE) Comparison', fontsize=18, fontweight='bold')
ax1.annotate('Aufgaben', xy=(-0.15, 1.05), xycoords='axes fraction', fontsize=18, fontweight='bold', ha='left', va='bottom')
ax1.grid(True, alpha=0.3, axis='both')
ax1.legend([line1], [approach_labels[0]], loc='upper right', fontsize=12)
ax1.set_xlim(0, 250)
ax1.invert_yaxis()
ax1.tick_params(axis='x', labelsize=14)

# BOTTOM: Approaches I-III HE
ax2.set_yticks(approach_y_positions)
ax2.set_yticklabels(approach_tasks, fontsize=14)
ax2.set_xlabel('Repr. Human Effort (HE)', fontsize=16, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='both')
ax2.legend([line2, line3, line4], approach_labels[1:4], loc='upper right', fontsize=12)
ax2.set_xlim(0, 220)
ax2.invert_yaxis()
ax2.tick_params(axis='x', labelsize=14)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Display the plot
plt.savefig(r"C:\\Users\\56xsl\\Downloads\\he_only_comparison.png", format="png")

plt.show()

# Optional: Save the plot as PNG
# plt.savefig('he_only_comparison.png', dpi=300, bbox_inches='tight')
