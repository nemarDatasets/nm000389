"""FINISHER-05x (2026-10-07) shared helpers: copy-with-verify, checksums, text install, privacy scan, validator."""
import hashlib, json, os, re, shutil, subprocess, sys, zipfile, time

ROOT = '/voyager/ceph/groups/sdp190/bpinto/ieeg-nemar-20261005'
PY = ROOT + '/env/bin/python'
VAL = ROOT + '/env/bin/bids-validator-deno'


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def sha256(p, bs=1 << 24):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(bs)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def manifest(id_):
    """Dryad manifest rows from the b2dryad ledger inventory: name -> (digest_type, digest, bytes)."""
    led = json.load(open(f'{ROOT}/ledger/{id_}/result.json'))
    return {r['path']: (r['digest_type'], r['digest'], r['bytes']) for r in led['inventory']}


def digest(p, kind):
    if kind == 'md5':
        h = hashlib.md5()
        with open(p, 'rb') as f:
            for b in iter(lambda: f.read(1 << 24), b''):
                h.update(b)
        return h.hexdigest()
    return sha256(p)


def copy_verified(src, dst, expect=None):
    """Byte copy; returns sha256 of dst; checks size and (if given) Dryad digest (kind, digest, bytes)."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    s = os.path.getsize(dst)
    if expect:
        kind, dg, nb = expect
        assert s == nb, (dst, s, nb)
        got = digest(dst, kind)
        assert got == dg, (dst, kind, got, dg)
    return sha256(dst)


def install_texts(textdir, tree):
    """Copy the hand-written text files (README.md, dataset_description.json, ...) into the tree (relative layout kept)."""
    out = []
    for r, ds, fs in os.walk(textdir):
        for f in fs:
            if f.startswith('._') or f == '.DS_Store':
                continue
            s = os.path.join(r, f)
            rel = os.path.relpath(s, textdir)
            d = os.path.join(tree, rel)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copyfile(s, d)
            out.append(rel)
            if f.endswith('.json'):
                json.load(open(d))  # must parse
    return sorted(out)


PAT = {
    'iso_date': re.compile(r'\b(19|20)\d\d-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b'),
    'dmy_date': re.compile(r'\b(0[1-9]|[12]\d|3[01])[./-](0[1-9]|1[0-2])[./-](19|20)\d\d\b'),
    'yymmdd_hhmm': re.compile(r'\b[12]\d(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])_[0-2]\d[0-5]\d\b'),
    'email': re.compile(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', re.I),
    'phi_words': re.compile(r'\b(MRN|medical record|patient name|date of birth|birthdate|DOB)\b', re.I),
    'path': re.compile(r'(/Users/|/home/|[A-Z]:\\\\|\\\\Users\\\\)'),
}
TEXT_EXT = ('.tsv', '.json', '.txt', '.md', '.csv', '.m', '.py', '.rtf', '.sh', '.bidsignore')


def scan_text(rel, txt, find, allow=()):
    for k, p in PAT.items():
        n = 0
        for m in p.finditer(txt):
            ctx = txt[max(0, m.start() - 50): m.end() + 50].replace('\n', ' ')
            if any(a in ctx for a in allow):
                continue
            find.append({'file': rel, 'kind': k, 'match': m.group(0), 'context': ctx})
            n += 1
            if n > 10:
                break


def mat_strings(p):
    """All char/string leaves of a MAT file (v5 via scipy, v7.3 via h5py char arrays)."""
    import numpy as np
    out = []
    try:
        import scipy.io as sio
        m = sio.loadmat(p)

        def walk(x, path):
            if isinstance(x, np.ndarray):
                if x.dtype.kind in 'US':
                    out.extend((path, str(v)) for v in x.flat)
                elif x.dtype == object:
                    for i, e in enumerate(x.flat):
                        walk(e, f'{path}[{i}]')
                elif x.dtype.names:
                    for n in x.dtype.names:
                        for i, e in enumerate(x[n].flat):
                            walk(e, f'{path}.{n}[{i}]')
        for k, v in m.items():
            if k == '__header__':
                out.append(('__header__', v.decode('latin-1') if isinstance(v, bytes) else str(v)))
            elif not k.startswith('__'):
                walk(v, k)
    except NotImplementedError:
        import h5py
        with h5py.File(p, 'r') as h:
            def vis(name, obj):
                if isinstance(obj, h5py.Dataset) and obj.attrs.get('MATLAB_class', b'') in (b'char',):
                    a = obj[()]
                    out.append((name, ''.join(chr(c) for c in a.ravel(order='F') if c)))
            h.visititems(vis)
    return out


def privacy_scan(tree, rep, allow=(), extra_names=()):
    """Scan text files, zip member names + small text members, MAT strings; returns dict."""
    find = []
    stats = {'text': 0, 'zip': 0, 'mat': 0, 'mat_strings': 0}
    for r, ds, fs in os.walk(tree):
        ds[:] = [d for d in ds if d not in ('.git', '.nemar', '.datalad')]
        for f in fs:
            p = os.path.join(r, f)
            rel = os.path.relpath(p, tree)
            low = f.lower()
            scan_text(rel + '::name', rel, find, allow)
            for nm in extra_names:
                if nm.lower() in rel.lower():
                    find.append({'file': rel, 'kind': 'name_token', 'match': nm})
            if low.endswith(TEXT_EXT) or f in ('README', 'CHANGES', '.bidsignore'):
                if os.path.getsize(p) < 50e6:
                    scan_text(rel, open(p, 'rb').read().decode('utf-8', 'replace'), find, allow)
                    stats['text'] += 1
            elif low.endswith('.zip'):
                z = zipfile.ZipFile(p)
                names = [i.filename for i in z.infolist()]
                scan_text(rel + '::members', '\n'.join(names), find, allow)
                for i in z.infolist():
                    if i.filename.lower().endswith(('.txt', '.md', '.json', '.rtf', '.m', '.py')) and i.file_size < 5e6:
                        scan_text(rel + '::' + i.filename, z.read(i).decode('utf-8', 'replace'), find, allow)
                stats['zip'] += 1
            elif low.endswith('.mat'):
                ss = mat_strings(p)
                stats['mat'] += 1
                stats['mat_strings'] += len(ss)
                scan_text(rel + '::matstrings', '\n'.join(f'{a}={b}' for a, b in ss), find, allow)
    res = {'findings': find, 'stats': stats, 'n_findings': len(find)}
    os.makedirs(rep, exist_ok=True)
    json.dump(res, open(os.path.join(rep, 'privacy.json'), 'w'), indent=1)
    return res


def validate(tree, rep):
    os.makedirs(rep, exist_ok=True)
    env = dict(os.environ, DENO_DIR=os.environ.get('DENO_DIR', '/work/deno'))
    r = subprocess.run([VAL, '--json', tree], capture_output=True, text=True, env=env)
    open(os.path.join(rep, 'validator.json'), 'w').write(r.stdout)
    open(os.path.join(rep, 'validator.stderr'), 'w').write(r.stderr)
    try:
        j = json.loads(r.stdout)
        issues = j.get('issues', {}).get('issues', [])
    except Exception:
        return {'rc': r.returncode, 'parse_error': True, 'tail': (r.stdout + r.stderr)[-3000:]}
    errs = [i for i in issues if i.get('severity') == 'error']
    warns = [i for i in issues if i.get('severity') == 'warning']
    summ = {'rc': r.returncode, 'errors': len(errs), 'warnings': len(warns),
            'error_codes': sorted({i.get('code') for i in errs}), 'warning_codes': sorted({i.get('code') for i in warns}),
            'error_examples': [(i.get('code'), i.get('location')) for i in errs[:15]]}
    json.dump(summ, open(os.path.join(rep, 'validator-summary.json'), 'w'), indent=1)
    return summ


def write_sha256sums(d, names_digests, extra_lines=()):
    with open(os.path.join(d, 'SHA256SUMS'), 'w') as f:
        for n, dg in names_digests:
            f.write(f'{dg}  {n}\n')
        for l in extra_lines:
            f.write(l + '\n')


def tree_listing(tree):
    rows = []
    for r, ds, fs in os.walk(tree):
        ds[:] = [d for d in ds if d not in ('.git', '.nemar')]
        for f in fs:
            p = os.path.join(r, f)
            rows.append((os.path.relpath(p, tree), os.path.getsize(p)))
    return sorted(rows)
