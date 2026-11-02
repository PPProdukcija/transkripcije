import json, re, sys, itertools
asr_path, units_path, out_srt = sys.argv[1:4]
MAX=28
asr=json.load(open(asr_path))
W=[]
for s in asr:
    cur=None
    for t,ts in zip(s["tokens"],s["ts"]):
        if t.startswith(" ") or cur is None: cur=[t.strip(),ts]; W.append(cur)
        else: cur[0]+=t
units=[]
for ln in open(units_path,encoding="utf-8"):
    ln=ln.strip()
    if not ln or ln.startswith("#"): continue
    sp,a,b,txt=ln.split("|",3); units.append((sp,float(a),float(b),txt.strip()))
CLITIC=set("je se su li mi ti ga joj im nam vam me te ih će ću ćemo ćete bi bih bismo biste sam si smo ste ju".split())
WEAK=set("u na o i a da sa s od za iz kod po pod nad pred prema kroz bez do ka uz među koji koja koje kojeg kome kojoj kojima što kako kad kada ako jer ili ni ne ali već pa te nego čak baš to ta taj ovaj ova ovo ovde tamo vrlo veoma".split())
def bad(prev_last,next_first):
    p=re.sub(r"[^\w]","",prev_last.lower()); n=re.sub(r"[^\w]","",next_first.lower())
    pen=0
    if n in CLITIC: pen+=8
    if p in WEAK and not prev_last.endswith((",",".","?","!",":")): pen+=5
    if re.fullmatch(r"\d[\d.,%]*",prev_last) : pen+=10
    if prev_last[:1].isupper() and next_first[:1].isupper() and not prev_last.endswith((",",".","?","!",":")): pen+=6
    return pen
def wrapk(c,k):
    ws=c.split(); n=len(ws)
    if k>n: return None
    if k==1: return [c]
    L=[len(w.replace("⟦","").replace("⟧","")) for w in ws]
    pre=[0]
    for x in L: pre.append(pre[-1]+x)
    def seg(i,j): return pre[j]-pre[i]+(j-i-1)
    best=None
    for T in sorted(set(seg(i,j) for i in range(n) for j in range(i+1,n+1))):
        if T*k < seg(0,n)-k: continue
        INF=1e9
        dp=[[INF]*(k+1) for _ in range(n+1)]; bk=[[None]*(k+1) for _ in range(n+1)]
        dp[0][0]=0
        for j in range(1,n+1):
            for kk in range(1,k+1):
                for i in range(j-1,-1,-1):
                    if seg(i,j)>T: break
                    if dp[i][kk-1]>=INF: continue
                    v=dp[i][kk-1]+(bad(ws[i-1],ws[i]) if i>0 else 0)
                    if v<dp[j][kk]: dp[j][kk]=v; bk[j][kk]=i
        if dp[n][k]>=INF: continue
        score=T+dp[n][k]
        if best is None or score<best[0]:
            cuts=[];j=n;kk=k
            while kk>0: i=bk[j][kk]; cuts.append((i,j)); j=i; kk-=1
            best=(score,[" ".join(ws[i:j]) for i,j in reversed(cuts)])
        if best and T>best[0]: break
    return best[1] if best else None
def vis(s): return len(s.replace("⟦","").replace("⟧",""))
def layout(sent):
    clauses=[c.strip() for c in re.split(r"(?<=[,:;])\s+",sent) if c.strip()]
    import math
    opts=[[(k,wrapk(c,k)) for k in range(max(1,math.ceil(vis(c)/MAX)),max(1,math.ceil(vis(c)/MAX))+3) if wrapk(c,k)] for c in clauses]
    best=None
    for combo in itertools.product(*opts):
        lines=[];cid=[];kk=[];base=0
        for ci,(k,L) in enumerate(combo):
            for l in L:
                base+=200*max(0,vis(l)-MAX)
                if k>1 and vis(l)<8: base+=10
            if k>1: base+=0.25*(max(map(vis,L))-min(map(vis,L)))+4*(k-1)
            if k>1 and vis(clauses[ci])<=MAX: base+=15
            if k>1 and len(clauses[ci].split())<=2: base+=30
            lines+=L; cid+=[ci]*k; kk+=[k]*k
        n=len(lines); INF=1e18; dp=[INF]*(n+1); bk=[0]*(n+1); dp[0]=0
        for i in range(1,n+1):
            for sz in (1,2):
                j=i-sz
                if j<0: continue
                c=dp[j]
                if sz==1:
                    c+= 80 if len(lines[j].split())>=3 else (55 if vis(lines[j])<14 else 25)
                    if kk[j]>1: c+=30
                else: c+=0.1*abs(vis(lines[j])-vis(lines[j+1]))
                if i<n and cid[i]==cid[i-1]: c+=25
                if c<dp[i]: dp[i]=c; bk[i]=j
        tot=base+dp[n]
        if best is None or tot<best[0]:
            cs=[];i=n
            while i>0: cs.append(lines[bk[i]:i]); i=bk[i]
            best=(tot,cs[::-1])
    return best[1]
