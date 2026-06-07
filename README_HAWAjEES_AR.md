# Hawajees Remix Tool

أداة لمعالجة مقاطع الهواجيس التي تملك حق استخدامها.

## ماذا تفعل؟

- تحذف صوت الشاعر فقط من المقاطع التي تحددها.
- تحافظ على الأغنية إذا بدأت بعد سكوت الشاعر.
- تتيح إضافة تسجيلك أنت فوق النغمة.
- تخفض الموسيقى تلقائياً أثناء إلقائك، ثم ترفعها بعد السكوت.

## القاعدة الأهم

لا تضع وقت الأغنية داخل `--poet-ranges`.

إذا كان الشاعر من:

```text
0:07 إلى 0:43
1:10 إلى 1:55
```

وبعدها تبدأ أغنية، فاكتب فقط:

```text
--poet-ranges "0:07-0:43,1:10-1:55"
```

ولا تكتب:

```text
--poet-ranges "0:07-3:30"
```

لأن هذا قد يحذف الأغنية أيضاً.

## التثبيت على Windows

افتح PowerShell داخل مجلد المشروع ثم نفذ:

```powershell
py -m pip install -U demucs
winget install Gyan.FFmpeg
```

اختبر التثبيت:

```powershell
ffmpeg -version
demucs --help
```

## الاستخدام 1: حذف الشاعر فقط والحفاظ على الأغنية

```powershell
python tools/hawajees_remix.py `
  --input "original.mp3" `
  --poet-ranges "0:07-0:43,1:10-1:55" `
  --output "music_without_poet_song_preserved.mp3"
```

## الاستخدام 2: حذف الشاعر وإضافة صوتك أنت

```powershell
python tools/hawajees_remix.py `
  --input "original.mp3" `
  --poet-ranges "0:07-0:43,1:10-1:55" `
  --voice "my_voice.wav" `
  --voice-start 7 `
  --output "final_my_voice_then_song.mp3"
```

## الاستخدام 3: جودة أعلى

```powershell
python tools/hawajees_remix.py `
  --input "original.mp3" `
  --poet-ranges "0:07-0:43,1:10-1:55" `
  --voice "my_voice.wav" `
  --model "htdemucs_ft" `
  --output "final_best_quality.mp3"
```

## ملاحظات مهمة

- لا يوجد حذف صوت مضمون 100% من ملف ممزوج.
- إذا كان صوت الشاعر فوق الأغنية مباشرة، قد تتأثر الأغنية في ذلك الجزء فقط.
- إذا بدأت الأغنية بعد سكوت الشاعر، لا تدخل وقت الأغنية في `--poet-ranges`.
- الأفضل أن تسجل صوتك بصيغة WAV.
- اترك ثانية صمت قبل بداية تسجيلك.
