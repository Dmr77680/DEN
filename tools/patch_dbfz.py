#!/usr/bin/env python3
# DEN: Dragon Ball FighterZ online (redirige dbf.channel.or.jp vers Nextendo + liste des jeux compatibles)
import re, sys
p = "src/core/hle/service/sockets/sfdnsres.cpp"
s = open(p, encoding="utf-8").read()
if "DEN_DBFZ" in s:
    print("deja applique"); sys.exit(0)

s = s.replace("static std::optional<std::string> GetNextendoRedirectIp(const std::string& host) {",
              "static std::optional<std::string> GetNextendoRedirectIp(const std::string& host,\n"
              "                                                        u64 program_id) {", 1)
block = '''    // DEN_DBFZ: Dragon Ball FighterZ signs in to Bandai Namco's own API before any NEX traffic.
    // Only redirected while that game runs.
    constexpr u64 DragonBallFighterZ = 0x0100A250097F0000ULL;
    if (program_id == DragonBallFighterZ && host == "dbf.channel.or.jp") {
        LOG_INFO(Service, "[Nextendo] Redirecting DBFZ API host '{}' -> '{}'", host, server_ip);
        return server_ip;
    }

'''
anchor = '    if (host.starts_with("nncs2-")'
assert s.count(anchor) == 1
s = s.replace(anchor, block + anchor, 1)

assert s.count("GetNextendoRedirectIp(host);") == 2
s = s.replace("GetNextendoRedirectIp(host);", "GetNextendoRedirectIp(host, system.GetApplicationProcessProgramID());")
for name in ("GetHostByNameRequestImpl", "GetAddrInfoRequestImpl"):
    s = s.replace(f"{name}(HLERequestContext& ctx) {{", f"{name}(Core::System& system, HLERequestContext& ctx) {{", 1)
    n = s.count(f"= {name}(ctx);")
    assert n >= 1, name
    s = s.replace(f"= {name}(ctx);", f"= {name}(system, ctx);")
open(p, "w", encoding="utf-8").write(s)

t = "src/common/nextendo_compatible_titles.h"
h = open(t, encoding="utf-8").read()
a = "        {0x01006fe013472000, \"1.1.1\"},  // Mario Party Superstars\n"
assert a in h
h = h.replace(a, a + "        {0x0100a250097f0000, \"01.50\"},       // DRAGON BALL FighterZ\n", 1)
open(t, "w", encoding="utf-8").write(h)
print("ok")
