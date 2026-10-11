import json, re, difflib
MAX=32
CYR=dict(zip("абвгдђежзијклљмнњопрстћуфхцчџш",["a","b","v","g","d","dj","e","z","z","i","j","k","l","lj","m","n","nj","o","p","r","s","t","c","u","f","h","c","c","dz","s"]))
LAT={"č":"c","ć":"c","š":"s","ž":"z","đ":"dj","dž":"dz"}
def norm(w):
    w=w.lower(); w="".join(CYR.get(c,c) for c in w)
    for k,v in LAT.items(): w=w.replace(k,v)
    return re.sub(r"[^a-z]","",w)
# parakeet chars with times
asr=json.load(open("asr.json"))
pch=[];pt=[];chunk_end=[]
for d in asr:
    for tok,t in zip(d["pk_tokens"],d["pk_ts"]):
        for c in norm(tok): pch.append(c); pt.append(t)
    chunk_end.append((d["start"],d["end"]))
sents=[l.strip() for l in open("text.txt") if l.strip()]
words=[w for s in sents for w in s.split()]
mch=[];owner=[]
for i,w in enumerate(words):
    for c in norm(w): mch.append(c); owner.append(i)
sm=difflib.SequenceMatcher(None,mch,pch,autojunk=False)
wt=[None]*len(words)
for a,b,n in sm.get_matching_blocks():
    for k in range(n):
        i=owner[a+k]
        if wt[i] is None: wt[i]=pt[b+k]
# interpolate missing
for i in range(len(words)):
    if wt[i] is None:
        p=next((j for j in range(i-1,-1,-1) if wt[j] is not None),None)
        n=next((j for j in range(i+1,len(words)) if wt[j] is not None),None)
        wt[i]= (wt[p]+wt[n])/2 if p is not None and n is not None else (wt[p]+0.3 if p is not None else wt[n]-0.3)
for i in range(1,len(wt)): wt[i]=max(wt[i],wt[i-1]+0.05)
def wrap(clause):
    ws=clause.split()
    if len(clause)<=MAX: return [clause]
    n=-(-len(clause)//MAX)
    # balanced split into n lines via DP minimizing max length
    best=None
    import itertools
    for cuts in itertools.combinations(range(1,len(ws)),n-1):
        b=[0,*cuts,len(ws)]; lines=[" ".join(ws[b[i]:b[i+1]]) for i in range(n)]
        sc=max(map(len,lines))+0.01*sum(abs(len(l)-len(clause)/n) for l in lines)
        if best is None or sc<best[0]: best=(sc,lines)
    return best[1]
def split2(line):
    ws=line.split(); best=None
    for k in range(1,len(ws)):
        a=" ".join(ws[:k]); b=" ".join(ws[k:]); sc=abs(len(a)-len(b))
        if best is None or sc<best[0]: best=(sc,[a,b])
    return best[1]
cues=[]; wi=0
for block in open("layout.txt").read().strip().split("\n\n"):
    pair=[l.strip() for l in block.split("\n")]
    for l in pair: assert "," not in l[:-1] and len(l)<=32, l
    nw=sum(len(l.split()) for l in pair)
    assert [w for l in pair for w in l.split()]==words[wi:wi+nw], pair
    cues.append({"lines":pair,"w0":wi,"w1":wi+nw-1}); wi+=nw
assert wi==len(words)
def chunk_of(t):
    for a,b in chunk_end:
        if a-0.3<=t<=b+0.3: return (a,b)
for i,c in enumerate(cues):
    c["start"]=max(0,wt[c["w0"]]-0.08)
for i,c in enumerate(cues):
    last=wt[c["w1"]]; ch=chunk_of(last)
    nxt=cues[i+1]["start"] if i+1<len(cues) else 1e9
    est=last+max(0.35,0.07*len(norm(words[c["w1"]])))
    end=min(ch[1]+0.15,nxt) if ch and ch[1]<nxt else est
    if nxt-end<0.4: end=nxt   # close small gaps
    c["end"]=min(end,nxt)
def ts(t,sep=","):
    h=int(t//3600);m=int(t%3600//60);s=t%60
    return f"{h:02d}:{m:02d}:{int(s):02d}{sep}{int(round((s-int(s))*1000)):03d}"
with open("out.srt","w") as f:
    for i,c in enumerate(cues,1): f.write(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n"+"\n".join(c["lines"])+"\n\n")
json.dump(cues,open("cues.json","w"),ensure_ascii=False,indent=1)
print(open("out.srt").read())
