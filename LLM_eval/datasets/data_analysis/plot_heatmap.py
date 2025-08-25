import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

# Data for each group
data = {
    "C": pd.DataFrame([
        [18, 3, 3, 3, 0, 0],      # Factual
        [1, 3, 12, 31, 4, 0],     # Conceptual
        [0, 0, 7, 4, 9, 0],       # Procedural
        [0, 0, 0, 0, 0, 1],       # Metacognitive
    ], columns=["Knowledge", "Comprehension", "Application", "Analysis", "Synthesis", "Evaluation"],
       index=["Factual", "Conceptual", "Procedural", "Metacognitive"]),
    "A.I": pd.DataFrame([
        [8, 2, 0, 0, 0, 0],       # Factual
        [0, 0, 2, 0, 2, 0],       # Conceptual
        [11, 2, 67, 0, 6, 0],     # Procedural
        [0, 0, 0, 0, 0, 0],       # Metacognitive
    ], columns=["Knowledge", "Comprehension", "Application", "Analysis", "Synthesis", "Evaluation"],
       index=["Factual", "Conceptual", "Procedural", "Metacognitive"]),
    "A.II": pd.DataFrame([
        [2, 0, 0, 0, 0, 0],       # Factual
        [0, 0, 0, 0, 0, 0],       # Conceptual
        [3, 0, 86, 0, 8, 1],      # Procedural
        [0, 0, 0, 0, 0, 0],       # Metacognitive
    ], columns=["Knowledge", "Comprehension", "Application", "Analysis", "Synthesis", "Evaluation"],
       index=["Factual", "Conceptual", "Procedural", "Metacognitive"]),
    "A.III": pd.DataFrame([
        [22, 0, 0, 0, 0, 0],      # Factual
        [0, 0, 0, 0, 0, 0],       # Conceptual
        [16, 0, 57, 0, 4, 0],     # Procedural
        [0, 0, 0, 0, 0, 0],       # Metacognitive
    ], columns=["Knowledge", "Comprehension", "Application", "Analysis", "Synthesis", "Evaluation"],
       index=["Factual", "Conceptual", "Procedural", "Metacognitive"]),
}

fig, axes = plt.subplots(4, 1, figsize=(6, 8))
custom_cmap = LinearSegmentedColormap.from_list("custom_blue", ["#ffffff", "#00549F"], N=256)
for ax, (title, df) in zip(axes, data.items()):
    # Prepare annotation labels with % (hide zeros)
    percent_labels = df.applymap(lambda x: f"{x}%" if x != 0 else "")
    sns.heatmap(df, annot=percent_labels, fmt="", cmap=custom_cmap, cbar=False, ax=ax, linewidths=0.2, linecolor='gray', annot_kws={"size":8}, vmin=0, vmax=90)
    ax.set_title(title, loc='left', fontsize=10, fontweight='bold')
    ax.set_ylabel("")
    # Move x-axis labels to top
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    ax.set_xlabel("")
    ax.set_xticklabels(df.columns, rotation=0, fontsize=8)
    ax.set_yticklabels(df.index, rotation=0, fontsize=8)
    # Remove grid for aesthetics
    ax.grid(False)

plt.tight_layout()
plt.show()