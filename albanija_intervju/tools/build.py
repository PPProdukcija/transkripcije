import sys
D=sys.argv[1]
L2C=[("Lj","Љ"),("LJ","Љ"),("lj","љ"),("Nj","Њ"),("NJ","Њ"),("nj","њ"),("Dž","Џ"),("DŽ","Џ"),("dž","џ")]
M=dict(zip("ABVGDĐEŽZIJKLMNOPRSTĆUFHCČŠabvgdđežzijklmnoprstćufhcčš","АБВГДЂЕЖЗИЈКЛМНОПРСТЋУФХЦЧШабвгдђежзијклмнопрстћуфхцчш"))
def cyr(s):
    for a,b in L2C: s=s.replace(a,b)
    return "".join(M.get(c,c) for c in s)
cues=[]
for ln in open(f"{D}/cues.txt",encoding="utf-8"):
    p=ln.rstrip("\n").split("|"); a,b=float(p[0]),float(p[1]); L=[x for x in p[2:] if x]
    assert len(L)<=2 and b>a, ln
    for x in L: assert len(x)<=28 and "," not in x[:-1], x
    cues.append((a,b,L))
for i in range(len(cues)-1): assert cues[i][1]<=cues[i+1][0]+1e-6, cues[i]
def ts(t): h=int(t//3600);m=int(t%3600//60);s=t%60; ms=round((s-int(s))*1000); return f"{h:02d}:{m:02d}:{int(s):02d},{ms:03d}"
off0=cues[0][0]
for name,f,off in [("titlovi_latinica.srt",str,0),("titlovi_cirilica.srt",cyr,0),("titlovi_latinica_od_nule.srt",str,off0),("titlovi_cirilica_od_nule.srt",cyr,off0)]:
    with open(f"{D}/{name}","w",encoding="utf-8") as o:
        for i,(a,b,L) in enumerate(cues,1): o.write(f"{i}\n{ts(a-off)} --> {ts(b-off)}\n"+"\n".join(f(x) for x in L)+"\n\n")
print(len(cues),"cues; max line",max(len(x) for c in cues for x in c[2]))
