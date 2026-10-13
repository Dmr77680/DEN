#!/usr/bin/env python3
# Corrige le build : ajoute le bouton Nextendo aussi dans la variante paysage de l'ecran des jeux.
# Lance depuis la racine du depot :  python3 fix_land.py
p = "src/android/app/src/main/res/layout-land/fragment_games.xml"
s = open(p, encoding="utf-8").read()
if "friends_button" in s:
    raise SystemExit("deja applique")
anchor = '''        <com.google.android.material.card.MaterialCardView
            android:id="@+id/settings_button"'''
if s.count(anchor) != 1:
    raise SystemExit("ANCRE INTROUVABLE: trouve %d" % s.count(anchor))
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
open(p, "w", encoding="utf-8", newline="\n").write(s.replace(anchor, card + anchor))
print("OK : bouton ajoute en mode paysage")
