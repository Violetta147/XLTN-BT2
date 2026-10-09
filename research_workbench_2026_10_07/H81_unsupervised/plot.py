"""Plot saved unlabeled held-file density only."""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
p=Path(sys.argv[1]);d=pd.read_csv(p/'held_density.csv');d.pivot(index='file',columns='k',values='negative_log_density').plot.bar();plt.ylabel('Held-file negative log density (lower is better)');plt.tight_layout();plt.savefig(p/'held_density.png',dpi=180)
