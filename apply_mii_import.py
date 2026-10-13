#!/usr/bin/env python3
# Ajoute "Importer un Mii" (fichier .charinfo / .mii / .storedata / .coredata) dans la base Mii d'Eden.
# A lancer APRES apply_friends_ui.py, depuis la racine du depot :  python3 apply_mii_import.py
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

if os.path.exists(".nextendo_mii_import_applied"):
    raise SystemExit("deja applique")
if not os.path.exists(".nextendo_friends_ui_applied"):
    raise SystemExit("applique d'abord apply_friends_ui.py")

base = "src/android/app/src/main/"

# 1) JNI
p = base + "jni/native.cpp"
s = read(p)
s = rep(s, '#include "core/hle/service/filesystem/filesystem.h"\n',
        '#include "core/hle/service/filesystem/filesystem.h"\n'
        '#include "core/hle/service/mii/mii_manager.h"\n'
        '#include "core/hle/service/mii/types/char_info.h"\n'
        '#include "core/hle/service/mii/types/core_data.h"\n'
        '#include "core/hle/service/mii/types/store_data.h"\n'
        '#include "core/hle/service/mii/types/ver3_store_data.h"\n', "includes")
anchor = "jstring Java_org_yuzu_yuzu_1emu_NativeLibrary_nextendoOnlineCountsJson(JNIEnv* env, jclass clazz) {"
fn = r'''// 0 = ok, 1 = taille de fichier inconnue, 2 = Mii invalide, 3 = ajout refuse (base pleine ?)
jint Java_org_yuzu_yuzu_1emu_NativeLibrary_importMiiFile(JNIEnv* env, jclass clazz,
                                                         jbyteArray jdata) {
    const jsize size = env->GetArrayLength(jdata);
    std::vector<u8> data(static_cast<std::size_t>(size));
    env->GetByteArrayRegion(jdata, 0, size, reinterpret_cast<jbyte*>(data.data()));

    Service::Mii::MiiManager manager;
    Service::Mii::DatabaseSessionMetadata metadata{};
    metadata.interface_version = 1;
    metadata.magic = Service::Mii::MiiMagic;
    manager.Initialize(metadata);

    Service::Mii::CharInfo char_info{};
    if (data.size() == sizeof(Service::Mii::CharInfo)) {
        std::memcpy(&char_info, data.data(), sizeof(char_info));
    } else if (data.size() == sizeof(Service::Mii::StoreData)) {
        Service::Mii::StoreData store_data{};
        std::memcpy(&store_data, data.data(), sizeof(store_data));
        if (store_data.IsValid() != Service::Mii::ValidationResult::NoErrors) {
            return 2;
        }
        char_info.SetFromStoreData(store_data);
    } else if (data.size() == sizeof(Service::Mii::Ver3StoreData)) {
        Service::Mii::Ver3StoreData v3{};
        std::memcpy(&v3, data.data(), sizeof(v3));
        if (manager.ConvertV3ToCharInfo(char_info, v3).IsError()) {
            return 2;
        }
    } else if (data.size() == sizeof(Service::Mii::CoreData)) {
        Service::Mii::CoreData core{};
        std::memcpy(&core, data.data(), sizeof(core));
        if (manager.ConvertCoreDataToCharInfo(char_info, core).IsError()) {
            return 2;
        }
    } else {
        return 1;
    }

    if (char_info.Verify() != Service::Mii::ValidationResult::NoErrors) {
        return 2;
    }
    const auto result = manager.Append(metadata, char_info);
    return result.IsError() ? 3 : 0;
}

'''
s = rep(s, anchor, fn + anchor, "native.cpp")
write(p, s)

# 2) NativeLibrary.kt
p = base + "java/org/yuzu/yuzu_emu/NativeLibrary.kt"
s = read(p)
s = rep(s, "    external fun nextendoFriendsListJson(): String\n",
        "    external fun nextendoFriendsListJson(): String\n\n    external fun importMiiFile(data: ByteArray): Int\n",
        "NativeLibrary.kt")
write(p, s)

# 3) GamesFragment : selecteur de fichier + menu du bouton vert
p = base + "java/org/yuzu/yuzu_emu/ui/GamesFragment.kt"
s = read(p)
s = rep(s, "    private lateinit var mainActivity: MainActivity\n",
        '''    private lateinit var mainActivity: MainActivity

    // [Nextendo] Mii import: pick a .charinfo / .mii file and add it to the Mii database
    private val miiPicker =
        registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
            if (uri == null) {
                return@registerForActivityResult
            }
            val ctx = requireContext().applicationContext
            Thread {
                val code = try {
                    val bytes = ctx.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                    if (bytes == null) 1 else org.yuzu.yuzu_emu.NativeLibrary.importMiiFile(bytes)
                } catch (_: Exception) {
                    1
                }
                val msg = when (code) {
                    0 -> "Mii importé ! Il apparaîtra dans le sélecteur de Mii du jeu."
                    1 -> "Fichier Mii non reconnu (taille inattendue)."
                    2 -> "Ce Mii est invalide."
                    else -> "Import impossible (base de Mii pleine ?)."
                }
                android.os.Handler(android.os.Looper.getMainLooper()).post {
                    Toast.makeText(ctx, msg, Toast.LENGTH_LONG).show()
                }
            }.start()
        }
''', "GamesFragment picker")
s = rep(s, "        binding.friendsButton.setOnClickListener { NextendoFriendsDialog.show(requireActivity()) }\n",
        '''        binding.friendsButton.setOnClickListener {
            com.google.android.material.dialog.MaterialAlertDialogBuilder(requireContext())
                .setTitle("Nextendo")
                .setItems(arrayOf("Amis Nextendo", "Importer un Mii")) { _, which ->
                    if (which == 0) {
                        NextendoFriendsDialog.show(requireActivity())
                    } else {
                        miiPicker.launch(arrayOf("*/*"))
                    }
                }
                .show()
        }
''', "GamesFragment button")
write(p, s)

open(".nextendo_mii_import_applied", "w").write("ok\n")
print("OK : import de Mii ajoute")
