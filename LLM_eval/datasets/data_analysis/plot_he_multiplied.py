import matplotlib.pyplot as plt
import numpy as np

# Data from the table
tasks = ['Find API Endpoint', 'Analyze JSON keys', 'Map Entities', 'Map Properties', 'Check Entity Classes', 'Map Supp. Entities', 'Find Connection Property',
         'Generate Root RDF', 'Generate Entity RDF', 'Generate Device RDF', 'Generate Supp. Entity RDF']

# Separate task lists for different contexts
context_tasks = ['Find API Endpoint', 'Analyze JSON keys', 'Map Entities', 'Map Properties', 'Check Entity Classes', 'Map Supp. Entities', 'Find Connection Property']
approach_tasks = ['Generate Root RDF', 'Generate Entity RDF', 'Generate Device RDF', 'Generate Supp. Entity RDF']

# Keep approach tasks separate from summary
# approach_tasks_with_summary = approach_tasks + ['Total (Context + Approach)']

# Rep. numbers from the images
context_rep = [2, 9, 9, 1, 7, 3, 1]  # Find API Endpoint, Analyze JSON keys, Map Entities, Map Properties, Check Entity Classes, Map Supp. Entities, Find Connection Property
approach_rep = [1, 4, 4, 3]  # Generate Root Triple, Generate Container Triple, Generate Device Triple, Generate Supp. Entity Triple

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

# Calculate multiplied values for context tasks
approach4_he_multiplied = [he * rep for he, rep in zip(approach4_he, context_rep) if he is not None]
approach4_std_multiplied = [std * rep for std, rep in zip(approach4_std, context_rep) if std is not None]

# Calculate multiplied values for approach tasks
approach1_he_clean = [he for he in approach1_he if he is not None]
approach1_std_clean = [std for std in approach1_std if std is not None]
approach1_he_multiplied = [he * rep for he, rep in zip(approach1_he_clean, approach_rep)]
approach1_std_multiplied = [std * rep for std, rep in zip(approach1_std_clean, approach_rep)]

approach2_he_clean = [he for he in approach2_he if he is not None]
approach2_std_clean = [std for std in approach2_std if std is not None]
approach2_he_multiplied = [he * rep for he, rep in zip(approach2_he_clean, approach_rep)]
approach2_std_multiplied = [std * rep for std, rep in zip(approach2_std_clean, approach_rep)]

approach3_he_clean = [he for he in approach3_he if he is not None]
approach3_std_clean = [std for std in approach3_std if std is not None]
approach3_he_multiplied = [he * rep for he, rep in zip(approach3_he_clean, approach_rep)]
approach3_std_multiplied = [std * rep for std, rep in zip(approach3_std_clean, approach_rep)]

# Calculate total values (sum of context + approach for each approach)
context_total = sum(approach4_he_multiplied)
approach1_total = context_total + sum(approach1_he_multiplied)
approach2_total = context_total + sum(approach2_he_multiplied)
approach3_total = context_total + sum(approach3_he_multiplied)

# Create figure with 1x2 subplots (horizontal layout) - removing third subplot
fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), gridspec_kw={'width_ratios': [7, 8]}, sharey='row')

# X positions for tasks
context_x_positions = np.arange(len(context_tasks))
approach_x_positions = np.arange(len(approach_tasks))

# Colors for each approach (reordered to put Context first)
colors = ['#612158', '#F6A800', '#0098A1', '#BDCD00']
approach_labels = ['Kontext', 'KG manuell', 'RML manuell', 'SIoT']

# Get the maximum HE value for consistent scaling (including multiplied values)
max_he_original = max(max([x for x in approach1_he if x is not None]), 
                     max([x for x in approach2_he if x is not None]), 
                     max([x for x in approach3_he if x is not None]),
                     max([x for x in approach4_he if x is not None])) * 1.1

max_he_multiplied = max(max(approach4_he_multiplied),
                       max(approach1_he_multiplied),
                       max(approach2_he_multiplied),
                       max(approach3_he_multiplied),
                       approach1_total, approach2_total, approach3_total) * 1.1

max_he = 820  # Set fixed maximum value

# LEFT SUBPLOT: Context (Dataset VI) - Human Effort
approach4_he_clean = [he for he in approach4_he if he is not None]
approach4_std_clean = [std for std in approach4_std if std is not None]
x_positions_approach4 = [i for i, he in enumerate(approach4_he) if he is not None]

# Plot original values with 50% transparency
# line1_orig, = ax1.plot(x_positions_approach4, approach4_he_clean, color=colors[0], linewidth=4, alpha=0.15)
# ax1.errorbar(x_positions_approach4, approach4_he_clean, yerr=approach4_std_clean, 
#            fmt='o', color=colors[0], capsize=5, capthick=2, markersize=14, alpha=0.15, elinewidth=2.5, ecolor=colors[0])

# Plot multiplied values with normal colors
line1_mult, = ax1.plot(x_positions_approach4, approach4_he_multiplied, color=colors[0], linewidth=4, alpha=1)
ax1.errorbar(x_positions_approach4, approach4_he_multiplied, yerr=approach4_std_multiplied, 
           fmt='o', color=colors[0], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[0])

# RIGHT SUBPLOT: Approaches I-III - Human Effort
x_positions_approach1 = [i for i in range(len(approach_tasks))]  # 0, 1, 2, 3
x_positions_approach2 = [i for i in range(len(approach_tasks))]  # 0, 1, 2, 3
x_positions_approach3 = [i for i in range(len(approach_tasks))]  # 0, 1, 2, 3

