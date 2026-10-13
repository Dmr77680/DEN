#!/usr/bin/env python3
# Corrige la connexion Nextendo : le jeton OAuth ne contient pas ton PID, DEN le demande a /oauth/userinfo.
# Lance depuis la racine du depot, APRES apply_signin.py :  python3 fix_signin2.py
import os
if os.path.exists(".nextendo_signin2_applied"):
    raise SystemExit("deja applique")
if not os.path.exists(".nextendo_signin_applied"):
    raise SystemExit("applique d'abord apply_signin.py")

p = "src/web_service/nextendo_api.cpp"
s = open(p, encoding="utf-8").read()

def rep(s, a, b, what):
    if s.count(a) != 1:
        raise SystemExit("ANCRE INTROUVABLE (%s): trouve %d" % (what, s.count(a)))
    return s.replace(a, b)

old = '''        if ((out.pid == 0 || out.username.empty()) && !out.token.empty()) {
            // Ask the profile endpoint for what the token response did not include.
            const auto profile = Send("GET", "/api/profile", {}, out.token);
            if (profile && profile->status == 200) {
                const auto pj = nlohmann::json::parse(profile->body, nullptr, false);
                if (pj.is_object()) {
                    if (out.pid == 0) {
                        out.pid = read_u64(pj, "pid");
                    }
                    if (out.username.empty()) {
                        out.username = read_str(pj, "username");
                    }
                    if (out.friend_code.empty()) {
                        out.friend_code = read_str(pj, "friend_code");
                    }
                }
            }
        }
'''
new = '''        LOG_INFO(WebService, "SignInWithBrowser: expires_in={} scope=\\"{}\\"",
                 read_u64(json, "expires_in"), read_str(json, "scope"));

        if ((out.pid == 0 || out.username.empty()) && !out.token.empty()) {
            // The OAuth token response carries no account fields: ask the identity endpoints.
            for (const char* path : {"/oauth/userinfo", "/api/me", "/api/profile"}) {
                const auto info = Send("GET", path, {}, out.token);
                if (!info) {
                    LOG_ERROR(WebService, "SignInWithBrowser: GET {} had no response", path);
                    continue;
                }
                const auto pj = nlohmann::json::parse(info->body, nullptr, false);
                std::string info_keys;
                if (pj.is_object()) {
                    for (const auto& item : pj.items()) {
                        info_keys += item.key() + " ";
                    }
                }
                LOG_INFO(WebService, "SignInWithBrowser: GET {} -> HTTP {}, fields: {}", path,
                         info->status, info_keys);
                if (info->status != 200 || !pj.is_object()) {
                    continue;
                }
                std::vector<const nlohmann::json*> sources{&pj};
                for (const char* key : {"account", "user", "profile"}) {
                    const auto it = pj.find(key);
                    if (it != pj.end() && it->is_object()) {
                        sources.push_back(&*it);
                    }
                }
                for (const auto* src : sources) {
                    for (const char* key : {"pid", "id", "sub", "principal_id"}) {
                        if (out.pid == 0) {
                            out.pid = read_u64(*src, key);
                        }
                    }
                    for (const char* key : {"username", "preferred_username", "name", "nickname"}) {
                        if (out.username.empty()) {
                            out.username = read_str(*src, key);
                        }
                    }
                    for (const char* key : {"friend_code", "friendCode", "code"}) {
                        if (out.friend_code.empty()) {
                            out.friend_code = read_str(*src, key);
                        }
                    }
                }
                if (out.pid != 0) {
                    break;
                }
            }
        }
'''
s = rep(s, old, new, "fallback block")

# Page de retour : DEN au lieu de citron
s = rep(s, '"citron.</p>"', '"DEN.</p>"', "page ok")
s = rep(s, '<p>Go back to citron and try "', '<p>Go back to DEN and try "', "page cancel")
open(p, "w", encoding="utf-8", newline="\n").write(s)

open(".nextendo_signin2_applied", "w").write("ok\n")
print("OK : connexion corrigee (userinfo)")
