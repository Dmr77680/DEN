#!/usr/bin/env python3
# Cree PRIVACY.md et TERMS.md a la racine du depot.  Usage :  python3 add_legal.py
import os
for name in ("PRIVACY.md", "TERMS.md"):
    if os.path.exists(name):
        raise SystemExit(name + " existe deja")

privacy = """# DEN - Privacy Policy / Politique de confidentialité

*Last updated: 2026-10-03*

## English

DEN is an open-source fork of the Eden Switch emulator for Android with Nextendo Network support.

**What DEN stores on your device**
- After you sign in, a file (`nextendo_account.txt`) with your Nextendo account id, username, friend code and sign-in token. It stays on your device.

**What DEN sends to Nextendo Network** (only while you are signed in)
- Your sign-in token, to authenticate requests.
- Your online presence: whether you are online and the title id/name of the game you are playing, so your friends can see it.
- Requests to read your friends list and the number of players online per game.

**What DEN does not do**
- DEN never sees or stores your e-mail or password: sign-in happens in your browser (OAuth with PKCE).
- DEN adds no analytics, advertising or tracking of its own.
- DEN does not sell or share your data.

You can sign out from the app at any time, which deletes the local account file. To delete your Nextendo account data, use the Nextendo website.

Data held by Nextendo Network is governed by Nextendo Network's own policies.

## Français

DEN est un fork open source de l'émulateur Switch Eden pour Android, compatible avec Nextendo Network.

**Ce que DEN conserve sur ton appareil** : après connexion, un fichier (`nextendo_account.txt`) avec l'identifiant de ton compte Nextendo, ton pseudo, ton code ami et ton jeton de connexion. Il reste sur ton appareil.

**Ce que DEN envoie à Nextendo Network** (seulement quand tu es connecté) : ton jeton pour authentifier les requêtes ; ta présence (en ligne, identifiant et nom du jeu en cours) pour que tes amis la voient ; des requêtes pour lire ta liste d'amis et le nombre de joueurs en ligne par jeu.

**Ce que DEN ne fait pas** : il ne voit ni ne stocke ton e-mail ni ton mot de passe (connexion dans le navigateur, OAuth PKCE) ; il n'ajoute ni statistiques, ni publicité, ni suivi ; il ne vend ni ne partage tes données.

Tu peux te déconnecter depuis l'appli à tout moment, ce qui supprime le fichier local. Les données conservées par Nextendo Network relèvent de ses propres règles.
"""

terms = """# DEN - Terms of Use / Conditions d'utilisation

*Last updated: 2026-10-03*

## English

DEN is a free, open-source fork of the Eden emulator (GPL-3.0-or-later). It is provided **as is, without warranty**.

- DEN is an independent project. It is not affiliated with, or endorsed by, Nintendo or Nextendo Network.
- You are responsible for using only games, firmware and keys that you legally own.
- Use of the Nextendo Network is subject to Nextendo Network's own rules. Follow them.
- Do not share your sign-in token or `nextendo_account.txt`: it gives access to your account.
- The source code is available at https://github.com/Dmr77680/eden-nextendo and is licensed under the GPL. Credit to the Eden and Citron projects, on which DEN is based.

## Français

DEN est un fork libre et gratuit de l'émulateur Eden (GPL-3.0-or-later), fourni **tel quel, sans garantie**.

- DEN est un projet indépendant, non affilié à Nintendo ni à Nextendo Network.
- Tu es responsable de n'utiliser que des jeux, firmwares et clés que tu possèdes légalement.
- L'utilisation de Nextendo Network est soumise aux règles de Nextendo Network.
- Ne partage jamais ton jeton ni `nextendo_account.txt` : ils donnent accès à ton compte.
- Le code source est disponible sur https://github.com/Dmr77680/eden-nextendo sous licence GPL. Merci aux projets Eden et Citron, dont DEN est issu.
"""
open("PRIVACY.md", "w", encoding="utf-8", newline="\n").write(privacy)
open("TERMS.md", "w", encoding="utf-8", newline="\n").write(terms)
print("OK : PRIVACY.md et TERMS.md crees")
