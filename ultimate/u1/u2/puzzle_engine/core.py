
import ast, math, operator, json, re
from pathlib import Path
from collections import Counter
import numpy as np, pandas as pd, networkx as nx
from sklearn.cluster import SpectralClustering
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import mean_absolute_error, adjusted_rand_score
from sklearn.feature_selection import mutual_info_regression
P=115792089237316195423570985008687907853269984665640564039457584007908834671663
N=115792089237316195423570985008687907852837564279074904382605163141518161494337
GX=55066263022277343669578718895168534326250603453777594175500187360389116729240
GY=32670510020758816978083085130507043184471273380659243275938904335757337482424
G=(GX,GY); BETA=55594575648329892869085402983802832744385952214688224221778511981742606582254
LAMBDA=37718080363155996902926221483475020450927657555482586988616620542887997980018
PRIMES=[2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
def inv(a,m): return pow(a%m,-1,m)
def add(A,B):
 if A is None:return B
 if B is None:return A
 x1,y1=A;x2,y2=B
 if x1==x2 and (y1+y2)%P==0:return None
 l=(3*x1*x1)*inv(2*y1,P)%P if A==B else (y2-y1)*inv(x2-x1,P)%P
 x3=(l*l-x1-x2)%P;return x3,(l*(x1-x3)-y1)%P
def mul(k,Q=G):
 R=None;A=Q;k%=N
 while k:
  if k&1:R=add(R,A)
  A=add(A,A);k>>=1
 return R
def glv_orbit(d): return sorted({d%N,LAMBDA*d%N,LAMBDA*LAMBDA*d%N,-d%N,-LAMBDA*d%N,-LAMBDA*LAMBDA*d%N})
def carry(a,b):
 c=run=count=long=0
 for i in range(max(a.bit_length(),b.bit_length())+2):
  c=1 if ((a>>i)&1)+((b>>i)&1)+c>=2 else 0
  if c:count+=1;run+=1;long=max(long,run)
  else:run=0
 return count,long
def borrow(a,b):
 if a<b:a,b=b,a
 br=run=count=long=0
 for i in range(max(a.bit_length(),b.bit_length())+2):
  br=1 if ((a>>i)&1)<(((b>>i)&1)+br) else 0
  if br:count+=1;run+=1;long=max(long,run)
  else:run=0
 return count,long
def factor(n):
 r=abs(n);o={}
 for p in PRIMES:
  e=0
  while r and r%p==0:r//=p;e+=1
  o[p]=e
 return o,r
def entropy(n,w=256):
 p=n.bit_count()/w
 return 0 if p in (0,1) else -(p*math.log2(p)+(1-p)*math.log2(1-p))
def build_states(vals):
 rows=[]
 for i,v in enumerate(vals):
  f,rem=factor(v);q=mul(v);nxt=vals[i+1] if i+1<len(vals) else v;c=carry(v,nxt);b=borrow(v,nxt)
  rows.append({'state':i+1,'value':v,'bit_length':v.bit_length(),'popcount':v.bit_count(),'entropy':entropy(v),'carry_count':c[0],'carry_chain':c[1],'borrow_count':b[0],'borrow_chain':b[1],'cofactor':rem,'x':q[0],'y':q[1],**{f'v_{p}':f[p] for p in PRIMES},**{f'mod_{p}':v%p for p in PRIMES}})
 return pd.DataFrame(rows)
def normalize(W):
 s=W.sum(1,keepdims=True);s[s==0]=1;return W/s
def matrix_tools(Pm):
 f=normalize(Pm);r=normalize(Pm.T);powers={k:np.linalg.matrix_power(f,k) for k in [2,4,8,16,32]}
 Gd=nx.DiGraph()
 for i in range(len(f)):
  for j in np.argsort(f[i])[-4:]:
   if i!=j:Gd.add_edge(i+1,j+1,weight=float(f[i,j]))
 cycles=nx.cycle_basis(Gd.to_undirected())[:1000]
 return f,r,powers,Gd,sorted(cycles,key=len)
def embeddings(Pm,X):
 vals,vec=np.linalg.eig(Pm.T);order=np.argsort(-np.abs(vals));sel=[i for i in order if abs(vals[i]-1)>1e-9][:3];spec=np.real(vec[:,sel])
 blocks=[];cur=Pm.copy()
 for _ in range(6):blocks.append(cur);cur=cur@Pm
 rw=PCA(3,random_state=135).fit_transform(np.concatenate(blocks,1));pca=PCA(3,random_state=135).fit_transform(X)
 ts=TSNE(2,perplexity=min(20,max(5,len(X)//4)),random_state=135,init='pca',learning_rate='auto').fit_transform(X)
 try:
  import umap; um=umap.UMAP(n_components=2,random_state=135).fit_transform(X)
 except Exception:um=ts.copy()
 return spec,rw,pca,ts,um
def stability(A,k=7,reps=12):
 labs=[SpectralClustering(k,affinity='precomputed',random_state=s).fit_predict(A) for s in range(reps)]
 scores=[adjusted_rand_score(labs[i],labs[j]) for i in range(reps) for j in range(i+1,reps)]
 return labs[0],{'mean_ari':float(np.mean(scores)),'min_ari':float(np.min(scores)),'max_ari':float(np.max(scores))}
def grammar(labels):
 u=sorted(set(labels));m={v:chr(65+i) for i,v in enumerate(u)};s=''.join(m[x] for x in labels);rows=[]
 for n in range(1,9):
  c=Counter(s[i:i+n] for i in range(len(s)-n+1))
  rows += [{'n':n,'motif':a,'count':b} for a,b in c.items() if b>=2]
 d={};phr=[];w='';q=1
 for ch in s:
  wc=w+ch
  if wc in d:w=wc
  else:d[wc]=q;q+=1;phr.append(wc);w=''
 if w:phr.append(w)
 return s,m,pd.DataFrame(rows),phr
def correlations(df):
 X=df.select_dtypes('number').replace([np.inf,-np.inf],np.nan).fillna(0);pear=X.corr();spear=X.corr('spearman');M=np.zeros((len(X.columns),len(X.columns)))
 for i,c in enumerate(X.columns):
  try:M[:,i]=mutual_info_regression(X.values,X[c],random_state=135)
  except:pass
 return pear,spear,pd.DataFrame(M,index=X.columns,columns=X.columns)
def cv_predict(df,target):
 X=df.select_dtypes('number').drop(columns=[target],errors='ignore').replace([np.inf,-np.inf],np.nan).fillna(0);y=df[target]
 cv=KFold(min(7,len(df)),shuffle=True,random_state=135);mods={'rf':RandomForestRegressor(n_estimators=300,min_samples_leaf=2,random_state=135),'extra':ExtraTreesRegressor(n_estimators=300,min_samples_leaf=2,random_state=135),'gbr':GradientBoostingRegressor(random_state=135)};rows=[];preds={}
 for n,m in mods.items():
  p=cross_val_predict(m,X,y,cv=cv);preds[n]=p;rows.append({'model':n,'mae':mean_absolute_error(y,p),'median_abs_error':float(np.median(abs(y-p)))})
 best=min(rows,key=lambda x:x['mae'])['model'];model=mods[best];model.fit(X,y);imp=pd.DataFrame({'feature':X.columns,'importance':model.feature_importances_}).sort_values('importance',ascending=False)
 return pd.DataFrame(rows),preds,imp
ALLOWED={'abs':abs,'log':math.log,'log2':math.log2,'sqrt':math.sqrt,'pow':pow,'min':min,'max':max,'gcd':math.gcd}
CONST={'N':N,'P':P,'Gx':GX,'Gy':GY,'lambda_glv':LAMBDA,'beta':BETA}
class E(ast.NodeVisitor):
 def __init__(s,e):s.e={**CONST,**ALLOWED,**e}
 def visit_Expression(s,n):return s.visit(n.body)
 def visit_Constant(s,n):return n.value
 def visit_Name(s,n):return s.e[n.id]
 def visit_BinOp(s,n):
  a,b=s.visit(n.left),s.visit(n.right);ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow,ast.BitXor:operator.xor};return ops[type(n.op)](a,b)
 def visit_UnaryOp(s,n):
  a=s.visit(n.operand);return -a if isinstance(n.op,ast.USub) else a
 def visit_Call(s,n):return s.visit(n.func)(*[s.visit(a) for a in n.args])
 def generic_visit(s,n):raise ValueError(type(n).__name__)
def eval_formula(x,e):return E(e).visit(ast.parse(x,mode='eval'))
def invariant_search(df,target,maxcols=24):
 X=df.select_dtypes('number').fillna(0);cols=list(X.columns[:maxcols]);rows=[]
 un={'id':lambda x:x,'abs':np.abs,'log1p':lambda x:np.log1p(abs(x)),'sqrt':lambda x:np.sqrt(abs(x)),'sq':lambda x:x*x};bi={'add':lambda a,b:a+b,'sub':lambda a,b:a-b,'mul':lambda a,b:a*b,'ratio':lambda a,b:a/(b+1e-15),'mod':lambda a,b:np.mod(a,abs(b)+1)}
 for c in cols:
  for n,f in un.items():
   try:
    v=f(X[c].values);cv=np.std(v)/(abs(np.mean(v))+1e-15);co=abs(pd.Series(v).corr(X[target])) if target in X else 0;rows.append({'expression':f'{n}({c})','stability':1/(1+cv),'predictive':co,'uniqueness':pd.Series(v).nunique()/len(v)})
   except:pass
 for ia,a in enumerate(cols):
  for b in cols[ia+1:]:
   for n,f in bi.items():
    try:
     v=f(X[a].values,X[b].values);v=np.nan_to_num(v);cv=np.std(v)/(abs(np.mean(v))+1e-15);co=abs(pd.Series(v).corr(X[target])) if target in X else 0;rows.append({'expression':f'{n}({a},{b})','stability':1/(1+cv),'predictive':co,'uniqueness':pd.Series(v).nunique()/len(v)})
    except:pass
 o=pd.DataFrame(rows);o['score']=.45*o.stability+.4*o.predictive+.15*o.uniqueness;return o.sort_values('score',ascending=False)
def numeric_tokens(path):
 t=Path(path).read_text(errors='ignore');return [int(x,16) if re.search('[a-fA-F]',x) else int(x) for x in re.findall(r'\b[0-9a-fA-F]{8,}\b',t)]
