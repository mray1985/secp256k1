
from pathlib import Path
import argparse,math,json
import pandas as pd,numpy as np
from puzzle_engine.core import *
def main():
 a=argparse.ArgumentParser();a.add_argument('--data',default='data');a.add_argument('--out',default='reports');a.add_argument('--formula',action='append',default=[]);z=a.parse_args();D=Path(z.data);O=Path(z.out);O.mkdir(exist_ok=True)
 st=pd.read_csv(next(D.glob('puzzle_1_70_delta_transition_states*')));P0=pd.read_csv(next(D.glob('puzzle_1_70_delta_transition_probability_matrix*')),index_col=0).values.astype(float)
 vals=[int(x) for x in st['delta']];state=build_states(vals);state['target_log2']=state.value.map(math.log2);state.to_csv(O/'state_engine.csv',index=False)
 f,r,pows,Gd,cycles=matrix_tools(P0);pd.DataFrame(f).to_csv(O/'transition_forward.csv');pd.DataFrame(r).to_csv(O/'transition_reverse.csv')
 for k,M in pows.items():pd.DataFrame(M).to_csv(O/f'transition_P{k}.csv')
 pd.DataFrame({'cycle':['->'.join(map(str,c)) for c in cycles[:1000]],'length':[len(c) for c in cycles[:1000]]}).to_csv(O/'cycles.csv',index=False)
 X=state.select_dtypes('number').fillna(0).values;spec,rw,pca,ts,um=embeddings(f,X);lab,stab=stability((f+f.T)/2)
 pd.DataFrame({'state':range(1,len(f)+1),'spec1':spec[:,0],'spec2':spec[:,1],'spec3':spec[:,2],'rw1':rw[:,0],'rw2':rw[:,1],'rw3':rw[:,2],'pca1':pca[:,0],'pca2':pca[:,1],'pca3':pca[:,2],'tsne1':ts[:,0],'tsne2':ts[:,1],'umap1':um[:,0],'umap2':um[:,1],'cluster':lab+1}).to_csv(O/'geometry.csv',index=False);(O/'cluster_stability.json').write_text(json.dumps(stab,indent=2))
 s,m,ng,phr=grammar(lab+1);(O/'symbolic_sequence.txt').write_text(s);ng.to_csv(O/'grammar_ngrams.csv',index=False);pd.DataFrame({'phrase':phr}).to_csv(O/'grammar_lz78.csv',index=False)
 scores,preds,imp=cv_predict(state,'target_log2');scores.to_csv(O/'prediction_cv.csv',index=False);imp.to_csv(O/'prediction_importance.csv',index=False)
 pear,spear,mi=correlations(state);pear.to_csv(O/'corr_pearson.csv');spear.to_csv(O/'corr_spearman.csv');mi.to_csv(O/'corr_mutual_information.csv')
 invariant_search(state,'target_log2').head(1000).to_csv(O/'invariants.csv',index=False)
 forms=z.formula or ['abs(delta)','delta % N','(x+y) % N','lambda_glv * delta % N'];rows=[]
 st2=st.copy();st2['delta']=st2['delta'].map(int)
 for form in forms:
  vals2=[]
  for _,row in st2.iterrows():
   try:vals2.append(float(eval_formula(form,row.to_dict())))
   except:vals2.append(np.nan)
  q=pd.Series(vals2);rows.append({'formula':form,'valid':q.notna().sum(),'cv':q.std()/(abs(q.mean())+1e-15),'corr_log_delta':q.corr(st2.delta.map(math.log2))})
 pd.DataFrame(rows).to_csv(O/'hypothesis_scores.csv',index=False)
 echo=next(D.glob('echo_curve_power_all_puzzles.txt'),None);tax=next(D.glob('tax_math_trials_P135_P160_full_hex.txt'),None)
 if echo and tax:
  e=numeric_tokens(echo);t=numeric_tokens(tax);(O/'echo_tax.json').write_text(json.dumps({'echo_count':len(e),'tax_count':len(t),'shared_exact':len(set(e)&set(t)),'echo_mean_bits':float(np.mean([x.bit_length() for x in e])) if e else None,'tax_mean_bits':float(np.mean([x.bit_length() for x in t])) if t else None},indent=2))
 print('Built',O)
if __name__=='__main__':main()
