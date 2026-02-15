# Weights Configuration

This directory contains weight configuration files for the graph engine. Each JSON file defines scoring weights that influence how the engine selects and sequences places.

## Weight Parameters

- **preference_match**: Bonus points for matching user preferences (higher = prioritize preferences more)
- **distance_penalty**: Penalty per kilometer of distance (negative = closer is better)
- **crowd_penalty**: Penalty for crowded places when user avoids crowded (negative = avoid crowded)
- **time_efficiency**: Bonus for places that fit well in remaining time window
- **logical_sequence**: Bonus for logical ordering (e.g., park before cafe)

## Available Weight Configurations

### default.json
Balanced weights suitable for most scenarios.
- Preference match: 10
- Distance penalty: -2
- Crowd penalty: -5
- Time efficiency: 3
- Logical sequence: 5

### preference_focused.json
Prioritizes matching user preferences over distance.
- Preference match: 15 (higher)
- Distance penalty: -1 (lower penalty)
- Crowd penalty: -5
- Time efficiency: 2
- Logical sequence: 3

### distance_focused.json
Prioritizes minimizing travel distance.
- Preference match: 5 (lower)
- Distance penalty: -5 (higher penalty)
- Crowd penalty: -5
- Time efficiency: 4
- Logical sequence: 3

### balanced.json
Well-balanced weights with slightly higher emphasis on logical sequencing.
- Preference match: 8
- Distance penalty: -3
- Crowd penalty: -6
- Time efficiency: 4
- Logical sequence: 6

## Usage

### In Code
```python
from engine import Engine

# Use default weights
engine = Engine()

# Use specific weights file (from data/weights/)
engine = Engine(weights_file='preference_focused')

# Use full path
engine = Engine(weights_file='data/weights/distance_focused.json')

# Override specific weights
engine = Engine(weights_file='default', weights={'preference_match': 20})
```

### Command Line
```bash
# Use default weights
python main.py test_inputs/test1_basic.json

# Use specific weights file
python main.py test_inputs/test1_basic.json --weights preference_focused
```

## Creating Custom Weights

Create a new JSON file in `data/weights/` directory with the following structure:

```json
{
  "preference_match": 10,
  "distance_penalty": -2,
  "crowd_penalty": -5,
  "time_efficiency": 3,
  "logical_sequence": 5
}
```

Then use it by specifying the filename (without .json extension):
```python
engine = Engine(weights_file='my_custom_weights')
```

