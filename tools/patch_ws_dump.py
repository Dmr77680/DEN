#!/usr/bin/env python3
# DEN: diagnostic NEX (trames websocket decodees en hexadecimal dans eden_log.txt)
import sys
p = "src/core/hle/service/ssl/ssl.cpp"
s = open(p, encoding="utf-8").read()
if "DEN_WSDUMP" in s:
    print("deja applique"); sys.exit(0)
if "DEN_SSLDUMP" not in s:
    print("ERREUR: appliquer d'abord patch_ssl_dump.py"); sys.exit(1)

helper = r'''
// DEN_WSDUMP: websocket frames (NEX over wss) shown as opcode / length / first bytes in hex.
// Client frames are masked; the mask is removed so the real payload is visible.
static bool DenLooksLikeHttp(const u8* p, size_t n) {
    if (n < 4) {
        return false;
    }
    const std::string_view v(reinterpret_cast<const char*>(p), 4);
    return v == "HTTP" || v == "POST" || v == "GET " || v == "PUT " || v == "HEAD";
}

static std::string DenWsDump(const u8* p, size_t n) {
    static constexpr char kHex[] = "0123456789abcdef";
    std::string out;
    size_t pos = 0;
    int frames = 0;
    while (pos + 2 <= n && frames < 8) {
        const u8 b0 = p[pos];
        const u8 b1 = p[pos + 1];
        const bool masked = (b1 & 0x80) != 0;
        u64 len = b1 & 0x7F;
        size_t off = pos + 2;
        if (len == 126) {
            if (off + 2 > n) {
                break;
            }
            len = (u64(p[off]) << 8) | p[off + 1];
            off += 2;
        } else if (len == 127) {
            break;
        }
        u8 mask[4]{};
        if (masked) {
            if (off + 4 > n) {
                break;
            }
            for (int i = 0; i < 4; ++i) {
                mask[i] = p[off + i];
            }
            off += 4;
        }
        const size_t avail = off <= n ? n - off : 0;
        const size_t have = len < avail ? static_cast<size_t>(len) : avail;
        out += "[op=" + std::to_string(b0 & 0x0F) + (masked ? " out" : " in") +
               " len=" + std::to_string(len) + "] ";
        const size_t show = have < 96 ? have : 96;
        for (size_t i = 0; i < show; ++i) {
            const u8 c = masked ? static_cast<u8>(p[off + i] ^ mask[i & 3]) : p[off + i];
            out += kHex[c >> 4];
            out += kHex[c & 0xF];
        }
        if (have > show) {
            out += "...";
        }
        out += " ";
        pos = off + have;
        ++frames;
    }
    if (out.empty()) {
        out = "(not a websocket frame)";
    }
    return out;
}
'''
anchor = "// DEN_SSLDUMP: readable one-line view"
assert s.count(anchor) == 1
s = s.replace(anchor, helper.lstrip("\n") + "\n" + anchor, 1)

if "#include <string_view>" not in s:
    s = s.replace("#include <string>\n", "#include <string>\n#include <string_view>\n", 1)

r_old = '''                if (tmp > 0) {
                    static std::atomic<u32> den_rd_dump{0};
'''
assert s.count(r_old) == 1
r_new = '''                if (tmp > 0 && !DenLooksLikeHttp(data.data(), tmp)) {
                    static std::atomic<u32> den_rd_ws{0};
                    if (++den_rd_ws <= 400) {
                        LOG_INFO(Service_SSL, "[Nextendo] WS in  conn={}: {}",
                                 static_cast<const void*>(this), DenWsDump(data.data(), tmp));
                    }
                }
''' + r_old
s = s.replace(r_old, r_new, 1)

w_old = '''                static std::atomic<u32> den_wr_dump{0};
'''
assert s.count(w_old) == 1
w_new = '''                if (!DenLooksLikeHttp(in_data.data(), in_data.size())) {
                    static std::atomic<u32> den_wr_ws{0};
                    if (++den_wr_ws <= 400) {
                        LOG_INFO(Service_SSL, "[Nextendo] WS out conn={}: {}",
                                 static_cast<const void*>(this),
                                 DenWsDump(in_data.data(), in_data.size()));
                    }
                }
''' + w_old
s = s.replace(w_old, w_new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
