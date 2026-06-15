import sys
from pathlib import Path
sys.path.insert(0,'src'); sys.path.insert(0,'experiments')
from anachronism import is_anachronistic
from redrob_ranker.io import iter_candidates
from redrob_ranker.eval_harness import load_labels
full = load_labels(Path('artifacts/h2_availblind_labels.jsonl'))
n=0; anach=0; anach_tier5=0
for cand in iter_candidates(Path('candidates.jsonl')):
    n+=1
    if is_anachronistic(cand):
        anach+=1
        if full.tiers.get(cand.get('candidate_id'),0)>=5: anach_tier5+=1
print(f'scanned {n}  anachronism(hard)={anach}  ({100*anach/n:.2f}% of pool)  of which blind-tier5={anach_tier5}')
print(f'official planted honeypots ~80; a calibrated hard detector flags ~{anach} ({100*anach/n:.2f}%), NOT thousands.')
