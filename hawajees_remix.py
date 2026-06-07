#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hawajees Remix Tool
يعمل على الملفات التي تملك حق استخدامها فقط.

الفكرة:
- تحدد أماكن صوت الشاعر فقط عبر --poet-ranges.
- هذه المقاطع يتم فصل الصوت منها.
- أي جزء خارج هذه الأوقات يبقى كما هو، لذلك الأغنية بعد سكوت الشاعر لا تُحذف.
- يمكن إضافة تسجيلك أنت فوق النغمة مع خفض الموسيقى تلقائياً أثناء إلقائك.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

# يتأكد أن البرنامج موجود في النظام
def need(command):
    if shutil.which(command) is None:
        raise SystemExit(f"Missing required command: {command}")

# يشغل أمر خارجي مثل ffmpeg أو demucs
def run(command):
    print("\n>>>", " ".join(map(str, command)))
    subprocess.run(command, check=True)

# يحول الوقت من 0:07 أو 1:10 أو 01:02:03 إلى ثواني
def to_seconds(value):
    parts = [float(x) for x in value.strip().split(":")]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"Bad time format: {value}")

# يقرأ المقاطع بهذا الشكل: 0:07-0:43,1:10-1:55
def parse_ranges(text):
    result = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        start_text, end_text = item.split("-")
        start = to_seconds(start_text)
        end = to_seconds(end_text)
        if end <= start:
            raise ValueError(f"Bad range: {item}")
        result.append((start, end))
    return sorted(result)

# يجلب مدة الملف الصوتي
def audio_duration(file_path):
    need("ffprobe")
    output = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1",
        str(file_path)
    ])
    return float(output.decode().strip())

# يقص جزءاً من الملف
def cut_audio(source, start, end, output):
    need("ffmpeg")
    run([
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}",
        "-to", f"{end:.3f}",
        "-i", str(source),
        "-vn", "-ar", "44100", "-ac", "2",
        str(output)
    ])

# يستخدم Demucs لفصل الصوت عن الموسيقى في مقطع الشاعر فقط
def remove_voice_with_demucs(segment, output_dir, model):
    need("demucs")
    run([
        "demucs",
        "-n", model,
        "--two-stems", "vocals",
        "-o", str(output_dir),
        str(segment)
    ])
    files = list(output_dir.rglob("no_vocals.wav"))
    if not files:
        raise SystemExit("Demucs finished, but no_vocals.wav was not found.")
    return files[0]

# تنظيف بسيط بعد الفصل، بدون تخريب الموسيقى
def clean_music(input_file, output_file):
    need("ffmpeg")
    run([
        "ffmpeg", "-y",
        "-i", str(input_file),
        "-af", "highpass=f=35,lowpass=f=15500,afftdn=nf=-25,alimiter=limit=0.94",
        str(output_file)
    ])

# يبني ملف موسيقى نهائي: حذف الشاعر من الأوقات المحددة فقط
def build_music_bed(input_file, poet_ranges, work_dir, model):
    duration = audio_duration(input_file)
    segments_dir = work_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)
    timeline = []
    cursor = 0.0
    for start, end in poet_ranges:
        if start > cursor:
            timeline.append(("keep", cursor, start))
        timeline.append(("remove", start, min(end, duration)))
        cursor = min(end, duration)
    if cursor < duration:
        timeline.append(("keep", cursor, duration))
    output_segments = []
    for index, (mode, start, end) in enumerate(timeline, start=1):
        raw = segments_dir / f"{index:03d}_{mode}_raw.wav"
        cut_audio(input_file, start, end, raw)
        if mode == "keep":
            # هذا الجزء يبقى كما هو: أغنية، موسيقى، سكتات، أي شيء خارج صوت الشاعر
            final_segment = segments_dir / f"{index:03d}_KEEP_ORIGINAL.wav"
            run(["ffmpeg", "-y", "-i", str(raw), "-ar", "44100", "-ac", "2", str(final_segment)])
        else:
            # هذا الجزء فقط يتم حذف صوت الشاعر منه
            demucs_dir = work_dir / f"demucs_{index:03d}"
            no_vocals = remove_voice_with_demucs(raw, demucs_dir, model)
            final_segment = segments_dir / f"{index:03d}_POET_REMOVED.wav"
            clean_music(no_vocals, final_segment)
        output_segments.append(final_segment)
    concat_file = work_dir / "concat.txt"
    concat_text = ""
    for file_path in output_segments:
        concat_text += f"file '{file_path.resolve().as_posix()}'\n"
    concat_file.write_text(concat_text, encoding="utf-8")
    bed_file = work_dir / "music_bed_poet_removed_song_preserved.wav"
    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-af", "loudnorm=I=-17:LRA=10:TP=-1.7",
        str(bed_file)
    ])
    return bed_file

