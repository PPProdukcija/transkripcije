import json, sys, numpy as np, soundfile as sf, sherpa_onnx as so
M="/tmp/claude-0/models"
wav,_=sf.read("audio.wav",dtype="float32")
prev=json.load(open("asr.json"))
# build split points: for long chunks, split at biggest parakeet gaps so pieces <= 12s
segs=[]
for d in prev:
    st,en=d["start"],d["end"]; ts=d["pk_ts"]; toks=d["pk_tokens"]
    cuts=[st]
    while en-cuts[-1]>14:
        lo=cuts[-1]+6; hi=cuts[-1]+13
        best=None
        for i in range(1,len(ts)):
            if lo<ts[i]<hi and toks[i].startswith(" "):
                g=ts[i]-ts[i-1]
                if best is None or g>best[0]: best=(g,(ts[i-1]+ts[i])/2+0.05)
        cuts.append(best[1] if best else cuts[-1]+12)
    cuts.append(en)
    segs+= [(cuts[i],cuts[i+1]) for i in range(len(cuts)-1)]
W=f"{M}/sherpa-onnx-whisper-large-v3"
wh=so.OfflineRecognizer.from_whisper(encoder=f"{W}/large-v3-encoder.int8.onnx",decoder=f"{W}/large-v3-decoder.int8.onnx",
   tokens=f"{W}/large-v3-tokens.txt",language="sr",task="transcribe",num_threads=4)
out=[]
for a,b in segs:
    x=wav[max(0,int((a-0.15)*16000)):int((b+0.15)*16000)]
    s=wh.create_stream(); s.accept_waveform(16000,np.concatenate([np.zeros(1600,np.float32),x,np.zeros(1600,np.float32)])); wh.decode_stream(s)
    print(f"[{a:.2f}-{b:.2f}] {s.result.text}",flush=True); out.append({"start":a,"end":b,"text":s.result.text})
json.dump(out,open("wh2.json","w"),ensure_ascii=False,indent=1)
