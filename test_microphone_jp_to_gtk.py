#!/usr/bin/env python3
import argparse
import queue
import sys
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(0)

q = queue.Queue()
OUT_PATH = "/hostroot/text.txt"

def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text

def write_text(s: str):
    try:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            f.write(s + "\n")
    except Exception as e:
        # 写文件失败也不要让识别停掉
        print("write_text error:", e, file=sys.stderr)

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-l", "--list-devices", action="store_true",
                    help="show list of audio devices and exit")
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)

parser = argparse.ArgumentParser(parents=[parser])
parser.add_argument("-d", "--device", type=int_or_str,
                    help="input device (numeric ID or substring)")
parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument("-m", "--model", type=str,
                    help="language model; e.g. ja, en-us; default is ja")
parser.add_argument("--model-path", type=str,
                    help="local model dir path (preferred if you have it)")
parser.add_argument("--partial", action="store_true",
                    help="write partial results too (real-time subtitles)")
parser.add_argument("--keep-last-final", action="store_true",
                    help="when showing partial, keep last final line above it")
args = parser.parse_args(remaining)

if args.samplerate is None:
    device_info = sd.query_devices(args.device, "input")
    args.samplerate = int(device_info["default_samplerate"])

# 模型：优先用本地路径，其次用 lang
if args.model_path:
    model = Model(args.model_path)
else:
    lang = args.model if args.model else "ja"
    model = Model(lang=lang)

write_text("（マイク入力待ち…）")

last_partial = ""
last_final = ""

with sd.RawInputStream(
    samplerate=args.samplerate,
    blocksize=8000,
    device=args.device,
    dtype="int16",
    channels=1,
    callback=callback
):
    print("#" * 80)
    print("Press Ctrl+C to stop the recording")
    print("#" * 80)

    rec = KaldiRecognizer(model, args.samplerate)

    while True:
        data = q.get()
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text = (res.get("text") or "").strip()
            if text:
                last_final = text
                print("FINAL:", text)
                write_text(text)
        else:
            if args.partial:
                pres = json.loads(rec.PartialResult())
                p = (pres.get("partial") or "").strip()
                if p and p != last_partial:
                    last_partial = p
                    print("PART:", p, end="\r")
                    if args.keep_last_final and last_final:
                        write_text(last_final + "\n" + p)
                    else:
                        write_text(p)
