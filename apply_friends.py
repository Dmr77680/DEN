#!/usr/bin/env python3
# Nextendo friends + presence + online counts for Eden Android.
# Lance depuis la racine du depot Eden :  python3 apply_friends.py
import base64, zlib, os, sys

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)

def rep(s, a, b, n=1, what=""):
    c = s.count(a)
    if c != n:
        raise SystemExit("ANCRE INTROUVABLE (%s): attendu %d, trouve %d\n--- %s" % (what, n, c, a[:200]))
    return s.replace(a, b)

if os.path.exists(".nextendo_friends_applied"):
    raise SystemExit("deja applique")

# ---- 0) verifications de depart ----
fc = read("src/core/hle/service/friend/friend.cpp")
if "NextendoFriends" in fc or "IServiceForApplication" not in fc:
    raise SystemExit("friend.cpp d'Eden n'a pas la forme attendue (stub + nd:app). Stop.")

# ---- 1) service Friend porte depuis Citron (+ thread de sync) ----
BLOBS = {
    "src/core/hle/service/friend/friend.cpp": (
        "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"
        "kCVzOwpEw4aUu6jIdgmhgDqdN0P1SpiK6RcChtJ5N/UA/ow8Pnv76l1RHGusPy/ZWPuI3d7ttkS3daXzo9VFs5iD3ktO4C6/Kfwy"
        "naRx8eHjixenJ816na2qsKyBksZ+igmZca1fooOUTf0grV8RqlCjtdGlvm6vFZ7yNUBU+mjXaF90xK4333IP53rtNY/beg3yfrr1"
        "WpX7S648zdSZp87K0m1Wbfyn3q2rYE+/Qlq3XSbupwaQ0pibGm2XxNLUgFAjPqb2HMrCRmoSRhrVsXKDX3v1N7YxwuNLt2hFEEK9"
        "RdBArzR7FQCwVqNaaDN6dNehzYxDfI0GRkf6VQaY8ZRfg1Os0rbEz71Gy4I3+yq9ae52azZbbc0zzuA1xYrpdrhe04I796rNVNqG"
        "FZutSm45RldzM6zeyuQ9vdJGT3yQ68r21BN6vX7qji/ve7xeq9rYyDr6rtWo9t7W/G1rEsZqLQo+vfVZa7WXbj20lPu3rKM/Zj1O"
        "vwzCivJpqffr5kZTTz0xOI7W0mrSa8D1eql1rDK7ea7Y1Oy7uY6eu04bgytJ7XPHqp0bnCdrbdOCg2StVtbKyKnj2bju6aE+Utdp"
        "utT1bxMwlPvgumRW5QRYa0XNPn7rDmddlayeB946ut157VNL3o+uRpPEeWyVuutxB8357Qs7W0ezy/qRfWn7mofonLfZysfb3Nxr"
        "i5Cim9iK0ifvAVa/57yHV42WOU+uOn1pTlsr7c1U51izWU0V0lqnvzLXqRpNlafUikpQ4qtUu53J0al243L/pXIQIiWWF8+kQ4gi"
        "7VeOi74jfbptT28R3uJF5yHbT92hhCKFub3yZZQb/5D18uXvgsz3Ry31Aoj+mghaLOUiy6Gkg8iNMXnCJ/UQSN7uoad79HJKtGbN"
        "58bCAWZV5XbmmxUMHeBPwcJc4eljJrK1qRx3SY5kQ5bYwqTUAzWYK7Y4Y5Eu2PFE9rTkiSYELxxZfhHPlqFzY+bNr5xP14HWpN//"
        "Ozl3fF9wADnA5LaF5LOkhlHye+FGhOmE2ZmuN6usbKHPqFja8UOkX2HWwuSjDXFpJHLDCm+Gkut/cQXflo4Q6NMgMtECKoCKKfct"
        "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"
        "zc74ZNHG51jey4Znmn39nSWTFSPb+X/TUtiZ"
    ),
    "src/core/hle/service/friend/friend.h": (
        "eNqdVO9r2zAQ/e6/4uigS0ecdIWN4ZR+6Y+tLCul2WAwRlDlS6zVkTxJTuKN7m/fk5ymWclKqb4Ymbt37z3dXb9Po8uTr+mZKvnY"
        "VI1V08J/5qXPaH2lg/3X76ipf9V0OqtL4Y2lS2t+sPRJ/2n5B29IKm+Nfj7CWzrN+ZH8oZKsHafniPJqothm9P5ymB709lNjUySx"
        "TZIXlRXTmSCjJeOmtCzrnGlHGsv9ouS+YzsH0t23V+wkiRYzdpWQDEaW6XciS+EcjRrneTZIbjcjRm1elp1ZxTpH8Cr6k8nrkmmi"
        "tCjxt6qvSyWzhHAg4dsFFCPefKePzJUjXzBdC3kztaYGjGu0xD/LIidRqjkPyHLJwik9JeWpM2vhPQubm4XeI+cNYJTvxRLO51nm"
        "CmE5H1feHs6Nyo9Ir4qOA/x4WiN3kMT4lvO5hmmTICujlvCdvjMLxQtjbw7XMUdQFVI3lYXDywp3cFxHdh6yab05olbEuBt9zrLW"
        "4F2ID99xdw255UijnScJzFcUXmNvsI7+c194j8ycrVU5r3SGE7ygY1jruX20lcbOh+HpFf+s2fljA4il3yXplxvIG5kXJjSdFF4Z"
        "/Zz8E8EzZNauigScewpO67c1HoPA+b3lj/vb1r9F4wIhUhgaU2GeJMp2tlkfSv3bpCM1RR87YtjZUGhIOt9iAVpW+NjLk+isQyie"
        "qRCOOhVoY1JFWTZ7AR1vp6ecd8mZ0NGW0wl7WbAjgQHA1QKArevRFWOEoC5fQCH6zYUgXyhHi4J1oART2DFmvN/WDfi58IKE9HWo"
        "SHWFO7vBai+9dNv5G43YiOiiYs4Dt7A9uiTi8omNZ2sZssirGVOa0jVPwqZ4MMSVKQNvTHAUG+wx+FmFjcZQCFWRJACcCdjaQBUG"
        "PBLwpgyZc8UL3EQZdkEDKqmTlrEZgQW35A2JqVC6RyMxiQUk9MJ+M4OPzWqH9Np3j4qbtundEC/zJbqSd8KD34a99N/FlvwFQIIc"
        "CQ=="
    ),
    "src/core/hle/service/friend/friend_interface.cpp": (
        "eNqNUl1PwjAUfe+vuJkJAbMxIDExQ30BURI0RHwwMYY03R2r2dql7YhI8LfbjQ2igLEvt/f2nHO/6vswmw5fvBFPcCCzleKL2Dzj"
        "hwlg50Kv072EVf6Zw22aJ9RIBVMl35EZ4v+P37sAxo2S4rTChDMUGr1xiMLwiKMK4G468XrtjieVZ0moCDnjgiV5iOAwqdCPE/Q1"
        "qqXl+pHiKMLKzLmw+IgybMcOIYKmqDPrwWyLDoJRiYM1IdtbHWlqY+86pgrDeWbU1YMM8wRvIC3t3LWNKcufrbTBtAG6tDbMpNAG"
        "mCWeQ5GvRcCeAMZ1JVvlVC6xWWm13D29pNhyCpI21HBWKY5ywQyXYiwiCVHl6Nc3uK7QxVl3XGjUjQwU2mltvapfF5wjUWfj7hW6"
        "BwqPslgEo0XC3zpH3n6o9Q7UhhRTi811Vhag9RHVPzC1+qZfmidccDs5dU9FmKDSzd1kWn2y2S/1q9pqy44rxIjmiekTsgH77U5+"
        "CvINbRALWA=="
    ),
}
for dst, b in BLOBS.items():
    write(dst, zlib.decompress(base64.b64decode(b)).decode("utf-8"))
    print("ecrit", dst)

