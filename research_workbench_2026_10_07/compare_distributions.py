"""Exploratory descriptive analysis of saved contours; no F0 inference or tuning."""
import argparse,json,math,subprocess,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import recovery_pitch as api
HERE,OUT,REPO,core,audit=api.HERE,api.OUT,api.REPO,api.core,api.audit
PUBLIC_MODELS=['praat6_ac_10ms','praat7_filtered_v0.45','pyin_f40','PEFAC_native_q0.5']
LABELS=['Praat6 raw AC','Praat7 filtered AC','pYIN 40ms','PEFAC, pv>0.5']
def register():
    assert not (HERE/'R02_REGISTRY.json').exists()
    old=json.loads((HERE/'H68_REGISTRY.json').read_text())
    sources=[REPO/p for p in old['source_hashes']]
    sources += [HERE/p for p in ('compare_distributions.py','R02_DISTRIBUTION_PLAN.md','results/R01_reference_matches.csv','results/R01_new_native_frames.csv','results/R01_label_count_audit.csv','results/H30_raw_native_frames.csv','results/H33_raw_native_frames.csv','results/H48_all_files.csv','results/H66_fixed.csv','results/H67_fixed.csv','results/H68_fixed.csv')]
    for prefix in ('H66_predictions','H67_predictions','H68_native'):
        sources+=sorted(OUT.glob(prefix+'_*.npz'))
    sources+=sorted(core.TRAIN.glob('*.lab'))+sorted((REPO/'TinHieuKiemThu').glob('*.lab'))
    audit.json_write(HERE/'R02_REGISTRY.json',dict(kind='cached_distribution_analysis',rollback=api.matrix.commit_id(),source_hashes={str(p.relative_to(REPO)):audit.digest(p) for p in sources},external_protected=old['external_protected'],new_inference=False,selection_or_promotion=False))
    print('R02 sources registered; no statistics/inference run')
def describe(identity,name,times,values,target,origin):
    samples=[float(v) for v in values if np.isfinite(v) and v>0]
    n=len(samples);mean=math.fsum(samples)/n
    deviations=np.array([v-mean for v in samples]);squares=deviations**2;ss=math.fsum(float(x) for x in squares);std=math.sqrt(ss/n)
    assert math.isclose(mean,np.mean(samples),rel_tol=1e-12) and math.isclose(std,np.std(samples),rel_tol=1e-12)
    quantiles=np.quantile(samples,[.01,.05,.25,.5,.75,.95,.99],method='linear')
    # Independent linear interpolation of sorted order statistics.
    ordered=sorted(samples)
    for q,value in zip((.01,.05,.25,.5,.75,.95,.99),quantiles):
        position=q*(n-1);i=math.floor(position);j=math.ceil(position);expected=ordered[i]+(position-i)*(ordered[j]-ordered[i]);assert math.isclose(value,expected,rel_tol=1e-12)
    third=math.fsum(float(x)**3 for x in deviations)/n;fourth=math.fsum(float(x)**4 for x in deviations)/n
    count_top=math.ceil(.05*n);top_share=100*math.fsum(sorted(float(x) for x in squares)[-count_top:])/ss if ss else 0.
    over400=np.array(samples)>400;over_ss=math.fsum(float(v) for v in squares[over400])
    row=dict(option_id=identity,file=name,origin=origin,native_or_canonical_hop_s=float(np.median(np.diff(times))),F0mean=mean,F0std=std,F0num=n,min_hz=min(samples),max_hz=max(samples),median_hz=float(quantiles[3]),skewness=third/std**3 if std else 0.,excess_kurtosis=fourth/std**4-3 if std else 0.,robust_IQR_sigma=float((quantiles[4]-quantiles[2])/1.3489795003921634),robust_90pct_sigma=float((quantiles[5]-quantiles[1])/3.2897072539029444),top5pct_deviation_variance_share_pct=top_share,above400_count=int(over400.sum()),above400_variance_share_pct=100*over_ss/ss if ss else 0.,teacher_mean=target['F0mean'],teacher_std=target['F0std'],teacher_count=target['F0num'],mean_signed_hz=mean-target['F0mean'],std_signed_hz=std-target['F0std'],count_signed=n-target['F0num'],mean_ratio=mean/target['F0mean'],std_ratio=std/target['F0std'],count_ratio=n/target['F0num'])
    row.update({f'q{round(q*100):02d}_hz':float(v) for q,v in zip((.01,.05,.25,.5,.75,.95,.99),quantiles)})
    return row
