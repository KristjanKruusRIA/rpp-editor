# RPP Editor - REAPER Project File Editor

A GUI application for editing and comparing REAPER project files (.rpp). This tool allows you to load two RPP files, compare their tracks, and copy settings between them.

## Features

- **Load and compare two RPP files** - Side-by-side comparison of track settings
- **Track comparison** - View differences in volume, pan, effects, and other settings
- **Copy settings** - Copy track settings (volume, pan, effects) between files
- **Visual highlighting** - Tracks with differences are highlighted in red
- **Save functionality** - Save modified files or export to new files
- **Project information** - View REAPER version, track count, and tempo

## Installation

1. Make sure you have Python 3.7+ installed
2. Install required dependencies:
```bash
pip install rpp attrs
```

## Usage

### Running the Application

```bash
python rpp_editor_gui.py
```

### Basic Workflow

1. **Load Files**: Click "Browse..." buttons to load two RPP files for comparison
2. **Compare Tracks**: View tracks side-by-side; differences are highlighted in red
3. **Select Tracks**: Click on tracks in either list to select them
4. **View Differences**: The bottom panel shows detailed differences between selected tracks
5. **Copy Settings**: Use the copy buttons to transfer settings between tracks
   - Choose which settings to copy using checkboxes (Volume, Pan, Effects)
6. **Save Changes**: Use File menu to save modified files

### Understanding the Interface

#### File Selection Panel
- Shows loaded file names and basic project information
- Displays REAPER version, track count, and tempo

#### Track Comparison Panel
- **Left side**: Tracks from File 1
- **Right side**: Tracks from File 2
- **Red highlighting**: Indicates tracks with differences
- **Columns**: Track name, volume, pan, and effects list

#### Copy Controls Panel
- **Copy buttons**: Transfer settings between selected tracks
- **Checkboxes**: Choose which settings to copy
- **Differences panel**: Shows detailed comparison of selected tracks

### Example Files

The application includes two example files:
- `test1.rpp` - Track with Decapitator plugin, volume = 1.0
- `test2.rpp` - Same track with AVOX SYBIL plugin, volume = 0.79

## Technical Details

### Dependencies

- **rpp**: Python library for parsing REAPER project files
- **attrs**: Data class decorators
- **tkinter**: GUI framework (included with Python)

### File Structure

- `rpp_editor_gui.py` - Main GUI application
- `rpp_parser.py` - RPP file parsing and manipulation module
- `test1.rpp`, `test2.rpp` - Example REAPER project files

### Supported Features

- **Track settings**: Volume (VOLPAN), pan, mute, solo
- **Effects**: VST plugins, JS scripts, and other effects
- **Project info**: REAPER version, tempo, track count
- **File operations**: Load, save, save as

## Troubleshooting

### Common Issues

1. **File not loading**: Ensure the RPP file is valid and not corrupted
2. **Missing effects**: Some effect types may not be fully supported
3. **Save errors**: Check file permissions and disk space

### Error Messages

- "Failed to load RPP file": File may be corrupted or in unsupported format
- "Failed to save file": Check write permissions to the target directory

## Limitations

- Currently supports VST and JS effects (DX and other formats may have limited support)
- Large projects with many tracks may take time to load
- Some advanced REAPER features may not be preserved during copy operations

## License

This project uses the RPP library by Perlence, which is licensed under BSD-3-Clause.

## Contributing

Feel free to report issues or suggest improvements. The codebase is designed to be extensible for additional RPP file manipulation features.