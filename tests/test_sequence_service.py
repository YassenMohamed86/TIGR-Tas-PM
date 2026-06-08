import pytest
from modules.sequence_service import (
    parse_raw_sequence, SequenceObject, SequenceValidationError
)

# All test data is CATEGORY 2 (synthetic) — for computational validation only.

# TEST 1: Valid raw sequence parses correctly
def test_valid_raw_sequence():
    obj = parse_raw_sequence("ATCGATCGATCG")
    assert obj.sequence == "ATCGATCGATCG"
    assert obj.length   == 12
    assert obj.strand   == "+"
    assert obj.source   == "raw"
    print("PASS: valid raw sequence parsed")

# TEST 2: Lowercase input is uppercased
def test_lowercase_uppercased():
    obj = parse_raw_sequence("atcgatcg")
    assert obj.sequence == "ATCGATCG"
    print("PASS: lowercase uppercased")

# TEST 3: Whitespace and newlines stripped
def test_whitespace_stripped():
    obj = parse_raw_sequence("  ATCG\nATCG\t")
    assert obj.sequence == "ATCGATCG"
    print("PASS: whitespace stripped")

# TEST 4: Invalid base raises SequenceValidationError
def test_invalid_base_raises():
    with pytest.raises(SequenceValidationError) as exc:
        parse_raw_sequence("ATCGXATCG")
    assert "X" in str(exc.value) or "invalid" in str(exc.value).lower()
    print("PASS: invalid base raises SequenceValidationError")

# TEST 5: Empty sequence raises SequenceValidationError
def test_empty_sequence_raises():
    with pytest.raises(SequenceValidationError):
        parse_raw_sequence("")
    print("PASS: empty sequence raises error")

# TEST 6: Sequence shorter than minimum raises SequenceValidationError
def test_too_short_raises():
    with pytest.raises(SequenceValidationError):
        parse_raw_sequence("ATCG")
    print("PASS: sequence too short raises error")

# TEST 7: Reverse complement is correct
def test_reverse_complement():
    obj = parse_raw_sequence("AATTCCGG")
    assert obj.rev_comp == "CCGGAATT"
    print(f"PASS: reverse complement correct: {obj.rev_comp}")

# TEST 8: FASTA file parsing strips header
def test_fasta_parsing(tmp_path):
    from modules.sequence_service import parse_fasta_file
    fasta = tmp_path / "test.fa"
    fasta.write_text(">test_gene\nATCGATCGATCGATCGATCG\n")
    obj = parse_fasta_file(str(fasta))
    assert obj.sequence == "ATCGATCGATCGATCGATCG"
    assert obj.source   == "fasta"
    print("PASS: FASTA file parsed correctly")
