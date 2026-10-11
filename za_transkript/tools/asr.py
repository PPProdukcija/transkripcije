import json, sys, numpy as np, soundfile as sf, sherpa_onnx as so
M="/tmp/claude-0/models"
wav, sr = sf.read(sys.argv[1], dtype="float32")
vcfg = so.VadModelConfig(); vcfg.silero_vad.model=f"{M}/silero_vad.onnx"
vcfg.silero_vad.min_silence_duration=0.25; vcfg.silero_vad.min_speech_duration=0.2
vcfg.silero_vad.max_speech_duration=20; vcfg.silero_vad.threshold=0.4; vcfg.sample_rate=16000
vad = so.VoiceActivityDetector(vcfg, buffer_size_in_seconds=120)
chunks=[]
w=512
for i in range(0, len(wav), w):
    vad.accept_waveform(wav[i:i+w])
    while not vad.empty():
        chunks.append((vad.front.start/16000, np.array(vad.front.samples))); vad.pop()
vad.flush()
while not vad.empty():
    chunks.append((vad.front.start/16000, np.array(vad.front.samples))); vad.pop()
W=f"{M}/sherpa-onnx-whisper-large-v3"
wh = so.OfflineRecognizer.from_whisper(encoder=f"{W}/large-v3-encoder.int8.onnx", decoder=f"{W}/large-v3-decoder.int8.onnx",
    tokens=f"{W}/large-v3-tokens.txt", language="sr", task="transcribe", num_threads=4)
P=f"{M}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"
pk = so.OfflineRecognizer.from_transducer(encoder=f"{P}/encoder.int8.onnx", decoder=f"{P}/decoder.int8.onnx",
    joiner=f"{P}/joiner.int8.onnx", tokens=f"{P}/tokens.txt", model_type="nemo_transducer", num_threads=4)
out=[]
for st, samp in chunks:
    pad = np.concatenate([np.zeros(1600,np.float32), samp, np.zeros(1600,np.float32)])
    s1=wh.create_stream(); s1.accept_waveform(16000,pad); wh.decode_stream(s1)
    s2=pk.create_stream(); s2.accept_waveform(16000,pad); pk.decode_stream(s2)
    r=s2.result
    d={"start":st,"end":st+len(samp)/16000,"whisper":s1.result.text,"pk":r.text,
       "pk_tokens":r.tokens,"pk_ts":[t+st-0.1 for t in r.timestamps]}
    out.append(d); print(f"[{d['start']:.2f}-{d['end']:.2f}] {d['whisper']}\n      PK: {d['pk']}", flush=True)
json.dump(out, open("asr.json","w"), ensure_ascii=False, indent=1)
