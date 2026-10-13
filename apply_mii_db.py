#!/usr/bin/env python3
# Import d'une base de Mii complete (MiiDatabase.dat, 6808 octets : Ryujinx, Switch, Eden, yuzu...).
# A lancer APRES apply_mii_import.py, depuis la racine du depot :  python3 apply_mii_db.py
import os
if os.path.exists(".nextendo_mii_db_applied"):
    raise SystemExit("deja applique")
if not os.path.exists(".nextendo_mii_import_applied"):
    raise SystemExit("applique d'abord apply_mii_import.py")

def rep(s, a, b, what):
    if s.count(a) != 1:
        raise SystemExit("ANCRE INTROUVABLE (%s): trouve %d" % (what, s.count(a)))
    return s.replace(a, b)

base = "src/android/app/src/main/"

p = base + "jni/native.cpp"
s = open(p, encoding="utf-8").read()
s = rep(s, '#include "core/hle/service/mii/mii_manager.h"\n',
        '#include "core/hle/service/mii/mii_database.h"\n#include "core/hle/service/mii/mii_manager.h"\n',
        "include")
a = "    Service::Mii::CharInfo char_info{};\n    if (data.size() == sizeof(Service::Mii::CharInfo)) {\n"
s = rep(s, a, '''    // Base complete (MiiDatabase.dat) : on importe tous les Mii qu'elle contient.
    if (data.size() == sizeof(Service::Mii::NintendoFigurineDatabase)) {
        Service::Mii::NintendoFigurineDatabase db{};
        std::memcpy(&db, data.data(), sizeof(db));
        if (db.CheckIntegrity().IsError()) {
            return 2;
        }
        int imported = 0;
        for (std::size_t i = 0; i < db.GetDatabaseLength(); ++i) {
            const auto store_data = db.Get(i);
            if (store_data.IsSpecial() ||
                store_data.IsValid() != Service::Mii::ValidationResult::NoErrors) {
                continue;
            }
            Service::Mii::CharInfo info{};
            info.SetFromStoreData(store_data);
            if (info.Verify() != Service::Mii::ValidationResult::NoErrors) {
                continue;
            }
            if (!manager.Append(metadata, info).IsError()) {
                ++imported;
            }
        }
        return imported > 0 ? 10 + imported : 3;
    }

''' + a, "db block")
open(p, "w", encoding="utf-8", newline="\n").write(s)

p = base + "java/org/yuzu/yuzu_emu/ui/GamesFragment.kt"
s = open(p, encoding="utf-8").read()
s = rep(s, "                val msg = when (code) {\n",
        '''                val msg = when (code) {
                    in 10..200 -> "${code - 10} Mii importé(s) depuis la base. Ils apparaîtront dans le sélecteur de Mii du jeu."
''', "kotlin msg")
open(p, "w", encoding="utf-8", newline="\n").write(s)

open(".nextendo_mii_db_applied", "w").write("ok\n")
print("OK : import de MiiDatabase.dat ajoute")
