"""Optional plot from saved decoder metrics only."""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
p=Path(sys.argv[1]);d=pd.read_csv(p/'inner_traces.csv');d[d.outer_held=='final'].groupby('option_id').average_mape.agg(['mean','max']).plot.bar();plt.ylabel('Average MAPE (%)');plt.title('H76 train-file decoder validation');plt.tight_layout();plt.savefig(p/'decoder_validation.png',dpi=180)
