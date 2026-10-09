"""Optional plot of measured full-train selected metrics only."""
from pathlib import Path
import sys
import pandas as pd
import matplotlib.pyplot as plt
out=Path(sys.argv[1]);x=pd.read_csv(out/'selected_metrics.csv');x=x[x.stage=='full_train'];fig,ax=plt.subplots(figsize=(8,4));ax.bar(x.file,x.average_mape);ax.axhline(2,color='red',linestyle='--');ax.set_ylabel('Average MAPE (%)');ax.set_title('H73 selected configuration, full train');fig.tight_layout();fig.savefig(out/'full_train.png',dpi=180)
