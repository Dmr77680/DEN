#!/usr/bin/env python3
"""DEN : README bilingue (FR/EN) + notes de release v0.1.0. Lancer a la racine du depot."""
import os
if not os.path.exists("src"):
    raise SystemExit("lance ce script a la racine du depot")

README = r'''# DEN — Eden + Nextendo

**🇫🇷 Français** · [🇬🇧 English below](#-english)

DEN est un fork de l'émulateur Switch **[Eden](https://git.eden-emu.dev/eden-emu/eden)** pour **Android**, adapté pour se connecter à **Nextendo**, un réseau de jeu en ligne alternatif pour la Switch.

> Projet personnel et non officiel. Il n'est affilié ni à l'équipe d'Eden, ni à Citron, ni à Nextendo, ni à Nintendo.

## ✅ Ce qui fonctionne

- **Jeu en ligne sur Nextendo** : Mario Kart 8 Deluxe (salons et courses, stable dans nos tests), Super Mario Maker 2. Mario Party Superstars a été testé brièvement.
- **Amis Nextendo** : ta liste d'amis est visible dans les jeux. Un écran « Amis Nextendo » (bouton dans l'en-tête de la liste des jeux) montre qui est en ligne ou hors ligne.
- **Compteur de joueurs en ligne** affiché en vert sur chaque jeu compatible.
- **Badge orange « MAJ x.y.z »** quand ta version du jeu n'est pas celle que Nextendo exige (17 jeux de la liste Nextendo).
- **Import de Mii** (menu de la liste des jeux) : fichiers `.charinfo` / `.mii` et `MiiDatabase.dat` de Ryujinx.
- **Connexion à ton compte via le navigateur** (menu « Se connecter à Nextendo ») : récupère ton identité, tes amis et ta présence.

## ⚠️ Ce qui ne fonctionne pas (encore)

- **Jouer en ligne après « Se connecter à Nextendo »** : le serveur de jeu refuse pour l'instant le jeton de ce nouveau mode de connexion (erreur **2306-0802**). Pour jouer en ligne, tu dois placer ton fichier `nextendo_account.txt` (obtenu avec un autre client Nextendo, par exemple Citron) dans le dossier `Android/data/dev.eden.eden_emulator.relWithDebInfo/files/config/`. Nous avons demandé à Nextendo de corriger ça.
- **Splatoon 3** : bloqué au démarrage dans les versions précédentes. Un correctif est inclus dans cette version mais **n'est pas encore confirmé** ; l'en ligne n'est pas testé.
- **Stabilité** : testé uniquement sur **Retroid Pocket 5**. Un appareil en surcadençage ou qui chauffe peut avoir des chutes de FPS et des déconnexions.
- Le nom du jeu auquel joue un ami peut s'afficher sous forme de code pour certains titres.

## Installation

1. Télécharge **`DEN.apk`** dans l'onglet [Releases](../../releases) et installe-le (autorise les sources inconnues).
2. Ajoute **tes propres** jeux, clés et firmware, obtenus légalement depuis ta console. Ce dépôt ne distribue ni jeux, ni clés, ni firmware.
3. Place ton `nextendo_account.txt` dans `files/config/` (voir ci-dessus) et lance un jeu compatible.

> 🔒 **Ne partage jamais ton `nextendo_account.txt`** : il contient un jeton qui donne accès à ton compte, comme un mot de passe.

## Compiler soi-même

Lance le workflow GitHub Actions **Build Android** (onglet *Actions*). L'APK sort dans l'artefact **DEN**.

## Crédits et licence

- **[Eden](https://git.eden-emu.dev/eden-emu/eden)** : l'émulateur de base (README d'origine : [README.eden.md](./README.eden.md)).
- **Citron** : inspiration pour certaines parties du support Nextendo.
- **yuzu** : le projet dont Eden est issu.

Licence **GPL-3.0 ou ultérieure** (voir [LICENSE.txt](./LICENSE.txt)). Les mentions de copyright des fichiers d'origine sont conservées.

---

# 🇬🇧 English

DEN is a fork of the **[Eden](https://git.eden-emu.dev/eden-emu/eden)** Switch emulator for **Android**, adapted to connect to **Nextendo**, an alternative online gaming network for the Switch.

> Personal, unofficial project. Not affiliated with the Eden team, Citron, Nextendo or Nintendo.

## ✅ What works

- **Online play on Nextendo**: Mario Kart 8 Deluxe (lobbies and races, stable in our tests), Super Mario Maker 2. Mario Party Superstars was briefly tested.
- **Nextendo friends**: your friend list is visible in games. A "Nextendo Friends" screen (button in the games list header) shows who is online or offline.
- **Online player counter** shown in green on each compatible game.
- **Orange "UPDATE x.y.z" badge** when your game version is not the one Nextendo requires (17 games on Nextendo's list).
- **Mii import** (games list menu): `.charinfo` / `.mii` files and Ryujinx `MiiDatabase.dat`.
- **Sign in through your browser** ("Sign in to Nextendo" menu): fetches your identity, friends and presence.

## ⚠️ What doesn't work (yet)

- **Playing online after "Sign in to Nextendo"**: the game server currently rejects the token from this new sign-in method (error **2306-0802**). To play online, put your `nextendo_account.txt` (obtained with another Nextendo client, e.g. Citron) in `Android/data/dev.eden.eden_emulator.relWithDebInfo/files/config/`. We have asked Nextendo to fix this.
- **Splatoon 3**: stuck at startup in earlier versions. A fix is included in this release but **not yet confirmed**; online play is untested.
- **Stability**: tested only on a **Retroid Pocket 5**. An overclocked or overheating device may see FPS drops and disconnections.
- The name of the game a friend is playing may show as a code for some titles.

## Install

1. Download **`DEN.apk`** from the [Releases](../../releases) tab and install it (allow unknown sources).
2. Add **your own** games, keys and firmware, legally dumped from your console. This repository does not distribute games, keys or firmware.
3. Put your `nextendo_account.txt` in `files/config/` (see above) and launch a compatible game.

> 🔒 **Never share your `nextendo_account.txt`**: it contains a token that gives access to your account, like a password.

## Build it yourself

Run the **Build Android** GitHub Actions workflow (*Actions* tab). The APK comes out in the **DEN** artifact.

## Credits and license

- **[Eden](https://git.eden-emu.dev/eden-emu/eden)**: the base emulator (original README: [README.eden.md](./README.eden.md)).
- **Citron**: inspiration for parts of the Nextendo support.
- **yuzu**: the project Eden descends from.

Licensed under **GPL-3.0 or later** (see [LICENSE.txt](./LICENSE.txt)). Original copyright notices are preserved.
'''

