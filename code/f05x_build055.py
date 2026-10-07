#!/usr/bin/env python3
"""FINISHER-05x IEEG055 (Siebenhuehner et al. 2020 PLoS Biol; Dryad doi:10.5061/dryad.0k86k80) -> derivative BIDS tree.

- sourcedata/dryad-0k86k80/: all 17 original release files byte-for-byte (Dryad digest re-checked) + SHA256SUMS.
- sub-seegNNN/ieeg/ and sub-megNNNN/meg/: per-subject zip archives, one per connectome type, holding exactly that
  subject's CSV members of the original zip (member names, timestamps and bytes unchanged; re-deflated container);
  per-subject supporting CSVs (masks, distances, GMPI; parcel distances/fidelity, cross-parcel PLV) extracted verbatim.
- group/: group-level supporting CSVs and the plot data, extracted verbatim (spaces in names -> '_'; mapping in files.tsv).
- phenotype/neuropsychology.tsv: Neuropsychological_Data.csv re-expressed as TSV (values unchanged).
- Round-trip: every member of every original zip is matched exactly once (sha-256 of member bytes) in the derivative.
Usage: f05x_build055.py <textdir> [workers]
"""
import csv, hashlib, io, json, os, re, shutil, sys, zipfile
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from f05x_lib import *  # noqa

ID = 'IEEG055'; SLUG = 'dryad-0k86k80'
SRC = f'{ROOT}/work/{ID}/sourcedata/{SLUG}'
TREE = f'{ROOT}/work/{ID}/bids'
REP = f'{ROOT}/work/{ID}/reports/f05x'
TEXT = sys.argv[1]; W = int(sys.argv[2]) if len(sys.argv) > 2 else 16

CONN = {  # original zip -> (modality, desc label)
    'SEEG connectome CFS.zip': ('seeg', 'CFS'),
    'SEEG connectome PAC.zip': ('seeg', 'PAC'),
    'SEEG_connectome_AC_ENV.zip': ('seeg', 'ACenv'),
    'SEEG connectome PS_PLV.zip': ('seeg', 'PSplv'),
    'SEEG connectome PS_wPLI.zip': ('seeg', 'PSwpli'),
    'MEG connectome CFS.zip': ('meg', 'CFS'),
    'MEG connectome PAC.zip': ('meg', 'PAC'),
    'MEG connectome AC Env.zip': ('meg', 'ACenv'),
    'MEG connectome PS (PLV).zip': ('meg', 'PSplv'),
    'MEG connectome PS (wPLI).zip': ('meg', 'PSwpli'),
    'MEG_connectome_CFS_(EO-EC).zip': ('meg', 'CFSeoec'),
    'MEG_connectome_PS_(wPLI_EO-EC).zip': ('meg', 'PSwplieoec'),
}
RX = re.compile(r'(?:^|/)(S\d+)[ /]')


def label(code, mod):
    return ('seeg' + code[1:]) if mod == 'seeg' else ('meg' + code[1:])


def split_zip(zname):
    mod, desc = CONN[zname]
    z = zipfile.ZipFile(f'{SRC}/{zname}')
    groups = {}
    for i in z.infolist():
        if i.is_dir():
            continue
        m = RX.search(i.filename)
        assert m, (zname, i.filename)
        groups.setdefault(m.group(1), []).append(i)
    res = {'zip': zname, 'members': {}, 'outputs': {}}
    dt = 'ieeg' if mod == 'seeg' else 'meg'
    for code, infos in sorted(groups.items()):
        lab = label(code, mod)
        out = f'{TREE}/sub-{lab}/{dt}/sub-{lab}_desc-{desc}_connectomes.zip'
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zo:
            for i in infos:
                b = z.read(i)
                zi = zipfile.ZipInfo(i.filename, date_time=i.date_time)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = i.external_attr
                zo.writestr(zi, b)
                res['members'][i.filename] = hashlib.sha256(b).hexdigest()
        # round-trip: re-open output, compare every member
        zr = zipfile.ZipFile(out)
        got = {i.filename: hashlib.sha256(zr.read(i)).hexdigest() for i in zr.infolist()}
        exp = {i.filename: res['members'][i.filename] for i in infos}
        assert got == exp, (out, 'roundtrip mismatch')
        res['outputs'][os.path.relpath(out, TREE)] = {'n_members': len(infos), 'sha256': sha256(out), 'subject': code}
    assert len(res['members']) == sum(1 for i in z.infolist() if not i.is_dir())
    return res


