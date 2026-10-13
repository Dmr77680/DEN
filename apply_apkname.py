#!/usr/bin/env python3
# L'APK produit s'appelle DEN.apk (au lieu de app-mainline-...apk) et l'artefact GitHub "DEN".
# Lance depuis la racine du depot :  python3 apply_apkname.py
import os
if os.path.exists(".nextendo_apkname_applied"):
    raise SystemExit("deja applique")

def rep(s, a, b, what):
    if s.count(a) != 1:
        raise SystemExit("ANCRE INTROUVABLE (%s): trouve %d" % (what, s.count(a)))
    return s.replace(a, b)

p = "src/android/app/build.gradle.kts"
s = open(p, encoding="utf-8").read()
s = rep(s, "            into(artifactsDir)\n",
        '''            into(artifactsDir)
            rename {
                when {
                    it.endsWith(".apk") -> "DEN.apk"
                    it.endsWith(".aab") -> "DEN.aab"
                    else -> it
                }
            }
''', "build.gradle.kts")
open(p, "w", encoding="utf-8", newline="\n").write(s)

p = ".github/workflows/android.yml"
s = open(p, encoding="utf-8").read()
s = rep(s, "name: eden-nextendo-apk", "name: DEN", "android.yml")
open(p, "w", encoding="utf-8", newline="\n").write(s)

open(".nextendo_apkname_applied", "w").write("ok\n")
print("OK : l'APK s'appellera DEN.apk")
