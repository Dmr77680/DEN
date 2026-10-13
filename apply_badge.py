#!/usr/bin/env python3
# Badge orange "MAJ x.y.z" sur la liste des jeux quand la version installee n'est pas celle
# acceptee par les serveurs Nextendo (meme table que Citron).
# Lance depuis la racine du depot, APRES apply_green.py :  python3 apply_badge.py
import os

p = "src/android/app/src/main/java/org/yuzu/yuzu_emu/adapters/GameAdapter.kt"
if os.path.exists(".nextendo_badge_applied"):
    raise SystemExit("deja applique")
s = open(p, encoding="utf-8").read()

old = '''        private fun displayTitle(model: Game): CharSequence {
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
'''.replace("\\u2022", "•")
new = '''        // [Nextendo] only this game version can reach the Nextendo servers (same table as Citron)
        private val nextendoVersions = mapOf(
            "0100152000022000" to "4.0.0",  // Mario Kart 8 Deluxe
            "01006a800016e000" to "13.0.5", // Super Smash Bros. Ultimate
            "0100f8f0000a2000" to "5.5.2",  // Splatoon 2 (EU)
            "01003bc0000a0000" to "5.5.2",  // Splatoon 2 (US)
            "01003c700009c800" to "5.5.2",  // Splatoon 2 (JP)
            "01006f8002326000" to "3.0.3",  // Animal Crossing: New Horizons
            "0100dca0064a6000" to "1.4.0",  // Luigi's Mansion 3
            "01009b500007c000" to "5.5.1",  // ARMS
            "0100bde00862a000" to "3.1.1",  // Mario Tennis Aces
            "0100c2500fc20000" to "11.3.0", // Splatoon 3
            "01009b90006dc000" to "3.0.3",  // Super Mario Maker 2
            "010015100b514000" to "1.2.1",  // Super Mario Bros. Wonder
            "0100277011f1a000" to "1.0.2",  // Super Mario Bros. 35
            "0100770008dd8000" to "1.4.0",  // Monster Hunter Generations Ultimate
            "010047700d540000" to "2.0.1",  // Clubhouse Games: 51 Worldwide Classics
            "0100c6f01c4f8000" to "1.3.0",  // METAL GEAR SOLID: Peace Walker
            "01006fe013472000" to "1.1.1"   // Mario Party Superstars
        )

        private fun displayTitle(model: Game): CharSequence {
            val base = model.title.replace("[\\\\t\\\\n\\\\r]+".toRegex(), " ")
            val id = (model.programId.toLongOrNull() ?: 0L).toString(16).padStart(16, '0')
            val count = onlineCounts[id] ?: 0
            val wanted = nextendoVersions[id]
            val needsUpdate = wanted != null && model.version.isNotEmpty() && model.version != wanted

            if (count <= 0 && !needsUpdate) {
                return base
            }
            val text = android.text.SpannableStringBuilder(base)
            if (needsUpdate) {
                val badge = "\\u26A0 MAJ $wanted"
                val start = text.length + 2
                text.append("  ").append(badge)
                text.setSpan(
                    android.text.style.ForegroundColorSpan(0xFFFF9800.toInt()),
                    start,
                    start + badge.length,
                    android.text.Spannable.SPAN_EXCLUSIVE_EXCLUSIVE
                )
            }
            if (count > 0) {
                val badge = "\\u2022 $count en ligne"
                val start = text.length + 2
                text.append("  ").append(badge)
                text.setSpan(
                    android.text.style.ForegroundColorSpan(0xFF4CAF50.toInt()),
                    start,
                    start + badge.length,
                    android.text.Spannable.SPAN_EXCLUSIVE_EXCLUSIVE
                )
            }
            return text
        }
'''
if s.count(old) != 1:
    raise SystemExit("ANCRE INTROUVABLE: applique d'abord apply_green.py (trouve %d)" % s.count(old))
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="\n").write(s)
open(".nextendo_badge_applied", "w").write("ok\n")
print("OK : badge MAJ ajoute")
