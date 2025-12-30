"""
RPP Parser Module for REAPER Project Files
Provides functionality to parse, compare, and modify REAPER project files.
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import rpp


@dataclass
class EnvelopePoint:
    """Represents a single point in an envelope."""

    time: float
    value: float
    curve_type: int = 0
    tension: float = 0.0
    selected: bool = False


@dataclass
class Envelope:
    """Contains information about an envelope in an RPP file."""

    type: str  # "volume", "pan", or "parameter"
    name: str  # Human-readable name
    eguid: str  # Envelope GUID
    active: bool
    visible: bool
    armed: bool
    points: List[EnvelopePoint]
    parameter_info: Optional[str] = None  # For PARMENV, contains parameter details
    raw_element: Any = None  # The original rpp.Element


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
    volume_envelope: Optional[Envelope] = None
    pan_envelope: Optional[Envelope] = None
    parameter_envelopes: List[Envelope] = field(default_factory=list)  # VST parameter envelopes

    def __str__(self):
        prefix = "Master" if self.is_master else "Track"
        env_info = []
        if self.volume_envelope and self.volume_envelope.active:
            env_info.append("Vol Env")
        if self.pan_envelope and self.pan_envelope.active:
            env_info.append("Pan Env")
        if self.parameter_envelopes:
            active_param_envs = [e for e in self.parameter_envelopes if e.active]
            if active_param_envs:
                env_info.append(f"{len(active_param_envs)} Param Envs")

        env_str = f" [{', '.join(env_info)}]" if env_info else ""
        return f"{prefix} '{self.name}' (Vol: {self.volume:.2f}, Pan: {self.pan:.2f}){env_str}"


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

            # Parse master envelopes (these would be at project level if they exist)
            # Master doesn't typically have VOLENV2/PANENV2, but could have master parameter
            # envelopes
            parameter_envelopes = []
            masterfxlist_element = self.project.find(".//MASTERFXLIST")
            if masterfxlist_element:
                parameter_envelopes = self._parse_parameter_envelopes(masterfxlist_element)

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
                volume_envelope=None,  # Master typically doesn't have volume envelope
                pan_envelope=None,  # Master typically doesn't have pan envelope
                parameter_envelopes=parameter_envelopes,
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

        # Iterate through children in order to preserve effect sequence
        for child in masterfxlist_element.children:
            # Skip non-element children (lists representing settings/attributes)
            if not hasattr(child, "tag"):
                continue

            if child.tag == "VST" and len(child.attrib) >= 2:
                effect_info = {
                    "type": "VST",
                    "name": child.attrib[1],  # VST name
                    "plugin_file": (child.attrib[2] if len(child.attrib) > 2 else ""),
                    "raw_element": child,
                }
                effects.append(effect_info)
            elif child.tag == "JS":
                if len(child.attrib) >= 2:
                    # For JS effects, use the script path if the name is empty
                    js_name = child.attrib[1] if child.attrib[1].strip() else child.attrib[0]
                    effect_info = {
                        "type": "JS",
                        "name": js_name,
                        "raw_element": child,
                    }
                    effects.append(effect_info)
                elif len(child.attrib) >= 1:
                    # Handle case where only script path is provided
                    effect_info = {
                        "type": "JS",
                        "name": child.attrib[0],
                        "raw_element": child,
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

            # Parse envelopes
            volume_envelope = self._parse_volume_envelope(track_element)
            pan_envelope = self._parse_pan_envelope(track_element)

            # Parse parameter envelopes from FXCHAIN
            parameter_envelopes = []
            fxchain_element = track_element.find("./FXCHAIN")
            if fxchain_element:
                parameter_envelopes = self._parse_parameter_envelopes(fxchain_element)

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
                volume_envelope=volume_envelope,
                pan_envelope=pan_envelope,
                parameter_envelopes=parameter_envelopes,
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

        # Iterate through children in order to preserve effect sequence
        for child in fxchain_element.children:
            # Skip non-element children (lists representing settings/attributes)
            if not hasattr(child, "tag"):
                continue

            if child.tag == "VST" and len(child.attrib) >= 2:
                effect_info = {
                    "type": "VST",
                    "name": child.attrib[1],  # VST name
                    "plugin_file": (child.attrib[2] if len(child.attrib) > 2 else ""),
                    "raw_element": child,
                }
                effects.append(effect_info)
            elif child.tag == "JS":
                if len(child.attrib) >= 2:
                    # For JS effects, use the script path if the name is empty
                    js_name = child.attrib[1] if child.attrib[1].strip() else child.attrib[0]
                    effect_info = {
                        "type": "JS",
                        "name": js_name,
                        "raw_element": child,
                    }
                    effects.append(effect_info)
                elif len(child.attrib) >= 1:
                    # Handle case where only script path is provided
                    effect_info = {
                        "type": "JS",
                        "name": child.attrib[0],
                        "raw_element": child,
                    }
                    effects.append(effect_info)

        return effects

    def _parse_envelope_points(self, envelope_element) -> List[EnvelopePoint]:
        """Parse envelope points from PT entries."""
        points = []

        for child in envelope_element.children:
            if isinstance(child, list) and len(child) >= 3 and child[0] == "PT":
                try:
                    time = float(child[1])
                    value = float(child[2])
                    curve_type = int(child[3]) if len(child) > 3 else 0
                    tension = float(child[4]) if len(child) > 4 else 0.0
                    selected = bool(int(child[5])) if len(child) > 5 else False

                    point = EnvelopePoint(
                        time=time,
                        value=value,
                        curve_type=curve_type,
                        tension=tension,
                        selected=selected,
                    )
                    points.append(point)
                except (ValueError, IndexError):
                    # Skip malformed points
                    continue

        return points

    def _get_envelope_property(self, envelope_element, prop_name: str, default=None):
        """Get a property value from envelope element."""
        for child in envelope_element.children:
            if isinstance(child, list) and len(child) >= 2 and child[0] == prop_name:
                try:
                    if prop_name == "EGUID":
                        # Ensure EGUID is always returned as a string
                        eguid_value = str(child[1]).strip("{}")
                        return eguid_value
                    elif prop_name in ["ACT", "VIS", "ARM"]:
                        return child[1:]
                    else:
                        return child[1]
                except (ValueError, IndexError):
                    continue
        return default

    def _parse_volume_envelope(self, track_element) -> Optional[Envelope]:
        """Parse VOLENV2 from a track."""
        volenv_element = track_element.find("./VOLENV2")
        if not volenv_element:
            return None

        eguid = self._get_envelope_property(volenv_element, "EGUID", "")
        if not isinstance(eguid, str):
            eguid = str(eguid) if eguid is not None else ""
        act_data = self._get_envelope_property(volenv_element, "ACT", [0, -1])
        active = bool(int(act_data[0])) if act_data and len(act_data) > 0 else False

        vis_data = self._get_envelope_property(volenv_element, "VIS", [0, 1, 1])
        visible = bool(int(vis_data[0])) if vis_data and len(vis_data) > 0 else False

        arm_data = self._get_envelope_property(volenv_element, "ARM", [0])
        armed = bool(int(arm_data[0])) if arm_data and len(arm_data) > 0 else False

        points = self._parse_envelope_points(volenv_element)

        return Envelope(
            type="volume",
            name="Volume",
            eguid=eguid,
            active=active,
            visible=visible,
            armed=armed,
            points=points,
            raw_element=volenv_element,
        )

    def _parse_pan_envelope(self, track_element) -> Optional[Envelope]:
        """Parse PANENV2 from a track."""
        panenv_element = track_element.find("./PANENV2")
        if not panenv_element:
            return None

        eguid = self._get_envelope_property(panenv_element, "EGUID", "")
        if not isinstance(eguid, str):
            eguid = str(eguid) if eguid is not None else ""
        act_data = self._get_envelope_property(panenv_element, "ACT", [0, -1])
        active = bool(int(act_data[0])) if act_data and len(act_data) > 0 else False

        vis_data = self._get_envelope_property(panenv_element, "VIS", [0, 1, 1])
        visible = bool(int(vis_data[0])) if vis_data and len(vis_data) > 0 else False

        arm_data = self._get_envelope_property(panenv_element, "ARM", [0])
        armed = bool(int(arm_data[0])) if arm_data and len(arm_data) > 0 else False

        points = self._parse_envelope_points(panenv_element)

        return Envelope(
            type="pan",
            name="Pan",
            eguid=eguid,
            active=active,
            visible=visible,
            armed=armed,
            points=points,
            raw_element=panenv_element,
        )

    def _parse_parameter_envelopes(self, fxchain_element) -> List[Envelope]:
        """Parse PARMENV elements from an FXCHAIN."""
        envelopes = []

        for child in fxchain_element.children:
            if hasattr(child, "tag") and child.tag == "PARMENV":
                # Parse parameter info from attributes
                # Format: PARMENV 0:_Threshold 0 2 1 "Threshold / ReaComp"
                param_info = " ".join(child.attrib) if child.attrib else "Unknown Parameter"

                # Extract parameter name from the info
                param_name = "Unknown Parameter"
                if child.attrib and len(child.attrib) > 0:
                    # Try to extract readable name
                    first_part = child.attrib[0]
                    if ":" in first_part:
                        param_name = first_part.split(":", 1)[1].replace("_", " ").strip()

                    # If there's a quoted name at the end, use that
                    for attr in child.attrib:
                        if attr.startswith('"') and attr.endswith('"'):
                            param_name = attr.strip('"')
                            break

                eguid = self._get_envelope_property(child, "EGUID", "")
                if not isinstance(eguid, str):
                    eguid = str(eguid) if eguid is not None else ""
                act_data = self._get_envelope_property(child, "ACT", [0, -1])
                active = bool(int(act_data[0])) if act_data and len(act_data) > 0 else False

                vis_data = self._get_envelope_property(child, "VIS", [0, 1, 1])
                visible = bool(int(vis_data[0])) if vis_data and len(vis_data) > 0 else False

                arm_data = self._get_envelope_property(child, "ARM", [0])
                armed = bool(int(arm_data[0])) if arm_data and len(arm_data) > 0 else False

                points = self._parse_envelope_points(child)

                envelope = Envelope(
                    type="parameter",
                    name=param_name,
                    eguid=eguid,
                    active=active,
                    visible=visible,
                    armed=armed,
                    points=points,
                    parameter_info=param_info,
                    raw_element=child,
                )
                envelopes.append(envelope)

        return envelopes

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
        copy_envelopes=True,
    ):
        """Copy settings from source track to target track."""

        # Handle master track differently
        if target_track.is_master:
            self._copy_master_track_settings(
                source_track, target_track, copy_volume, copy_pan, copy_effects, copy_envelopes
            )
        elif source_track.is_master:
            # Can't copy from master to regular track directly, but we can copy some settings
            self._copy_from_master_to_track(
                source_track, target_track, copy_volume, copy_pan, copy_effects, copy_envelopes
            )
        else:
            # Regular track to track copy
            self._copy_regular_track_settings(
                source_track, target_track, copy_volume, copy_pan, copy_effects, copy_envelopes
            )

    def _copy_master_track_settings(
        self,
        source_track: TrackInfo,
        target_track: TrackInfo,
        copy_volume=True,
        copy_pan=True,
        copy_effects=True,
        copy_envelopes=True,
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

        if copy_envelopes:
            self._copy_envelopes(source_track, target_track)

    def _copy_from_master_to_track(
        self,
        source_track: TrackInfo,
        target_track: TrackInfo,
        copy_volume=True,
        copy_pan=True,
        copy_effects=True,
        copy_envelopes=True,
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

        if copy_envelopes:
            self._copy_envelopes(source_track, target_track)

    def _copy_regular_track_settings(
        self,
        source_track: TrackInfo,
        target_track: TrackInfo,
        copy_volume=True,
        copy_pan=True,
        copy_effects=True,
        copy_envelopes=True,
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

            if source_fxchain:
                # Create a deep copy of the source FXCHAIN
                new_fxchain = copy.deepcopy(source_fxchain)

                if target_fxchain:
                    # Replace existing FXCHAIN
                    track_children = target_track.raw_element.children
                    fxchain_index = track_children.index(target_fxchain)
                    track_children[fxchain_index] = new_fxchain
                else:
                    # Create new FXCHAIN if target doesn't have one
                    # Insert FXCHAIN after MAINSEND or at the end
                    track_children = target_track.raw_element.children
                    insert_index = len(track_children)

                    # Try to find MAINSEND to insert after it
                    for i, child in enumerate(track_children):
                        if hasattr(child, "tag") and child.tag == "MAINSEND":
                            insert_index = i + 1
                            break

                    track_children.insert(insert_index, new_fxchain)

                # Update track info
                target_track.effects = source_track.effects.copy()

        if copy_envelopes:
            self._copy_envelopes(source_track, target_track)

    def _copy_envelopes(self, source_track: TrackInfo, target_track: TrackInfo):
        """Copy envelope data from source track to target track."""
        import copy

        # Find and remove all existing envelope elements from target track
        envelope_types = ["VOLENV2", "PANENV2", "PARMENV"]
        for envelope_type in envelope_types:
            existing_envelopes = target_track.raw_element.findall(f"./{envelope_type}")
            for envelope in existing_envelopes:
                target_track.raw_element.children.remove(envelope)

        # Copy envelopes from source to target
        for envelope_type in envelope_types:
            source_envelopes = source_track.raw_element.findall(f"./{envelope_type}")
            for source_envelope in source_envelopes:
                # Create a deep copy of the envelope
                new_envelope = copy.deepcopy(source_envelope)
                # Add it to the target track
                target_track.raw_element.children.append(new_envelope)

        # Update the track info with copied envelope data
        target_track.volume_envelope = source_track.volume_envelope
        target_track.pan_envelope = source_track.pan_envelope
        if source_track.parameter_envelopes:
            target_track.parameter_envelopes = source_track.parameter_envelopes.copy()
        else:
            target_track.parameter_envelopes = []

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
            "has_master_effects": any(track.is_master and track.effects for track in self.tracks),
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

    # Compare envelopes
    def compare_envelope(env1, env2, env_name):
        """Compare two envelopes."""
        if env1 is None and env2 is None:
            return None
        if env1 is None or env2 is None:
            return {
                "track1": "Present" if env1 else "None",
                "track2": "Present" if env2 else "None",
            }

        # Compare envelope properties - return individual differences for flattening
        env_diffs = {}
        if env1.active != env2.active:
            env_diffs["active"] = {"track1": env1.active, "track2": env2.active}
        if len(env1.points) != len(env2.points):
            env_diffs["point_count"] = {"track1": len(env1.points), "track2": len(env2.points)}

        # Compare first and last point values if both have points
        if env1.points and env2.points:
            if abs(env1.points[0].value - env2.points[0].value) > 0.001:
                env_diffs["start_value"] = {
                    "track1": env1.points[0].value,
                    "track2": env2.points[0].value,
                }
            if abs(env1.points[-1].value - env2.points[-1].value) > 0.001:
                env_diffs["end_value"] = {
                    "track1": env1.points[-1].value,
                    "track2": env2.points[-1].value,
                }

        return env_diffs if env_diffs else None

    # Compare volume envelopes
    vol_env_diff = compare_envelope(track1.volume_envelope, track2.volume_envelope, "volume")
    if vol_env_diff:
        # Flatten nested envelope differences for GUI display
        if isinstance(vol_env_diff, dict) and "track1" in vol_env_diff and "track2" in vol_env_diff:
            differences["volume_envelope"] = vol_env_diff
        else:
            # Handle nested envelope properties
            for prop_name, prop_diff in vol_env_diff.items():
                differences[f"volume_envelope_{prop_name}"] = prop_diff

    # Compare pan envelopes
    pan_env_diff = compare_envelope(track1.pan_envelope, track2.pan_envelope, "pan")
    if pan_env_diff:
        # Flatten nested envelope differences for GUI display
        if isinstance(pan_env_diff, dict) and "track1" in pan_env_diff and "track2" in pan_env_diff:
            differences["pan_envelope"] = pan_env_diff
        else:
            # Handle nested envelope properties
            for prop_name, prop_diff in pan_env_diff.items():
                differences[f"pan_envelope_{prop_name}"] = prop_diff

    # Compare parameter envelopes
    track1_param_env_names = [env.name for env in track1.parameter_envelopes if env.active]
    track2_param_env_names = [env.name for env in track2.parameter_envelopes if env.active]

    if track1_param_env_names != track2_param_env_names:
        differences["parameter_envelopes"] = {
            "track1": track1_param_env_names,
            "track2": track2_param_env_names,
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
