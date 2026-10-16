#!/usr/bin/env python3
"""Resolve every reference cited in the book against Crossref and write references.bib.

Each entry below is a (citation key, search title, first-author surname, year)
tuple.  The script queries the Crossref REST API, accepts a hit only when the
returned title and year agree with the expectation, and writes BibTeX built
from the registered metadata.  Anything that cannot be resolved is reported and
left out, so the bibliography never contains an invented DOI.
"""
from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from difflib import SequenceMatcher

API = "https://api.crossref.org/works"
UA = {"User-Agent": "practical-bioinformatics-book/1.0 (bibliography builder)"}

# key, title to search, expected first-author surname, expected year
REFS: list[tuple[str, str, str, int]] = [
    # --- alignment and phylogenetics -------------------------------------
    ("needleman1970", "A general method applicable to the search for similarities in the amino acid sequence of two proteins", "Needleman", 1970),
    ("smith1981", "Identification of common molecular subsequences", "Smith", 1981),
    ("pearson1988", "Improved tools for biological sequence comparison", "Pearson", 1988),
    ("altschul1990", "Basic local alignment search tool", "Altschul", 1990),
    ("altschul1997", "Gapped BLAST and PSI-BLAST: a new generation of protein database search programs", "Altschul", 1997),
    ("henikoff1992", "Amino acid substitution matrices from protein blocks", "Henikoff", 1992),
    ("thompson1994", "CLUSTAL W: improving the sensitivity of progressive multiple sequence alignment through sequence weighting, position-specific gap penalties and weight matrix choice", "Thompson", 1994),
    ("sievers2011", "Fast, scalable generation of high-quality protein multiple sequence alignments using Clustal Omega", "Sievers", 2011),
    ("katoh2013", "MAFFT multiple sequence alignment software version 7: improvements in performance and usability", "Katoh", 2013),
    ("edgar2004", "MUSCLE: multiple sequence alignment with high accuracy and high throughput", "Edgar", 2004),
    ("saitou1987", "The neighbor-joining method: a new method for reconstructing phylogenetic trees", "Saitou", 1987),
    ("felsenstein1985", "Confidence limits on phylogenies: an approach using the bootstrap", "Felsenstein", 1985),
    ("stamatakis2014", "RAxML version 8: a tool for phylogenetic analysis and post-analysis of large phylogenies", "Stamatakis", 2014),
    ("minh2020", "IQ-TREE 2: New Models and Efficient Methods for Phylogenetic Inference in the Genomic Era", "Minh", 2020),
    ("tamura2021", "MEGA11: Molecular Evolutionary Genetics Analysis Version 11", "Tamura", 2021),
    ("eddy2011", "Accelerated Profile HMM Searches", "Eddy", 2011),
    # --- databases --------------------------------------------------------
    ("sayers2024", "Database resources of the National Center for Biotechnology Information", "Sayers", 2024),
    ("uniprot2023", "UniProt: the Universal Protein Knowledgebase in 2023", "", 2023),
    ("berman2000", "The Protein Data Bank", "Berman", 2000),
    ("burley2023", "RCSB Protein Data Bank (RCSB.org): delivery of experimentally-determined PDB structures alongside one million computed structure models of proteins from artificial intelligence/machine learning", "Burley", 2023),
    ("cunningham2022", "Ensembl 2022", "Cunningham", 2022),
    ("landrum2018", "ClinVar: improving access to variant interpretations and supporting evidence", "Landrum", 2018),
    ("sherry2001", "dbSNP: the NCBI database of genetic variation", "Sherry", 2001),
    ("amberger2019", "OMIM.org: leveraging knowledge across phenotype-gene relationships", "Amberger", 2019),
    ("barrett2013", "NCBI GEO: archive for functional genomics data sets--update", "Barrett", 2013),
    ("kanehisa2000", "KEGG: kyoto encyclopedia of genes and genomes", "Kanehisa", 2000),
    ("ashburner2000", "Gene ontology: tool for the unification of biology. The Gene Ontology Consortium", "Ashburner", 2000),
    ("go2023", "The Gene Ontology knowledgebase in 2023", "", 2023),
    ("milacic2024", "The Reactome Pathway Knowledgebase 2024", "Milacic", 2024),
    ("szklarczyk2023", "The STRING database in 2023: protein-protein association networks and functional enrichment analyses", "Szklarczyk", 2023),
    ("paysanlafosse2023", "InterPro in 2022", "Paysan-Lafosse", 2023),
    ("mistry2021", "Pfam: The protein families database in 2021", "Mistry", 2021),
    ("cantelli2022", "The European Bioinformatics Institute: empowering cooperation in response to a global health crisis", "Cantelli", 2021),
    # --- sequencing, alignment to genomes, variants ------------------------
    ("li2009bwa", "Fast and accurate short read alignment with Burrows-Wheeler transform", "Li", 2009),
    ("danecek2021", "Twelve years of SAMtools and BCFtools", "Danecek", 2021),
    ("langmead2012", "Fast gapped-read alignment with Bowtie 2", "Langmead", 2012),
    ("dobin2013", "STAR: ultrafast universal RNA-seq aligner", "Dobin", 2013),
    ("kim2019", "Graph-based genome alignment and genotyping with HISAT2 and HISAT-genotype", "Kim", 2019),
    ("patro2017", "Salmon provides fast and bias-aware quantification of transcript expression", "Patro", 2017),
    ("bray2016", "Near-optimal probabilistic RNA-seq quantification", "Bray", 2016),
    ("liao2014", "featureCounts: an efficient general purpose program for assigning sequence reads to genomic features", "Liao", 2014),
    ("anders2015htseq", "HTSeq--a Python framework to work with high-throughput sequencing data", "Anders", 2015),
    ("mckenna2010", "The Genome Analysis Toolkit: a MapReduce framework for analyzing next-generation DNA sequencing data", "McKenna", 2010),
    ("depristo2011", "A framework for variation discovery and genotyping using next-generation DNA sequencing data", "DePristo", 2011),
    ("danecek2011", "The variant call format and VCFtools", "Danecek", 2011),
    ("bolger2014", "Trimmomatic: a flexible trimmer for Illumina sequence data", "Bolger", 2014),
    ("chen2018", "fastp: an ultra-fast all-in-one FASTQ preprocessor", "Chen", 2018),
    ("ewels2016", "MultiQC: summarize analysis results for multiple tools and samples in a single report", "Ewels", 2016),
    ("robinson2011igv", "Integrative genomics viewer", "Robinson", 2011),
    ("thorvaldsdottir2013", "Integrative Genomics Viewer (IGV): high-performance genomics data visualization and exploration", "Thorvaldsdottir", 2013),
    # --- assembly and annotation -------------------------------------------
    ("bankevich2012", "SPAdes: a new genome assembly algorithm and its applications to single-cell sequencing", "Bankevich", 2012),
    ("koren2017", "Canu: scalable and accurate long-read assembly via adaptive k-mer weighting and repeat separation", "Koren", 2017),
    ("kolmogorov2019", "Assembly of long, error-prone reads using repeat graphs", "Kolmogorov", 2019),
    ("gurevich2013", "QUAST: quality assessment tool for genome assemblies", "Gurevich", 2013),
    ("manni2021", "BUSCO Update: Novel and Streamlined Workflows along with Broader and Deeper Phylogenetic Coverage for Scoring of Eukaryotic, Prokaryotic, and Viral Genomes", "Manni", 2021),
    ("seemann2014", "Prokka: rapid prokaryotic genome annotation", "Seemann", 2014),
    ("hyatt2010", "Prodigal: prokaryotic gene recognition and translation initiation site identification", "Hyatt", 2010),
    ("tatusova2016", "NCBI prokaryotic genome annotation pipeline", "Tatusova", 2016),
    ("stanke2006", "AUGUSTUS: ab initio prediction of alternative transcripts", "Stanke", 2006),
    ("lowe1997", "tRNAscan-SE: a program for improved detection of transfer RNA genes in genomic sequence", "Lowe", 1997),
    ("nurk2022", "The complete sequence of a human genome", "Nurk", 2022),
    ("liao2023", "A draft human pangenome reference", "Liao", 2023),
    ("lander2001", "Initial sequencing and analysis of the human genome", "Lander", 2001),
    ("venter2001", "The sequence of the human genome", "Venter", 2001),
    # --- structural bioinformatics -----------------------------------------
    ("jumper2021", "Highly accurate protein structure prediction with AlphaFold", "Jumper", 2021),
    ("varadi2022", "AlphaFold Protein Structure Database: massively expanding the structural coverage of protein-sequence space", "Varadi", 2022),
    ("baek2021", "Accurate prediction of protein structures and interactions using a three-track neural network", "Baek", 2021),
    ("kabsch1983", "Dictionary of protein secondary structure: pattern recognition of hydrogen-bonded and geometrical features", "Kabsch", 1983),
    ("trott2010", "AutoDock Vina: improving the speed and accuracy of docking with a new scoring function", "Trott", 2010),
    ("pettersen2021", "UCSF ChimeraX: Structure visualization for researchers, educators, and developers", "Pettersen", 2021),
    ("cho1994", "Crystal structure of a p53 tumor suppressor-DNA complex: understanding tumorigenic mutations", "Cho", 1994),
    ("kendrew1958", "A three-dimensional model of the myoglobin molecule obtained by x-ray analysis", "Kendrew", 1958),
    ("abramson2024", "Accurate structure prediction of biomolecular interactions with AlphaFold 3", "Abramson", 2024),
    # --- software, languages, statistics ------------------------------------
    ("cock2009", "Biopython: freely available Python tools for computational molecular biology and bioinformatics", "Cock", 2009),
    ("gentleman2004", "Bioconductor: open software development for computational biology and bioinformatics", "Gentleman", 2004),
    ("huber2015", "Orchestrating high-throughput genomic analysis with Bioconductor", "Huber", 2015),
    ("lawrence2013", "Software for computing and annotating genomic ranges", "Lawrence", 2013),
    ("wickham2019", "Welcome to the Tidyverse", "Wickham", 2019),
    ("harris2020", "Array programming with NumPy", "Harris", 2020),
    ("virtanen2020", "SciPy 1.0: fundamental algorithms for scientific computing in Python", "Virtanen", 2020),
    ("hunter2007", "Matplotlib: A 2D Graphics Environment", "Hunter", 2007),
        ("benjamini1995", "Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing", "Benjamini", 1995),
    ("storey2003", "Statistical significance for genomewide studies", "Storey", 2003),
    ("love2014", "Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2", "Love", 2014),
    ("robinson2010", "edgeR: a Bioconductor package for differential expression analysis of digital gene expression data", "Robinson", 2010),
    ("ritchie2015", "limma powers differential expression analyses for RNA-sequencing and microarray studies", "Ritchie", 2015),
    ("johnson2007", "Adjusting batch effects in microarray expression data using empirical Bayes methods", "Johnson", 2007),
    ("leek2010", "Tackling the widespread and critical impact of batch effects in high-throughput data", "Leek", 2010),
        ("becht2019", "Dimensionality reduction for visualizing single-cell data using UMAP", "Becht", 2019),
    ("yu2012", "clusterProfiler: an R package for comparing biological themes among gene clusters", "Yu", 2012),
    ("subramanian2005", "Gene set enrichment analysis: a knowledge-based approach for interpreting genome-wide expression profiles", "Subramanian", 2005),
    ("knuth1984", "Literate Programming", "Knuth", 1984),
    ("xie2015", "Dynamic Documents with R and knitr", "Xie", 2015),
    # --- workflows and reproducibility --------------------------------------
    ("gruning2018", "Bioconda: sustainable and comprehensive software distribution for the life sciences", "Gruning", 2018),
    ("ditommaso2017", "Nextflow enables reproducible computational workflows", "Di Tommaso", 2017),
    ("koster2012", "Snakemake--a scalable bioinformatics workflow engine", "Koster", 2012),
    ("wilkinson2016", "The FAIR Guiding Principles for scientific data management and stewardship", "Wilkinson", 2016),
    ("sandve2013", "Ten simple rules for reproducible computational research", "Sandve", 2013),
    ("wilson2017", "Good enough practices in scientific computing", "Wilson", 2017),
    ("perez2007", "IPython: A System for Interactive Scientific Computing", "Perez", 2007),
    # --- disease, clinical and public health genomics -------------------------
    ("richards2015", "Standards and guidelines for the interpretation of sequence variants: a joint consensus recommendation of the American College of Medical Genetics and Genomics and the Association for Molecular Pathology", "Richards", 2015),
    ("karczewski2020", "The mutational constraint spectrum quantified from variation in 141,456 humans", "Karczewski", 2020),
    ("1000g2015", "A global reference for human genetic variation", "", 2015),
    ("weinstein2013", "The Cancer Genome Atlas Pan-Cancer analysis project", "Weinstein", 2013),
    ("cerami2012", "The cBio cancer genomics portal: an open platform for exploring multidimensional cancer genomics data", "Cerami", 2012),
    ("tate2019", "COSMIC: the Catalogue Of Somatic Mutations In Cancer", "Tate", 2019),
    ("alexandrov2020", "The repertoire of mutational signatures in human cancer", "Alexandrov", 2020),
    ("robertson2017", "Comprehensive Molecular Characterization of Muscle-Invasive Bladder Cancer", "Robertson", 2017),
    ("icgc2020", "Pan-cancer analysis of whole genomes", "", 2020),
    ("relling2015", "Pharmacogenomics in the clinic", "Relling", 2015),
    ("whirlcarrillo2021", "An Evidence-Based Framework for Evaluating Pharmacogenomics Knowledge for Personalized Medicine", "Whirl-Carrillo", 2021),
    ("wood2019", "Improved metagenomic analysis with Kraken 2", "Wood", 2019),
    ("hadfield2018", "Nextstrain: real-time tracking of pathogen evolution", "Hadfield", 2018),
    ("rambaut2020", "A dynamic nomenclature proposal for SARS-CoV-2 lineages to assist genomic epidemiology", "Rambaut", 2020),
    ("quick2017", "Multiplex PCR method for MinION and Illumina sequencing of Zika and other virus genomes directly from clinical samples", "Quick", 2017),
    ("hu2021", "Characteristics of SARS-CoV-2 and COVID-19", "Hu", 2021),
    ("tegally2022", "The evolving SARS-CoV-2 epidemic in Africa: Insights from rapidly expanding genomic surveillance", "Tegally", 2022),
    # --- machine learning in genomics -----------------------------------------
    ("libbrecht2015", "Machine learning applications in genetics and genomics", "Libbrecht", 2015),
    ("zou2019", "A primer on deep learning in genomics", "Zou", 2019),
    ("eraslan2019", "Deep learning: new computational modelling techniques for genomics", "Eraslan", 2019),
    ("lecun2015", "Deep learning", "LeCun", 2015),
    ("avsec2021", "Effective gene expression prediction from sequence by integrating long-range interactions", "Avsec", 2021),
    # --- ethics, law, society ---------------------------------------------------
    ("gymrek2013", "Identifying personal genomes by surname inference", "Gymrek", 2013),
    ("homer2008", "Resolving individuals contributing trace amounts of DNA to highly complex mixtures", "Homer", 2008),
    ("erlich2014", "Routes for breaching and protecting genetic privacy", "Erlich", 2014),
    ("popejoy2016", "Genomics is failing on diversity", "Popejoy", 2016),
    ("sirugo2019", "The Missing Diversity in Human Genetic Studies", "Sirugo", 2019),
    ("h3africa2014", "Research capacity. Enabling the genomic revolution in Africa", "H3Africa", 2014),
    ("knoppers2014", "Framework for responsible sharing of genomic and health-related data", "Knoppers", 2014),
    ("fiume2019", "Federated discovery and sharing of genomic data using Beacons", "Fiume", 2019),
]


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    plain = re.sub(r"<[^>]+>", " ", plain)          # Crossref sometimes returns markup
    plain = plain.replace("&amp;", " ").replace("&", " ")
    return TOKEN_RE.findall(plain)