# ---- 2) JNI : compteurs de joueurs en ligne ----
p = "src/android/app/src/main/jni/native.cpp"
s = read(p)
s = rep(s, '#include "network/announce_multiplayer_session.h"\n',
        '#include "network/announce_multiplayer_session.h"\n#ifdef ENABLE_WEB_SERVICE\n#include "web_service/nextendo_api.h"\n#endif\n', what="include native.cpp")
anchor = "jboolean Java_org_yuzu_yuzu_1emu_NativeLibrary_gameRequiresFirmware(JNIEnv* env, jclass clazz, jstring jprogramId) {"
new_fn = '''jstring Java_org_yuzu_yuzu_1emu_NativeLibrary_nextendoOnlineCountsJson(JNIEnv* env, jclass clazz) {
    std::string json = "{";
#ifdef ENABLE_WEB_SERVICE
    const auto counts = WebService::NextendoApi::GetOnlineCounts();
    bool first = true;
    for (const auto& [title_id, count] : counts) {
        if (!first) {
            json += ",";
        }
        json += "\\"" + title_id + "\\":" + std::to_string(count);
        first = false;
    }
#endif
    json += "}";
    return Common::Android::ToJString(env, json);
}

'''
s = rep(s, anchor, new_fn + anchor, what="JNI anchor")
write(p, s)

