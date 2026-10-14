import pathlib, sys

def sub(path, old, new):
    p = pathlib.Path(path)
    t = p.read_text(encoding='utf-8')
    if old not in t:
        print('deja corrige ou absent:', path, '->', old[:45])
        return
    p.write_text(t.replace(old, new), encoding='utf-8')
    print('OK', path)

sub('RELEASE_NOTES.md',
    '**Splatoon 3** : problèmes graphiques et de connexion, en cours de correction',
    '**Splatoon 3** : problèmes graphiques (textures), en cours de correction')
sub('RELEASE_NOTES.md',
    '**Splatoon 3**: graphical and connection issues, being worked on',
    '**Splatoon 3**: graphical issues (textures), being worked on')

# Le script release_041 a ete lance deux fois : on retire les doublons exacts du README
p = pathlib.Path('README.md')
lines = p.read_text(encoding='utf-8').split('\n')
seen, out, removed = set(), [], 0
for ln in lines:
    if ln.startswith('- **Pokémon') and ln in seen:
        removed += 1
        continue
    if ln.startswith('- **Pokémon'):
        seen.add(ln)
    out.append(ln)
p.write_text('\n'.join(out), encoding='utf-8')
print('README : doublons retires =', removed)
