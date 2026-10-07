import json
import numpy as np
from threadpoolctl import threadpool_limits
import voicing_matrix as api


def main():
    rng=np.random.default_rng(5100);bank={}
    for name in ('synthetic_A','synthetic_B'):
        state=np.tile(np.arange(3),40)
        x=rng.normal(0,.1,(len(state),17))+state[:,None]*.7
        x[:,0]=np.clip(.1+.38*state+rng.normal(0,.02,len(state)),0,1)
        x[:,1]=-6+2.9*state+rng.normal(0,.1,len(state))
        x[:,2]=5000-2000*state+rng.normal(0,50,len(state))
        x[:,3]=.9-.35*state+rng.normal(0,.02,len(state))
        pred=(state==2)&(np.arange(len(state))%2==0)
        bank[name]=dict(x=x,labels=np.array(['sil','uv','v'])[state],pitch=np.full(len(state),200.),
                        base_pred=pred,base_f0=np.where(pred,200.,np.nan))
    checked=0;poisoned=0
    with threadpool_limits(limits=1):
        for recipe in api.RECIPES:
            assert recipe['columns']==[col for block in recipe['blocks'] for col in api.BLOCKS[block]]
            for seed in api.SEEDS:
                model=api.fit(bank,sorted(bank),recipe,seed)
                pred,f0,prob,recover=api.infer(bank['synthetic_A'],model)
                assert np.all(pred[bank['synthetic_A']['base_pred']])
                if model:assert np.isfinite(prob).all() and ((prob>=0)&(prob<=1)).all()
                checked+=1
                if recipe['method']=='gmm':
                    expected=api.response(bank['synthetic_A']['x'],model)
                    other={name:{**data,'labels':np.full(len(data['labels']),'v')} for name,data in bank.items()}
                    api.MODEL_CACHE.clear()
                    result=api.fit(other,sorted(other),recipe,seed)
                    assert np.array_equal(expected,api.response(bank['synthetic_A']['x'],result))
                    poisoned+=1
    api.audit.json_write(api.OUT/'H51_precheck.json',dict(synthetic_only=True,uses_BT2_WAV=False,recipe_seed_checks=checked,
        unsupervised_label_poison_checks=poisoned,all_feature_subsets_present=True,old_pitch_mask_preserved=True))
    print('PASS H51 synthetic matrix',checked,'recipe-seed instances;',poisoned,'GMM poison checks')


if __name__=='__main__':main()
