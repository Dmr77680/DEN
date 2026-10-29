// SPDX-FileCopyrightText: Copyright 2025 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later

package org.yuzu.yuzu_emu.utils

import android.app.ActivityManager
import android.content.Context
import android.os.Build
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

// DEN_EXIT_REASON: ecrit dans eden_log.txt la raison pour laquelle Android a ferme la session
// precedente (memoire basse, plantage natif, fermeture normale...).
object ExitReasonLogger {
    private fun reasonName(reason: Int): String = when (reason) {
        0 -> "UNKNOWN"
        1 -> "EXIT_SELF (fermeture normale)"
        2 -> "SIGNALED (tuee par un signal)"
        3 -> "LOW_MEMORY (tuee par manque de memoire)"
        4 -> "CRASH (Java)"
        5 -> "CRASH_NATIVE (plantage natif)"
        6 -> "ANR (ne repond plus)"
        7 -> "INITIALIZATION_FAILURE"
        8 -> "PERMISSION_CHANGE"
        9 -> "EXCESSIVE_RESOURCE_USAGE"
        10 -> "USER_REQUESTED"
        11 -> "USER_STOPPED"
        12 -> "DEPENDENCY_DIED"
        13 -> "OTHER"
        14 -> "FREEZER"
        15 -> "PACKAGE_STATE_CHANGE"
        16 -> "PACKAGE_UPDATED"
        else -> "reason=$reason"
    }

    fun log(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            return
        }
        try {
            val manager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
            val exits = manager.getHistoricalProcessExitReasons(context.packageName, 0, 3)
            if (exits.isEmpty()) {
                Log.info("[DEN] Fermeture precedente: aucune information")
                return
            }
            val format = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US)
            for (exit in exits) {
                Log.info(
                    "[DEN] Fermeture precedente: ${format.format(Date(exit.timestamp))} " +
                        "raison=${reasonName(exit.reason)} statut=${exit.status} " +
                        "importance=${exit.importance} memoire=${exit.rss / 1024} Mo " +
                        "description=${exit.description ?: "-"}"
                )
            }
        } catch (t: Throwable) {
            Log.warning("[DEN] Impossible de lire la raison de fermeture: ${t.message}")
        }
    }
}
