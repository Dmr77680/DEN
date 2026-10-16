// SPDX-FileCopyrightText: 2026 DEN
// SPDX-License-Identifier: GPL-3.0-or-later

package org.yuzu.yuzu_emu.ui

import android.app.Activity
import android.graphics.drawable.GradientDrawable
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import org.json.JSONObject
import org.yuzu.yuzu_emu.NativeLibrary
import org.yuzu.yuzu_emu.R
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.ConcurrentHashMap

// DEN_CHAT : messages prives entre amis Nextendo (serveur de DEN)
object DenChat {
    private const val BASE = "https://2-29-6-216.sslip.io"
    private const val CONVO_REFRESH_MS = 3000L
    private const val UNREAD_REFRESH_MS = 20000L

    private val main = Handler(Looper.getMainLooper())
    private val names = ConcurrentHashMap<Long, String>()

    @Volatile private var openPid = 0L

    class Reply(val code: Int, val json: JSONObject?)

    private fun request(method: String, path: String, body: JSONObject? = null): Reply {
        return try {
            val token = NativeLibrary.nextendoToken()
            if (token.isEmpty()) {
                Reply(401, null)
            } else {
                val conn = URL(BASE + path).openConnection() as HttpURLConnection
                try {
                    conn.requestMethod = method
                    conn.connectTimeout = 8000
                    conn.readTimeout = 8000
                    conn.setRequestProperty("Authorization", "Bearer $token")
                    conn.setRequestProperty("Accept", "application/json")
                    if (body != null) {
                        conn.doOutput = true
                        conn.setRequestProperty("Content-Type", "application/json")
                        conn.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
                    }
                    val code = conn.responseCode
                    val stream = if (code in 200..299) conn.inputStream else conn.errorStream
                    val text = stream?.bufferedReader()?.use { it.readText() } ?: ""
                    val json = try { JSONObject(text) } catch (_: Exception) { null }
                    Reply(code, json)
                } finally {
                    conn.disconnect()
                }
            }
        } catch (_: Throwable) {
            Reply(0, null)
        }
    }

    fun rememberNames(list: List<Pair<Long, String>>) {
        for ((pid, name) in list) {
            if (name.isNotEmpty()) names[pid] = name
        }
    }

    // Nombre de messages non lus par ami (appel bloquant : a lancer hors du fil principal)
    fun unreadCounts(): Map<Long, Int> {
        val out = HashMap<Long, Int>()
        val r = request("GET", "/v1/unread")
        val arr = r.json?.optJSONArray("unread") ?: return out
        for (i in 0 until arr.length()) {
            val e = arr.optJSONObject(i) ?: continue
            out[e.optLong("pid")] = e.optInt("count")
        }
        return out
    }

    private fun refreshNamesFromFriends() {
        try {
            val root = JSONObject(NativeLibrary.nextendoFriendsListJson())
            val arr = root.optJSONArray("friends") ?: return
            for (i in 0 until arr.length()) {
                val e = arr.getJSONObject(i)
                val n = e.optString("name")
                if (n.isNotEmpty()) names[e.optLong("pid")] = n
            }
        } catch (_: Throwable) {
        }
    }