STOP = {"a", "an", "the", "of", "for", "and", "in", "to", "on", "with", "using", "from", "by"}


def title_score(expected: str, found: str) -> float:
    """Similarity that tolerates subtitles present on one side only.

    Combines a character-level ratio over the common prefix length with
    token-set containment, so a short search title still matches the full
    registered title but an unrelated paper does not.
    """
    exp_t = [t for t in tokens(expected) if t not in STOP]
    got_t = [t for t in tokens(found) if t not in STOP]
    if not exp_t or not got_t:
        return 0.0
    containment = len(set(exp_t) & set(got_t)) / min(len(set(exp_t)), len(set(got_t)))
    n = min(len(" ".join(exp_t)), len(" ".join(got_t)))
    prefix_ratio = SequenceMatcher(None, " ".join(exp_t)[:n], " ".join(got_t)[:n]).ratio()
    return 0.6 * containment + 0.4 * prefix_ratio


def author_ok(expected_surname: str, item: dict) -> bool:
    if not expected_surname:
        return True
    want = tokens(expected_surname)[-1]
    for a in item.get("author", []):
        fam = tokens(a.get("family", ""))
        if fam and (want == fam[-1] or want in fam):
            return True
    # consortium papers register the group name as the publisher or have no authors
    return not item.get("author")


