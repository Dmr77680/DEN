// SPDX-FileCopyrightText: 2026 DEN
// SPDX-License-Identifier: GPL-3.0-or-later

package org.yuzu.yuzu_emu.utils

import android.app.Activity
import android.app.Application
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.TextUtils
import android.util.Base64
import android.view.Gravity
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import org.json.JSONObject
import org.yuzu.yuzu_emu.NativeLibrary
import org.yuzu.yuzu_emu.R
import org.yuzu.yuzu_emu.YuzuApplication
import org.yuzu.yuzu_emu.features.settings.model.BooleanSetting
import org.yuzu.yuzu_emu.ui.NextendoFriendsDialog
import java.lang.ref.WeakReference

// DEN_FRIEND_NOTIF
// Interroge la liste d'amis Nextendo toutes les 30 s tant que DEN est au premier plan (menus ou
// jeu) et affiche une banniere (icone + pseudo) quand un ami passe de hors ligne a en ligne.
// Le premier releve sert de reference : aucune banniere au lancement pour les amis deja en ligne.
object NextendoFriendNotifier {
    private const val FIRST_POLL_MS = 6_000L
    private const val POLL_MS = 30_000L
    private const val SHOW_MS = 4_000L

    private class Banner(val title: String, val subtitle: String, val avatar: Bitmap?)

    private val ui = Handler(Looper.getMainLooper())
    private val queue = ArrayDeque<Banner>()
    private var current: WeakReference<Activity>? = null
    private var started = false
    private var showing = false
    private var generation = 0

    // Uniquement touches par le thread de sondage
    private var last: Map<Long, Int>? = null
    private var lastAccount = ""

    fun start(app: Application) {
        if (started) return
        started = true
        app.registerActivityLifecycleCallbacks(object : Application.ActivityLifecycleCallbacks {
            override fun onActivityResumed(activity: Activity) {
                current = WeakReference(activity)
                flush()
            }

            override fun onActivityPaused(activity: Activity) {
                if (current?.get() === activity) current = null
            }

            override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) {}
            override fun onActivityStarted(activity: Activity) {}
            override fun onActivityStopped(activity: Activity) {}
            override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) {}
            override fun onActivityDestroyed(activity: Activity) {}
        })
        val thread = Thread({
            var delay = FIRST_POLL_MS
            while (true) {
                try {
                    Thread.sleep(delay)
                } catch (_: InterruptedException) {
                    return@Thread
                }
                delay = POLL_MS
                try {
                    poll()
                } catch (_: Exception) {
                }
            }
        }, "DEN-FriendNotifier")
        thread.isDaemon = true
        thread.start()
    }

    private fun poll() {
        // DEN au arriere-plan : pas de trafic, et on repart d'un nouveau releve au retour
        if (current?.get() == null) {
            last = null
            return
        }
        val account = NativeLibrary.nextendoAccountName()
        if (account.isEmpty()) {
            last = null
            lastAccount = ""
            return
        }
        if (account != lastAccount) {
            lastAccount = account
            last = null
        }
        if (!BooleanSetting.NEXTENDO_FRIEND_NOTIFICATIONS.getBoolean()) {
            last = null
            return
        }
        val root = JSONObject(NativeLibrary.nextendoFriendsListJson())
        if (!root.optBoolean("ok")) return
        val arr = root.optJSONArray("friends") ?: return

        val previous = last
        val now = HashMap<Long, Int>()
        val banners = ArrayList<Banner>()
        for (i in 0 until arr.length()) {
            val e = arr.getJSONObject(i)
            val pid = e.optLong("pid")
            val status = e.optInt("status")
            now[pid] = status
            val before = previous?.get(pid)
            if (before != null && before <= 0 && status > 0) {
                val name = e.optString("name")
                val appId = e.optString("app_id")
                val appName = e.optString("app_name")
                val game = if (appId.isNotEmpty() || appName.isNotEmpty()) {
                    NextendoFriendsDialog.gameName(appId, appName)
                } else {
                    ""
                }
                val ctx = YuzuApplication.appContext
                val avatar = try {
                    val img = e.optString("image")
                    if (img.isEmpty()) {
                        null
                    } else {
                        val bytes = Base64.decode(img, Base64.DEFAULT)
                        BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                    }
                } catch (_: Exception) {
                    null
                }
                banners.add(
                    Banner(
                        ctx.getString(R.string.nextendo_friend_online, name),
                        if (game.isEmpty()) "" else ctx.getString(R.string.nextendo_playing, game),
                        avatar
                    )
                )
            }
        }
        last = now
        if (banners.isNotEmpty()) {
            ui.post {
                for (b in banners) queue.addLast(b)
                flush()
            }
        }
    }

    // Thread principal uniquement
    private fun flush() {
        if (showing) return
        val activity = current?.get() ?: return
        val host = activity.findViewById<ViewGroup>(android.R.id.content) ?: return
        val banner = queue.removeFirstOrNull() ?: return
        showing = true
        val gen = ++generation

        val density = activity.resources.displayMetrics.density
        fun dp(v: Int) = (v * density).toInt()

        val card = LinearLayout(activity).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(10), dp(8), dp(18), dp(8))
            background = GradientDrawable().apply {
                cornerRadius = dp(28).toFloat()
                setColor(0xE6202124.toInt())
                setStroke(dp(1), 0x66FFFFFF)
            }
            elevation = dp(8).toFloat()
            isClickable = false
            isFocusable = false
        }
        val img = ImageView(activity).apply {
            scaleType = ImageView.ScaleType.CENTER_CROP
            clipToOutline = true
            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                setColor(0x33808080)
            }
            if (banner.avatar != null) setImageBitmap(banner.avatar)
        }
        card.addView(img, LinearLayout.LayoutParams(dp(40), dp(40)))

        val texts = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(12), 0, 0, 0)
        }
        texts.addView(
            TextView(activity).apply {
                text = banner.title
                setTextColor(Color.WHITE)
                textSize = 14f
                setTypeface(typeface, Typeface.BOLD)
                maxLines = 1
                ellipsize = TextUtils.TruncateAt.END
                maxWidth = dp(260)
            }
        )
        if (banner.subtitle.isNotEmpty()) {
            texts.addView(
                TextView(activity).apply {
                    text = banner.subtitle
                    setTextColor(0xFFB0BEC5.toInt())
                    textSize = 12f
                    maxLines = 1
                    ellipsize = TextUtils.TruncateAt.END
                    maxWidth = dp(260)
                }
            )
        }
        card.addView(
            texts,
            LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
        )

        val params = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT,
            FrameLayout.LayoutParams.WRAP_CONTENT,
            Gravity.TOP or Gravity.CENTER_HORIZONTAL
        )
        params.topMargin = dp(16)
        card.alpha = 0f
        card.translationY = -dp(40).toFloat()
        host.addView(card, params)

        fun finish() {
            if (gen != generation) return
            (card.parent as? ViewGroup)?.removeView(card)
            showing = false
            flush()
        }

        card.animate().alpha(1f).translationY(0f).setDuration(250).withEndAction {
            ui.postDelayed({
                card.animate().alpha(0f).translationY(-dp(40).toFloat()).setDuration(250)
                    .withEndAction { finish() }
                    .start()
            }, SHOW_MS)
        }.start()
        // Securite : si l'animation est interrompue (ecran quitte), ne pas bloquer les suivantes
        ui.postDelayed({ if (showing) finish() }, SHOW_MS + 1_500L)
    }
}
