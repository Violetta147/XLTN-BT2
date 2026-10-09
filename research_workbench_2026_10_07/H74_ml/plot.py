"""Optional plot using saved train-only inner validation metrics."""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
p=Path(sys.argv[1]);d=pd.read_csv(p/'inner_traces.csv');d=d[d.outer_held=='final'];a=d.groupby('option_id').average_mape.agg(['mean','max']);a.plot.bar();plt.ylabel('Average MAPE (%)');plt.title('H74 train-file validation; historical energy control');plt.tight_layout();plt.savefig(p/'train_validation.png',dpi=180)
