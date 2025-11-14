"""
RPP Parser Module for REAPER Project Files
Provides functionality to parse, compare, and modify REAPER project files.
"""

import rpp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TrackInfo:
    """Contains information about a track in an RPP file."""
    track_id: str
    name: str
    volume: float
    pan: float
    mute: bool
    solo: bool
    effects: List[Dict[str, Any]]
    raw_element: Any  # The original rpp.Element for this track
    
    def __str__(self):
        return f"Track '{self.name}' (Vol: {self.volume:.2f}, Pan: {self.pan:.2f})"


class RPPParser:
    """Parser for REAPER project files using the rpp library."""
    
    def __init__(self, file_path: str = None):
        self.file_path = file_path
        self.project = None
        self.tracks = []
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path: str):
        """Load and parse an RPP file."""
        self.file_path = file_path
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.project = rpp.loads(content)
            self.tracks = self._parse_tracks()
            
        except Exception as e:
            raise Exception(f"Failed to load RPP file '{file_path}': {str(e)}")
    
    def _parse_tracks(self) -> List[TrackInfo]:
        """Parse all tracks from the project."""
        tracks = []
        
        if not self.project:
            return tracks
        
        # Find all TRACK elements
        track_elements = self.project.findall('.//TRACK')
        
        for track_element in track_elements:
            track_info = self._parse_single_track(track_element)
            if track_info:
                tracks.append(track_info)
        
        return tracks
    
    def _parse_single_track(self, track_element) -> Optional[TrackInfo]:
        """Parse a single track element."""
        try:
            # Extract track ID from the track element attributes
            track_id = track_element.attrib[0] if track_element.attrib else "Unknown"
            
            # Find track name
            name_element = track_element.find('./NAME')
            name = name_element[1] if name_element else "Untitled Track"
            
            # Parse VOLPAN (volume and pan information)
            volpan_element = track_element.find('./VOLPAN')
            volume = 1.0
            pan = 0.0
            
            if volpan_element:
                # VOLPAN format: VOLPAN volume pan -1 -1 1
                volume = float(volpan_element[1])
                pan = float(volpan_element[2])
            
            # Parse MUTESOLO (mute and solo information)
            mutesolo_element = track_element.find('./MUTESOLO')
            mute = False
            solo = False
            
            if mutesolo_element:
                # MUTESOLO format: MUTESOLO mute solo 0
                mute = bool(int(mutesolo_element[1]))
                solo = bool(int(mutesolo_element[2]))
            
            # Parse effects chain
            effects = self._parse_effects(track_element)
            
            return TrackInfo(
                track_id=track_id,
                name=name,
                volume=volume,
                pan=pan,
                mute=mute,
                solo=solo,
                effects=effects,
                raw_element=track_element
            )
            
        except Exception as e:
            print(f"Error parsing track: {e}")
            return None
    
    def _parse_effects(self, track_element) -> List[Dict[str, Any]]:
        """Parse effects from the FXCHAIN of a track."""
        effects = []
        
        fxchain_element = track_element.find('./FXCHAIN')
        if not fxchain_element:
            return effects
        
        # Find all VST elements in the FX chain
        vst_elements = fxchain_element.findall('.//VST')
        
        for vst_element in vst_elements:
            if len(vst_element.attrib) >= 2:
                effect_info = {
                    'type': 'VST',
                    'name': vst_element.attrib[1],  # VST name
                    'plugin_file': vst_element.attrib[2] if len(vst_element.attrib) > 2 else '',
                    'raw_element': vst_element
                }
                effects.append(effect_info)
        
        # Find other effect types (JS, DX, etc.)
        js_elements = fxchain_element.findall('.//JS')
        for js_element in js_elements:
            if len(js_element.attrib) >= 2:
                effect_info = {
                    'type': 'JS',
                    'name': js_element.attrib[1],
                    'raw_element': js_element
                }
                effects.append(effect_info)
        
        return effects
    
    def get_track_by_name(self, name: str) -> Optional[TrackInfo]:
        """Find a track by name."""
        for track in self.tracks:
            if track.name == name:
                return track
        return None
    
    def get_track_by_id(self, track_id: str) -> Optional[TrackInfo]:
        """Find a track by ID."""
        for track in self.tracks:
            if track.track_id == track_id:
                return track
        return None
    
    def copy_track_settings(self, source_track: TrackInfo, target_track: TrackInfo, 
                           copy_volume=True, copy_pan=True, copy_effects=True):
        """Copy settings from source track to target track."""
        
        if copy_volume or copy_pan:
            # Update VOLPAN element
            volpan_element = target_track.raw_element.find('./VOLPAN')
            if volpan_element:
                if copy_volume:
                    volpan_element[1] = str(source_track.volume)
                    target_track.volume = source_track.volume
                    
                if copy_pan:
                    volpan_element[2] = str(source_track.pan)
                    target_track.pan = source_track.pan
        
        if copy_effects:
            # Remove existing effects
            target_fxchain = target_track.raw_element.find('./FXCHAIN')
            source_fxchain = source_track.raw_element.find('./FXCHAIN')
            
            if target_fxchain and source_fxchain:
                # Clear existing VST/JS effects
                for vst in target_fxchain.findall('.//VST'):
                    target_fxchain.remove(vst)
                for js in target_fxchain.findall('.//JS'):
                    target_fxchain.remove(js)
                
                # Copy effects from source
                for vst in source_fxchain.findall('.//VST'):
                    target_fxchain.append(vst)
                for js in source_fxchain.findall('.//JS'):
                    target_fxchain.append(js)
                
                # Update track info
                target_track.effects = source_track.effects.copy()
    
    def save_file(self, output_path: str = None):
        """Save the modified project to a file."""
        if not self.project:
            raise Exception("No project loaded")
        
        if not output_path:
            output_path = self.file_path
        
        try:
            content = rpp.dumps(self.project)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Failed to save RPP file '{output_path}': {str(e)}")
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get general project information."""
        if not self.project:
            return {}
        
        info = {
            'version': self.project.attrib[0] if self.project.attrib else 'Unknown',
            'reaper_version': self.project.attrib[1] if len(self.project.attrib) > 1 else 'Unknown',
            'track_count': len(self.tracks),
            'tempo': 120  # Default
        }
        
        # Find tempo
        tempo_element = self.project.find('.//TEMPO')
        if tempo_element:
            info['tempo'] = float(tempo_element[1])
        
        return info


def compare_tracks(track1: TrackInfo, track2: TrackInfo) -> Dict[str, Dict[str, Any]]:
    """Compare two tracks and return differences."""
    differences = {}
    
    # Compare basic properties
    if track1.name != track2.name:
        differences['name'] = {'track1': track1.name, 'track2': track2.name}
    
    if abs(track1.volume - track2.volume) > 0.001:
        differences['volume'] = {'track1': track1.volume, 'track2': track2.volume}
    
    if abs(track1.pan - track2.pan) > 0.001:
        differences['pan'] = {'track1': track1.pan, 'track2': track2.pan}
    
    if track1.mute != track2.mute:
        differences['mute'] = {'track1': track1.mute, 'track2': track2.mute}
    
    if track1.solo != track2.solo:
        differences['solo'] = {'track1': track1.solo, 'track2': track2.solo}
    
    # Compare effects
    track1_effect_names = [fx['name'] for fx in track1.effects]
    track2_effect_names = [fx['name'] for fx in track2.effects]
    
    if track1_effect_names != track2_effect_names:
        differences['effects'] = {
            'track1': track1_effect_names,
            'track2': track2_effect_names
        }
    
    return differences


if __name__ == "__main__":
    # Test the parser with the example files
    try:
        parser1 = RPPParser("test1.rpp")
        parser2 = RPPParser("test2.rpp")
        
        print("=== Test1.rpp ===")
        for track in parser1.tracks:
            print(track)
            print(f"  Effects: {[fx['name'] for fx in track.effects]}")
        
        print("\n=== Test2.rpp ===")
        for track in parser2.tracks:
            print(track)
            print(f"  Effects: {[fx['name'] for fx in track.effects]}")
        
        # Compare tracks with same name
        if parser1.tracks and parser2.tracks:
            track1 = parser1.tracks[0]
            track2 = parser2.tracks[0]
            
            print(f"\n=== Comparing tracks ===")
            differences = compare_tracks(track1, track2)
            
            if differences:
                print("Differences found:")
                for key, values in differences.items():
                    print(f"  {key}: {values['track1']} vs {values['track2']}")
            else:
                print("No differences found")
                
    except Exception as e:
        print(f"Error: {e}")