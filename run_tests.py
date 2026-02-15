from preprocessor import Preprocessor
from engine import Engine
import json
import os
import glob
from pathlib import Path


def run_single_test(test_file: str, show_all_scores: bool = False) -> dict:
    """
    Run a single test file and return results.
    
    Args:
        test_file: Path to test JSON file
        show_all_scores: If True, show all scored sequences
        
    Returns:
        Dictionary with test results
    """
    print("\n" + "=" * 80)
    print(f"TEST: {os.path.basename(test_file)}")
    print("=" * 80)
    
    try:
        # Initialize components
        preprocessor = Preprocessor()
        engine = Engine()
        
        # Load and preprocess
        graph = preprocessor.preprocess_from_file(test_file)
        
        # Display user info
        user = graph.user_data
        print(f"\nUser Info:")
        print(f"  Location: ({user['lat']}, {user['lng']})")
        print(f"  Time Available: {user['time_available_minutes']} minutes")
        print(f"  Start Time: {user['start_time']}")
        print(f"  Preferences: {', '.join(user.get('preferences', []))}")
        print(f"  Avoid: {', '.join(user.get('avoid', [])) if user.get('avoid') else 'None'}")
        print(f"  Places Available: {len(graph.nodes)}")
        
        # Process with engine
        if show_all_scores:
            result, all_scored_sequences = engine.process_with_all_scores(graph)
            
            print(f"\n  Valid Sequences Found: {len(all_scored_sequences)}")
            
            if all_scored_sequences:
                print(f"\n  Top 5 Sequences:")
                for idx, (sequence, score) in enumerate(all_scored_sequences[:5], 1):
                    place_names = [graph.nodes[pid].name for pid in sequence]
                    start_time_minutes = engine.time_to_minutes(user.get("start_time", "00:00"))
                    total_time, _ = engine.calculate_sequence_time(sequence, graph, start_time_minutes)
                    print(f"    {idx}. {sequence} (Score: {score:.2f}, Time: {total_time:.1f} min)")
                    print(f"       {' -> '.join(place_names)}")
        else:
            result = engine.process(graph)
        
        # Display result
        print(f"\n  Result:")
        if result.sequence:
            place_names = [graph.nodes[pid].name for pid in result.sequence]
            print(f"    Sequence: {result.sequence}")
            print(f"    Places: {' -> '.join(place_names)}")
            print(f"    Total Time: {result.total_time_minutes} minutes")
            
            if "_score" in result.explanation:
                print(f"    Score: {result.explanation['_score']}")
            
            print(f"    Explanations:")
            for place_id in result.sequence:
                place = graph.nodes[place_id]
                explanation = result.explanation.get(place_id, "No explanation")
                print(f"      - {place.name}: {explanation}")
            
            # Prepare output JSON
            clean_explanation = {k: v for k, v in result.explanation.items() if k != "_score"}
            output = {
                "sequence": result.sequence,
                "total_time_minutes": result.total_time_minutes,
                "explanation": clean_explanation
            }
            
            return {
                "test_file": test_file,
                "status": "success",
                "result": output,
                "places_count": len(graph.nodes),
                "valid_sequences": len(all_scored_sequences) if show_all_scores else None
            }
        else:
            error_msg = result.explanation.get("error", "Unknown error")
            print(f"    ERROR: {error_msg}")
            return {
                "test_file": test_file,
                "status": "failed",
                "error": error_msg,
                "places_count": len(graph.nodes)
            }
    
    except Exception as e:
        print(f"\n  ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "test_file": test_file,
            "status": "error",
            "error": str(e)
        }


def run_all_tests(test_dir: str = "test_inputs", show_all_scores: bool = False):
    """
    Run all test files in the test directory.
    
    Args:
        test_dir: Directory containing test JSON files
        show_all_scores: If True, show all scored sequences for each test
    """
    # Find all test files
    test_files = sorted(glob.glob(os.path.join(test_dir, "test*.json")))
    
    if not test_files:
        print(f"No test files found in {test_dir}")
        return
    
    print("=" * 80)
    print(f"RUNNING ALL TESTS ({len(test_files)} test files)")
    print("=" * 80)
    
    results = []
    success_count = 0
    failed_count = 0
    error_count = 0
    
    # Run each test
    for test_file in test_files:
        result = run_single_test(test_file, show_all_scores)
        results.append(result)
        
        if result["status"] == "success":
            success_count += 1
        elif result["status"] == "failed":
            failed_count += 1
        else:
            error_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(test_files)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Errors: {error_count}")
    print()
    
    # Show failed tests
    if failed_count > 0 or error_count > 0:
        print("Failed/Error Tests:")
        for result in results:
            if result["status"] != "success":
                print(f"  - {os.path.basename(result['test_file'])}: {result.get('error', 'Unknown error')}")
        print()
    
    return results


if __name__ == "__main__":
    import sys
    
    # Check for flags
    show_all_scores = "--all-scores" in sys.argv or "-a" in sys.argv
    test_dir = "test_inputs"
    
    # Allow custom test directory
    if "--test-dir" in sys.argv:
        idx = sys.argv.index("--test-dir")
        if idx + 1 < len(sys.argv):
            test_dir = sys.argv[idx + 1]
    
    # Run all tests
    run_all_tests(test_dir, show_all_scores)

