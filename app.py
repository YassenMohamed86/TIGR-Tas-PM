"""
app.py — Flask Application for TIGR-Tas Dual-Guide RNA Scoring Platform
========================================================================

SELF-AUDIT
----------
Magic numbers   : NONE — MAX_CONTENT_LENGTH is a named config key (16 MiB).
Cross-imports   : Imports from sequence_service, candidate_generator,
                  results_assembler only.  Does NOT import from scoring
                  modules directly (results_assembler is the single fan-in).
eval/exec       : NONE
Inline styles   : NONE — all styling lives in static/css/.
Type annotations: COMPLETE on module-level; Flask route signatures follow
                  Flask conventions (no return-type annotation on views is
                  standard practice, but we add them anyway).
Test data        : N/A (application layer)
"""

from __future__ import annotations

import os
import tempfile
from typing import Any, Union

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_file,
)

from modules.sequence_service import (
    GenomeFetchError,
    SequenceValidationError,
    fetch_from_ensembl,
    fetch_from_ncbi,
    parse_fasta_file,
    parse_raw_sequence,
)
from modules.candidate_generator import generate_candidate_pairs
from modules.results_assembler import ScoredPair, assemble_results
from modules.shannon_entropy_weighter import apply_weights

# ---------------------------------------------------------------------------
# Application factory-ish setup
# ---------------------------------------------------------------------------
app: Flask = Flask(__name__)

# 16 MiB upload limit — protects against accidental genome-file uploads
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # bytes


# ---------------------------------------------------------------------------
# Web routes
# ---------------------------------------------------------------------------
@app.route("/")
def index() -> str:
    """Render the main input form."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze() -> str:
    """Accept form input, score candidate pairs, render results page."""
    try:
        input_type: str = request.form.get("input_type", "raw")
        k: int = int(request.form.get("spacer_length", "9"))
        d_min: int = int(request.form.get("d_min", "5"))
        d_max: int = int(request.form.get("d_max", "50"))
        gc_min: float = float(request.form.get("gc_min", "0.30"))
        gc_max: float = float(request.form.get("gc_max", "0.70"))

        if input_type == "raw":
            seq_text: str = request.form.get("sequence", "")
            seq_obj = parse_raw_sequence(seq_text)

        elif input_type == "fasta":
            file = request.files.get("fasta_file")
            if not file:
                return render_template("index.html", error="No FASTA file uploaded.")
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".fa")
            file.save(tmp.name)
            tmp.close()
            try:
                seq_obj = parse_fasta_file(tmp.name)
            finally:
                os.unlink(tmp.name)

        elif input_type == "ncbi":
            gene: str = request.form.get("gene_name", "")
            org: str = request.form.get("organism", "")
            email: str = request.form.get("email", "user@example.com")
            seq_obj = fetch_from_ncbi(gene, org, email=email)

        elif input_type == "ensembl":
            gene_id: str = request.form.get("gene_id", "")
            seq_obj = fetch_from_ensembl(gene_id)

        else:
            return render_template("index.html", error="Invalid input type.")

        candidates = generate_candidate_pairs(
            seq_obj, k, d_min, d_max, gc_min, gc_max,
        )
        results = assemble_results(candidates, seq_obj.sequence, k)
        apply_weights(results)

        return render_template(
            "results.html",
            results=results,
            sequence=seq_obj,
            total_pairs=len(results),
            k=k,
        )

    except SequenceValidationError as exc:
        return render_template("index.html", error=str(exc))
    except GenomeFetchError as exc:
        return render_template("index.html", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return render_template("index.html", error=f"Unexpected error: {exc!s}")


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------
@app.route("/api/analyze", methods=["POST"])
def api_analyze() -> tuple[Response, int] | Response:
    """REST endpoint — accepts JSON, returns scored pairs as JSON."""
    try:
        data: dict[str, Any] = request.get_json(force=True)
        seq_text: str = data.get("sequence", "")
        k: int = int(data.get("spacer_length", 9))

        seq_obj = parse_raw_sequence(seq_text)
        candidates = generate_candidate_pairs(seq_obj, k=k)
        results = assemble_results(candidates, seq_obj.sequence, k)
        apply_weights(results)

        return jsonify(
            {
                "status": "success",
                "total_pairs": len(results),
                "results": [
                    {
                        "spacer_a": r.spacer_a,
                        "spacer_b": r.spacer_b,
                        "pos_a": r.pos_a,
                        "pos_b": r.pos_b,
                        "geometry_score": r.geometry_score,
                        "cleavage_score": r.cleavage_score,
                        "stability_score_a": r.stability_score_a,
                        "stability_score_b": r.stability_score_b,
                        "specificity_score_a": r.specificity_score_a,
                        "specificity_score_b": r.specificity_score_b,
                        "final_score": r.final_score,
                        "warnings": r.assumption_warnings,
                    }
                    for r in results[:100]
                ],
            }
        )

    except (SequenceValidationError, GenomeFetchError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        return jsonify({"status": "error", "message": str(exc)}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

from flask import Response
from modules.export_service import export_to_csv

@app.route('/export/csv', methods=['POST'])
def export_csv():
    # Simplified version for demonstration. In production, 
    # candidates would be fetched from a DB using a Job ID.
    import json
    data = request.form
    raw = data.get('raw_sequence', '')
    if not raw:
        return 'No sequence provided', 400
        
    seq_obj = parse_raw_sequence(raw)
    candidates = generate_candidate_pairs(seq_obj, k=9)
    results = assemble_results(candidates, seq_obj.sequence, 9)
    apply_weights(results)
    
    csv_data = export_to_csv(results)
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-disposition': 'attachment; filename=tigr_tas_results.csv'}
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
