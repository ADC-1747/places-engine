# Logical Sequences Configuration

This directory contains logical sequence configuration files that define preferred ordering patterns between different place types.

## Format

Each file contains a JSON array of sequence rules:

```json
[
  {
    "from_type": "park",
    "to_type": "cafe",
    "reason": "good rest stop after walk",
    "description": "Park then cafe makes sense - rest after walking"
  }
]
```

## Fields

- **from_type**: The place type that should come first (e.g., "park")
- **to_type**: The place type that should come after (e.g., "cafe")
- **reason**: Short explanation text used in output explanations
- **description**: Longer description for documentation (optional)

## Usage

The engine automatically loads sequences from `data/sequences/default.json` at initialization.

You can specify a custom sequences file:

```python
from engine import Engine

# Use custom sequences file
engine = Engine(sequences_file="custom_sequences")
```

## Examples

### Default sequences
- **park → cafe**: Good rest stop after walk

### Adding More Sequences

You can add more logical sequences, for example:

```json
[
  {
    "from_type": "park",
    "to_type": "cafe",
    "reason": "good rest stop after walk"
  },
  {
    "from_type": "museum",
    "to_type": "cafe",
    "reason": "good place to discuss and reflect"
  },
  {
    "from_type": "restaurant",
    "to_type": "park",
    "reason": "nice walk after meal"
  }
]
```

## Notes

- Sequence rules are case-insensitive (converted to lowercase)
- Multiple rules can apply to the same sequence
- Rules add bonus points to the sequence score (weighted by `logical_sequence` weight)