def run():
    assert not (OUT/'R02_receipt.json').exists()
    reg=json.loads((HERE/'R02_REGISTRY.json').read_text())
    for p,d in reg['source_hashes'].items():assert audit.digest(REPO/p)==d,p
    for p,d in reg['external_protected'].items():assert audit.digest(Path(p))==d,p
    from reference_reconstruction import guard
    head=guard();targets={p.name:core.read_stats(core.TRAIN_GT/p.with_suffix('.lab').name) for p in sorted(core.TRAIN.glob('*.wav'))}
    baselines=pd.read_csv(OUT/'H47_nested_contours.csv',float_precision='round_trip');baselines=baselines[baselines.model=='candidate']
    collections={};duplicates=[]
    def add(identity,name,times,values,origin):
        key=(identity,name);times=np.asarray(times);values=np.asarray(values)
        if key in collections:
            old=collections[key];assert np.array_equal(old[0],times) and np.allclose(old[1],values,equal_nan=True,atol=0,rtol=0)
            duplicates.append(dict(option_id=identity,file=name,duplicate_origin=origin));return
        collections[key]=(times,values,origin)
    table=pd.read_csv(OUT/'R01_new_native_frames.csv',float_precision='round_trip')
    for (identity,name),g in table.groupby(['option_id','file']):add(identity,name,g.time_s,g.f0_hz,'R01_native')
    for family in ('H30','H33'):
        table=pd.read_csv(OUT/f'{family}_raw_native_frames.csv',float_precision='round_trip')
        for (identity,name),g in table.groupby(['option_id','file']):add(identity,name,g.time_s,g.raw_f0_hz,f'{family}_cached_native')
    for name,g in baselines.groupby('file'):
        add('hard170',name,g.time_s,g.f0_hz,'H47_canonical_cached')
        for family,identity in [('H66','custom_AR1'),('H67','custom_AR4')]:
            p=dict(np.load(OUT/f'{family}_predictions_{Path(name).stem}.npz'));add(identity,name,p['times'],p['f0'][1],f'{family}_canonical_cached')
        p=dict(np.load(OUT/f'H68_native_{Path(name).stem}.npz'));add('PEFAC_native_q0.5',name,p['native_times'],np.where(p['pv']>.5,p['raw_f0'],np.nan),'H68_cached_native')
    rows=[];paired=[]
    for (identity,name),(times,values,origin) in sorted(collections.items()):
        rows.append(describe(identity,name,times,values,targets[name],origin))
        base=baselines[baselines.file==name];bt=base.time_s.to_numpy();bf=base.f0_hz.to_numpy();bp=base.pred_voiced.to_numpy(bool);pair=[]
        for t,f in zip(times,values):
            if not (np.isfinite(f) and f>0):continue
            j=int(np.argmin(abs(bt-t)))
            if bp[j] and abs(bt[j]-t)<=.005+1e-12:pair.append(float(f/bf[j]))
        pair=np.array(pair)
        paired.append(dict(option_id=identity,file=name,paired_voiced_count=len(pair),ratio_half_count=int(((pair>=.45)&(pair<=.55)).sum()),ratio2_count=int(((pair>=1.8)&(pair<=2.2)).sum()),ratio3_count=int(((pair>=2.7)&(pair<=3.3)).sum()),ratio4_count=int(((pair>=3.6)&(pair<=4.4)).sum()),note='disagreement with cached hard170; not octave ground truth'))
    summary=pd.DataFrame(rows);summary.to_csv(OUT/'R02_distribution_summary.csv',index=False)
    pd.DataFrame(paired).to_csv(OUT/'R02_paired_ratio_disagreements.csv',index=False)
    # Check shared definition against previously saved reference statistics.
    previous=pd.read_csv(OUT/'R01_reference_matches.csv',float_precision='round_trip');previous=previous[previous.std_ddof==0]
    checked=0
    for row in rows:
        prefix='' if row['origin']=='R01_native' else 'H30:' if row['origin']=='H30_cached_native' else 'H33:' if row['origin']=='H33_cached_native' else None
        if prefix is not None:
            match=previous[(previous.file==row['file'])&(previous.option_id==prefix+row['option_id'])].iloc[0]
            for key in ('F0mean','F0std','F0num'):assert np.isclose(row[key],match[key],atol=1e-9,rtol=1e-9)
            checked+=1
    density=[]
    for name in targets:
        ac_auto=collections[('praat6_ac_auto',name)];ac10=collections[('praat6_ac_10ms',name)];assert np.array_equal(ac_auto[0],ac10[0]) and np.array_equal(ac_auto[1],ac10[1])
        ca=summary[(summary.file==name)&(summary.option_id=='praat6_cc_auto')].iloc[0];ct=summary[(summary.file==name)&(summary.option_id=='praat6_cc_10ms')].iloc[0]
        density.append(dict(file=name,CC_auto_hop_ms=ca.native_or_canonical_hop_s*1000,CC_10ms_hop_ms=ct.native_or_canonical_hop_s*1000,CC_voiced_count_ratio=ca.F0num/ct.F0num,AC_auto_identical_to_10ms=True))
    pd.DataFrame(density).to_csv(OUT/'R02_time_density_pattern.csv',index=False)
    old_new=[]
    for split,data,gt in [('train',core.TRAIN,core.TRAIN_GT),('test_cached_reference_only',REPO/'TinHieuKiemThu',core.HERE/'test_3gt')]:
        for lab in sorted(data.glob('*.lab')):
            old={line.split()[0]:float(line.split()[1]) for line in lab.read_text().splitlines() if line.startswith(('F0mean','F0std'))};new=core.read_stats(gt/lab.name)
            old_new.append(dict(file=lab.with_suffix('.wav').name,split=split,old_mean=old['F0mean'],new_mean=new['F0mean'],mean_delta=new['F0mean']-old['F0mean'],old_std=old['F0std'],new_std=new['F0std'],std_delta=new['F0std']-old['F0std'],teacher_count=new['F0num']))
    pd.DataFrame(old_new).to_csv(OUT/'R02_old_new_reference.csv',index=False)
    figures=plot(collections,targets,summary)
    outputs=[OUT/f'R02_{p}.csv' for p in ('distribution_summary','paired_ratio_disagreements','time_density_pattern','old_new_reference')]+figures
    audit.json_write(OUT/'R02_receipt.json',dict(status='PASS',preregistered_analysis_commit=head,new_F0_inference=False,test_inference=False,descriptive_only=True,groups=len(rows),duplicate_Praat7_groups=duplicates,AC_auto_10ms_exact_duplicate_files=4,independent_scalar_and_quantile_checks=True,prior_native_stats_groups_verified=checked,artifacts={str(p.relative_to(REPO)):audit.digest(p) for p in outputs},limitations=['Teacher distribution unavailable; only mean/std/count.','Different native windows/masks/steps; no uniform software ranking as frame accuracy.','4 training files; overlapping frames and reused settings are not independent replications.','Ratios to baseline are disagreement, not frame truth.','No change to GT/baseline and no tuning/filtering from shapes.']))
    print(summary[summary.option_id.isin(PUBLIC_MODELS+['hard170'])][['option_id','file','mean_ratio','std_ratio','count_ratio','above400_count','above400_variance_share_pct','top5pct_deviation_variance_share_pct','robust_IQR_sigma','robust_90pct_sigma']].to_string(index=False))
    print('Time density:',density);print('PASS R02',len(rows),'cached groups;',checked,'native statistics parity checks')
