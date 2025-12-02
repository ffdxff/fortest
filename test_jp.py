#!/usr/bin/env python3

import wave
import sys
import json
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(0)

# ---- WAV 输入 ----
if len(sys.argv) < 2:
    print("Usage: python3 test_jp.py input.wav")
    sys.exit(1)

wav_path = sys.argv[1]
wf = wave.open(wav_path, "rb")

if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("Audio file must be WAV format mono PCM.")
    sys.exit(1)

# ---- 使用日语模型 ----
model = Model(model_name="vosk-model-small-ja-0.22")

rec = KaldiRecognizer(model, wf.getframerate())
rec.SetWords(True)

final_text = ""

print("Recognizing...")

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break

    if rec.AcceptWaveform(data):
        res = json.loads(rec.Result())
        text = res.get("text", "")
        if text:
            print("Sentence:", text)
            final_text += text + "\n"

# ---- 最终结果 ----
res = json.loads(rec.FinalResult())
text = res.get("text", "")
if text:
    final_text += text

print("\n===== Final Result =====")
print(final_text)

# ---- 写入到 /hostroot/text.txt，用于 Yocto GTK viewer ----
OUTPUT_PATH = "/hostroot/text.txt"

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(final_text)

print("\n✔ Written to:", OUTPUT_PATH)
