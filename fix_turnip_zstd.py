#!/usr/bin/env python3
# DEN_TURNIP_ZSTD : desactive zstd et xmlconfig (pas de bibliotheques Android pour elles dans le build croise)
import sys
p = ".github/workflows/turnip.yml"
s = open(p, encoding="utf-8").read()
if "DEN_TURNIP_ZSTD" in s:
    sys.exit("deja applique")
old = "            -Dstrip=true -Dwrap_mode=default\n"
new = ("            -Dzstd=disabled -Dxmlconfig=disabled -Dlibunwind=disabled -Dlmsensors=disabled \\\n"
       "            -Dstrip=true -Dwrap_mode=default # DEN_TURNIP_ZSTD\n")
if s.count(old) != 1:
    sys.exit("ANCRE INTROUVABLE: %d" % s.count(old))
open(p, "w", encoding="utf-8").write(s.replace(old, new))
print("OK DEN_TURNIP_ZSTD")
