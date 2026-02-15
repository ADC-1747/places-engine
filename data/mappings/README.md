# Preference Mappings

This directory contains preference mapping configuration files. These files map user preferences (e.g., "coffee", "walk") to place types (e.g., ["cafe", "coffee"], ["park", "trail"]).

## Format

Each JSON file should have the following structure:

```json
{
  "preference": ["place_type1", "place_type2", ...]
}
```

## Example

```json
{
  "coffee": ["cafe", "coffee"],
  "walk": ["park", "trail", "walk"],
  "quiet": ["library", "bookstore", "park", "museum", "gallery"]
}
```

## Usage

### In Code
```python
from engine import Engine

# Use default mappings
engine = Engine()

# Use specific mappings file
engine = Engine(mappings_file='custom_mappings')

# Use full path
engine = Engine(mappings_file='data/mappings/custom_mappings.json')
```

## Creating Custom Mappings

Create a new JSON file in this directory with your preference mappings. Then use it:

```python
engine = Engine(mappings_file='my_custom_mappings')
```

## Available Files

- **default.json**: Standard preference mappings for common preferences