def query(title: str, author: str, rows: int = 10) -> list[dict]:
    params = {"query.bibliographic": f"{title} {author}".strip(), "rows": str(rows),
              "select": "DOI,title,author,issued,container-title,volume,issue,page,type,publisher"}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    delay = 2.0
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as fh:
                return json.load(fh)["message"]["items"]
        except Exception as exc:  # noqa: BLE001
            transient = any(code in str(exc) for code in ("429", "502", "503", "504", "timed out"))
            if attempt == 5 or not transient:
                if attempt == 5:
                    raise
                raise
            time.sleep(delay)
            delay *= 1.8
    return []


def escape(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "and").replace("&", r"\&")
    return text.replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")


def to_bibtex(key: str, item: dict) -> str:
    kind = item.get("type", "")
    entry = {"journal-article": "article", "proceedings-article": "inproceedings",
             "book": "book", "book-chapter": "incollection",
             "posted-content": "misc"}.get(kind, "article")
    authors = " and ".join(
        f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
        for a in item.get("author", []) if a.get("family")
    ) or item.get("publisher", "")
    year = item["issued"]["date-parts"][0][0]
    title = escape(item["title"][0])
    venue = escape((item.get("container-title") or [""])[0])
    fields = [f"  author = {{{authors}}}", f"  title = {{{{{title}}}}}", f"  year = {{{year}}}"]
    if venue:
        fields.append(f"  {'journal' if entry == 'article' else 'booktitle'} = {{{venue}}}")
    for src, dst in (("volume", "volume"), ("issue", "number"), ("page", "pages")):
        if item.get(src):
            fields.append(f"  {dst} = {{{item[src]}}}")
    if item.get("publisher") and entry in {"book", "incollection", "misc"}:
        fields.append(f"  publisher = {{{escape(item['publisher'])}}}")
    fields.append(f"  doi = {{{item['DOI']}}}")
    return f"@{entry}{{{key},\n" + ",\n".join(fields) + "\n}\n"