def norm(s): return re.sub(r"[^\w]","",s.lower())
cues=[]
for ui,(sp,a,b,txt) in enumerate(units):
    toks=txt.split(" "); sents=[]; cur=[]
    for i,tk in enumerate(toks):
        cur.append(tk)
        nxt=toks[i+1] if i+1<len(toks) else ""
        endp=re.search(r"[.?!…][“”»\"]?$",tk) and not re.fullmatch(r"\d+\.",tk)
        if endp and (not nxt or re.match(r"[„“\"(]?[A-ZČĆŠĐŽ0-9]",nxt)):
            sents.append(" ".join(cur)); cur=[]
    if cur: sents.append(" ".join(cur))
    ucues=[c for s in sents for c in layout(s)]
    # time mapping by char fraction
    ws=[(w,t) for w,t in W if a-0.2<=t<=b+0.2]
    rl=[len(norm(w)) or 1 for w,_ in ws]; tot=sum(rl) or 1
    cum=[];acc=0
    for r in rl: cum.append(acc/tot); acc+=r
    stot=sum(vis(" ".join(c)) for c in ucues); sacc=0
    for c in ucues:
        f=sacc/stot; sacc+=vis(" ".join(c))+1
        if f==0: st=a
        elif not ws: st=a+f*(b-a)
        else:
            k=max(i for i in range(len(ws)) if cum[i]<=f+1e-9)
            # interpolate inside word k
            nxt=ws[k+1][1] if k+1<len(ws) else b
            frac=(f-cum[k])/((cum[k+1] if k+1<len(cum) else 1)-cum[k]+1e-9)
            st=ws[k][1]+frac*(nxt-ws[k][1])-0.05
        cues.append([max(a-0.05,st),None,c,ui])
    cues[-1][1]=b+0.25
for i in range(len(cues)):
    c=cues[i]
    if i+1<len(cues):
        n=cues[i+1]
        if n[3]==c[3]: c[1]=n[0]
        else: c[1]=min(c[1] if c[1] else units[c[3]][2]+0.25, n[0]-0.04)
for i,c in enumerate(cues):
    if c[1] is None: c[1]=units[c[3]][2]+0.25
    if c[1]-c[0]<0.9:
        lim=cues[i+1][0]-0.04 if i+1<len(cues) else c[0]+1.2
        c[1]=max(c[1],min(c[0]+1.0,lim))
# fix monotonic
for i in range(1,len(cues)):
    if cues[i][0]<cues[i-1][1]: cues[i-1][1]=cues[i][0]
L2C=[("Lj","Љ"),("LJ","Љ"),("lj","љ"),("Nj","Њ"),("NJ","Њ"),("nj","њ"),("Dž","Џ"),("DŽ","Џ"),("dž","џ")]
M=dict(zip("ABVGDĐEŽZIJKLMNOPRSTĆUFHCČŠabvgdđežzijklmnoprstćufhcčš","АБВГДЂЕЖЗИЈКЛМНОПРСТЋУФХЦЧШабвгдђежзијклмнопрстћуфхцчш"))
def cyr(s):
    out=[]
    for i,part in enumerate(re.split(r"[⟦⟧]",s)):
        if i%2: out.append(part); continue
        for x,y in L2C: part=part.replace(x,y)
        out.append("".join(M.get(ch,ch) for ch in part))
    return "".join(out)
def ts(t): t=max(0,t); h=int(t//3600);m=int(t%3600//60);s=t%60; ms=int(round((s-int(s))*1000)); 
def ts(t):
    t=max(0,t); ms_total=int(round(t*1000)); h=ms_total//3600000; m=ms_total%3600000//60000; s=ms_total%60000//1000; ms=ms_total%1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
bad=[]
with open(out_srt,"w",encoding="utf-8") as o:
    for i,(a,b,L,u) in enumerate(cues,1):
        for l in L:
            if vis(l)>MAX: bad.append(l)
            if re.search(r",\s",l) : bad.append(l)
        o.write(f"{i}\n{ts(a)} --> {ts(b)}\n"+"\n".join(cyr(x) for x in L)+"\n\n")
with open(out_srt.replace(".srt","_latinica_pregled.txt"),"w",encoding="utf-8") as o:
    for i,(a,b,L,u) in enumerate(cues,1): o.write(f"{i} {ts(a)} {b-a:.1f}s | "+" / ".join(x.replace('⟦','').replace('⟧','') for x in L)+"\n")
print(len(cues),"cues; problems:",bad[:10])
