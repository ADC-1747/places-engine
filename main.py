from preprocessor import Preprocessor
from engine import Engine
import json
import sys


def process_input(input_file: str, output_file: str = None, verbose: bool = False, weights_file: str = None):
    """
    Process an input JSON file and generate a sequence.
    
    Args:
        input_file: Path to input JSON file
        output_file: Optional path to output JSON file (if None, prints to stdout)
        verbose: If True, show detailed processing information
        weights_file: Optional weights file name or path (defaults to "default.json")
    """
    # Initialize components
    preprocessor = Preprocessor()
    engine = Engine(weights_file=weights_file)
    
    if verbose and weights_file:
        print(f"Using weights file: {weights_file}")
    
    # Load and preprocess
    if verbose:
        print(f"Loading input file: {input_file}")
    
    graph = preprocessor.preprocess_from_file(input_file)
    
    if verbose:
        print(f"Processed {len(graph.nodes)} places")
        print(f"User preferences: {', '.join(graph.user_data.get('preferences', []))}")
        print(f"Time available: {graph.user_data.get('time_available_minutes', 0)} minutes")
        print()
    
    # Process with engine
    result = engine.process(graph)
    
    # Prepare output
    clean_explanation = {k: v for k, v in result.explanation.items() if k != "_score"}
    output = {
        "sequence": result.sequence,
        "total_time_minutes": result.total_time_minutes,
        "explanation": clean_explanation
    }
    
    # Output results
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        if verbose:
            print(f"Output written to: {output_file}")
    else:
        print(json.dumps(output, indent=2))
    
    return result


if __name__ == "__main__":
    # Parse arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Parse weights file
    weights_file = None
    if "--weights" in sys.argv:
        idx = sys.argv.index("--weights")
        if idx + 1 < len(sys.argv):
            weights_file = sys.argv[idx + 1]
    
    # Filter out flags
    args = [arg for arg in sys.argv[1:] 
            if arg not in ["--verbose", "-v", "--weights"] and 
            (sys.argv.index(arg) == 0 or sys.argv[sys.argv.index(arg) - 1] != "--weights")]
    
    # Default to first test file if no argument provided
    if len(args) > 0:
        input_file = args[0]
    else:
        input_file = "test_inputs/test1_basic.json"
    
    # Second argument is output file (if not a flag)
    output_file = args[1] if len(args) > 1 and not args[1].startswith("-") else None
    
    process_input(input_file, output_file, verbose, weights_file)
