#!/usr/bin/env python3
# Corrige l'acces HTTPS de l'API Nextendo sur Android (certificats CA).
# Lance depuis la racine du depot Eden :  python3 apply_cacert.py
import os

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)

def rep(s, a, b, what=""):
    c = s.count(a)
    if c != 1:
        raise SystemExit("ANCRE INTROUVABLE (%s): attendu 1, trouve %d" % (what, c))
    return s.replace(a, b)

if os.path.exists(".nextendo_cacert_applied"):
    raise SystemExit("deja applique")

# 1) JNI
p = "src/android/app/src/main/jni/native.cpp"
s = read(p)
if "nextendoOnlineCountsJson" not in s:
    raise SystemExit("applique d'abord apply_friends.py")
anchor = "jstring Java_org_yuzu_yuzu_1emu_NativeLibrary_nextendoOnlineCountsJson(JNIEnv* env, jclass clazz) {"
fn = """void Java_org_yuzu_yuzu_1emu_NativeLibrary_setNextendoCaCertPath(JNIEnv* env, jclass clazz,
                                                                 jstring jpath) {
#ifdef ENABLE_WEB_SERVICE
    WebService::NextendoApi::SetCaCertPathOverride(Common::Android::GetJString(env, jpath));
#endif
}

"""
s = rep(s, anchor, fn + anchor, "native.cpp")
write(p, s)

# 2) Kotlin : export du magasin de certificats Android vers un fichier PEM
p = "src/android/app/src/main/java/org/yuzu/yuzu_emu/NativeLibrary.kt"
s = read(p)
a = "    external fun nextendoOnlineCountsJson(): String\n"
b = a + '''
    // Android has no system CA file OpenSSL can read; the CA store is exported to a PEM.
    external fun setNextendoCaCertPath(path: String)

    @JvmStatic
    fun exportNextendoCaCerts(): String {
        return try {
            val keystore = java.security.KeyStore.getInstance("AndroidCAStore").apply {
                load(null)
            }
            val pem = StringBuilder()
            val aliases = keystore.aliases()
            while (aliases.hasMoreElements()) {
                val alias = aliases.nextElement()
                val cert = keystore.getCertificate(alias) ?: continue
                val encoded = android.util.Base64.encodeToString(
                    cert.encoded,
                    android.util.Base64.NO_WRAP
                )
                pem.append("-----BEGIN CERTIFICATE-----\\n")
                pem.append(encoded.chunked(64).joinToString("\\n"))
                pem.append("\\n-----END CERTIFICATE-----\\n")
            }
            val file = java.io.File(YuzuApplication.appContext.filesDir, "nextendo_cacert.pem")
            file.writeText(pem.toString())
            setNextendoCaCertPath(file.absolutePath)
            file.absolutePath
        } catch (e: Exception) {
            Log.error("[NativeLibrary] Nextendo CA export failed: ${e.message}")
            ""
        }
    }
'''
s = rep(s, a, b, "NativeLibrary.kt")
write(p, s)

# 3) appel au demarrage de l'application
p = "src/android/app/src/main/java/org/yuzu/yuzu_emu/YuzuApplication.kt"
s = read(p)
s = rep(s, "        createNotificationChannels()\n    }\n",
        "        createNotificationChannels()\n\n        // [Nextendo] CA bundle for the account/friends HTTPS API\n        Thread { NativeLibrary.exportNextendoCaCerts() }.start()\n    }\n", "YuzuApplication.kt")
write(p, s)

open(".nextendo_cacert_applied", "w").write("ok\n")
print("TERMINE")
