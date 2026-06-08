"""
TIGR-Tas Dual-Guide RNA Scoring Platform — Sequence Service Module
==================================================================

Standardises all sequence inputs into a canonical SequenceObject.
This module contains ZERO scoring logic.

SELF-AUDIT
----------
- [ ] Every biophysical constant is a named constant at module level.
- [ ] Every constant has an evidence-level comment.
- [ ] No cross-imports from scoring modules (geometry, cleavage, thermo, specificity).
- [ ] No eval() or exec() anywhere.
- [ ] No inline styles in HTML.
- [ ] Full type annotations on every function.
- [ ] All test data is CATEGORY 2 (synthetic).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Named Constants
# ---------------------------------------------------------------------------

MIN_SEQUENCE_LENGTH: int = 8
"""Minimum number of bases for a sequence to be considered valid.  [ESTABLISHED]
Short guide-RNA spacers are typically ≥8 nt; anything shorter is almost
certainly a user error or an incomplete input."""

VALID_BASES: frozenset[str] = frozenset("ATCG")
"""The only unambiguous DNA bases accepted.  [ESTABLISHED]"""

COMPLEMENT_MAP = str.maketrans("ATCG", "TAGC")
"""Standard Watson-Crick complement translation table.  [ESTABLISHED]"""

DEFAULT_NCBI_EMAIL: str = "user@example.com"
"""Fallback e-mail passed to NCBI Entrez when the caller does not supply one.
[UNKNOWN — placeholder; should be replaced with a real contact address in
production.]"""

ENSEMBL_REST_BASE: str = "https://rest.ensembl.org"
"""Root URL of the Ensembl REST API.  [ESTABLISHED]"""

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class SequenceValidationError(ValueError):
    """Raised when a sequence fails validation checks."""


class GenomeFetchError(Exception):
    """Raised when an external genome fetch (NCBI / Ensembl) fails."""


# ---------------------------------------------------------------------------
# Core Data Object
# ---------------------------------------------------------------------------


@dataclass
class SequenceObject:
    """Canonical representation of a DNA sequence inside the platform."""

    sequence: str
    length: int
    strand: str
    rev_comp: str
    source: str
    gene_name: str = ""
    organism: str = ""
    chromosome: str = ""
    start_pos: int = 0
    end_pos: int = 0


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _reverse_complement(seq: str) -> str:
    """Return the reverse complement of *seq* using :data:`COMPLEMENT_MAP`.

    Parameters
    ----------
    seq:
        An uppercase DNA string consisting only of characters in
        :data:`VALID_BASES`.

    Returns
    -------
    str
        The reverse-complemented sequence.
    """
    return seq.translate(COMPLEMENT_MAP)[::-1]


def _validate_sequence(seq: str, source_label: str) -> str:
    """Normalise and validate a raw DNA string.

    1. Strip **all** whitespace (spaces, tabs, newlines).
    2. Uppercase.
    3. Reject empty strings.
    4. Reject sequences shorter than :data:`MIN_SEQUENCE_LENGTH`.
    5. Reject sequences containing characters outside :data:`VALID_BASES`.

    Parameters
    ----------
    seq:
        The raw input text (may contain whitespace, mixed case, etc.).
    source_label:
        A human-readable label used in error messages (e.g. ``"raw"``,
        ``"fasta"``).

    Returns
    -------
    str
        The cleaned, uppercase, validated sequence.

    Raises
    ------
    SequenceValidationError
        If any validation check fails.
    """
    # 1. Strip ALL whitespace / newlines / tabs
    cleaned: str = re.sub(r"\s+", "", seq)

    # 2. Uppercase
    cleaned = cleaned.upper()

    # 3. Empty check
    if not cleaned:
        raise SequenceValidationError(
            f"Empty sequence provided (source: {source_label})."
        )

    # 4. Minimum-length check
    if len(cleaned) < MIN_SEQUENCE_LENGTH:
        raise SequenceValidationError(
            f"Sequence length {len(cleaned)} is below the minimum of "
            f"{MIN_SEQUENCE_LENGTH} (source: {source_label})."
        )

    # 5. Invalid-base check
    for idx, ch in enumerate(cleaned):
        if ch not in VALID_BASES:
            raise SequenceValidationError(
                f"Invalid base '{ch}' at position {idx} in {source_label} "
                f"sequence. Only A, T, C, G are accepted."
            )

    return cleaned


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_raw_sequence(text: str) -> SequenceObject:
    """Parse a raw DNA string into a :class:`SequenceObject`.

    Parameters
    ----------
    text:
        Free-form text that should contain only DNA bases (plus optional
        whitespace that will be stripped).

    Returns
    -------
    SequenceObject
        A validated, canonical sequence object with ``source='raw'``.

    Raises
    ------
    SequenceValidationError
        If the input is empty, too short, or contains invalid bases.
    """
    cleaned: str = _validate_sequence(text, source_label="raw")
    return SequenceObject(
        sequence=cleaned,
        length=len(cleaned),
        strand="+",
        rev_comp=_reverse_complement(cleaned),
        source="raw",
    )


def parse_fasta_file(filepath: str) -> SequenceObject:
    """Read a FASTA file and return a :class:`SequenceObject`.

    Only the first record is used.  Header lines (starting with ``>``) are
    discarded; all remaining lines are concatenated and validated.

    Parameters
    ----------
    filepath:
        Absolute or relative path to a ``.fa`` / ``.fasta`` file.

    Returns
    -------
    SequenceObject
        A validated, canonical sequence object with ``source='fasta'``.

    Raises
    ------
    SequenceValidationError
        If the assembled sequence is empty, too short, or invalid.
    FileNotFoundError
        If *filepath* does not exist.
    """
    with open(filepath, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    sequence_lines: list[str] = [
        line.strip() for line in lines if not line.startswith(">")
    ]
    raw_seq: str = "".join(sequence_lines)
    cleaned: str = _validate_sequence(raw_seq, source_label="fasta")

    return SequenceObject(
        sequence=cleaned,
        length=len(cleaned),
        strand="+",
        rev_comp=_reverse_complement(cleaned),
        source="fasta",
    )


def fetch_from_ncbi(
    gene_name: str,
    organism: str,
    upstream_bp: int = 1000,
    email: str = DEFAULT_NCBI_EMAIL,
) -> SequenceObject:
    """Fetch a gene sequence from NCBI via Biopython Entrez.

    Uses ``esearch`` to look up the gene, then ``efetch`` to retrieve the
    nucleotide sequence in FASTA format.

    Parameters
    ----------
    gene_name:
        HGNC / official gene symbol (e.g. ``"BRCA1"``).
    organism:
        Species name (e.g. ``"Homo sapiens"``).
    upstream_bp:
        Number of bases upstream of the gene to include.
    email:
        Contact e-mail sent to NCBI (required by their usage policy).

    Returns
    -------
    SequenceObject
        A validated sequence object with ``source='ncbi'``.

    Raises
    ------
    GenomeFetchError
        If the NCBI query returns no results or the network request fails.
    """
    try:
        from Bio import Entrez, SeqIO  # type: ignore[import-untyped]
    except ImportError as exc:
        raise GenomeFetchError(
            "Biopython is required for NCBI fetching. "
            "Install it with: pip install biopython"
        ) from exc

    Entrez.email = email

    try:
        # --- Search for the gene ---
        search_term: str = f"{gene_name}[Gene] AND {organism}[Organism]"
        search_handle = Entrez.esearch(
            db="nucleotide", term=search_term, retmax=1
        )
        search_results = Entrez.read(search_handle)
        search_handle.close()

        id_list: list[str] = search_results.get("IdList", [])
        if not id_list:
            raise GenomeFetchError(
                f"No NCBI nucleotide records found for gene='{gene_name}', "
                f"organism='{organism}'."
            )

        ncbi_id: str = id_list[0]

        # --- Fetch the sequence ---
        fetch_handle = Entrez.efetch(
            db="nucleotide",
            id=ncbi_id,
            rettype="fasta",
            retmode="text",
        )
        record = SeqIO.read(fetch_handle, "fasta")
        fetch_handle.close()

        raw_seq: str = str(record.seq)
        cleaned: str = _validate_sequence(raw_seq, source_label="ncbi")

        return SequenceObject(
            sequence=cleaned,
            length=len(cleaned),
            strand="+",
            rev_comp=_reverse_complement(cleaned),
            source="ncbi",
            gene_name=gene_name,
            organism=organism,
        )

    except GenomeFetchError:
        raise
    except Exception as exc:
        raise GenomeFetchError(
            f"NCBI fetch failed for gene='{gene_name}', "
            f"organism='{organism}': {exc}"
        ) from exc


def fetch_from_ensembl(
    gene_id: str,
    upstream_bp: int = 1000,
) -> SequenceObject:
    """Fetch a gene sequence from the Ensembl REST API.

    Parameters
    ----------
    gene_id:
        A stable Ensembl gene identifier (e.g. ``"ENSG00000139618"``).
    upstream_bp:
        Number of bases upstream of the gene to include.

    Returns
    -------
    SequenceObject
        A validated sequence object with ``source='ensembl'``.

    Raises
    ------
    GenomeFetchError
        If the Ensembl REST request fails or returns no usable data.
    """
    try:
        import requests  # type: ignore[import-untyped]
    except ImportError as exc:
        raise GenomeFetchError(
            "The 'requests' library is required for Ensembl fetching. "
            "Install it with: pip install requests"
        ) from exc

    url: str = (
        f"{ENSEMBL_REST_BASE}/sequence/id/{gene_id}"
        f"?expand_5prime={upstream_bp}&type=genomic"
    )
    headers: dict[str, str] = {"Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data: dict = response.json()
        raw_seq: str = data.get("seq", "")

        if not raw_seq:
            raise GenomeFetchError(
                f"Ensembl returned an empty sequence for gene_id='{gene_id}'."
            )

        cleaned: str = _validate_sequence(raw_seq, source_label="ensembl")

        return SequenceObject(
            sequence=cleaned,
            length=len(cleaned),
            strand="+",
            rev_comp=_reverse_complement(cleaned),
            source="ensembl",
            gene_name=gene_id,
        )

    except GenomeFetchError:
        raise
    except Exception as exc:
        raise GenomeFetchError(
            f"Ensembl fetch failed for gene_id='{gene_id}': {exc}"
        ) from exc