    // ---------- Conversation ----------
    fun open(activity: Activity, pid: Long, friendName: String) {
        names[pid] = friendName
        val density = activity.resources.displayMetrics.density
        fun dp(v: Int) = (v * density).toInt()

        val status = TextView(activity).apply {
            textSize = 13f
            setPadding(0, 0, 0, dp(4))
        }
        val list = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(2), dp(4), dp(2), dp(4))
        }
        val scroll = ScrollView(activity).apply { addView(list) }
        val input = EditText(activity).apply {
            hint = activity.getString(R.string.den_chat_hint)
            filters = arrayOf(android.text.InputFilter.LengthFilter(500))
            // DEN_CHAT_KB : la touche Entree du clavier envoie le message, le clavier ne passe
            // pas en plein ecran, et on le force meme avec une manette / un clavier physique.
            inputType = android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            imeOptions = android.view.inputmethod.EditorInfo.IME_ACTION_SEND or
                android.view.inputmethod.EditorInfo.IME_FLAG_NO_EXTRACT_UI
            maxLines = 4
            setOnClickListener {
                val imm = activity.getSystemService(android.content.Context.INPUT_METHOD_SERVICE)
                    as android.view.inputmethod.InputMethodManager
                imm.showSoftInput(this, 2) // 2 = SHOW_FORCED
            }
        }
        val sendBtn = Button(activity).apply { text = activity.getString(R.string.den_chat_send) }
        val bar = LinearLayout(activity).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            addView(input, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            addView(sendBtn)
        }
        val box = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(8), dp(20), 0)
            addView(status)
            val landscape = activity.resources.configuration.orientation ==
                android.content.res.Configuration.ORIENTATION_LANDSCAPE
            minimumHeight = dp(if (landscape) 150 else 300) // DEN_CHAT_KB2
            addView(scroll, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
            addView(bar, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        }

        var lastId = 0L
        var lastFriendMsgId = 0L
        var blocked = false
        var alive = true
        var busy = false

        fun addBubble(text: String, fromMe: Boolean) {
            val tv = TextView(activity).apply {
                this.text = text
                textSize = 15f
                setPadding(dp(12), dp(8), dp(12), dp(8))
                background = GradientDrawable().apply {
                    cornerRadius = dp(14).toFloat()
                    setColor(if (fromMe) 0x554CAF50 else 0x33808080)
                }
                setTextIsSelectable(true)
            }
            val lp = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = if (fromMe) Gravity.END else Gravity.START
                topMargin = dp(4)
                if (fromMe) marginStart = dp(48) else marginEnd = dp(48)
            }
            list.addView(tv, lp)
        }

        fun poll() {
            if (!alive || busy) return
            busy = true
            Thread {
                val r = request("GET", "/v1/messages?with=$pid&after=$lastId")
                activity.runOnUiThread {
                    busy = false
                    if (!alive) return@runOnUiThread
                    val arr = r.json?.optJSONArray("messages")
                    if (r.code != 200 || arr == null) {
                        status.text = activity.getString(R.string.den_chat_error)
                        return@runOnUiThread
                    }
                    status.text = ""
                    blocked = r.json?.optBoolean("blocked") ?: false
                    var added = false
                    for (i in 0 until arr.length()) {
                        val m = arr.getJSONObject(i)
                        val id = m.optLong("id")
                        if (id <= lastId) continue
                        val mine = m.optBoolean("from_me")
                        addBubble(m.optString("text"), mine)
                        lastId = id
                        if (!mine) lastFriendMsgId = id
                        added = true
                    }
                    if (list.childCount == 0) {
                        status.text = activity.getString(R.string.den_chat_empty)
                    }
                    if (added) {
                        scroll.post { scroll.fullScroll(View.FOCUS_DOWN) }
                        Thread {
                            request("POST", "/v1/read", JSONObject().put("with", pid).put("up_to", lastId))
                        }.start()
                    }
                }
            }.start()
        }

        sendBtn.setOnClickListener {
            val text = input.text.toString().trim()
            if (text.isEmpty()) return@setOnClickListener
            sendBtn.isEnabled = false
            Thread {
                val r = request("POST", "/v1/send", JSONObject().put("to", pid).put("text", text))
                activity.runOnUiThread {
                    sendBtn.isEnabled = true
                    if (r.code == 200) {
                        input.setText("")
                        poll()
                    } else {
                        val msg = r.json?.optString("error").orEmpty()
                        Toast.makeText(
                            activity,
                            if (msg.isNotEmpty()) msg else activity.getString(R.string.den_chat_error),
                            Toast.LENGTH_LONG
                        ).show()
                    }
                }
            }.start()
        }

        input.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == android.view.inputmethod.EditorInfo.IME_ACTION_SEND) {
                sendBtn.performClick()
                true
            } else {
                false
            }
        }

        val dialog = MaterialAlertDialogBuilder(activity)
            .setTitle(friendName)
            .setView(box)
            .setNegativeButton(activity.getString(R.string.nextendo_close), null)
            .setNeutralButton(activity.getString(R.string.den_chat_options), null)
            .create()

        fun showOptions() {
            val items = arrayOf(
                activity.getString(if (blocked) R.string.den_chat_unblock else R.string.den_chat_block),
                activity.getString(R.string.den_chat_report)
            )
            MaterialAlertDialogBuilder(activity)
                .setTitle(friendName)
                .setItems(items) { _, which ->
                    if (which == 0) {
                        val newState = !blocked
                        Thread {
                            val r = request("POST", "/v1/block", JSONObject().put("pid", pid).put("blocked", newState))
                            activity.runOnUiThread {
                                if (r.code == 200) {
                                    blocked = newState
                                    Toast.makeText(
                                        activity,
                                        activity.getString(if (newState) R.string.den_chat_blocked_ok else R.string.den_chat_unblocked_ok),
                                        Toast.LENGTH_LONG
                                    ).show()
                                } else {
                                    Toast.makeText(activity, activity.getString(R.string.den_chat_error), Toast.LENGTH_LONG).show()
                                }
                            }
                        }.start()
                    } else {
                        if (lastFriendMsgId == 0L) {
                            Toast.makeText(activity, activity.getString(R.string.den_chat_no_msg_to_report), Toast.LENGTH_LONG).show()
                        } else {
                            val mid = lastFriendMsgId
                            Thread {
                                val r = request(
                                    "POST", "/v1/report",
                                    JSONObject().put("pid", pid).put("message_id", mid).put("reason", "reported from DEN")
                                )
                                activity.runOnUiThread {
                                    Toast.makeText(
                                        activity,
                                        activity.getString(if (r.code == 200) R.string.den_chat_reported else R.string.den_chat_error),
                                        Toast.LENGTH_LONG
                                    ).show()
                                }
                            }.start()
                        }
                    }
                }
                .setNegativeButton(activity.getString(R.string.nextendo_close), null)
                .show()
        }

        val ticker = object : Runnable {
            override fun run() {
                if (!alive) return
                poll()
                main.postDelayed(this, CONVO_REFRESH_MS)
            }
        }
        dialog.setOnShowListener {
            dialog.getButton(android.app.AlertDialog.BUTTON_NEUTRAL).setOnClickListener { showOptions() }
            openPid = pid
            ticker.run()
        }
        dialog.setOnDismissListener {
            alive = false
            main.removeCallbacks(ticker)
            if (openPid == pid) openPid = 0L
        }
        dialog.show()
        // Permet au clavier de s'afficher dans la fenetre de dialogue
        dialog.window?.clearFlags(
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_ALT_FOCUSABLE_IM
        )
        dialog.window?.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        // DEN_CHAT_KB2 : clavier ouvert -> la liste se reduit, la zone de saisie reste visible
        val decor = dialog.window?.decorView
        if (decor != null) {
            val land = activity.resources.configuration.orientation ==
                android.content.res.Configuration.ORIENTATION_LANDSCAPE
            decor.viewTreeObserver.addOnGlobalLayoutListener {
                val r = android.graphics.Rect()
                decor.getWindowVisibleDisplayFrame(r)
                val kb = r.bottom < activity.resources.displayMetrics.heightPixels * 0.85
                val want = if (kb) 0 else dp(if (land) 150 else 300)
                if (box.minimumHeight != want) {
                    box.minimumHeight = want
                    scroll.post { scroll.fullScroll(android.view.View.FOCUS_DOWN) }
                }
            }
        }
    }

    // ---------- Notification de nouveaux messages (tant que DEN est ouvert) ----------
    private var hostActivity: Activity? = null
    private var polling = false
    private var firstCheck = true
    private var lastNamesRefresh = 0L
    private val seen = HashMap<Long, Long>()

    private val tick = object : Runnable {
        override fun run() {
            val act = hostActivity
            if (!polling || act == null) return
            Thread { check(act) }.start()
            main.postDelayed(this, UNREAD_REFRESH_MS)
        }
    }

    fun startPolling(activity: Activity) {
        hostActivity = activity
        if (polling) return
        polling = true
        firstCheck = true
        main.postDelayed(tick, 4000)
    }

    fun stopPolling() {
        polling = false
        hostActivity = null
        main.removeCallbacks(tick)
    }

    private fun check(act: Activity) {
        try {
            if (NativeLibrary.nextendoAccountName().isEmpty()) return
            val r = request("GET", "/v1/unread")
            val arr = r.json?.optJSONArray("unread") ?: return
            val now = System.currentTimeMillis()
            var needNames = false
            for (i in 0 until arr.length()) {
                if (!names.containsKey(arr.getJSONObject(i).optLong("pid"))) needNames = true
            }
            if (needNames && now - lastNamesRefresh > 300000) {
                lastNamesRefresh = now
                refreshNamesFromFriends()
            }
            val fallback = act.getString(R.string.den_chat_friend_fallback)
            val fresh = ArrayList<String>()
            for (i in 0 until arr.length()) {
                val e = arr.getJSONObject(i)
                val pid = e.optLong("pid")
                val lastId = e.optLong("last_id")
                val before = seen[pid] ?: 0L
                seen[pid] = lastId
                if (lastId > before && pid != openPid) {
                    fresh.add(names[pid] ?: fallback)
                }
            }
            val wasFirst = firstCheck
            firstCheck = false
            if (fresh.isEmpty()) return
            val who = fresh.joinToString(", ")
            act.runOnUiThread {
                Toast.makeText(
                    act,
                    act.getString(if (wasFirst) R.string.den_chat_unread else R.string.den_chat_new, who),
                    Toast.LENGTH_LONG
                ).show()
            }
        } catch (_: Throwable) {
        }
    }
}