def extract_member(z, i, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    b = z.read(i)
    open(dst, 'wb').write(b)
    assert hashlib.sha256(open(dst, 'rb').read()).hexdigest() == hashlib.sha256(b).hexdigest()
    return hashlib.sha256(b).hexdigest()


def safe(n):
    return re.sub(r'[^A-Za-z0-9._-]+', '_', n)


if __name__ == '__main__':
    assert not os.path.exists(TREE + '/.nemar'), 'tree already uploaded; refusing to rebuild'
    if os.path.exists(TREE):
        shutil.rmtree(TREE)
    os.makedirs(TREE)
    man = manifest(ID)
    report = {'id': ID, 'files': {}, 'roundtrip': {}, 'maps': []}
    sd = f'{TREE}/sourcedata/{SLUG}'
    sums = []
    for n, exp in sorted(man.items()):
        dg = copy_verified(f'{SRC}/{n}', f'{sd}/{n}', exp)
        report['files'][f'sourcedata/{SLUG}/{n}'] = dg
        sums.append((n, dg))
    write_sha256sums(sd, sums)
    log('sourcedata done')

    with ProcessPoolExecutor(W) as ex:
        results = list(ex.map(split_zip, sorted(CONN, key=lambda k: -man[k][2])))
    for r in results:
        report['roundtrip'][r['zip']] = {'members': len(r['members']), 'outputs': len(r['outputs']), 'exact': True}
        for k, v in r['outputs'].items():
            report['files'][k] = v['sha256']
    log('connectome split done')

    maps = []  # (derivative path, original zip, original member, sha256)
    # supporting SEEG
    z = zipfile.ZipFile(f'{SRC}/Supporting_Files_SEEG.zip')
    for i in z.infolist():
        if i.is_dir():
            continue
        m = re.match(r'(masks|distances|GMPI)/(S\d+)\.csv$', i.filename)
        if m:
            lab = label(m.group(2), 'seeg'); kind = {'masks': 'mask', 'distances': 'distances', 'GMPI': 'gmpi'}[m.group(1)]
            dst = f'sub-{lab}/ieeg/sub-{lab}_desc-{kind}_contacts.csv'
        else:
            dst = f'group/seeg/{safe(i.filename)}'
        maps.append((dst, 'Supporting_Files_SEEG.zip', i.filename, extract_member(z, i, f'{TREE}/{dst}')))
    # supporting MEG
    z = zipfile.ZipFile(f'{SRC}/Supporting_Files_MEG.zip')
    for i in z.infolist():
        if i.is_dir():
            continue
        m = re.match(r'(S\d+)/(.+)\.csv$', i.filename)
        if m:
            lab = label(m.group(1), 'meg')
            kind = {'Cross-Parcel PLV parc2009_200': 'crossparcelPLV200', 'Parcel Distances parc2009_200': 'parceldistances200',
                    'Parcel Fidelity parc2009_200': 'parcelfidelity200', 'Cross-Parcel PLV parc2009': 'crossparcelPLV148',
                    'Parcel Fidelity parc2009': 'parcelfidelity148'}[m.group(2)]
            dst = f'sub-{lab}/meg/sub-{lab}_desc-{kind}_parcels.csv'
        else:
            dst = f'group/meg/{safe(i.filename)}'
        maps.append((dst, 'Supporting_Files_MEG.zip', i.filename, extract_member(z, i, f'{TREE}/{dst}')))
    # plot data
    z = zipfile.ZipFile(f'{SRC}/Plot_Data.zip')
    for i in z.infolist():
        if i.is_dir():
            continue
        dst = 'group/plot_data/' + '/'.join(safe(p) for p in i.filename.split('/'))
        maps.append((dst, 'Plot_Data.zip', i.filename, extract_member(z, i, f'{TREE}/{dst}')))
    assert len({m[0] for m in maps}) == len(maps), 'name collision'
    with open(f'{TREE}/group/files.tsv', 'w') as f:
        f.write('derivative_path\tsource_archive_file\tsource_member\tsha256\n')
        for m in maps:
            f.write('\t'.join(m) + '\n')
    report['maps'] = len(maps)
    for m in maps:
        report['files'][m[0]] = m[3]
    log('supporting/plot extracted', len(maps))

    # phenotype
    rows = list(csv.reader(open(f'{SRC}/Neuropsychological_Data.csv', newline=''), delimiter=';'))
    hdr = rows[0]
    os.makedirs(f'{TREE}/phenotype', exist_ok=True)
    cols = ['participant_id', 'forward_digits', 'backward_digits', 'letter_number_sequencing', 'digit_symbol_coding',
            'tmt_a', 'tmt_b', 'zoo_map_plan', 'zoo_map_time']
    assert hdr == ['subj', 'ForwDigits', 'BackDigits', 'LNS', 'Digit symbol coding_test', 'TMT-A', 'TMT-B', 'Zoo map_plan', 'Zoo map_time'], hdr
    with open(f'{TREE}/phenotype/neuropsychology.tsv', 'w') as f:
        f.write('\t'.join(cols) + '\n')
        for r in rows[1:]:
            if not r:
                continue
            f.write('\t'.join(['sub-' + label(r[0], 'meg')] + r[1:]) + '\n')
    back = [l.rstrip('\n').split('\t') for l in open(f'{TREE}/phenotype/neuropsychology.tsv')][1:]
    assert [[('S' + b[0][7:])] + b[1:] for b in back] == [r for r in rows[1:] if r], 'neuropsych roundtrip'
    report['roundtrip']['Neuropsychological_Data.csv'] = {'rows': len(back), 'exact': True}

    # participants
    subs = sorted(d for d in os.listdir(TREE) if d.startswith('sub-'))
    np_subj = {('sub-' + label(r[0], 'meg')) for r in rows[1:] if r}
    eoec = set(); main_meg = set()
    for r in results:
        for k, v in r['outputs'].items():
            s = k.split('/')[0]
            if r['zip'].startswith('MEG_connectome_'):
                eoec.add(s)
            elif r['zip'].startswith('MEG'):
                main_meg.add(s)
    with open(f'{TREE}/participants.tsv', 'w') as f:
        f.write('participant_id\tsource_code\tcohort\tmeg_main_cohort\tmeg_eoec_cohort\tneuropsychology\n')
        for s in subs:
            mod = 'SEEG' if s.startswith('sub-seeg') else 'MEG'
            code = 'S' + s[len('sub-seeg'):] if mod == 'SEEG' else 'S' + s[len('sub-meg'):]
            yn = lambda b: 'yes' if b else 'no'
            f.write(f"{s}\t{code}\t{mod}\t{yn(s in main_meg) if mod == 'MEG' else 'n/a'}\t{yn(s in eoec) if mod == 'MEG' else 'n/a'}\t{yn(s in np_subj) if mod == 'MEG' else 'n/a'}\n")
    report['n_subjects'] = {'seeg': sum(s.startswith('sub-seeg') for s in subs), 'meg': sum(s.startswith('sub-meg') for s in subs),
                            'meg_main': len(main_meg), 'meg_eoec': len(eoec)}
    log('participants', report['n_subjects'])

    report['texts'] = install_texts(TEXT, TREE)
    os.makedirs(f'{TREE}/code', exist_ok=True)
    for f in ('f05x_build055.py', 'f05x_lib.py'):
        shutil.copyfile(f'{ROOT}/harness/{f}', f'{TREE}/code/{f}')
    report['validator'] = validate(TREE, REP)
    log('validator', report['validator'])
    pr = privacy_scan(TREE, REP)
    report['privacy'] = {'n_findings': pr['n_findings'], 'stats': pr['stats'], 'findings_head': pr['findings'][:30]}
    log('privacy', pr['n_findings'])
    report['listing_n'] = len(tree_listing(TREE))
    json.dump(report, open(REP + '/build.json', 'w'), indent=1)
    print('RESULT', json.dumps({'validator': report['validator'], 'privacy_n': pr['n_findings'], 'n_files': report['listing_n'],
                                'subjects': report['n_subjects']}))
