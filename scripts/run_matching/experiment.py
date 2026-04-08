import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "backend"))
from app.services.matching_service import matching_service
import json

def test_matching():
    # Load everything to memory
    matching_service.load_artifacts()

    if matching_service.projects_df.empty:
        print("Data layer empty. Ensure pipeline ran completely.")
        return

    # Grab the first 3 projects to test
    sample_ids = matching_service.projects_df['project_id'].head(3).tolist()

    for pid in sample_ids:
        print(f"\n==========================================")
        print(f" PROJECT {pid}: ")
        proj_data = matching_service._get_project(pid)
        print(f" Title: {proj_data.get('project_title', proj_data.get('title'))}")
        print(f" Need: {proj_data.get('funding_need_min')} - {proj_data.get('funding_need_max')}")
        print(f"==========================================")

        # 1. Score Readiness
        readiness = matching_service.score_readiness(pid)
        if readiness:
            print(f" >> READINESS SCORE: {readiness['total_score']} / 100")
            print(f"    Sub-scores: {json.dumps(readiness['sub_scores'])}")
            print(f"    Risks: {readiness.get('risk_flags')}")

        # 2. Match Investors
        print("\n >> TOP 2 INVESTORS:")
        inv_matches = matching_service.match_investors(pid, top_k=2)
        for m in inv_matches:
            print(f"   [Score {m['total_score']}] Investor '{m['investor_name']}'")
            print(f"     Factors: {json.dumps(m['factor_contributions'])}")
            print(f"     Rationale: {m['rationale']}")

        # 3. Match Volunteers
        print("\n >> TOP 2 VOLUNTEERS:")
        vol_matches = matching_service.match_volunteers(pid, top_k=2)
        for v in vol_matches:
            print(f"   [Score {v['total_score']}] Volunteer '{v['name']}'")
            print(f"     Capabilities Matched: {v['skill_fit']}% Skills, {v['operational_fit']}% Ops")

        # 4. Retrieve Grants
        print("\n >> TOP DEFAULT GRANT:")
        grant_matches = matching_service.retrieve_grants(pid, top_k=1)
        if grant_matches:
            g = grant_matches[0]
            print(f"   [Score {g['relevance_score']}] Grant '{g['title']}' via Funder {g['funder']}")
            print(f"     Rationale: {g['rationale']}")

if __name__ == "__main__":
    test_matching()
