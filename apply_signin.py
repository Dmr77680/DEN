#!/usr/bin/env python3
# Ajoute "Se connecter a Nextendo" (navigateur + OAuth PKCE) avec TON identifiant d'application.
# Usage, depuis la racine du depot :  python3 apply_signin.py TON_CLIENT_ID
# (APRES apply_mii_import.py)
import os, re, sys

if len(sys.argv) != 2 or not re.fullmatch(r"[A-Za-z0-9._-]{3,80}", sys.argv[1]):
    raise SystemExit("Usage : python3 apply_signin.py TON_CLIENT_ID   (l'identifiant donne par nextendo.network/developers)")
CLIENT_ID = sys.argv[1]
if os.path.exists(".nextendo_signin_applied"):
    raise SystemExit("deja applique")
if not os.path.exists(".nextendo_mii_import_applied"):
    raise SystemExit("applique d'abord apply_mii_import.py")

def read(p):
    return open(p, encoding="utf-8").read()

def write(p, s):
    open(p, "w", encoding="utf-8", newline="\n").write(s)

def rep(s, a, b, what):
    if s.count(a) != 1:
        raise SystemExit("ANCRE INTROUVABLE (%s): trouve %d" % (what, s.count(a)))
    return s.replace(a, b)

base = "src/android/app/src/main/"

# 1) Serveur Nextendo : nouveau flux OAuth (chemins /oauth/..., identifiant DEN, reponse tolerante)
p = "src/web_service/nextendo_api.cpp"
s = read(p)
s = rep(s, 'constexpr const char* ClientId = "nextendo-citron";',
        'constexpr const char* ClientId = "%s";' % CLIENT_ID, "ClientId")
s = rep(s, '"{}/api/oauth/authorize?response_type=code&client_id={}"',
        '"{}/oauth/authorize?response_type=code&client_id={}"', "authorize path")
s = rep(s, '"&redirect_uri={}&scope=identity+friends+sauvegardes+history+presence"',
        '"&redirect_uri={}&scope=identity+friends+presence+profil+game.matchmaking"', "scope")
# L'application n'a qu'une redirection enregistree (port 47823) : on l'essaie en premier.
s = rep(s, 'const int port = server.bind_to_any_port("127.0.0.1");',
        'const int port = server.bind_to_port("127.0.0.1", 47823)\n'
        '                         ? 47823\n'
        '                         : server.bind_to_any_port("127.0.0.1");', "port")
s = rep(s, '"&app=citron&state={}"', '"&state={}"', "app param")
s = rep(s, 'client.Post("/api/oauth/token", form)', 'client.Post("/oauth/token", form)', "token path")
old_parse = '''        const auto json = nlohmann::json::parse(result->body);
        const auto& account = json.at("account");

        out.pid = account.at("pid").get<u64>();
        out.username = account.value("username", std::string{});
        out.friend_code = account.value("friend_code", std::string{});
        out.token = json.value("nex_token", std::string{});
'''
new_parse = '''        const auto json = nlohmann::json::parse(result->body);
        std::string keys;
        for (const auto& item : json.items()) {
            keys += item.key() + " ";
        }
        LOG_INFO(WebService, "SignInWithBrowser: token response fields: {}", keys);

        const auto read_u64 = [](const nlohmann::json& j, const char* key) -> u64 {
            const auto it = j.find(key);
            if (it == j.end()) {
                return 0;
            }
            if (it->is_number_integer()) {
                return it->get<u64>();
            }
            if (it->is_string()) {
                try {
                    return std::stoull(it->get<std::string>());
                } catch (...) {
                }
            }
            return 0;
        };
        const auto read_str = [](const nlohmann::json& j, const char* key) -> std::string {
            const auto it = j.find(key);
            return it != j.end() && it->is_string() ? it->get<std::string>() : std::string{};
        };

        // The response may carry the account fields at the top level or in a sub-object.
        const nlohmann::json* account = &json;
        for (const char* key : {"account", "user", "profile"}) {
            const auto it = json.find(key);
            if (it != json.end() && it->is_object()) {
                account = &*it;
                break;
            }
        }
        out.pid = read_u64(*account, "pid");
        if (out.pid == 0) {
            out.pid = read_u64(*account, "id");
        }
        out.username = read_str(*account, "username");
        out.friend_code = read_str(*account, "friend_code");
        out.token = read_str(json, "nex_token");
        if (out.token.empty()) {
            out.token = read_str(json, "access_token");
        }

        if ((out.pid == 0 || out.username.empty()) && !out.token.empty()) {
            // Ask the profile endpoint for what the token response did not include.
            const auto profile = Send("GET", "/api/profile", {}, out.token);
            if (profile && profile->status == 200) {
                const auto pj = nlohmann::json::parse(profile->body, nullptr, false);
                if (pj.is_object()) {
                    if (out.pid == 0) {
                        out.pid = read_u64(pj, "pid");
                    }
                    if (out.username.empty()) {
                        out.username = read_str(pj, "username");
                    }
                    if (out.friend_code.empty()) {
                        out.friend_code = read_str(pj, "friend_code");
                    }
                }
            }
        }
'''
s = rep(s, old_parse, new_parse, "token parse")
s = rep(s, 'out.error = "The account server returned an incomplete sign-in.";',
        'out.error = fmt::format("Incomplete sign-in (fields: {}pid={})", keys, out.pid);', "incomplete msg")
