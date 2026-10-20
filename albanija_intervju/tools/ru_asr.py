import json, sys, numpy as np, soundfile as sf, sherpa_onnx as so
M="/tmp/claude-0/models"; D=sys.argv[1]
wav,_=sf.read(f"{D}/audio.wav",dtype="float32")
v=so.VadModelConfig(); v.silero_vad.model=f"{M}/silero_vad.onnx"; v.silero_vad.min_silence_duration=0.3
v.silero_vad.min_speech_duration=0.2; v.silero_vad.max_speech_duration=14; v.silero_vad.threshold=0.4; v.sample_rate=16000
vad=so.VoiceActivityDetector(v,buffer_size_in_seconds=900); ch=[]
def drain():
    while not vad.empty(): ch.append((vad.front.start/16000,len(vad.front.samples)/16000)); vad.pop()
for i in range(0,len(wav),512): vad.accept_waveform(wav[i:i+512]); drain()
vad.flush(); drain()
# hard split anything >25s
segs=[]
for st,d in ch:
    while d>25: segs.append((st,20)); st+=20; d-=20
    segs.append((st,d))
P=f"{M}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"
pk=so.OfflineRecognizer.from_transducer(encoder=f"{P}/encoder.int8.onnx",decoder=f"{P}/decoder.int8.onnx",joiner=f"{P}/joiner.int8.onnx",tokens=f"{P}/tokens.txt",model_type="nemo_transducer",num_threads=4)
W=f"{M}/sherpa-onnx-whisper-large-v3"
wh=so.OfflineRecognizer.from_whisper(encoder=f"{W}/large-v3-encoder.int8.onnx",decoder=f"{W}/large-v3-decoder.int8.onnx",tokens=f"{W}/large-v3-tokens.txt",language="ru",task="transcribe",num_threads=4)
out=[]
for st,d in segs:
    x=np.concatenate([np.zeros(1600,np.float32),wav[int(st*16000):int((st+d)*16000)],np.zeros(1600,np.float32)])
    a=pk.create_stream(); a.accept_waveform(16000,x); pk.decode_stream(a)
    b=wh.create_stream(); b.accept_waveform(16000,x); wh.decode_stream(b)
    r=a.result; o={"start":st,"end":st+d,"wh":b.result.text,"pk":r.text,"tokens":r.tokens,"ts":[t+st-0.1 for t in r.timestamps]}
    out.append(o); print(f"[{st:7.2f}-{st+d:7.2f}] WH: {o['wh']}\n                   PK: {o['pk']}",flush=True)
    json.dump(out,open(f"{D}/asr.json","w"),ensure_ascii=False,indent=1)