# Works that carry no registered DOI (JMLR and similar) are written by hand.
# Their metadata was taken from the publisher's own listing; they are reported
# separately so the author can confirm them at proof stage.
MANUAL = {
    "maaten2008": """@article{maaten2008,
  author = {van der Maaten, Laurens and Hinton, Geoffrey},
  title = {{Visualizing Data using t-SNE}},
  year = {2008},
  journal = {Journal of Machine Learning Research},
  volume = {9},
  pages = {2579--2605},
  note = {No DOI is registered for this article}
}
""",
    "pedregosa2011": """@article{pedregosa2011,
  author = {Pedregosa, Fabian and Varoquaux, Ga\\"{e}l and Gramfort, Alexandre and Michel, Vincent and Thirion, Bertrand and Grisel, Olivier and Blondel, Mathieu and Prettenhofer, Peter and Weiss, Ron and Dubourg, Vincent and Vanderplas, Jake and Passos, Alexandre and Cournapeau, David and Brucher, Matthieu and Perrot, Matthieu and Duchesnay, Edouard},
  title = {{Scikit-learn: Machine Learning in Python}},
  year = {2011},
  journal = {Journal of Machine Learning Research},
  volume = {12},
  pages = {2825--2830},
  note = {No DOI is registered for this article}
}
""",
    "rcoreteam": """@manual{rcoreteam,
  author = {{R Core Team}},
  title = {{R: A Language and Environment for Statistical Computing}},
  organization = {R Foundation for Statistical Computing},
  address = {Vienna, Austria},
  year = {2024},
  url = {https://www.R-project.org/}
}
""",
    "fastqc": """@misc{fastqc,
  author = {Andrews, Simon},
  title = {{FastQC: A Quality Control Tool for High Throughput Sequence Data}},
  year = {2010},
  howpublished = {\\url{https://www.bioinformatics.babraham.ac.uk/projects/fastqc/}},
  note = {Software}
}
""",
}