write(p, s)

# 2) JNI
p = base + "jni/native.cpp"
s = read(p)
s = rep(s, '#include "core/hle/service/filesystem/filesystem.h"\n',
        '#include "common/nextendo_account.h"\n#include "core/hle/service/filesystem/filesystem.h"\n', "include")
anchor = "jstring Java_org_yuzu_yuzu_1emu_NativeLibrary_nextendoOnlineCountsJson(JNIEnv* env, jclass clazz) {"
fn = r'''jstring Java_org_yuzu_yuzu_1emu_NativeLibrary_nextendoAccountName(JNIEnv* env, jclass clazz) {
    const std::string name =
        Common::NextendoAccount::IsLinked() ? Common::NextendoAccount::GetUsername() : "";
    return Common::Android::ToJString(env, name);
}

void Java_org_yuzu_yuzu_1emu_NativeLibrary_nextendoSignOut(JNIEnv* env, jclass clazz) {
    Common::NextendoAccount::Clear();
}

void Java_org_yuzu_yuzu_1emu_NativeLibrary_nextendoSignIn(JNIEnv* env, jclass clazz) {
#ifdef ENABLE_WEB_SERVICE
    std::thread([] {
        JNIEnv* thread_env = Common::Android::GetEnvForThread();
        const jclass cls = Common::Android::GetNativeLibraryClass();
        const jmethodID url_method =
            thread_env->GetStaticMethodID(cls, "onNextendoOAuthUrl", "(Ljava/lang/String;)V");
        const jmethodID result_method = thread_env->GetStaticMethodID(
            cls, "onNextendoSignInResult", "(ZLjava/lang/String;)V");
        const auto open_url = [&](const std::string& url) {
            const jstring jurl = Common::Android::ToJString(thread_env, url);
            thread_env->CallStaticVoidMethod(cls, url_method, jurl);
            thread_env->DeleteLocalRef(jurl);
        };
        const auto result = WebService::NextendoApi::SignInWithBrowser(open_url);
        if (result.ok) {
            Common::NextendoAccount::Save(result.pid, result.username, result.friend_code,
                                          result.token);
        }
        const std::string message = result.ok ? result.username : result.error;
        const jstring jmsg = Common::Android::ToJString(thread_env, message);
        thread_env->CallStaticVoidMethod(cls, result_method, static_cast<jboolean>(result.ok),
                                         jmsg);
        thread_env->DeleteLocalRef(jmsg);
    }).detach();
#endif
}

'''
s = rep(s, anchor, fn + anchor, "native.cpp")
write(p, s)

