"""
RPP Parser Module for REAPER Project Files
Provides functionality to parse, compare, and modify REAPER project files.
"""

import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import rpp


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
    is_master: bool = False  # True if this is the master track

    def __str__(self):
        prefix = "Master" if self.is_master else "Track"
        return f"{prefix} '{self.name}' (Vol: {self.volume:.2f}, Pan: {self.pan:.2f})"


class RPPParser:
    """Parser for REAPER project files using the rpp library."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path: Optional[str] = file_path
        self.project: Optional[Any] = None
        self.tracks: List[TrackInfo] = []

        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        """Load and parse an RPP file."""
        self.file_path = file_path

        try:
            with open(file_path, "r", encoding="utf-8") as f:
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

        # Parse master track first
        master_track = self._parse_master_track()
        if master_track:
            tracks.append(master_track)

        # Find all regular TRACK elements
        track_elements = self.project.findall(".//TRACK")

        for track_element in track_elements:
            track_info = self._parse_single_track(track_element)
            if track_info:
                tracks.append(track_info)

        return tracks

    def _parse_master_track(self) -> Optional[TrackInfo]:
        """Parse the master track."""
        if not self.project:
            return None

        try:
            # Master track doesn't have a TRACK element, we get data directly from project root

            # Parse MASTER_VOLUME (volume and pan information)
            master_volume_element = self.project.find(".//MASTER_VOLUME")
            volume = 1.0
            pan = 0.0

            if master_volume_element:
                # MASTER_VOLUME format: MASTER_VOLUME volume pan -1 -1 1
                volume = float(master_volume_element[1])
                pan = float(master_volume_element[2])

            # Parse MASTERMUTESOLO (mute and solo information)
            mastermutesolo_element = self.project.find(".//MASTERMUTESOLO")
            mute = False
            solo = False

            if mastermutesolo_element:
                # MASTERMUTESOLO format: MASTERMUTESOLO mute
                mute = bool(int(mastermutesolo_element[1]))
                # Master track doesn't have solo, but we keep the field for consistency

            # Parse master effects from MASTERFXLIST
            effects = self._parse_master_effects()

            return TrackInfo(
                track_id="MASTER",
                name="Master",
                volume=volume,
                pan=pan,
                mute=mute,
                solo=solo,
                effects=effects,
                raw_element=self.project,  # Use the project root as the raw element
                is_master=True,
            )

        except Exception as e:
            print(f"Error parsing master track: {e}")
            return None

    def _parse_master_effects(self) -> List[Dict[str, Any]]:
        """Parse effects from the MASTERFXLIST."""
        effects = []

        if not self.project:
            return effects

        masterfxlist_element = self.project.find(".//MASTERFXLIST")
        if not masterfxlist_element:
            return effects

        # Find all VST elements in the master FX list
        vst_elements = masterfxlist_element.findall(".//VST")

        for vst_element in vst_elements:
            if len(vst_element.attrib) >= 2:
                effect_info = {
                    "type": "VST",
                    "name": vst_element.attrib[1],  # VST name
                    "plugin_file": (
                        vst_element.attrib[2] if len(vst_element.attrib) > 2 else ""
                    ),
                    "raw_element": vst_element,
                }
                effects.append(effect_info)

        # Find other effect types (JS, DX, etc.)
        js_elements = masterfxlist_element.findall(".//JS")
        for js_element in js_elements:
            if len(js_element.attrib) >= 2:
                effect_info = {
                    "type": "JS",
                    "name": js_element.attrib[1],
                    "raw_element": js_element,
                }
                effects.append(effect_info)

        return effects

    def _parse_single_track(self, track_element) -> Optional[TrackInfo]:
        """Parse a single track element."""
        try:
            # Extract track ID from the track element attributes
            track_id = track_element.attrib[0] if track_element.attrib else "Unknown"

            # Find track name
            name_element = track_element.find("./NAME")
            name = name_element[1] if name_element else "Untitled Track"

            # Parse VOLPAN (volume and pan information)
            volpan_element = track_element.find("./VOLPAN")
            volume = 1.0
            pan = 0.0

            if volpan_element:
                # VOLPAN format: VOLPAN volume pan -1 -1 1
                volume = float(volpan_element[1])
                pan = float(volpan_element[2])

            # Parse MUTESOLO (mute and solo information)
            mutesolo_element = track_element.find("./MUTESOLO")
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
                raw_element=track_element,
                is_master=False,
            )

        except Exception as e:
            print(f"Error parsing track: {e}")
            return None

    def _parse_effects(self, track_element) -> List[Dict[str, Any]]:
        """Parse effects from the FXCHAIN of a track."""
        effects = []

        fxchain_element = track_element.find("./FXCHAIN")
        if not fxchain_element:
            return effects

        # Find all VST elements in the FX chain
        vst_elements = fxchain_element.findall(".//VST")

        for vst_element in vst_elements:
            if len(vst_element.attrib) >= 2:
                effect_info = {
                    "type": "VST",
                    "name": vst_element.attrib[1],  # VST name
                    "plugin_file": (
                        vst_element.attrib[2] if len(vst_element.attrib) > 2 else ""
                    ),
                    "raw_element": vst_element,
                }
                effects.append(effect_info)

        # Find other effect types (JS, DX, etc.)
        js_elements = fxchain_element.findall(".//JS")
        for js_element in js_elements:
            if len(js_element.attrib) >= 2:
                effect_info = {
                    "type": "JS",
                    "name": js_element.attrib[1],
                    "raw_element": js_element,
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

    def copy_track_settings(
        self,
        source_track: TrackInfo,
        target_track: TrackInfo,
        copy_volume=True,
        copy_pan=True,
        copy_effects=True,
    ):
        """Copy settings from source track to target track."""

        # Handle master track differently
        if target_track.is_master:
            self._copy_master_track_settings(
                source_track, target_track, copy_volume, copy_pan, copy_effects
            )
        elif source_track.is_master:
            # Can't copy from master to regular track directly, but we can copy some settings
            self._copy_from_master_to_track(
                source_track, target_track, copy_volume, copy_pan, copy_effects
            )
        else:
            # Regular track to track copy
            self._copy_regular_track_settings(
                source_track, target_track, copy_volume, copy_pan, copy_effects
            )

    def _copy_master_track_settings(
        self,
        source_track: TrackInfo,
        target_track: TrackInfo,
        copy_volume=True,
        copy_pan=True,
        copy_effects=True,
    ):
        """Copy settings to master track."""

        if copy_volume or copy_pan:
            # Update MASTER_VOLUME element
            master_volume_element = target_track.raw_element.find(".//MASTER_VOLUME")
            if master_volume_element:
                if copy_volume:
                    master_volume_element[1] = str(source_track.volume)
                    target_track.volume = source_track.volume

                if copy_pan:
                    master_volume_element[2] = str(source_track.pan)
                    target_track.pan = source_track.pan

        if copy_effects:
            # Replace the entire MASTERFXLIST
            target_masterfxlist = target_track.raw_element.find(".//MASTERFXLIST")
            if source_track.is_master:
                source_masterfxlist = source_track.raw_element.find(".//MASTERFXLIST")
            else:
                # Source is regular track, get FXCHAIN
                source_masterfxlist = source_track.raw_element.find("./FXCHAIN")

            if target_masterfxlist and source_masterfxlist:
                # Create a deep copy of the source effects list
                new_masterfxlist = copy.deepcopy(source_masterfxlist)

                # If copying from regular track to master, we need to rename FXCHAIN to MASTERFXLIST
                if not source_track.is_master:
                    new_masterfxlist.tag = "MASTERFXLIST"

                # Find the index of the target MASTERFXLIST in the project
                project_children = target_track.raw_element.children
                masterfxlist_index = project_children.index(target_masterfxlist)

                # Replace the old MASTERFXLIST with the new one
                project_children[masterfxlist_index] = new_masterfxlist

                # Update track info
                target_track.effects = source_track.effects.copy()

    def _copy_from_master_to_track(
        self,
        source_track: TrackInfo,
        target_track: TrackInfo,
        copy_volume=True,
        copy_pan=True,
        copy_effects=True,
    ):
        """Copy settings from master track to regular track."""

        if copy_volume or copy_pan:
            # Update VOLPAN element
            volpan_element = target_track.raw_element.find("./VOLPAN")
            if volpan_element:
                if copy_volume:
                    volpan_element[1] = str(source_track.volume)
                    target_track.volume = source_track.volume

                if copy_pan:
                    volpan_element[2] = str(source_track.pan)
                    target_track.pan = source_track.pan

        if copy_effects:
            # Copy from MASTERFXLIST to FXCHAIN
            target_fxchain = target_track.raw_element.find("./FXCHAIN")
            source_masterfxlist = source_track.raw_element.find(".//MASTERFXLIST")

            if target_fxchain and source_masterfxlist:
                # Create a deep copy and rename to FXCHAIN
                new_fxchain = copy.deepcopy(source_masterfxlist)
                new_fxchain.tag = "FXCHAIN"

                # Find the index of the target FXCHAIN in the track
                track_children = target_track.raw_element.children
                fxchain_index = track_children.index(target_fxchain)

                # Replace the old FXCHAIN with the new one
                track_children[fxchain_index] = new_fxchain

                # Update track info
                target_track.effects = source_track.effects.copy()

    def _copy_regular_track_settings(
        self,
        source_track: TrackInfo,
        target_track: TrackInfo,
        copy_volume=True,
        copy_pan=True,
        copy_effects=True,
    ):
        """Copy settings between regular tracks."""

        if copy_volume or copy_pan:
            # Update VOLPAN element
            volpan_element = target_track.raw_element.find("./VOLPAN")
            if volpan_element:
                if copy_volume:
                    volpan_element[1] = str(source_track.volume)
                    target_track.volume = source_track.volume

                if copy_pan:
                    volpan_element[2] = str(source_track.pan)
                    target_track.pan = source_track.pan

        if copy_effects:
            # Replace the entire FXCHAIN to preserve correct structure
            target_fxchain = target_track.raw_element.find("./FXCHAIN")
            source_fxchain = source_track.raw_element.find("./FXCHAIN")

            if target_fxchain and source_fxchain:
                # Create a deep copy of the source FXCHAIN
                new_fxchain = copy.deepcopy(source_fxchain)

                # Find the index of the target FXCHAIN in the track
                track_children = target_track.raw_element.children
                fxchain_index = track_children.index(target_fxchain)

                # Replace the old FXCHAIN with the new one
                track_children[fxchain_index] = new_fxchain

                # Update track info
                target_track.effects = source_track.effects.copy()

    def save_file(self, output_path: Optional[str] = None):
        """Save the modified project to a file."""
        if not self.project:
            raise Exception("No project loaded")

        if not output_path:
            if not self.file_path:
                raise Exception("No output path specified and no file path set")
            output_path = self.file_path

        try:
            content = rpp.dumps(self.project)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Failed to save RPP file '{output_path}': {str(e)}")

    def get_project_info(self) -> Dict[str, Any]:
        """Get general project information."""
        if not self.project:
            return {}

        # Count regular tracks (excluding master)
        regular_tracks = [track for track in self.tracks if not track.is_master]

        info = {
            "version": self.project.attrib[0] if self.project.attrib else "Unknown",
            "reaper_version": (
                self.project.attrib[1] if len(self.project.attrib) > 1 else "Unknown"
            ),
            "track_count": len(regular_tracks),
            "total_track_count": len(self.tracks),  # Including master
            "has_master_effects": any(
                track.is_master and track.effects for track in self.tracks
            ),
            "tempo": 120,  # Default
        }

        # Find tempo
        tempo_element = self.project.find(".//TEMPO")
        if tempo_element:
            info["tempo"] = float(tempo_element[1])

        return info


def compare_tracks(track1: TrackInfo, track2: TrackInfo) -> Dict[str, Dict[str, Any]]:
    """Compare two tracks and return differences."""
    differences = {}

    # Compare basic properties
    if track1.name != track2.name:
        differences["name"] = {"track1": track1.name, "track2": track2.name}

    if abs(track1.volume - track2.volume) > 0.001:
        differences["volume"] = {"track1": track1.volume, "track2": track2.volume}

    if abs(track1.pan - track2.pan) > 0.001:
        differences["pan"] = {"track1": track1.pan, "track2": track2.pan}

    if track1.mute != track2.mute:
        differences["mute"] = {"track1": track1.mute, "track2": track2.mute}

    if track1.solo != track2.solo:
        differences["solo"] = {"track1": track1.solo, "track2": track2.solo}

    # Compare effects
    track1_effect_names = [fx["name"] for fx in track1.effects]
    track2_effect_names = [fx["name"] for fx in track2.effects]

    if track1_effect_names != track2_effect_names:
        differences["effects"] = {
            "track1": track1_effect_names,
            "track2": track2_effect_names,
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

        # Compare master tracks
        master1 = next((t for t in parser1.tracks if t.is_master), None)
        master2 = next((t for t in parser2.tracks if t.is_master), None)

        if master1 and master2:
            print("\n=== Comparing master tracks ===")
            differences = compare_tracks(master1, master2)

            if differences:
                print("Master track differences found:")
                for key, values in differences.items():
                    print(f"  {key}: {values['track1']} vs {values['track2']}")
            else:
                print("No master track differences found")

        # Compare regular tracks with same name
        regular1 = [t for t in parser1.tracks if not t.is_master]
        regular2 = [t for t in parser2.tracks if not t.is_master]

        if regular1 and regular2:
            track1 = regular1[0]
            track2 = regular2[0]

            print("\n=== Comparing regular tracks ===")
            differences = compare_tracks(track1, track2)

            if differences:
                print("Regular track differences found:")
                for key, values in differences.items():
                    print(f"  {key}: {values['track1']} vs {values['track2']}")
            else:
                print("No regular track differences found")

    except Exception as e:
        print(f"Error: {e}")