def main() -> int:
    out, failures, report, suspicious = [], [], [], []
    for key, title, author, year in REFS:
        try:
            items = query(title, author)
        except Exception as exc:  # noqa: BLE001
            failures.append((key, f"query error: {exc}"))
            time.sleep(1.2)
            continue
        best, best_score = None, 0.0
        for item in items:
            if not item.get("title"):
                continue
            parts = item.get("issued", {}).get("date-parts", [[None]])[0]
            if not parts or not parts[0]:
                continue
            got_year = parts[0]
            if abs(got_year - year) > 1:
                continue
            if not author_ok(author, item):
                continue
            score = title_score(title, item["title"][0])
            if score > best_score:
                best, best_score = item, score
        if best is None or best_score < 0.85:
            failures.append((key, f"best accepted match {best_score:.2f}: "
                                  f"{best['title'][0][:70] if best else 'none'}"))
            time.sleep(1.2)
            continue
        out.append(to_bibtex(key, best))
        row = (key, best["DOI"], best["issued"]["date-parts"][0][0], round(best_score, 3),
               re.sub(r"<[^>]+>", "", best["title"][0])[:90])
        report.append(row)
        if best_score < 0.93:
            suspicious.append(row)
        time.sleep(1.2)

    for key, entry in MANUAL.items():
        out.append(entry)
        report.append((key, "no DOI registered", "", "manual", "hand-written entry - confirm at proof"))

    header = (
        "% references.bib - Practical Approach to Learning Bioinformatics\n"
        "% Generated by scripts/build_bibliography.py. Every entry except those\n"
        "% listed under MANUAL in that script was resolved against the Crossref\n"
        "% REST API and carries a registered DOI, with the first-author surname\n"
        "% and publication year verified against the search expectation.\n"
        "% Regenerate with: python scripts/build_bibliography.py\n\n"
    )
    with open("references.bib", "w") as fh:
        fh.write(header + "\n".join(sorted(out)))
    with open("scripts/bibliography_report.tsv", "w") as fh:
        fh.write("key\tdoi\tyear\tmatch_score\tresolved_title\n")
        for row in sorted(report):
            fh.write("\t".join(str(c) for c in row) + "\n")
        for key, why in failures:
            fh.write(f"{key}\tUNRESOLVED\t\t\t{why}\n")
    print(f"resolved {len(out)}/{len(REFS) + len(MANUAL)} references "
          f"({len(MANUAL)} written by hand)")
    if suspicious:
        print("\nCHECK THESE MATCHES:")
        for row in suspicious:
            print(f"  {row[0]:<22} {row[3]}  {row[4]}")
    if failures:
        print("\nUNRESOLVED:")
        for key, why in failures:
            print(f"  {key}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
