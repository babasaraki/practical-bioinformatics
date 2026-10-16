#!/usr/bin/env python3
"""Provision the bundled example data for *Practical Approach to Learning
Bioinformatics*.

Every file used by a worked example in this book is downloaded by this script
from a public primary archive, or derived deterministically from such a
download.  Running the script reproduces ``data/`` exactly; ``data/MANIFEST.tsv``
records the SHA-256 of each file so readers can verify what they have.

Usage
-----
    python scripts/fetch_data.py            # fetch everything
    python scripts/fetch_data.py --check    # verify existing files only
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
UA = {"User-Agent": "practical-bioinformatics-book/1.0"}
PROV: list[dict] = []


def _get(url: str, tries: int = 4, pause: float = 1.0) -> bytes:
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as fh:
                return fh.read()
        except Exception as exc:  # noqa: BLE001 - retry on any transport error
            last = exc
            time.sleep(pause * (attempt + 1))
    raise RuntimeError(f"failed to download {url}: {last}")


def write(relpath: str, payload: bytes, source: str, note: str) -> None:
    dest = os.path.join(DATA, relpath)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as fh:
        fh.write(payload)
    PROV.append(
        {
            "path": relpath,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "source": source,
            "note": note,
        }
    )
    print(f"  {relpath:<46} {len(payload):>9,} B")


# ---------------------------------------------------------------------------
# 1. Nucleotide sequences (NCBI Nucleotide, E-utilities)
# ---------------------------------------------------------------------------
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def efetch(acc: str, rettype: str, db: str = "nuccore") -> bytes:
    params = {"db": db, "id": acc, "rettype": rettype, "retmode": "text"}
    return _get(f"{EUTILS}?{urllib.parse.urlencode(params)}")


def fetch_sequences() -> None:
    print("[1/8] nucleotide sequences from NCBI")
    jobs = [
        ("NC_045512.2", "fasta", "sequences/sars-cov-2-NC_045512.2.fasta",
         "SARS-CoV-2 isolate Wuhan-Hu-1, complete genome (29,903 bp)"),
        ("NC_045512.2", "gb", "sequences/sars-cov-2-NC_045512.2.gb",
         "Same record in GenBank flat-file format, used for feature-table examples"),
        ("NM_000546.6", "fasta", "sequences/TP53-NM_000546.6.fasta",
         "Homo sapiens tumour protein p53 (TP53), transcript variant 1, mRNA"),
        ("NM_000546.6", "gb", "sequences/TP53-NM_000546.6.gb",
         "Same TP53 transcript in GenBank format (CDS feature used in translation examples)"),
        ("NC_000908.2", "fasta", "sequences/mycoplasma-genitalium-NC_000908.2.fasta",
         "Mycoplasmoides genitalium G37 complete genome (580,076 bp) - compact genome for annotation work"),
    ]
    for acc, rettype, rel, note in jobs:
        write(rel, efetch(acc, rettype), f"NCBI Nucleotide {acc}", note)
        time.sleep(0.5)


# ---------------------------------------------------------------------------
# 2. Genome annotation (NCBI Datasets / EBI) - GFF3 for the compact genome
# ---------------------------------------------------------------------------
def fetch_annotation() -> None:
    """GFF3 annotation for the bundled compact genome, from NCBI Datasets."""
    print("[2/8] genome annotation from NCBI Datasets")
    import zipfile

    url = ("https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/accession/GCF_000027325.1/"
           "download?include_annotation_type=GENOME_GFF&filename=mgen.zip")
    payload = _get(url)
    zf = zipfile.ZipFile(io.BytesIO(payload))
    member = next(n for n in zf.namelist() if n.endswith("genomic.gff"))
    write("annotation/mycoplasma-genitalium.gff", zf.read(member),
          "NCBI Datasets, assembly GCF_000027325.1 (ASM2732v1), RefSeq annotation",
          "RefSeq GFF3 annotation for the bundled M. genitalium G37 genome")


# ---------------------------------------------------------------------------
# 3. Proteins (UniProtKB REST)
# ---------------------------------------------------------------------------
def fetch_proteins() -> None:
    print("[3/8] protein sequences from UniProtKB")
    base = "https://rest.uniprot.org/uniprotkb/"
    write("proteins/P04637.fasta", _get(base + "P04637.fasta"),
          "UniProtKB P04637 (P53_HUMAN)", "Human cellular tumour antigen p53, canonical sequence")
    write("proteins/P04637.txt", _get(base + "P04637.txt"),
          "UniProtKB P04637 (P53_HUMAN)", "Full UniProt flat-file record used for annotation parsing")

    # p53 orthologues for multiple alignment and phylogeny
    orthologs = {
        "P04637": "Homo sapiens", "P02340": "Mus musculus", "P10361": "Rattus norvegicus",
        "P41685": "Canis lupus familiaris", "P67939": "Macaca mulatta",
        "Q9TTA1": "Sus scrofa", "P79734": "Xenopus laevis", "P79820": "Danio rerio",
    }
    chunks = []
    for acc in orthologs:
        try:
            chunks.append(_get(f"{base}{acc}.fasta"))
        except Exception as exc:  # noqa: BLE001
            print(f"      skipped {acc}: {exc}")
        time.sleep(0.3)
    write("proteins/p53-orthologs.fasta", b"".join(chunks),
          "UniProtKB: " + ", ".join(orthologs),
          "p53 orthologues across eight vertebrates for multiple alignment and tree building")

    # Globin family - the classic teaching set for substitution matrices
    globins = ["P69905", "P68871", "P02144", "P02185"]  # HBA_HUMAN HBB_HUMAN MYG_HUMAN MYG_PHYCD
    chunks = []
    for acc in globins:
        chunks.append(_get(f"{base}{acc}.fasta"))
        time.sleep(0.3)
    write("proteins/globins.fasta", b"".join(chunks),
          "UniProtKB: " + ", ".join(globins),
          "Human alpha/beta haemoglobin and two myoglobins - pairwise alignment examples")


# ---------------------------------------------------------------------------
# 4. Structures (RCSB PDB and AlphaFold DB)
# ---------------------------------------------------------------------------
def fetch_structures() -> None:
    print("[4/8] structures from RCSB PDB and AlphaFold DB")
    for pdb_id, note in [
        ("1TUP", "p53 core domain bound to DNA (Cho et al. 1994) - structural analysis examples"),
        ("1MBN", "Sperm whale myoglobin (Watson 1969) - the first protein structure solved"),
    ]:
        write(f"structures/{pdb_id.lower()}.pdb",
              _get(f"https://files.rcsb.org/download/{pdb_id}.pdb"),
              f"RCSB PDB entry {pdb_id}", note)
        time.sleep(0.5)
    meta = json.loads(_get("https://alphafold.ebi.ac.uk/api/prediction/P04637"))[0]
    version = meta.get("latestVersion", "?")
    write("structures/AF-P04637-F1-model.pdb", _get(meta["pdbUrl"]),
          f"AlphaFold Protein Structure Database, AF-P04637-F1 (v{version})",
          "Predicted structure of human p53; per-residue pLDDT occupies the B-factor column")
    write("structures/AF-P04637-F1-confidence.json", _get(meta["paeDocUrl"])
          if meta.get("paeDocUrl") else _get(meta["pdbUrl"]),
          f"AlphaFold Protein Structure Database, AF-P04637-F1 (v{version})",
          "Predicted aligned error matrix accompanying the p53 AlphaFold model")


# ---------------------------------------------------------------------------
# 5. Expression counts (Bioconductor pasilla package, Artistic-2.0)
# ---------------------------------------------------------------------------
def fetch_expression() -> None:
    print("[5/8] RNA-seq count matrix")
    import re
    import tarfile

    contrib = "https://bioconductor.org/packages/release/data/experiment/src/contrib/"
    index = _get(contrib + "PACKAGES").decode()
    block = index[index.index("Package: pasilla"):]
    version = re.search(r"Version:\s*([\d.]+)", block).group(1)
    url = f"{contrib}pasilla_{version}.tar.gz"
    try:
        tar = tarfile.open(fileobj=io.BytesIO(_get(url)), mode="r:gz")
    except Exception as exc:  # noqa: BLE001
        print(f"      pasilla unavailable ({exc}); skipping count matrix")
        return
    wanted = {
        "pasilla/inst/extdata/pasilla_gene_counts.tsv": "expression/pasilla_gene_counts.tsv",
        "pasilla/inst/extdata/pasilla_sample_annotation.csv": "expression/pasilla_sample_annotation.csv",
    }
    for member, rel in wanted.items():
        try:
            payload = tar.extractfile(member).read()
        except Exception:  # noqa: BLE001
            print(f"      member {member} not found")
            continue
        write(rel, payload,
              f"Bioconductor pasilla {version} (Artistic-2.0); counts from Brooks et al. 2011, GEO GSE18508",
              "Drosophila RNAi knockdown of pasilla: 7 samples, used for the differential expression walk-through")


# ---------------------------------------------------------------------------
# 6. Variants (ClinVar via NCBI E-utilities) -> minimal VCF
# ---------------------------------------------------------------------------
def fetch_variants() -> None:
    """A real ClinVar slice over TP53, taken with a remote tabix query."""
    print("[6/8] ClinVar slice over TP53 (GRCh38 chr17:7,668,402-7,687,550)")
    try:
        import pysam
    except ImportError:
        print("      pysam not installed; skipping VCF")
        return
    url = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz"
    # Reading the tabix index over the network is flaky on long sessions, so the
    # index is pulled down once and handed to pysam explicitly.
    index_path = os.path.join(DATA, "variants", ".clinvar.vcf.gz.tbi")
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    if not os.path.exists(index_path):
        with open(index_path, "wb") as fh:
            fh.write(_get(url + ".tbi"))
    tbx, header = None, []
    for attempt in range(4):
        try:
            tbx = pysam.TabixFile(url, index=index_path)
            records = list(tbx.fetch("17", 7668402, 7687550))
            header = list(tbx.header)
            break
        except Exception as exc:  # noqa: BLE001
            print(f"      tabix attempt {attempt + 1} failed ({exc}); retrying")
            time.sleep(3 * (attempt + 1))
    else:
        print("      ClinVar slice unavailable; skipping VCF")
        return
    header = [l for l in header
              if l.startswith("##fileformat") or l.startswith("##INFO=<ID=CLN")
              or l.startswith("##INFO=<ID=AF_") or l.startswith("##INFO=<ID=ALLELEID")
              or l.startswith("##INFO=<ID=GENEINFO") or l.startswith("##INFO=<ID=MC")
              or l.startswith("##reference") or l.startswith("##fileDate")]
    header.insert(1, "##contig=<ID=17,length=83257441>")
    header.append("##source=ClinVar GRCh38 VCF, region slice over TP53")
    header.append("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
    keep = ("ALLELEID", "CLNSIG", "CLNREVSTAT", "CLNDN", "CLNVC", "GENEINFO", "MC", "AF_TGP")
    rows = []
    for rec in records:
        chrom, pos, vid, ref, alt, qual, filt, info = rec.split("\t")[:8]
        trimmed = ";".join(f for f in info.split(";") if f.split("=")[0] in keep)
        rows.append(f"{chrom}\t{pos}\t{vid}\t{ref}\t{alt}\t{qual}\t{filt}\t{trimmed}")
    write("variants/tp53_clinvar.vcf", ("\n".join(header + rows) + "\n").encode(),
          "NCBI ClinVar GRCh38 VCF (ftp.ncbi.nlm.nih.gov/pub/clinvar), remote tabix slice",
          f"{len(rows):,} ClinVar records across TP53 with clinical significance, review status "
          "and molecular consequence - used for variant filtering and interpretation examples")


# ---------------------------------------------------------------------------
# 7. Interaction network (STRING API)
# ---------------------------------------------------------------------------
def fetch_network() -> None:
    print("[7/8] STRING interaction network")
    genes = ["TP53", "MDM2", "CDKN1A", "ATM", "CHEK2", "BAX", "RB1", "E2F1", "CCNE1", "CDK2",
             "BRCA1", "BRCA2", "RAD51", "MYC", "PTEN", "AKT1", "PIK3CA", "EGFR", "ERBB2",
             "FGFR3", "RAS", "KRAS", "CDKN2A", "MDM4", "SIRT1", "TP63", "TP73", "CASP3",
             "CASP9", "APAF1"]
    url = ("https://string-db.org/api/tsv/network?identifiers=" + "%0d".join(genes) +
           "&species=9606&required_score=700&caller_identity=practical_bioinformatics_book")
    write("networks/p53_string_network.tsv", _get(url),
          "STRING v12 API (string-db.org), CC BY 4.0",
          "High-confidence (score >= 0.700) human interactions among 30 cell-cycle and DNA-damage genes")


# ---------------------------------------------------------------------------
# 8. Sequencing reads - simulated from the bundled reference
# ---------------------------------------------------------------------------
def make_reads() -> None:
    print("[8/8] simulating sequencing reads from the bundled reference")
    path = os.path.join(DATA, "sequences", "mycoplasma-genitalium-NC_000908.2.fasta")
    if not os.path.exists(path):
        print("      reference missing; skipping")
        return
    with open(path) as fh:
        genome = "".join(l.strip() for l in fh if not l.startswith(">")).upper()
    rng = random.Random(20250101)
    comp = str.maketrans("ACGTN", "TGCAN")
    n_pairs, read_len, frag = 20000, 150, 350
    r1, r2 = [], []
    for i in range(n_pairs):
        start = rng.randrange(0, len(genome) - frag)
        fragment = genome[start:start + frag]
        mate1 = fragment[:read_len]
        mate2 = fragment[-read_len:].translate(comp)[::-1]
        out = []
        for seq in (mate1, mate2):
            bases, quals = [], []
            for pos, base in enumerate(seq):
                # error probability rises along the read, as on a real instrument
                q = max(2, min(40, int(rng.gauss(38 - 14 * (pos / read_len) ** 2, 3))))
                if rng.random() < 10 ** (-q / 10):
                    base = rng.choice([b for b in "ACGT" if b != base])
                bases.append(base)
                quals.append(chr(q + 33))
            out.append(("".join(bases), "".join(quals)))
        name = f"SIM:1:FC1:1:{i // 1000 + 1}:{i % 1000}:{start}"
        r1.append(f"@{name}/1\n{out[0][0]}\n+\n{out[0][1]}")
        r2.append(f"@{name}/2\n{out[1][0]}\n+\n{out[1][1]}")
    for tag, reads in (("R1", r1), ("R2", r2)):
        write(f"reads/mgen_sim_{tag}.fastq.gz",
              gzip.compress(("\n".join(reads) + "\n").encode(), 6),
              "Simulated in silico by scripts/fetch_data.py (seed 20250101)",
              f"{n_pairs:,} paired 150 bp reads sampled from NC_000908.2 with position-dependent "
              "quality decay and matching sequencing errors; mate {tag}".replace("{tag}", tag))


def write_manifest() -> None:
    lines = ["path\tbytes\tsha256\tsource\tdescription"]
    for rec in sorted(PROV, key=lambda r: r["path"]):
        lines.append(f"{rec['path']}\t{rec['bytes']}\t{rec['sha256']}\t{rec['source']}\t{rec['note']}")
    with open(os.path.join(DATA, "MANIFEST.tsv"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwrote data/MANIFEST.tsv with {len(PROV)} entries")


def check_manifest() -> int:
    manifest = os.path.join(DATA, "MANIFEST.tsv")
    if not os.path.exists(manifest):
        print("no MANIFEST.tsv; run without --check first")
        return 1
    bad = 0
    with open(manifest) as fh:
        next(fh)
        for line in fh:
            rel, _, digest = line.split("\t")[:3]
            target = os.path.join(DATA, rel)
            if not os.path.exists(target):
                print(f"MISSING  {rel}")
                bad += 1
                continue
            with open(target, "rb") as data_fh:
                got = hashlib.sha256(data_fh.read()).hexdigest()
            if got != digest:
                print(f"CHANGED  {rel}")
                bad += 1
    print("all files verified" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify existing files against the manifest")
    args = ap.parse_args()
    if args.check:
        return check_manifest()
    for step in (fetch_sequences, fetch_annotation, fetch_proteins, fetch_structures,
                 fetch_expression, fetch_variants, fetch_network, make_reads):
        try:
            step()
        except Exception as exc:  # noqa: BLE001
            print(f"  !! {step.__name__} failed: {exc}")
    write_manifest()
    return 0


if __name__ == "__main__":
    sys.exit(main())
