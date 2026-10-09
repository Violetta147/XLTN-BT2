"""Plot saved component contributions only, no inference or fitting."""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
p=Path(sys.argv[1]);d=pd.read_csv(p/'component_audit.csv');d=d[d.held=='full'];d.groupby(['label','component']).mean_contribution.mean().unstack().plot.bar();plt.ylabel('Mean magnitude contribution');plt.tight_layout();plt.savefig(p/'component_audit.png',dpi=180)
