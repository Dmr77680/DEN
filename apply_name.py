#!/usr/bin/env python3
# Le nom de l'application Android devient "DEN".
# Lance depuis la racine du depot :  python3 apply_name.py
import os

p = "src/android/app/build.gradle.kts"
with open(p, encoding="utf-8") as f:
    s = f.read()

edits = [
    ('            manifestPlaceholders += mapOf("appNameBase" to "Eden")\n            resValue("string", "app_name_suffixed", "Eden")\n',
     '            manifestPlaceholders += mapOf("appNameBase" to "DEN")\n            resValue("string", "app_name_suffixed", "DEN")\n'),
    ('resValue("string", "app_name", "Eden$suffix")',
     'resValue("string", "app_name", "DEN$suffix")'),
    ('val currentName = manifestPlaceholders["appNameBase"] as? String ?: "Eden"',
     'val currentName = manifestPlaceholders["appNameBase"] as? String ?: "DEN"'),
]
for a, b in edits:
    if s.count(a) != 1:
        raise SystemExit("ANCRE INTROUVABLE: " + a[:80])
for a, b in edits:
    s = s.replace(a, b)
with open(p, "w", encoding="utf-8", newline="\n") as f:
    f.write(s)
print("TERMINE")
