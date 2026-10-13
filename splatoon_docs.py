import re, sys
FR = '- **Splatoon 3** : démarre et fonctionne (testé sur Retroid Pocket 5).'
EN = '- **Splatoon 3**: starts and runs (tested on a Retroid Pocket 5).'
FR_N = '- **Splatoon 3** : démarre et fonctionne (testé sur Retroid Pocket 5)'
EN_N = '- **Splatoon 3**: starts and runs (tested on a Retroid Pocket 5)'
def edit(path, anchors):
    s = open(path, encoding='utf-8').read()
    if 'démarre et fonctionne' in s:
        sys.exit('deja fait: ' + path)
    lines = s.split('\n')
    out, removed, added = [], 0, 0
    for ln in lines:
        if ln.startswith('- **Splatoon 3**') and re.search(r'bloqué|stuck at startup|correctif inclus|fix included', ln):
            removed += 1
            continue
        for prefix, new in anchors:
            if ln.startswith(prefix):
                out.append(new)
                added += 1
                break
        out.append(ln)
    if removed < 1 or added < 1:
        sys.exit('ancres introuvables dans %s (supprimes=%d, ajoutes=%d)' % (path, removed, added))
    open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
    print(path, 'OK', removed, added)
edit('README.md', [('- **Amis Nextendo**', FR), ('- **Nextendo friends**', EN)])
edit('RELEASE_NOTES.md', [('- Liste d\'amis Nextendo', FR_N), ('- Nextendo friend list', EN_N)])