# 3) NativeLibrary.kt
p = base + "java/org/yuzu/yuzu_emu/NativeLibrary.kt"
s = read(p)
s = rep(s, "    external fun nextendoFriendsListJson(): String\n", '''    external fun nextendoFriendsListJson(): String

    external fun nextendoSignIn()

    external fun nextendoSignOut()

    // "" when no Nextendo account is linked
    external fun nextendoAccountName(): String

    @Keep
    @JvmStatic
    fun onNextendoOAuthUrl(url: String) {
        try {
            val intent = android.content.Intent(android.content.Intent.ACTION_VIEW, url.toUri())
                .addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
            YuzuApplication.appContext.startActivity(intent)
        } catch (_: Exception) {
        }
    }

    @Keep
    @JvmStatic
    fun onNextendoSignInResult(success: Boolean, message: String) {
        android.os.Handler(android.os.Looper.getMainLooper()).post {
            val ctx = YuzuApplication.appContext
            val text = if (success) "Connecté à Nextendo : $message" else "Connexion échouée : $message"
            android.widget.Toast.makeText(ctx, text, android.widget.Toast.LENGTH_LONG).show()
            try {
                org.yuzu.yuzu_emu.utils.NextendoSignInService.stop(ctx)
            } catch (_: Exception) {
            }
        }
    }
''', "NativeLibrary.kt")
write(p, s)

# 4) Service de premier plan (garde l'app active pendant que le navigateur est ouvert)
write(base + "java/org/yuzu/yuzu_emu/utils/NextendoSignInService.kt", '''// SPDX-FileCopyrightText: 2026 DEN
// SPDX-License-Identifier: GPL-3.0-or-later

package org.yuzu.yuzu_emu.utils

import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import org.yuzu.yuzu_emu.NativeLibrary
import org.yuzu.yuzu_emu.R

// Keeps the process alive while the browser sign-in is pending, so Android doesn't freeze the
// local callback server.
class NextendoSignInService : Service() {
    companion object {
        private const val NOTIFICATION_ID = 0x4601

        fun start(context: Context) {
            ContextCompat.startForegroundService(
                context,
                Intent(context, NextendoSignInService::class.java)
            )
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, NextendoSignInService::class.java))
        }
    }

    override fun onBind(intent: Intent): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification =
            NotificationCompat.Builder(this, getString(R.string.app_notification_channel_id))
                .setSmallIcon(R.drawable.ic_stat_notification_logo)
                .setContentTitle("Connexion à Nextendo")
                .setContentText("Termine la connexion dans ton navigateur")
                .setOngoing(true)
                .build()
        startForeground(NOTIFICATION_ID, notification)
        NativeLibrary.nextendoSignIn()
        return START_NOT_STICKY
    }
}
''')

# 5) Manifeste
p = base + "AndroidManifest.xml"
s = read(p)
s = rep(s, '    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />\n',
        '    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />\n'
        '    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />\n', "perm")
s = rep(s, '        <service android:name="org.yuzu.yuzu_emu.utils.ForegroundService"',
        '        <service\n            android:name="org.yuzu.yuzu_emu.utils.NextendoSignInService"\n'
        '            android:exported="false"\n            android:foregroundServiceType="dataSync" />\n\n'
        '        <service android:name="org.yuzu.yuzu_emu.utils.ForegroundService"', "service")
write(p, s)

# 6) Menu du bouton vert
p = base + "java/org/yuzu/yuzu_emu/ui/GamesFragment.kt"
s = read(p)
s = rep(s, '.setItems(arrayOf("Amis Nextendo", "Importer un Mii")) { _, which ->',
        '''.setItems(
                    arrayOf(
                        "Amis Nextendo",
                        "Importer un Mii",
                        org.yuzu.yuzu_emu.NativeLibrary.nextendoAccountName().let {
                            if (it.isEmpty()) "Se connecter à Nextendo" else "Se déconnecter ($it)"
                        }
                    )
                ) { _, which ->''', "menu items")
s = rep(s, '''                    } else {
                        miiPicker.launch(arrayOf("*/*"))
                    }
''', '''                    } else if (which == 1) {
                        miiPicker.launch(arrayOf("*/*"))
                    } else if (org.yuzu.yuzu_emu.NativeLibrary.nextendoAccountName().isEmpty()) {
                        org.yuzu.yuzu_emu.utils.NextendoSignInService.start(requireContext())
                    } else {
                        org.yuzu.yuzu_emu.NativeLibrary.nextendoSignOut()
                        Toast.makeText(requireContext(), "Déconnecté de Nextendo", Toast.LENGTH_SHORT).show()
                    }
''', "menu action")
write(p, s)

open(".nextendo_signin_applied", "w").write("ok\n")
print("OK : connexion Nextendo ajoutee (client_id = %s)" % CLIENT_ID)
