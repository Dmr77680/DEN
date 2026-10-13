#!/usr/bin/env python3
# Affiche la phrase "N en ligne" en vert dans la liste des jeux.
# Lance depuis la racine du depot Eden :  python3 apply_green.py
import os

p = "src/android/app/src/main/java/org/yuzu/yuzu_emu/adapters/GameAdapter.kt"
with open(p, encoding="utf-8") as f:
    s = f.read()

old = '''        private fun displayTitle(model: Game): String {
            val base = model.title.replace("[\\\\t\\\\n\\\\r]+".toRegex(), " ")
            val id = (model.programId.toLongOrNull() ?: 0L).toString(16).padStart(16, '0')
            val count = onlineCounts[id] ?: return base
            return if (count > 0) "$base  • $count en ligne" else base
        }
'''
new = '''        private fun displayTitle(model: Game): CharSequence {
            val base = model.title.replace("[\\\\t\\\\n\\\\r]+".toRegex(), " ")
            val id = (model.programId.toLongOrNull() ?: 0L).toString(16).padStart(16, '0')
            val count = onlineCounts[id] ?: return base
            if (count <= 0) {
                return base
            }
            val badge = "• $count en ligne"
            val text = android.text.SpannableString("$base  $badge")
            val start = base.length + 2
            text.setSpan(
                android.text.style.ForegroundColorSpan(0xFF4CAF50.toInt()),
                start,
                start + badge.length,
                android.text.Spannable.SPAN_EXCLUSIVE_EXCLUSIVE
            )
            return text
        }
'''
if s.count(old) != 1:
    raise SystemExit("ANCRE INTROUVABLE: applique d'abord apply_friends.py (trouve %d)" % s.count(old))
s = s.replace(old, new)
with open(p, "w", encoding="utf-8", newline="\n") as f:
    f.write(s)
print("TERMINE")