# Plot Approach I - Original values (50% transparency)
# line2_orig, = ax2.plot(x_positions_approach1, approach1_he_clean, color=colors[1], linewidth=4, alpha=0.15)
# ax2.errorbar(x_positions_approach1, approach1_he_clean, yerr=approach1_std_clean, 
#            fmt='s', color=colors[1], capsize=5, capthick=2, markersize=14, alpha=0.15, elinewidth=2.5, ecolor=colors[1])

# Plot Approach I - Multiplied values (normal colors)
line2_mult, = ax2.plot(x_positions_approach1, approach1_he_multiplied, color=colors[1], linewidth=4, alpha=1)
ax2.errorbar(x_positions_approach1, approach1_he_multiplied, yerr=approach1_std_multiplied, 
           fmt='s', color=colors[1], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[1])

# Plot Approach II - Original values (50% transparency)
# line3_orig, = ax2.plot(x_positions_approach2, approach2_he_clean, color=colors[2], linewidth=4, alpha=0.15)
# ax2.errorbar(x_positions_approach2, approach2_he_clean, yerr=approach2_std_clean, 
#            fmt='d', color=colors[2], capsize=5, capthick=2, markersize=14, alpha=0.15, elinewidth=2.5, ecolor=colors[2])

# Plot Approach II - Multiplied values (normal colors)
line3_mult, = ax2.plot(x_positions_approach2, approach2_he_multiplied, color=colors[2], linewidth=4, alpha=1)
ax2.errorbar(x_positions_approach2, approach2_he_multiplied, yerr=approach2_std_multiplied, 
           fmt='d', color=colors[2], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[2])

# Plot Approach III - Original values (50% transparency)
# line4_orig, = ax2.plot(x_positions_approach3, approach3_he_clean, color=colors[3], linewidth=4, alpha=0.15)
# ax2.errorbar(x_positions_approach3, approach3_he_clean, yerr=approach3_std_clean, 
#            fmt='^', color=colors[3], capsize=5, capthick=2, markersize=14, alpha=0.15, elinewidth=2.5, ecolor=colors[3])

# Plot Approach III - Multiplied values (normal colors)
line4_mult, = ax2.plot(x_positions_approach3, approach3_he_multiplied, color=colors[3], linewidth=4, alpha=1)
ax2.errorbar(x_positions_approach3, approach3_he_multiplied, yerr=approach3_std_multiplied, 
           fmt='^', color=colors[3], capsize=5, capthick=2, markersize=14, alpha=1, elinewidth=2.5, ecolor=colors[3])

# Customize the first plot subplots
# LEFT: Context HE
ax1.set_xticks(context_x_positions)
ax1.set_xticklabels(context_tasks, fontsize=18, rotation=20, ha='right')
# ax1.set_title('Human Effort (HE) Comparison with Rep. Multiplication', fontsize=18, fontweight='bold')
# ax1.set_ylabel('Repr. Human Effort (HE)', fontsize=16, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='both')
ax1.legend([line1_mult], [approach_labels[0]], loc='upper right', fontsize=18)
ax1.set_ylim(0, max_he)
ax1.tick_params(axis='y', labelsize=14)

# RIGHT SUBPLOT: Approaches I-III HE
ax2.set_xticks(approach_x_positions)
ax2.set_xticklabels(approach_tasks, fontsize=18, rotation=20, ha='right')
ax2.grid(True, alpha=0.3, axis='both')
ax2.legend([line2_mult, line3_mult, line4_mult], approach_labels[1:4], loc='upper left', fontsize=18)
ax2.set_ylim(0, max_he)
ax2.tick_params(axis='y', labelsize=14)

# Adjust layout to prevent label cutoff
plt.tight_layout()
plt.subplots_adjust(wspace=0.05)

# Display the first plot
plt.savefig(r"C:\\Users\\56xsl\\Downloads\\he_multiplied_comparison.png", format="png")
plt.show()

# Create separate plot for totals
fig2, ax3 = plt.subplots(1, 1, figsize=(8, 6))

# Total values data
total_values = [approach1_total, approach2_total, approach3_total]
total_x_positions = np.arange(len(total_values))  # X positions for each approach
total_markers = ['s', 'd', '^']
total_labels = ['Approach I Total', 'Approach II Total', 'Approach III Total']
max_he_total = 3000  # Set fixed maximum value for total subplot

for i, (total, marker, label, color) in enumerate(zip(total_values, total_markers, total_labels, colors[1:4])):
    ax3.scatter([i], [total], color=color, s=200, marker=marker, alpha=1, edgecolors='black', linewidth=2, label=label)
    ax3.text(i, total + max_he_total*0.02, f'{total:.0f}', 
             horizontalalignment='center', fontsize=12, fontweight='bold')

# Customize the totals plot
ax3.set_xticks(total_x_positions)
ax3.set_xticklabels(['Approach I', 'Approach II', 'Approach III'], fontsize=14, rotation=45, ha='right')
ax3.set_ylabel('Repr. Human Effort (HE)', fontsize=16, fontweight='bold')
ax3.set_title('Total Human Effort Comparison (Context + Approach)', fontsize=18, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='both')
ax3.legend(loc='upper right', fontsize=12)
ax3.set_ylim(0, max_he_total)
ax3.set_xlim(-0.5, len(total_values)-0.5)
ax3.tick_params(axis='y', labelsize=14)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Display the second plot (totals)
plt.savefig(r"C:\\Users\\56xsl\\Downloads\\he_totals_comparison.pdf", format="pdf")
plt.show()

# Print summary values for reference
print("Summary of total HE values (Context + Approach):")
print(f"Context total: {context_total:.1f}")
print(f"Approach I total: {approach1_total:.1f}")
print(f"Approach II total: {approach2_total:.1f}")
print(f"Approach III total: {approach3_total:.1f}")
print(f"Approach II total: {approach2_total:.1f}")
print(f"Approach III total: {approach3_total:.1f}")