# يضيف صوتك ويخفض الموسيقى تلقائياً أثناء الإلقاء
def mix_with_voice(bed_file, voice_file, output_file, voice_start):
    need("ffmpeg")
    delay = int(voice_start * 1000)
    filter_complex = (
        "[0:a]volume=0.90,highpass=f=35,lowpass=f=15500[bed];"
        f"[1:a]adelay={delay}|{delay},volume=1.15,"
        "highpass=f=85,lowpass=f=12500,"
        "acompressor=threshold=-18dB:ratio=3.2:attack=8:release=160,"
        "aecho=0.75:0.22:80:0.16,"
        "alimiter=limit=0.92[voice];"
        "[bed][voice]sidechaincompress=threshold=0.018:ratio=7:attack=18:release=900[ducked];"
        "[ducked][voice]amix=inputs=2:duration=longest:normalize=0,"
        "loudnorm=I=-14:LRA=9:TP=-1.3,alimiter=limit=0.95[out]"
    )
    run([
        "ffmpeg", "-y",
        "-i", str(bed_file),
        "-i", str(voice_file),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-codec:a", "libmp3lame",
        "-b:a", "320k",
        str(output_file)
    ])

# يحفظ نسخة بدون صوت الشاعر فقط
def export_without_voice(bed_file, output_file):
    need("ffmpeg")
    run([
        "ffmpeg", "-y",
        "-i", str(bed_file),
        "-af", "loudnorm=I=-15:LRA=9:TP=-1.4,alimiter=limit=0.95",
        "-codec:a", "libmp3lame",
        "-b:a", "320k",
        str(output_file)
    ])

def main():
    parser = argparse.ArgumentParser(description="Selective Hawajees poet voice remover and remix builder.")
    parser.add_argument("--input", required=True, help="Original audio/video file.")
    parser.add_argument("--poet-ranges", required=True, help='Only poet voice ranges, example: "0:07-0:43,1:10-1:55".')
    parser.add_argument("--voice", default=None, help="Your recitation file, preferably WAV.")
    parser.add_argument("--voice-start", type=float, default=7.0, help="When your voice starts, in seconds.")
    parser.add_argument("--output", default="hawajees_final.mp3", help="Final output file.")
    parser.add_argument("--work-dir", default="hawajees_work", help="Temporary working folder.")
    parser.add_argument("--model", default="htdemucs", help="Demucs model: htdemucs or htdemucs_ft.")
    args = parser.parse_args()
    input_file = Path(args.input).resolve()
    output_file = Path(args.output).resolve()
    work_dir = Path(args.work_dir).resolve()
    if not input_file.exists():
        raise SystemExit(f"Input file not found: {input_file}")
    voice_file = None
    if args.voice:
        voice_file = Path(args.voice).resolve()
        if not voice_file.exists():
            raise SystemExit(f"Voice file not found: {voice_file}")
    poet_ranges = parse_ranges(args.poet_ranges)
    if not poet_ranges:
        raise SystemExit("You must provide --poet-ranges.")
    work_dir.mkdir(parents=True, exist_ok=True)
    bed_file = build_music_bed(input_file, poet_ranges, work_dir, args.model)
    if voice_file:
        mix_with_voice(bed_file, voice_file, output_file, args.voice_start)
    else:
        export_without_voice(bed_file, output_file)
    print("\nDONE:", output_file)
    print("Important: anything outside --poet-ranges was preserved.")

if __name__ == "__main__":
    main()