def plot(collections,targets,summary):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    names=sorted(targets);colors=['#e45756','#4c78a8','#54a24b','#b279a2'];maximum=max(650,max(float(np.nanmax(collections[(m,n)][1])) for m in PUBLIC_MODELS for n in names)+10);bins=np.linspace(50,maximum,61)
    figs=[]
    for kind in ('histogram','ecdf'):
        fig,axes=plt.subplots(2,2,figsize=(12,8),sharex=True)
        for ax,name in zip(axes.flat,names):
            target=targets[name];ax.axvspan(target['F0mean']-target['F0std'],target['F0mean']+target['F0std'],color='#888888',alpha=.15);ax.axvline(target['F0mean'],color='black',ls='--',lw=1.3)
            for model,label,color in zip(PUBLIC_MODELS,LABELS,colors):
                values=collections[(model,name)][1];values=values[np.isfinite(values)&(values>0)]
                if kind=='histogram':ax.hist(values,bins=bins,density=True,histtype='step',lw=1.5,label=label,color=color)
                else:ordered=np.sort(values);ax.step(ordered,np.arange(1,len(ordered)+1)/len(ordered),where='post',label=label,color=color,lw=1.5)
            ax.set_title(f"{name}: thầy mean={target['F0mean']}, std={target['F0std']}, N={int(target['F0num'])}");ax.set_xlim(50,maximum);ax.set_xlabel('F0 công cụ (Hz)');ax.set_ylabel('Mật độ chuẩn hóa' if kind=='histogram' else 'Tỷ lệ tích lũy');ax.grid(alpha=.2)
        handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=4,bbox_to_anchor=(.5,.945))
        fig.suptitle('Phân phối output native trên train; chỉ có mốc mean/std của thầy',y=.99)
        fig.text(.5,.018,'Đường đứt: mean thầy; vùng xám: mean ± std thầy. Vùng xám không phải phân phối/nhãn F0 từng khung.',ha='center',fontsize=10)
        fig.tight_layout(rect=[0,.04,1,.9]);path=HERE/'figures'/f'R02_{kind}.png';fig.savefig(path,dpi=160);plt.close(fig);figs.append(path)
    fig,axes=plt.subplots(1,3,figsize=(15,5.5));models=PUBLIC_MODELS+['hard170'];labels=LABELS+['hard170 (canonical)']
    for ax,key,title in zip(axes,('mean_ratio','std_ratio','count_ratio'),('Mean công cụ / mean thầy','Std công cụ / std thầy','Count công cụ / count thầy')):
        values=np.array([[summary[(summary.file==name)&(summary.option_id==model)].iloc[0][key] for model in models] for name in names]);maxvalue=max(1.1,float(values.max()));im=ax.imshow(values,cmap='coolwarm',norm=TwoSlopeNorm(vmin=0,vcenter=1,vmax=maxvalue));ax.set_title(title);ax.set_xticks(range(len(models)),labels,rotation=50,ha='right',fontsize=9);ax.set_yticks(range(len(names)),names)
        for i in range(len(names)):
            for j in range(len(models)):ax.text(j,i,f'{values[i,j]:.3f}',ha='center',va='center',color='black',fontsize=10)
    fig.suptitle('Mốc tỷ lệ 1 là bằng số liệu thầy; khác native time grid / V-UV criterion');fig.tight_layout(rect=[0,0,1,.93]);path=HERE/'figures/R02_ratios.png';fig.savefig(path,dpi=160);plt.close(fig);figs.append(path)
    return figs
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['register','run']);args=parser.parse_args();register() if args.action=='register' else run()
