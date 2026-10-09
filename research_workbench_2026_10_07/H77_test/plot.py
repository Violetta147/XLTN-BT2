"""Optional plot of measured train/test MAPE for the single frozen candidate."""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
p=Path(sys.argv[1]);d=pd.read_csv(p/'all_files.csv');d.set_index('file').average_mape.plot.bar();plt.axhline(2,color='red',linestyle='--');plt.ylabel('Average MAPE (%)');plt.title('H77 frozen classifier and decoder');plt.tight_layout();plt.savefig(p/'all_files.png',dpi=180)
