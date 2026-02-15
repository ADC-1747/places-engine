# Preferred Times

This directory contains preferred time window configuration files. These files define when different place types are ideally visited (e.g., cafe during breakfast hours, park in the morning).

## Format

Each JSON file should have the following structure:

```json
{
  "place_type": [
    {
      "start_minutes": 420,    // Minutes since midnight (07:00)
      "end_minutes": 600,      // Minutes since midnight (10:00)
      "name": "breakfast"      // Window name (for explanations)
    }
  ]
}
```

## Special Cases

For overnight windows (e.g., 20:00 to 02:00), use `end_minutes` < `start_minutes`:

```json
{
  "bar": [
    {
      "start_minutes": 1200,   // 20:00
      "end_minutes": 120,      // 02:00 (next day)
      "name": "evening"
    }
  ]
}
```

## Example

```json
{
  "cafe": [
    {"start_minutes": 420, "end_minutes": 600, "name": "breakfast"},
    {"start_minutes": 660, "end_minutes": 840, "name": "lunch"},
    {"start_minutes": 1020, "end_minutes": 1200, "name": "dinner"}
  ],
  "park": [
    {"start_minutes": 360, "end_minutes": 600, "name": "morning"},
    {"start_minutes": 960, "end_minutes": 1140, "name": "evening"}
  ]
}
```

## Usage

### In Code
```python
from engine import Engine

# Use default times
engine = Engine()

# Use specific times file
engine = Engine(times_file='custom_times')

# Use full path
engine = Engine(times_file='data/times/custom_times.json')
```

## Creating Custom Times

Create a new JSON file in this directory with your preferred time windows. Then use it:

```python
engine = Engine(times_file='my_custom_times')
```

## Available Files

- **default.json**: Standard preferred time windows for common place types

