"""Render saved post-freeze attribution only; no fitting or model selection."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

here = Path(__file__).resolve().parent
table = pd.read_csv(here / 'component_audit.csv')
group = table.groupby('component')[['v', 'uv', 'sil']].sum()
assert int(group.to_numpy().sum()) == int(table.frames.sum()) == 1291
fig, ax = plt.subplots(figsize=(8, 4.6), layout='constrained')
bottom = group.v * 0
for key, label, color in [('v', 'LAB voiced', '#14866d'), ('uv', 'LAB unvoiced', '#dba523'), ('sil', 'LAB silence', '#98a2b3')]:
    ax.bar(group.index, group[key], bottom=bottom, label=label, color=color)
    for idx in group.index:
        count = int(group.loc[idx, key])
        if count:
            ax.text(idx, bottom.loc[idx] + count / 2, str(count), ha='center', va='center', fontsize=10)
    bottom = bottom + group[key]
ax.set_xticks(group.index, ['0 (mapped V)', '1', '2', '3 (mapped V)'])
ax.set_xlabel('Frozen GMM component (maximum posterior assignment)')
ax.set_ylabel('Training frames')
ax.set_title('H81: teacher-label attribution AFTER model freeze')
ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
fig.savefig(here / 'component_attribution.png', dpi=150)
plt.close(fig)
print('Rendered saved training attribution; no fit, no selection, no test.')
