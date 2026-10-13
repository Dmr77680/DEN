#!/usr/bin/env python3
# Ajoute l'ecran "Amis Nextendo" (en ligne / hors ligne + jeu en cours) sur Android.
# Lance depuis la racine du depot :  python3 apply_friends_ui.py
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

if os.path.exists(".nextendo_friends_ui_applied"):
    raise SystemExit("deja applique")

base = "src/android/app/src/main/"

# 1) JNI
p = base + "jni/native.cpp"
s = read(p)
if "nextendoOnlineCountsJson" not in s:
    raise SystemExit("applique d'abord apply_friends.py")
anchor = "jstring Java_org_yuzu_yuzu_1emu_NativeLibrary_nextendoOnlineCountsJson(JNIEnv* env, jclass clazz) {"
fn = r'''jstring Java_org_yuzu_yuzu_1emu_NativeLibrary_nextendoFriendsListJson(JNIEnv* env, jclass clazz) {
    std::string json = "{\"ok\":false,\"error\":\"\",\"friends\":[]}";
#ifdef ENABLE_WEB_SERVICE
    const auto esc = [](const std::string& v) {
        std::string out;
        for (const char c : v) {
            switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    out += ' ';
                } else {
                    out += c;
                }
            }
        }
        return out;
    };
    const auto list = WebService::NextendoApi::GetFriends();
    json = std::string("{\"ok\":") + (list.ok ? "true" : "false") + ",\"error\":\"" +
           esc(list.error) + "\",\"friends\":[";
    for (std::size_t i = 0; i < list.friends.size(); ++i) {
        const auto& f = list.friends[i];
        json += i == 0 ? "" : ",";
        json += "{\"pid\":" + std::to_string(f.pid) + ",\"name\":\"" + esc(f.name) +
                "\",\"status\":" + std::to_string(f.presence_status) + ",\"app_id\":\"" +
                esc(f.app_id) + "\",\"app_name\":\"" + esc(f.app_name) + "\",\"image\":\"" +
                esc(f.image_base64) + "\"}";
    }
    json += "]}";
#endif
    return Common::Android::ToJString(env, json);
}

'''
s = rep(s, anchor, fn + anchor, "native.cpp")
write(p, s)

# 2) NativeLibrary.kt
p = base + "java/org/yuzu/yuzu_emu/NativeLibrary.kt"
s = read(p)
s = rep(s, "    external fun nextendoOnlineCountsJson(): String\n",
        "    external fun nextendoOnlineCountsJson(): String\n\n    external fun nextendoFriendsListJson(): String\n",
        "NativeLibrary.kt")
write(p, s)

