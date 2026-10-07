# Genuine cross-frequency coupling networks in human resting-state electrophysiological recordings (Siebenhühner et al., 2020): SEEG and MEG connectomes (derivative)

**This is a processed-data (derivative) dataset.** It repackages the authors' public Dryad release
(doi:[10.5061/dryad.0k86k80](https://doi.org/10.5061/dryad.0k86k80), version 5, CC0-1.0): per-subject connectivity
matrices (CSV) computed from resting-state SEEG and MEG, the supporting files used in their processing, neuropsychological
scores and the plotted values of the article's figures. **Raw SEEG/MEG recordings are not part of the release and are not
included here**; the article states: "Raw data cannot be made available due to data privacy regulations set by the
ethical committees."

Article: Siebenhühner F, Wang SH, Arnulfo G, Lampinen A, Nobili L, Palva JM, Palva S (2020). Genuine cross-frequency
coupling networks in human resting-state electrophysiological recordings. *PLoS Biol* 18(5):e3000685.
doi:[10.1371/journal.pbio.3000685](https://doi.org/10.1371/journal.pbio.3000685). Code:
<https://github.com/palvalab/Resting_State_CFC>.

## Cohorts (article, Methods)

- **SEEG, 59 patients** (`sub-seeg001` ...): drug-resistant focal epilepsy, presurgical assessment at the "Claudio
  Munari" Epilepsy Surgery Centre, Niguarda Hospital, Milan. One 10-min eyes-closed resting-state set per patient,
  192-channel Nihon Kohden Neurofax-110, 1000 Hz; contacts localised with CT/SEEGA and assigned to the 148-parcel
  Destrieux atlas; closest-white-matter referencing; contacts in seizure-onset/propagation zones and subcortical
  contacts excluded; pairs sharing a reference or closer than 2 cm excluded; 50 Hz harmonics removed; 500-ms windows
  with interictal events excluded; Morlet wavelets (m = 5), 49 centre frequencies 1.2-315 Hz.
- **MEG main cohort, 19 healthy participants** (`sub-meg0006` ...): 10-min eyes-open resting state, 27 sets (4
  participants contributed 2 sets and 2 contributed 3), 306-channel Vectorview/Triux (Elekta-Neuromag/MEGIN), BioMag
  Laboratory, Helsinki; tSSS, ICA artifact removal, MNE source modelling collapsed to 200 parcels (split Destrieux
  atlas) with fidelity weighting; Morlet filter bank (m = 5), 1.1-315 Hz. Low-fidelity parcels/edges excluded.
- **MEG eyes-open/eyes-closed cohort, 10 participants** (4 of them also in the main cohort): 10-min eyes-open and
  eyes-closed sessions, 148-parcel connectomes (S8 Fig). Set names ending in "c" are eyes-closed recordings (authors'
  README).

`participants.tsv` lists each subject's release code and cohort membership. The article reports no per-subject age or
sex, so none is given.

## Connectome measures

Per subject and frequency (phase synchrony, PS) or low-frequency:high-frequency pair (cross-frequency coupling, CFC;
ratios 1:2 to 1:7), each matrix is contact x contact (SEEG) or parcel x parcel (MEG), semicolon-separated CSV. Every
matrix has a `_surr.csv` counterpart with the surrogate values. From the authors' README: "The first dimension in CFC
data is that of the low-frequency parcel/contact and the second dimension that of the high-frequency parcel/contact.
Values for local CFC are found on the diagonal."

| desc label | original zip | measure | used for (authors' README) |
|---|---|---|---|
| `CFS` | `SEEG connectome CFS.zip` / `MEG connectome CFS.zip` | cross-frequency phase synchrony | Figs 4, 5, 6 (SEEG), 7, 8 (MEG), S3, S5, S7, S9, S10 |
| `PAC` | `SEEG connectome PAC.zip` / `MEG connectome PAC.zip` | phase-amplitude coupling | Figs 4, 5, 6, 7, S3, S5, S7, S9, S10, S11 |
| `ACenv` | `SEEG_connectome_AC_ENV.zip` / `MEG connectome AC Env.zip` | amplitude-envelope coupling | S6 Fig |
| `PSplv` | `SEEG connectome PS_PLV.zip` / `MEG connectome PS (PLV).zip` | phase synchrony, PLV | S4 Fig |
| `PSwpli` | `SEEG connectome PS_wPLI.zip` / `MEG connectome PS (wPLI).zip` | phase synchrony, wPLI | S4 Fig |
| `CFSeoec` | `MEG_connectome_CFS_(EO-EC).zip` | CFS, eyes-open/closed cohort | S8 Fig |
| `PSwplieoec` | `MEG_connectome_PS_(wPLI_EO-EC).zip` | PS (wPLI), eyes-open/closed cohort | S8 Fig |

Frequencies are encoded in the CSV member names (e.g. `S001 LF=1.20 HF=2.40.csv`, `S0006 set01 f=1.05.csv`); MEG
member names also carry the recording set (`set01`, ...).

## Layout

```
sub-seegNNN/ieeg/
  sub-seegNNN_desc-<measure>_connectomes.zip      that subject's CSV members of the original zip
  sub-seegNNN_desc-mask_contacts.csv              contact-pair mask (cortical contacts, >= 2 cm, no shared reference)
  sub-seegNNN_desc-distances_contacts.csv         Euclidean contact-to-contact distances
  sub-seegNNN_desc-gmpi_contacts.csv              Grey Matter Proximity Index per contact
sub-megNNNN/meg/
  sub-megNNNN_desc-<measure>_connectomes.zip
  sub-megNNNN_desc-parceldistances200_parcels.csv  distances between parcel centres (200 parcels)
  sub-megNNNN_desc-parcelfidelity200_parcels.csv   parcel fidelity (200 parcels; ...148 for the EO/EC cohort)
  sub-megNNNN_desc-crossparcelPLV200_parcels.csv   cross-parcel PLV in simulated data (fidelity analysis)
group/seeg/   all_frequencies_SEEG.csv, CF_matrix_SEEG.csv, Contacts_per_parcel.csv
group/meg/    CF_matrix_MEG.csv, morphing_targets_200_to_148.csv, Parcel_names_200.csv
group/plot_data/<figure>/   plotted values of Figs 3-8 and S3-S11 (see below)
group/files.tsv             derivative path -> original zip member -> sha-256, for every extracted file
phenotype/neuropsychology.tsv (+ .json)   8 test scores of the 19 main-cohort MEG participants
sourcedata/dryad-0k86k80/   the 17 original files, byte-for-byte, with SHA256SUMS and the authors' Read_Me.docx
code/                       f05x_build055.py, f05x_lib.py
```

Every per-subject derivative file has a JSON sidecar of the same name (description, `Sources` pointing to the original release file, variables, how it was repackaged).

The per-subject zips contain the original members with their original names and timestamps; only the container is new.
Every member of every original zip appears exactly once in the per-subject zips with identical bytes (checked by
sha-256 in `code/f05x_build055.py`). Extracted CSVs are byte-identical to the zip members (spaces and brackets in names
replaced by `_`; mapping in `group/files.tsv`). Zip and CSV derivative files are listed in `.bidsignore`.

Supporting files (authors' README): *CF matrix*: frequencies used as low frequencies (first column) and as high
frequencies (2nd to 7th column) for ratios 1:2-1:7; *All Frequencies SEEG*: list of all frequencies used; *Contacts per
parcel*: number of contacts across subjects per Destrieux parcel; *Morphing Targets 200 to 148*: parent 148-parcel for
each of the 200 parcels; *Parcel Names 200*: names and abbreviations of the 200 parcels; *Parcel Fidelity* and
*Cross-Parcel PLV*: see article Methods (removal of low-fidelity parcels and connections).

Plot data (authors' README): Fig 3, data from -500 ms to 499 ms in 1-ms steps (TFR files include frequencies); Figs 4,
5, 6, S3, S5, S6, S7, S8, group mean K or GS (row 1) with lower (row 2) and upper (row 3) confidence limits for all low
frequencies; S4 Fig, the same for PS; Figs 7 and S10, one directionality value per parcel of the 148-parcel Destrieux
atlas; Figs 8 and S11, Spearman's r of CFC with neuropsychological scores (rows: frequencies 1.05-95.6 Hz, columns:
ratios 1:2-1:7); S9 Fig, Spearman's r between MEG CFC parcel degrees and SEEG layer-combination degrees.

Neuropsychology: "A value of -1 indicates that a subject did not perform a test" (authors' README); values are copied
unchanged.

## Loading

```python
import zipfile, numpy as np
z = zipfile.ZipFile('sub-seeg001/ieeg/sub-seeg001_desc-CFS_connectomes.zip')
name = [n for n in z.namelist() if n.endswith('LF=1.20 HF=2.40.csv')][0]
K = np.loadtxt(z.open(name), delimiter=';')     # contacts x contacts (LF contact x HF contact)
```

## Privacy

Subject codes are the release's own pseudonyms (`S001`, `S0006`). File names, CSV contents and the authors' README
were scanned for names, dates, record numbers and paths; nothing identifying was found (CSV files hold only numbers).

## Ethics approval

"All research was carried out according to the Declaration of Helsinki. Prior to the study, each subject signed an
informed and written consent. The study protocol for SEEG, computerized tomography (CT), and MRI data obtained in the
La Niguarda Hospital were approved by the ethical committee of the Niguarda “Ca Granda” Hospital, Milan (ID 939). The
study protocol for MEG and MRI data obtained in the University of Helsinki was approved by the Coordinating Ethical
Committee of Helsinki University Central Hospital (HUCH) (ID 290/13/03/2013)." (Siebenhühner et al. 2020, *PLoS Biol*
18(5):e3000685, Methods, Ethics statement.)

## Funding

"This work was supported by the Academy of Finland (SA 266402, 303933, and SA 325404 to SP and SA 253130 and 296304 to
JMP) and Sigrid Juselius Foundation to SP & JMP." (article, Funding statement)

## Related

The 68-patient Niguarda SEEG cohort of Fuscà, Siebenhühner, Wang et al. (2023, *Nat Commun*,
doi:10.1038/s41467-023-40056-9; Dryad doi:10.5061/dryad.vdncjsxzn) comes from the same clinical programme; the
releases do not provide a subject mapping between the two.

## License and citation

CC0-1.0 (Dryad record license). Please cite the article (doi:10.1371/journal.pbio.3000685) and the Dryad dataset
(doi:10.5061/dryad.0k86k80).
