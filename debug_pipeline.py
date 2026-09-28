"""Debug script: runs each agent step-by-step to find bugs."""

import json
import traceback
import sys

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8")


def main():
    query = "Where am I spending the most money?"
    print(f"=== DEBUG: query={query!r} ===\n")

    # -- Step 1: Transaction Agent --
    print("=" * 60)
    print("STEP 1: Transaction Agent")
    print("=" * 60)
    try:
        from agents.transaction_agent import transaction_agent
        state = {"user_query": query}
        result = transaction_agent(state)
        state.update(result)
        txns = result["transaction_result"].get("transactions", [])
        print(f"[OK] {len(txns)} transactions returned")
        if txns:
            print(f"   Sample: {json.dumps(txns[0], indent=2)}")
    except Exception as e:
        print(f"[FAIL] {e}")
        traceback.print_exc()
        sys.exit(1)

    # -- Step 2: Category Agent --
    print("\n" + "=" * 60)
    print("STEP 2: Category Agent")
    print("=" * 60)
    try:
        from agents.category_agent import category_agent
        result = category_agent(state)
        state.update(result)
        cats = result["categorized_transactions"]
        print(f"[OK] {len(cats)} categorized transactions")
        categories = {}
        for t in cats:
            cat = t.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1
        print(f"   Categories: {categories}")
    except Exception as e:
        print(f"[FAIL] {e}")
        traceback.print_exc()
        sys.exit(1)

    # -- Step 3: Analysis Agent --
    print("\n" + "=" * 60)
    print("STEP 3: Analysis Agent")
    print("=" * 60)
    try:
        from agents.analysis_agent import analysis_agent
        result = analysis_agent(state)
        state.update(result)
        analysis = result["analysis"]
        print(f"[OK] keys: {list(analysis.keys())}")
        if analysis.get("metrics"):
            print(f"   Metrics: {json.dumps(analysis['metrics'], indent=2)}")
    except Exception as e:
        print(f"[FAIL] {e}")
        traceback.print_exc()
        sys.exit(1)

    # -- Step 4: Recommendation Agent --
    print("\n" + "=" * 60)
    print("STEP 4: Recommendation Agent")
    print("=" * 60)
    try:
        from agents.recommendation_agent import recommendation_agent
        result = recommendation_agent(state)
        state.update(result)
        recs = result["recommendations"]
        print(f"[OK] {len(recs)} recommendations")
        print(f"   Final response: {result['final_response'][:200]}...")
    except Exception as e:
        print(f"[FAIL] {e}")
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("ALL AGENTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
