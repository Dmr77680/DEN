#!/usr/bin/env python3
# DEN: diagnostic reseau (requetes/reponses HTTP en clair dans eden_log.txt, sans jetons)
import sys
p = "src/core/hle/service/ssl/ssl.cpp"
s = open(p, encoding="utf-8").read()
if "DEN_SSLDUMP" in s:
    print("deja applique"); sys.exit(0)

helper = r'''namespace Service::SSL {

// DEN_SSLDUMP: readable one-line view of an HTTP message for the log. Headers are cut short and
// credentials (Authorization, Cookie, anything with "token") are hidden; only the start of the
// body is shown.
static std::string DenHttpDump(const u8* p, size_t n, size_t body_max) {
    std::string raw;
    raw.reserve(n);
    for (size_t i = 0; i < n; ++i) {
        const char c = static_cast<char>(p[i]);
        raw += (c == '\r' || c == '\n' || (c >= 32 && c < 127)) ? c : '.';
    }
    std::string out;
    const size_t split = raw.find("\r\n\r\n");
    const std::string head = split == std::string::npos ? raw : raw.substr(0, split);
    size_t pos = 0;
    while (pos <= head.size()) {
        size_t end = head.find("\r\n", pos);
        if (end == std::string::npos) {
            end = head.size();
        }
        std::string line = head.substr(pos, end - pos);
        std::string low = line;
        for (auto& ch : low) {
            ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
        }
        const size_t colon = line.find(':');
        if (colon != std::string::npos &&
            (low.starts_with("authorization") || low.starts_with("cookie") ||
             low.find("token") != std::string::npos)) {
            line = line.substr(0, colon) + ": <hidden>";
        } else if (line.size() > 90) {
            line = line.substr(0, 90) + "...";
        }
        out += line;
        out += " | ";
        pos = end + 2;
    }
    if (split != std::string::npos) {
        std::string body = raw.substr(split + 4);
        const size_t total = body.size();
        if (body.size() > body_max) {
            body.resize(body_max);
        }
        for (auto& ch : body) {
            if (ch == '\r' || ch == '\n') {
                ch = ' ';
            }
        }
        out += "BODY(" + std::to_string(total) + " bytes): " + body;
    }
    return out;
}
'''
assert s.count("namespace Service::SSL {") == 1
s = s.replace("namespace Service::SSL {", helper, 1)

# reponses
a = '''                LOG_INFO(Service_SSL, "[Nextendo] Read: got={} result={}:{} head={}", tmp,
                         static_cast<u32>(res.GetModule()), res.GetDescription(), head);
'''
assert s.count(a) == 1
b = a + '''                if (tmp > 0) {
                    static std::atomic<u32> den_rd_dump{0};
                    if (++den_rd_dump <= 60) {
                        LOG_INFO(Service_SSL, "[Nextendo] HTTP response: {}",
                                 DenHttpDump(data.data(), tmp, 400));
                    }
                }
'''
s = s.replace(a, b, 1)

# requetes
c = '''                LOG_INFO(Service_SSL, "[Nextendo] Write: size={} wrote={} rewrite={} result={}:{}",
                         in_data.size(), tmp, did_rewrite, static_cast<u32>(res.GetModule()),
                         res.GetDescription());
'''
assert s.count(c) == 1
d = c + '''                static std::atomic<u32> den_wr_dump{0};
                if (++den_wr_dump <= 60) {
                    LOG_INFO(Service_SSL, "[Nextendo] HTTP request: {}",
                             DenHttpDump(in_data.data(), in_data.size(), 120));
                }
'''
s = s.replace(c, d, 1)

if "#include <string>" not in s:
    s = s.replace("#include <atomic>\n", "#include <atomic>\n#include <cctype>\n#include <string>\n", 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
