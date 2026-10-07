#!/usr/bin/env python3
"""FINISHER-05x finalize (text-only): re-install texts, write JSON sidecars for every per-subject derivative file,
re-validate, re-run the privacy scan. Usage: f05x_finalize.py <IEEGxxx> <textdir>"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from f05x_lib import *  # noqa

ID, TEXT = sys.argv[1], sys.argv[2]
TREE = f'{ROOT}/work/{ID}/bids'
REP = f'{ROOT}/work/{ID}/reports/f05x'
assert os.path.isdir(TREE)
texts = install_texts(TEXT, TREE)
for f in ('f05x_lib.py', 'f05x_finalize.py'):
    shutil.copyfile(f'{ROOT}/harness/{f}', f'{TREE}/code/{f}')


def put(path, d):
    j = os.path.splitext(path)[0] + '.json'
    json.dump(d, open(j, 'w'), indent=2, ensure_ascii=False)
    return j


n = 0
subs = sorted(d for d in os.listdir(TREE) if d.startswith('sub-'))
if ID == 'IEEG054':
    SD = 'bids::sourcedata/dryad-5qfttdz6t/'
    D = {
        'tfpower': ('Figure 1: wavelet time-frequency power, 44 retrieval trials x 150 frequencies (1-150 Hz) x 5000 samples (-3.999..1.0 s around vocalization, 1 kHz), one medial temporal lobe iEEG electrode (TT1).', 'fig1_NIH025_s1_chanTT1_data.mat', ['TF', 'freqvec', 'timevec']),
        'rippleband': ('Figure 1: 80-120 Hz ripple-band iEEG signal, 44 trials x 5000 samples, electrode TT1.', 'fig1_NIH025_s1_chanTT1_rippleband_trials.mat', ['ripple_band_TT1', 'ripple_band_trials_time']),
        'rippleraster': ('Figure 1: detected ripple indicator, 44 trials x 5000 samples, electrode TT1.', 'fig1_NIH025_s1_chanTT1_rippleraster.mat', ['ripple_raster_TT1', 'ripple_raster_time']),
        'ripplerate': ('Figure 1: smoothed ripple rate (and SE) for correct and incorrect trials, electrode TT1.', 'fig1_NIH025_s1_chanTT1_ripplerate.mat', ['ripplerate_sm_corr', 'ripplerate_sm_corr_se', 'ripplerate_sm_incorr', 'ripplerate_sm_incorr_se', 'timevec_sm']),
        'lfpieegripple': ('Figure 3: micro-LFP and LFP ripple-band signals [148 epochs x 96 MEA channels x 4001 samples] and z-scored ripple envelopes / ripple indicators of 4 nearby iEEG channels [148 x 4001 x 4].', 'fig3_LFP_iEEG_ripple_NIH037_data.mat', ['LFP_signal', 'LFPripple_sig', 'iEEGripple_envZ', 'iEEGripple_logic']),
        'ppc': ('Figure 3: maximum LFP pairwise phase consistency and iEEG ripple amplitude per iEEG ripple (one cell per iEEG channel).', 'fig3_LFP_iEEG_ripple_NIH037_PPC_computed.mat', ['LFPripple_ppc_max', 'iEEGripple_max']),
        'spikelfp': ('Figure 4: MEA LFP epochs [18 electrodes x 118 trials x 4001], spike rasters [33 units x 4001 x 118], spike indices and phases at 60 frequencies (2-400 Hz), LFP-ripple indicators, channel/unit bookkeeping, trial response.', 'fig4_spike_LFP_NIH037_s1_data.mat', ['LFP_timeseries', 'spike_raster', 'spike_id', 'spike_ph', 'spike_id_lfprip', 'spike_ph_lfprip', 'lfpripple_logic', 'freqs', 'lfp_channels', 'lfp_channels_u', 'el_cnt', 'response', 'trials']),
    }
    for s in subs:
        for f in sorted(os.listdir(f'{TREE}/{s}/ieeg')):
            if not f.endswith('.mat'):
                continue
            p = f'{TREE}/{s}/ieeg/{f}'
            suf = f[:-4].split('_')[-1]
            if suf == 'ripplewindows':
                ses = re.search(r'fig2session(\d)', f).group(1)
                d = {'Description': f'Figure 2: iEEG and micro-LFP ripple-band signal segments and windowed iEEG ripple amplitude, LFP ripple amplitude and z-scored spike rate for this participant, recording session column {ses} of the original cell arrays.',
                     'Sources': [SD + 'fig2_contspk_LFP_iEEG_data.mat (withheld, see WITHHELD.md; original on Dryad)'],
                     'Variables': ['iEEGripple_sig_cont', 'iEEGripple_win', 'lfpripple_sig_cont', 'lfpripple_win', 'spkrt_Z_win'],
                     'Repackaging': 'Cell {participant row, session column} of each variable saved unchanged (scipy.io.savemat, MAT v5); exact round-trip.',
                     'SamplingFrequency': 1000}
            else:
                desc, src, var = D[suf]
                d = {'Description': desc, 'Sources': [SD + src], 'Variables': var,
                     'Repackaging': 'Original file, bytes unchanged (renamed).'}
                if suf not in ('ripplerate', 'ppc'):
                    d['SamplingFrequency'] = 1000
            d['FileFormat'] = 'MATLAB v5 MAT'
            put(p, d); n += 1
elif ID == 'IEEG055':
    SD = 'bids::sourcedata/dryad-0k86k80/'
    CONN = {'SEEG connectome CFS.zip': ('seeg', 'CFS'), 'SEEG connectome PAC.zip': ('seeg', 'PAC'),
            'SEEG_connectome_AC_ENV.zip': ('seeg', 'ACenv'), 'SEEG connectome PS_PLV.zip': ('seeg', 'PSplv'),
            'SEEG connectome PS_wPLI.zip': ('seeg', 'PSwpli'), 'MEG connectome CFS.zip': ('meg', 'CFS'),
            'MEG connectome PAC.zip': ('meg', 'PAC'), 'MEG connectome AC Env.zip': ('meg', 'ACenv'),
            'MEG connectome PS (PLV).zip': ('meg', 'PSplv'), 'MEG connectome PS (wPLI).zip': ('meg', 'PSwpli'),
            'MEG_connectome_CFS_(EO-EC).zip': ('meg', 'CFSeoec'), 'MEG_connectome_PS_(wPLI_EO-EC).zip': ('meg', 'PSwplieoec')}
    inv = {(mod, desc): z for z, (mod, desc) in CONN.items()}
    MEAS = {'CFS': 'cross-frequency phase synchrony', 'PAC': 'phase-amplitude coupling', 'ACenv': 'amplitude-envelope coupling',
            'PSplv': 'phase synchrony (PLV)', 'PSwpli': 'phase synchrony (wPLI)', 'CFSeoec': 'cross-frequency phase synchrony, eyes-open/eyes-closed cohort (148 parcels)',
            'PSwplieoec': 'phase synchrony (wPLI), eyes-open/eyes-closed cohort (148 parcels)'}
    CSVD = {'mask': ('Contact-pair mask: retains only connections between contacts in cortical regions with a minimum distance of 2 cm and non-shared references (authors\' README).', 'masks/'),
            'distances': ('Euclidean distances between pairs of contacts.', 'distances/'),
            'gmpi': ('Grey Matter Proximity Index for each contact (article Methods).', 'GMPI/'),
            'parceldistances200': ('Subject-specific Euclidean distances between the centres of the 200 parcels.', 'Parcel Distances parc2009_200.csv'),
            'parcelfidelity200': ('Subject-specific parcel fidelity, 200 parcels (article Methods).', 'Parcel Fidelity parc2009_200.csv'),
            'parcelfidelity148': ('Subject-specific parcel fidelity, 148 parcels (eyes-open/eyes-closed cohort).', 'Parcel Fidelity parc2009.csv'),
            'crossparcelPLV200': ('Subject-specific cross-parcel PLV in simulated data, 200 parcels (fidelity analysis, article Methods).', 'Cross-Parcel PLV parc2009_200.csv'),
            'crossparcelPLV148': ('Subject-specific cross-parcel PLV in simulated data, 148 parcels.', 'Cross-Parcel PLV parc2009.csv')}
    for s in subs:
        for dt in os.listdir(f'{TREE}/{s}'):
            for f in sorted(os.listdir(f'{TREE}/{s}/{dt}')):
                p = f'{TREE}/{s}/{dt}/{f}'
                m = re.match(r'sub-[a-z0-9]+_desc-([A-Za-z0-9]+)_(connectomes|contacts|parcels)\.(zip|csv)$', f)
                if not m:
                    continue
                desc, suf, ext = m.groups()
                mod = 'seeg' if s.startswith('sub-seeg') else 'meg'
                code = 'S' + s.split('seeg' if mod == 'seeg' else 'meg', 1)[1]
                if ext == 'zip':
                    z = inv[(mod, desc)]
                    d = {'Description': f'{MEAS[desc]} connectomes of this subject: one semicolon-separated CSV matrix per frequency (PS) or low:high frequency pair (CFC), each with a _surr.csv surrogate counterpart. CFC: rows = low-frequency {"contact" if mod == "seeg" else "parcel"}, columns = high-frequency {"contact" if mod == "seeg" else "parcel"}, local CFC on the diagonal.',
                         'Sources': [SD + z], 'SourceMembersPrefix': code,
                         'Repackaging': 'Members of the original zip whose name carries this subject code, copied with identical names, timestamps and bytes into a new zip (exact sha-256 round-trip).',
                         'FileFormat': 'zip of CSV (semicolon-separated)'}
                else:
                    txt, src = CSVD[desc]
                    srczip = 'Supporting_Files_SEEG.zip' if mod == 'seeg' else 'Supporting_Files_MEG.zip'
                    member = (src + code + '.csv') if src.endswith('/') else (code + '/' + src)
                    d = {'Description': txt, 'Sources': [SD + srczip + '::' + member], 'Repackaging': 'Extracted verbatim (bytes unchanged).',
                         'FileFormat': 'CSV (semicolon-separated)'}
                put(p, d); n += 1
elif ID == 'IEEG056':
    SD = 'bids::sourcedata/dryad-vdncjsxzn/sEEG_data.mat'
    for s in subs:
        for f in sorted(os.listdir(f'{TREE}/{s}/ieeg')):
            p = f'{TREE}/{s}/ieeg/{f}'
            if f.endswith('_connectivity.mat'):
                d = {'Description': 'Resting-state SEEG phase synchronization and criticality metrics of this patient: complex PLV [24 frequencies x contacts x contacts], DFA exponents [24 x contacts], contact distances, reference mask, non-EZ and EZ contact masks, parcel assignment, patient selection flags, frequencies (Hz).',
                     'Sources': [SD], 'Variables': {'PLV': 'PLV{row}', 'DFA': 'DFA{row}', 'elec_dist': 'elec_dist{row}', 'ref_mask': 'ref_masks{row}',
                                                    'acceptcontHealthy': 'acceptcontHealthy{row}', 'acceptcontEZ': 'acceptcontEZ{row}',
                                                    'parcel_assign': 'parcel_assign{row}', 'HealthyEZcriteria': 'HealthyEZcriteria(row,:)', 'frequencies': 'frequencies'},
                     'SourceRow': int(s[4:]), 'Repackaging': 'Cells of the original arrays saved unchanged (scipy.io.savemat, MAT v5, compressed); exact round-trip.',
                     'FileFormat': 'MATLAB v5 MAT'}
            elif f.endswith('_desc-dfa_contacts.tsv'):
                d = {'Description': 'DFA exponents of this patient, one row per contact (same order as the MAT arrays), one column per frequency.',
                     'Sources': [SD], 'contact_index': {'Description': '1-based contact index (order of the release arrays).'},
                     'dfa_<f>Hz': {'Description': 'DFA scaling exponent of the amplitude envelope at centre frequency <f> Hz (values written with full float precision; n/a = NaN).'}}
            elif f.endswith('_contacts.tsv'):
                d = {'Description': 'Contacts of this patient (same order as the MAT arrays).', 'Sources': [SD],
                     'contact_index': {'Description': '1-based contact index.'},
                     'parcel_code': {'Description': 'parcel_assign code (group/seeg/parcel_order.tsv; 0 = Unknown).'},
                     'parcel_name': {'Description': 'Parcel name for parcel_code (Yeo/Schaefer 17-network cortical parcels and subcortical regions).'},
                     'non_ez_contact': {'Description': 'acceptcontHealthy mask (1 = non-EZ contact accepted for analysis).'},
                     'ez_contact': {'Description': 'acceptcontEZ mask (1 = EZ contact).'}}
            else:
                continue
            put(p, d); n += 1
log('sidecars', n)
rv = validate(TREE, REP)
log('validator', rv)
pr = privacy_scan(TREE, REP)
log('privacy', pr['n_findings'])
kinds = {}
for f in pr['findings']:
    if not f['file'].startswith('code/'):
        kinds.setdefault(f['kind'], []).append((f['file'], f['match']))
out = {'texts': texts, 'sidecars': n, 'validator': rv, 'privacy_n': pr['n_findings'], 'privacy_noncode': {k: v[:20] for k, v in kinds.items()},
       'n_files': len(tree_listing(TREE))}
json.dump(out, open(REP + '/finalize.json', 'w'), indent=1)
print('RESULT', json.dumps({k: out[k] for k in ('sidecars', 'validator', 'privacy_n', 'n_files')}), json.dumps(out['privacy_noncode'])[:3000])
