import importlib, sys

errors = []

# Check cleavage model
try:
    from app.export.assembly.cleavage_site_calculator import C5_CLEAVAGE_OFFSET
    assert C5_CLEAVAGE_OFFSET == 5, f'C5_CLEAVAGE_OFFSET = {C5_CLEAVAGE_OFFSET}, expected 5'
    print(f'PASS: C5_CLEAVAGE_OFFSET = {C5_CLEAVAGE_OFFSET} [ESTABLISHED]')
except Exception as e:
    errors.append(f'FAIL: C5_CLEAVAGE_OFFSET — {e}')

# Check overhang
try:
    from app.export.assembly.overhang_calculator import OverhangCalculator
    calc = OverhangCalculator()
    ctx  = 'GCACTGACGTCAAGACCCCA' + 'ATCGATCGA'
    ov   = calc.compute_overhang(ctx, cut_position=20)
    assert len(ov) == 8, f'Overhang length = {len(ov)}, expected 8'
    print(f'PASS: Overhang length = {len(ov)} nt [ESTABLISHED]')
except Exception as e:
    errors.append(f'FAIL: Overhang — {e}')

# Check tigRNA length
try:
    from app.export.assembly.tigrna_assembler import EXPECTED_TIGRNA_LENGTH
    assert EXPECTED_TIGRNA_LENGTH == 36, f'EXPECTED_TIGRNA_LENGTH = {EXPECTED_TIGRNA_LENGTH}'
    print(f'PASS: EXPECTED_TIGRNA_LENGTH = {EXPECTED_TIGRNA_LENGTH} [ESTABLISHED]')
except Exception as e:
    errors.append(f'FAIL: tigRNA length — {e}')

# Check PAM is NONE
try:
    from app.scanner.pam.cas_variant_registry import CasVariantRegistry
    v = CasVariantRegistry().get('TIGR-Tas')
    assert v is not None, 'TIGR-Tas variant not registered'
    assert v.pam_pattern in ('NONE',''), f'TIGR-Tas PAM = {v.pam_pattern}, expected NONE'
    print(f'PASS: TIGR-Tas pam_pattern = {v.pam_pattern!r} [ESTABLISHED]')
except Exception as e:
    errors.append(f'FAIL: PAM-independence — {e}')

if errors:
    print(chr(10).join(errors))
    raise SystemExit(f'{len(errors)} biological fact violations found — CERTIFICATION BLOCKED')
else:
    print('PASS: All TIGR-Tas biological facts correctly implemented')
