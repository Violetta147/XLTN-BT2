"""Plot saved stream labels; no learning or inference."""
import json,sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
p=Path(sys.argv[1]);truth=json.loads((p/'evaluation_only_labels.json').read_text());fig,axes=plt.subplots(2,1,figsize=(11,5),sharex=False)
for ax,identity in zip(axes,['primary','reverse']):
    b=np.load(p/f'{identity}_proof.npz');t=next(r for r in truth if r['stream']==identity and r['method']=='decoded');ax.step(b['block_times'],t['domains'],where='mid',label='Known phone/studio (evaluation only)');ax.step(b['block_times'],b['decoded_labels']+1.4,where='mid',label='Unlabeled clusters after temporal decoding')
    for v in t['true_boundaries_s']:ax.axvline(v,color='gray',alpha=.4)
    ax.set_title(identity);ax.set_ylim(-.2,2.6);ax.set_xlabel('Time (seconds)');ax.legend(loc='upper right',fontsize=8)
fig.tight_layout();fig.savefig(p/'stream_groups.png',dpi=180)
