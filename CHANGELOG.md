# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.3] - 2025-12-30

### Fixed
- **VST Effect Copying**: Fixed copying VST effects to tracks without existing FXCHAIN sections
  - Effects can now be copied to tracks that don't already have any effects
  - Resolves silent copy failures when target tracks lack FXCHAIN elements
  - Improved FXCHAIN creation and insertion logic for effect copying

## [1.1.2] - 2025-12-30

### Changed
- **File open dialog**: File open dialog remembers the last location instead of starting at the script root directory


## [1.1.1] - 2025-12-30

### Fixed
- **Track Comparison KeyError**: Fixed GUI crash when comparing tracks with envelope differences
  - Resolved `KeyError: 'track1'` that occurred during track comparison display
  - Flattened nested envelope difference structure to match GUI expectations
  - Added proper handling for envelope presence/absence differences

### Technical Details
- Modified `compare_envelope()` function to return flattened difference structures
- Updated envelope comparison logic to handle nested properties correctly
- All envelope differences now use consistent `{'track1': value, 'track2': value}` format
- Maintained backward compatibility with existing comparison functionality

## [1.1.0]

### Added
- **Comprehensive Envelope Support**: Added parsing and display for REAPER envelopes
  - Volume envelopes (VOLENV2)
  - Pan envelopes (PANENV2) 
  - VST parameter envelopes (PARMENV)
- **Envelope Copy Toggle**: Added envelope checkbox to "Copy Track Settings" GUI section
  - Users can now selectively copy envelopes between tracks
  - Works independently of volume, pan, and effects copy options
  - Supports all envelope types (volume, pan, parameter envelopes)
- **Enhanced Track Comparison**: Updated track comparison to include envelope information
- **Envelope Display Column**: Added envelopes column to track comparison view
  - Shows envelope counts and types for each track
  - Formats envelope information in readable format

### Fixed
- **JS Utility Parsing**: Fixed effect ordering issue where JS utilities appeared at end of effects chain instead of correct position
  - Effects now maintain their original order from the RPP file
  - Improved parsing of FXCHAIN elements to handle mixed children types
- **GUI Test Stability**: Fixed mocking issues in GUI tests that caused intermittent failures
  - Updated test setup to avoid accessing tree widget items during initialization
  - Improved error handling in widget tests

### Changed
- **Enhanced TrackInfo Class**: Extended with envelope-related fields
  - Added `volume_envelope`, `pan_envelope`, and `parameter_envelopes` attributes
  - Updated string representation to show envelope information
- **Parser Architecture**: Improved RPP parsing to handle envelope data structures
  - Added `EnvelopePoint` and `Envelope` dataclasses for structured envelope data
  - Enhanced track parsing methods with envelope extraction logic
- **GUI Layout**: Expanded copy settings section to accommodate envelope toggle
- **Documentation**: Updated README.md to document envelope functionality and features

### Technical Details
- Added `_parse_envelope_points()`, `_parse_volume_envelope()`, `_parse_pan_envelope()`, and `_parse_parameter_envelopes()` methods
- Implemented `_copy_envelopes()` helper method for envelope copying between tracks
- Enhanced all copy methods (`_copy_master_track_settings()`, `_copy_from_master_to_track()`, `_copy_regular_track_settings()`) to support envelope copying
- Added `_format_envelope_info()` helper method for GUI envelope display
- Updated `compare_tracks()` function to include envelope comparison logic

### Developer Notes
- All existing tests continue to pass (81 tests total)
- Added comprehensive envelope parsing with support for envelope points, activation states, and parameter information
- Envelope copying preserves all envelope properties including GUID, activation state, and point data
- GUI envelope toggle defaults to enabled (checked) for new copy operations

## [1.0.0] - 2025-12-29

### Added
- Complete master track support
- Structure-preserving effect copying
- Professional GUI with visual track differences
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions