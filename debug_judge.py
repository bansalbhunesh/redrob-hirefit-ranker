import json
from src.redrob_ranker.pessimistic_judge import PessimisticJudge
from src.redrob_ranker.features import compute_features
from generate_training_data import CALIBRATION_PAIRS

def main():
    judge = PessimisticJudge("ai_ml_engineering")
    
    candidates = {}
    with open("candidates.jsonl") as f:
        for line in f:
            c = json.loads(line)
            cid = c["candidate_id"]
            candidates[cid] = c

    for winner_id, loser_id in CALIBRATION_PAIRS:
        w = candidates[winner_id]
        l = candidates[loser_id]
        
        jw = judge.judge(w)
        jl = judge.judge(l)
        
        print(f"\nPair: {winner_id} vs {loser_id}")
        print(f"Winner ({jw.score:.3f}): {jw.gate_scores}")
        print(f"Loser  ({jl.score:.3f}): {jl.gate_scores}")

if __name__ == "__main__":
    main()
