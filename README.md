# RPP Editor - REAPER Project File Editor

[![RPP Editor CI](https://github.com/KristjanKruusRIA/rpp-editor/workflows/RPP%20Editor%20CI/badge.svg)](https://github.com/KristjanKruusRIA/rpp-editor/actions)
[![codecov](https://codecov.io/gh/KristjanKruusRIA/rpp-editor/graph/badge.svg?token=LXT0AMGQR8)](https://codecov.io/gh/KristjanKruusRIA/rpp-editor)

A GUI application for editing and comparing REAPER project files (.rpp). This tool allows you to load two RPP files, compare their tracks and master track, and copy settings between them.

## Features

- **Load and compare two RPP files** - Side-by-side comparison of track settings
- **Master track support** - Edit and copy master track effects and settings
- **Track comparison** - View differences in volume, pan, effects, and other settings
- **Copy settings** - Copy track settings (volume, pan, effects) between files
- **Visual highlighting** - Tracks with differences are highlighted in red
- **Save functionality** - Save modified files or export to new files
- **Project information** - View REAPER version, track count, and tempo

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/KristjanKruusRIA/rpp-editor.git
cd rpp-editor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

### Using pip (when published)

```bash
pip install rpp-editor
```

## Usage

### Running the Application

#### Using the installed package:
```bash
rpp-editor
```

#### Using the main script:
```bash
python main.py
```

#### From source:
```bash
python -m rpp_editor.gui
```

### Basic Workflow

1. **Load Files**: Click "Browse..." buttons to load two RPP files for comparison
2. **Compare Tracks**: View tracks side-by-side; differences are highlighted in red
3. **Master Track**: Master tracks appear at the top with 🎛️ icon and blue highlighting
4. **Select Tracks**: Click on tracks in either list to select them (including master tracks)
5. **View Differences**: The bottom panel shows detailed differences between selected tracks
6. **Copy Settings**: Use the copy buttons to transfer settings between tracks
   - Choose which settings to copy using checkboxes (Volume, Pan, Effects)
   - Works between: Master ↔ Master, Master ↔ Track, Track ↔ Track
7. **Save Changes**: Use File menu to save modified files

### Understanding the Interface

#### File Selection Panel
- Shows loaded file names and basic project information
- Displays REAPER version, track count, master FX status, and tempo

#### Track Comparison Panel
- **Left side**: Tracks from File 1
- **Right side**: Tracks from File 2
- **🎛️ Master tracks**: Blue highlighting with special icon
- **Red highlighting**: Indicates tracks with differences
- **Columns**: Track name, volume, pan, and effects list

#### Copy Controls Panel
- **Copy buttons**: Transfer settings between selected tracks
- **Checkboxes**: Choose which settings to copy
- **Differences panel**: Shows detailed comparison of selected tracks

## Development

### Project Structure

```
rpp-editor/
├── src/rpp_editor/          # Main package
│   ├── __init__.py          # Package initialization
│   ├── parser.py            # RPP file parsing logic
│   └── gui.py               # GUI application
├── tests/                   # Test suite
│   ├── conftest.py          # Test configuration
│   ├── test_parser.py       # Parser tests
│   └── test_integration.py  # Integration tests
├── examples/                # Example RPP files
│   ├── test1.rpp            # Example project 1
│   └── test2.rpp            # Example project 2
├── requirements.txt         # Dependencies
├── setup.py                 # Package setup
├── pytest.ini              # Test configuration
└── main.py                  # Entry point
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/rpp_editor --cov-report=html

# Run specific test file
pytest tests/test_parser.py -v
```

### Code Formatting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/
```

## Technical Details

### Dependencies

- **rpp**: Python library for parsing REAPER project files
- **attrs**: Data class decorators
- **tkinter**: GUI framework (included with Python)

### Supported Features

- **Track settings**: Volume (VOLPAN), pan, mute, solo
- **Master track**: Volume, pan, and complete effects chain (MASTERFXLIST)
- **Effects**: VST plugins, JS scripts, and other effects with complete metadata
- **Project info**: REAPER version, tempo, track count
- **File operations**: Load, save, save as with proper RPP format preservation

### Architecture

The application is built with a clean separation of concerns:

- **`parser.py`**: Core RPP parsing logic using the `rpp` library
- **`gui.py`**: Tkinter-based GUI with professional layout
- **`TrackInfo`**: Dataclass representing track information
- **Deep copying**: Ensures source files aren't modified during operations
- **Structure preservation**: Maintains exact REAPER project structure

## Troubleshooting

### Common Issues

1. **File not loading**: Ensure the RPP file is valid and not corrupted
2. **Missing effects**: Some effect types may not be fully supported
3. **Save errors**: Check file permissions and disk space

### Error Messages

- "Failed to load RPP file": File may be corrupted or in unsupported format
- "Failed to save file": Check write permissions to the target directory

## Limitations

- Currently focuses on VST and JS effects (DX and other formats may have limited support)
- Large projects with many tracks may take time to load
- Some advanced REAPER features may not be preserved during copy operations

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black src/ tests/ && isort src/ tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/KristjanKruusRIA/rpp-editor.git
cd rpp-editor
pip install -r requirements.txt
pip install -e .
pytest  # Run tests to ensure everything works
```

## License

This project uses the RPP library by Perlence, which is licensed under BSD-3-Clause.

## Changelog

### v1.0.0
- ✅ Complete master track support
- ✅ Structure-preserving effect copying
- ✅ Professional GUI with visual track differences
- ✅ Comprehensive test suite
- ✅ CI/CD pipeline with GitHub Actions