# ---- 3) Kotlin ----
p = "src/android/app/src/main/java/org/yuzu/yuzu_emu/NativeLibrary.kt"
s = read(p)
s = rep(s, "    external fun getDefaultAccountBackupJpeg(): ByteArray\n}",
        "    external fun getDefaultAccountBackupJpeg(): ByteArray\n\n    external fun nextendoOnlineCountsJson(): String\n}", what="NativeLibrary.kt")
write(p, s)

p = "src/android/app/src/main/java/org/yuzu/yuzu_emu/adapters/GameAdapter.kt"
s = read(p)
s = rep(s, "    private var viewType = 0\n",
        '''    private var viewType = 0

    // [Nextendo] lowercase 16-digit hex title id -> players currently online
    private var onlineCounts: Map<String, Int> = emptyMap()

    fun setOnlineCounts(counts: Map<String, Int>) {
        if (counts != onlineCounts) {
            onlineCounts = counts
            notifyDataSetChanged()
        }
    }
''', what="GameAdapter fields")
old_title = '.text = model.title.replace("[\\\\t\\\\n\\\\r]+".toRegex(), " ")'
s = rep(s, old_title, ".text = displayTitle(model)", n=4, what="GameAdapter titles")
s = rep(s, "        private fun bindListView(model: Game) {",
        '''        private fun displayTitle(model: Game): String {
            val base = model.title.replace("[\\\\t\\\\n\\\\r]+".toRegex(), " ")
            val id = (model.programId.toLongOrNull() ?: 0L).toString(16).padStart(16, '0')
            val count = onlineCounts[id] ?: return base
            return if (count > 0) "$base  \u2022 $count en ligne" else base
        }

        private fun bindListView(model: Game) {''', what="GameAdapter displayTitle")
write(p, s)

p = "src/android/app/src/main/java/org/yuzu/yuzu_emu/ui/GamesFragment.kt"
s = read(p)
s = rep(s, "import android.os.Bundle\n", "import android.os.Bundle\nimport android.os.Handler\nimport android.os.Looper\nimport org.json.JSONObject\n", what="GamesFragment imports")
s = rep(s, "    private val gamesViewModel: GamesViewModel by activityViewModels()\n",
        '''    // [Nextendo] players online per title, refreshed while the games list is visible
    private val onlineCountsHandler = Handler(Looper.getMainLooper())
    @Volatile private var onlineCountsPolling = false
    private val onlineCountsPoll = object : Runnable {
        override fun run() {
            Thread {
                try {
                    val json = NativeLibrary.nextendoOnlineCountsJson()
                    val obj = JSONObject(json)
                    val counts = HashMap<String, Int>()
                    val keys = obj.keys()
                    while (keys.hasNext()) {
                        val key = keys.next()
                        counts[key.lowercase()] = obj.getInt(key)
                    }
                    // An empty answer means the fetch failed; keep the last known counts.
                    if (counts.isNotEmpty()) {
                        onlineCountsHandler.post {
                            if (_binding != null && ::gameAdapter.isInitialized) {
                                gameAdapter.setOnlineCounts(counts)
                            }
                        }
                    }
                } catch (e: Exception) {
                    // ignore, retry on the next tick
                }
                if (onlineCountsPolling) {
                    onlineCountsHandler.postDelayed(this, 30_000L)
                }
            }.start()
        }
    }

    private val gamesViewModel: GamesViewModel by activityViewModels()
''', what="GamesFragment poll")
s = rep(s, "    override fun onPause() {\n        super.onPause()\n",
        "    override fun onPause() {\n        super.onPause()\n        onlineCountsPolling = false\n        onlineCountsHandler.removeCallbacks(onlineCountsPoll)\n", what="onPause")
s = rep(s, "    override fun onResume() {\n        super.onResume()\n",
        "    override fun onResume() {\n        super.onResume()\n        onlineCountsPolling = true\n        onlineCountsHandler.removeCallbacks(onlineCountsPoll)\n        onlineCountsHandler.post(onlineCountsPoll)\n", what="onResume")
write(p, s)

open(".nextendo_friends_applied", "w").write("ok\n")
print("\nTERMINE. Verifie avec : git status && git diff --stat")