# 3) Dialogue Kotlin (vues construites en code, pas de nouveau layout)
write(base + "java/org/yuzu/yuzu_emu/ui/NextendoFriendsDialog.kt", '''// SPDX-FileCopyrightText: 2026 DEN
// SPDX-License-Identifier: GPL-3.0-or-later

package org.yuzu.yuzu_emu.ui

import android.app.Activity
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.util.Base64
import android.view.Gravity
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import org.json.JSONObject
import org.yuzu.yuzu_emu.NativeLibrary

object NextendoFriendsDialog {
    private const val GREEN = 0xFF4CAF50.toInt()
    private const val GRAY = 0xFF9E9E9E.toInt()

    private class Friend(
        val name: String,
        val status: Int,
        val appId: String,
        val appName: String,
        val image: String
    )

    fun show(activity: Activity) {
        val density = activity.resources.displayMetrics.density
        fun dp(v: Int) = (v * density).toInt()

        val list = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(8), dp(20), dp(8))
        }
        val scroll = ScrollView(activity).apply { addView(list) }

        fun message(text: String) {
            list.removeAllViews()
            list.addView(TextView(activity).apply {
                this.text = text
                setPadding(0, dp(16), 0, dp(16))
            })
        }
        message("Chargement…")

        val dialog = MaterialAlertDialogBuilder(activity)
            .setTitle("Amis Nextendo")
            .setView(scroll)
            .setPositiveButton("Actualiser", null)
            .setNegativeButton("Fermer", null)
            .create()

        fun row(f: Friend): View {
            val row = LinearLayout(activity).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setPadding(0, dp(8), 0, dp(8))
            }
            val avatar = try {
                if (f.image.isEmpty()) null else {
                    val bytes = Base64.decode(f.image, Base64.DEFAULT)
                    BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                }
            } catch (_: Exception) {
                null
            }
            val img = ImageView(activity).apply {
                scaleType = ImageView.ScaleType.CENTER_CROP
                clipToOutline = true
                background = GradientDrawable().apply {
                    shape = GradientDrawable.OVAL
                    setColor(0x33808080)
                }
                if (avatar != null) setImageBitmap(avatar)
            }
            row.addView(img, LinearLayout.LayoutParams(dp(44), dp(44)))

            val dot = View(activity).apply {
                background = GradientDrawable().apply {
                    shape = GradientDrawable.OVAL
                    setColor(if (f.status > 0) GREEN else GRAY)
                }
            }
            val dotLp = LinearLayout.LayoutParams(dp(10), dp(10)).apply {
                marginStart = dp(12)
                marginEnd = dp(10)
            }
            row.addView(dot, dotLp)

            val col = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
            col.addView(TextView(activity).apply {
                text = f.name
                textSize = 16f
            })
            val playing = f.status > 0 && (f.appName.isNotEmpty() || f.appId.isNotEmpty())
            col.addView(TextView(activity).apply {
                text = when {
                    f.status <= 0 -> "Hors ligne"
                    playing -> "En jeu : " + f.appName.ifEmpty { f.appId }
                    else -> "En ligne"
                }
                textSize = 13f
                setTextColor(if (f.status > 0) GREEN else GRAY)
            })
            row.addView(col, LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f))
            return row
        }

        fun refresh() {
            message("Chargement…")
            Thread {
                var ok = false
                var error = ""
                val friends = mutableListOf<Friend>()
                try {
                    val root = JSONObject(NativeLibrary.nextendoFriendsListJson())
                    ok = root.optBoolean("ok")
                    error = root.optString("error")
                    val arr = root.getJSONArray("friends")
                    for (i in 0 until arr.length()) {
                        val e = arr.getJSONObject(i)
                        friends.add(
                            Friend(
                                e.optString("name"), e.optInt("status"),
                                e.optString("app_id"), e.optString("app_name"),
                                e.optString("image")
                            )
                        )
                    }
                } catch (_: Exception) {
                }
                friends.sortWith(compareByDescending<Friend> { it.status }.thenBy { it.name.lowercase() })
                activity.runOnUiThread {
                    if (!dialog.isShowing) return@runOnUiThread
                    when {
                        !ok -> message(
                            "Impossible de charger les amis" +
                                (if (error.isNotEmpty()) " ($error)" else "") +
                                ". Vérifie que ton compte Nextendo est lié."
                        )
                        friends.isEmpty() -> message("Aucun ami pour le moment.")
                        else -> {
                            list.removeAllViews()
                            val online = friends.count { it.status > 0 }
                            list.addView(TextView(activity).apply {
                                text = "$online en ligne sur ${friends.size}"
                                textSize = 13f
                                setTextColor(GREEN)
                                setPadding(0, 0, 0, dp(4))
                            })
                            friends.forEach { list.addView(row(it)) }
                        }
                    }
                }
            }.start()
        }

        dialog.setOnShowListener {
            dialog.getButton(android.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener { refresh() }
            refresh()
        }
        dialog.show()
    }
}
''')

# 4) Bouton dans l'en-tete de l'ecran des jeux
p = base + "res/layout/fragment_games.xml"
s = read(p)
anchor = '''        <com.google.android.material.card.MaterialCardView
            android:id="@+id/settings_button"'''
card = '''        <com.google.android.material.card.MaterialCardView
            android:id="@+id/friends_button"
            style="@style/EdenCard"
            android:layout_width="42dp"
            android:layout_height="42dp"
            android:background="@android:color/transparent"
            app:cardCornerRadius="21dp"
            app:cardBackgroundColor="@android:color/transparent"
            app:cardElevation="0dp"
            app:strokeColor="?attr/colorOutline"
            app:strokeWidth="1dp"
            android:padding="8dp"
            >

            <ImageView
                android:layout_width="18dp"
                android:layout_height="18dp"
                android:layout_gravity="center"
                android:src="@drawable/ic_account_circle"
                app:tint="#4CAF50"
                />

        </com.google.android.material.card.MaterialCardView>

        <Space
            android:layout_width="15dp"
            android:layout_height="wrap_content"
            />

'''
s = rep(s, anchor, card + anchor, "fragment_games.xml")
write(p, s)

p = base + "java/org/yuzu/yuzu_emu/ui/GamesFragment.kt"
s = read(p)
s = rep(s, "        binding.viewButton.setOnClickListener { showViewMenu(it) }\n",
        "        binding.viewButton.setOnClickListener { showViewMenu(it) }\n\n"
        "        // [Nextendo] friends screen\n"
        "        binding.friendsButton.setOnClickListener { NextendoFriendsDialog.show(requireActivity()) }\n",
        "GamesFragment.kt")
write(p, s)

open(".nextendo_friends_ui_applied", "w").write("ok\n")
print("OK : ecran Amis Nextendo ajoute")