NOTES = r'''## 🇫🇷 DEN v0.1.0 (pré-version)

Première version publique de DEN : Eden pour Android + support de Nextendo. **Pré-version : testée uniquement sur Retroid Pocket 5.**

### ✅ Ce qui marche
- Jeu en ligne Nextendo : **Mario Kart 8 Deluxe** (salons, courses), **Super Mario Maker 2**
- Liste d'amis Nextendo + écran « Amis Nextendo » (en ligne / hors ligne)
- Compteur de joueurs en ligne sur chaque jeu
- Badge orange « MAJ x.y.z » si la version du jeu n'est pas la bonne
- Import de Mii (`.charinfo`, `.mii`, `MiiDatabase.dat` de Ryujinx)
- Connexion à ton compte via le navigateur (identité, amis, présence)

### ⚠️ Ce qui ne marche pas encore
- **Jouer en ligne après « Se connecter à Nextendo »** : erreur 2306-0802 (le serveur de jeu refuse ce nouveau jeton, demande faite à Nextendo). Solution actuelle : placer ton `nextendo_account.txt` dans `Android/data/dev.eden.eden_emulator.relWithDebInfo/files/config/`.
- **Splatoon 3** : correctif inclus mais non confirmé, en ligne non testé.
- Appareils autres que Retroid Pocket 5 non testés ; surcadençage = risque de déconnexions.

### Installation
1. Télécharge `DEN.apk` ci-dessous et installe-le.
2. Ajoute tes propres jeux, clés et firmware (non fournis).
3. Place ton `nextendo_account.txt` dans `files/config/`.

🔒 Ne partage jamais ton `nextendo_account.txt` (équivaut à un mot de passe).

---

## 🇬🇧 DEN v0.1.0 (pre-release)

First public release of DEN: Eden for Android + Nextendo support. **Pre-release: tested only on a Retroid Pocket 5.**

### ✅ What works
- Nextendo online play: **Mario Kart 8 Deluxe** (lobbies, races), **Super Mario Maker 2**
- Nextendo friend list + "Nextendo Friends" screen (online / offline)
- Online player counter on each game
- Orange "UPDATE x.y.z" badge when the game version is wrong
- Mii import (`.charinfo`, `.mii`, Ryujinx `MiiDatabase.dat`)
- Browser sign-in to your account (identity, friends, presence)

### ⚠️ What doesn't work yet
- **Playing online after "Sign in to Nextendo"**: error 2306-0802 (the game server rejects this new token; request sent to Nextendo). Current workaround: put your `nextendo_account.txt` in `Android/data/dev.eden.eden_emulator.relWithDebInfo/files/config/`.
- **Splatoon 3**: fix included but unconfirmed, online untested.
- Devices other than Retroid Pocket 5 untested; overclocking may cause disconnections.

### Install
1. Download `DEN.apk` below and install it.
2. Add your own games, keys and firmware (not provided).
3. Put your `nextendo_account.txt` in `files/config/`.

🔒 Never share your `nextendo_account.txt` (it's equivalent to a password).
'''

open("README.md", "w", encoding="utf-8", newline="\n").write(README)
open("RELEASE_NOTES.md", "w", encoding="utf-8", newline="\n").write(NOTES)
print("OK")
