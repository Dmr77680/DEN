// DEN_UPDATE: verification des mises a jour de DEN (canal public GitHub Releases)
package org.yuzu.yuzu_emu.updater

import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import org.yuzu.yuzu_emu.NativeLibrary
import java.util.concurrent.TimeUnit

object DenUpdateChecker {
    // Depot public qui ne contient que les versions (APK + notes), pas le code source.
    private const val LATEST_URL =
        "https://api.github.com/repos/Dmr77680/den-releases/releases/latest"

    /** Retourne la nouvelle version si elle est plus recente que celle installee, sinon null. */
    fun check(installedVersion: String?): NativeLibrary.UpdateResult? {
        return try {
            val local = parse(installedVersion) ?: return null
            val client = OkHttpClient.Builder().callTimeout(15, TimeUnit.SECONDS).build()
            val request = Request.Builder()
                .url(LATEST_URL)
                .header("Accept", "application/vnd.github+json")
                .build()
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return null
                val text = response.body?.string() ?: return null
                val json = JSONObject(text)
                val tag = json.optString("tag_name")
                val remote = parse(tag) ?: return null
                if (compare(remote, local) <= 0) return null

                var apkUrl = ""
                val assets = json.optJSONArray("assets")
                if (assets != null) {
                    for (i in 0 until assets.length()) {
                        val url = assets.getJSONObject(i).optString("browser_download_url")
                        if (url.endsWith(".apk")) {
                            apkUrl = url
                            break
                        }
                    }
                }
                NativeLibrary.UpdateResult(
                    tag = tag,
                    title = json.optString("name", tag).ifEmpty { tag },
                    body = json.optString("body"),
                    url = json.optString("html_url"),
                    assets = if (apkUrl.isEmpty()) mutableListOf() else mutableListOf(apkUrl)
                )
            }
        } catch (e: Exception) {
            null
        }
    }

    private fun parse(version: String?): List<Int>? {
        val match = Regex("(\\d+)\\.(\\d+)(?:\\.(\\d+))?").find(version ?: "") ?: return null
        return listOf(
            match.groupValues[1].toInt(),
            match.groupValues[2].toInt(),
            match.groupValues[3].ifEmpty { "0" }.toInt()
        )
    }

    private fun compare(a: List<Int>, b: List<Int>): Int {
        for (i in 0 until 3) {
            if (a[i] != b[i]) return a[i].compareTo(b[i])
        }
        return 0
    }

    /** Texte des nouveautes sans mise en forme Markdown, limite en taille. */
    fun cleanNotes(body: String): String {
        val cleaned = body
            .replace("**", "")
            .replace("`", "")
            .lines()
            .joinToString("\n") { it.trimStart('#', ' ') }
            .trim()
        return if (cleaned.length > 1500) cleaned.take(1500) + "..." else cleaned
    }
}
