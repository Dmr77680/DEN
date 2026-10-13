#!/usr/bin/env python3
"""DEN diag: dump complete NEX replies (600 bytes) and log token shape. Run at repo root."""
import sys
p='src/core/hle/service/ssl/ssl.cpp'
s=open(p,encoding='utf-8').read()
a='NextendoDump(std::span<const u8>(data.data(), tmp), 160)'
if a not in s: sys.exit('anchor ssl.cpp introuvable (deja applique ?)')
s=s.replace(a,'NextendoDump(std::span<const u8>(data.data(), tmp), 600)')
open(p,'w',encoding='utf-8').write(s)
p='src/core/hle/service/acc/acc.cpp'
s=open(p,encoding='utf-8').read()
a='            nnex_claim = fmt::format(R"("nnex":"{}",)", tok);\n'
if a not in s: sys.exit('anchor acc.cpp introuvable')
s=s.replace(a,a+'            LOG_INFO(Service_ACC, "[Nextendo] nnex claim: token_len={} jwt_like={} dots={}", tok.size(),\n                     tok.rfind("eyJ", 0) == 0, std::count(tok.begin(), tok.end(), \'.\'));\n')
if '#include <algorithm>' not in s:
    s=s.replace('#include','#include <algorithm>\n#include',1)
open(p,'w',encoding='utf-8').write(s)
print('OK')
