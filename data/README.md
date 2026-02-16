# Data Directory

This directory contains all configuration and data files for the graph engine.

## Directory Structure

```
data/
├── weights/              # Weight configuration files
│   ├── default.json
│   ├── preference_focused.json
│   ├── distance_focused.json
│   ├── balanced.json
│   └── README.md
├── mappings/            # Preference mapping files
│   ├── default.json
│   └── README.md
├── times/               # Preferred time window files
│   ├── default.json
│   └── README.md
├── sequences/           # Logical sequence files
│   ├── default.json
│   └── README.md
└── README.md            # This file
```

## Subdirectories

### `weights/`
Contains weight configuration files that control how the engine scores sequences. See `weights/README.md` for details.

### `mappings/`
Contains preference mapping files that map user preferences (e.g., "coffee") to place types (e.g., ["cafe", "coffee"]). See `mappings/README.md` for details.

### `times/`
Contains preferred time window files that define when different place types are ideally visited. See `times/README.md` for details.

### `sequences/`
Contains logical sequence files that define preferred ordering patterns between place types (e.g., park before cafe). See `sequences/README.md` for details.

## Usage

The engine automatically loads these files from the `data/` directory. You can customize behavior by:

- **Changing weights**: Edit files in `weights/` or create new ones
- **Adding new preferences**: Edit files in `mappings/` or create new ones
- **Adjusting time windows**: Edit files in `times/` or create new ones
- **Adding logical sequences**: Edit files in `sequences/` or create new ones

### In Code
```python
from engine import Engine

# Use all defaults
engine = Engine()

# Use custom weights
engine = Engine(weights_file='preference_focused')

# Use custom mappings
engine = Engine(mappings_file='custom_mappings')

# Use custom times
engine = Engine(times_file='custom_times')

# Use custom sequences
engine = Engine(sequences_file='custom_sequences')

# Combine all
engine = Engine(
    weights_file='preference_focused',
    mappings_file='custom_mappings',
    times_file='custom_times',
    sequences_file='custom_sequences'
)
```

## File Loading

The engine loads these files at initialization:
1. `weights/{weights_file}.json` - Defaults to "default"
2. `mappings/{mappings_file}.json` - Defaults to "default"
3. `times/{times_file}.json` - Defaults to "default"
4. `sequences/{sequences_file}.json` - Defaults to "default"

If a file is not found, the engine will use hardcoded defaults and print a warning.

