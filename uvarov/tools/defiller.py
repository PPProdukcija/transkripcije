import re, sys
def cap(m): return m.group(1)+m.group(2).upper()
for p in sys.argv[1:]:
    out=[]
    for ln in open(p,encoding="utf-8"):
        if ln.count("|")<3: out.append(ln); continue
        a,b,c,t=ln.rstrip("\n").split("|",3)
        t=" "+t
        t=re.sub(r"((?<!\d)[.?!…] |^ )(?:Pa|Eto|Dakle), ",r"\1",t)
        t=re.sub(r" Eto\. "," ",t)
        t=re.sub(r", zar ne\?","?",t); t=re.sub(r", zar ne([,.])",r"\1",t); t=re.sub(r" zar ne, "," ",t)
        t=re.sub(r", da tako kažem,","",t); t=re.sub(r", da tako kažem([.:?])",r"\1",t); t=re.sub(r" da tako kažem, "," ",t)
        t=re.sub(r", eto,",",",t)
        t=re.sub(r"((?<!\d)[.?!…] |^ )([a-zčćšđž])",cap,t)
        out.append(f"{a}|{b}|{c}|{t.strip()}\n")
    open(p,"w",encoding="utf-8").writelines(out)
