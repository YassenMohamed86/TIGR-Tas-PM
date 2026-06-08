from celery import shared_task
from celery.utils.log import get_task_logger
from tasks.celery_app import celery_app

logger = get_task_logger(__name__)

@celery_app.task(name="tasks.scan_tasks.process_scan")
def process_scan(raw_sequence: str, k: int = 9):
    """
    Background task to process a DNA sequence.
    This offloads the Heavy compute cycle (candidate generation + 4-model scoring + shannon weighting).
    """
    from modules.sequence_service import parse_raw_sequence
    from modules.candidate_generator import generate_candidate_pairs
    from modules.results_assembler import assemble_results
    from modules.shannon_entropy_weighter import apply_weights
    
    logger.info(f"Starting background scan for sequence length {len(raw_sequence)}")
    try:
        seq_obj = parse_raw_sequence(raw_sequence)
        candidates = generate_candidate_pairs(seq_obj, k=k)
        results = assemble_results(candidates, seq_obj.sequence, k)
        apply_weights(results)
        
        # Convert dataclasses to dicts for JSON serialization back to Celery Result Backend
        return [r.__dict__ for r in results]
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}")
        raise
