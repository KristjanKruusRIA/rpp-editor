"""
Tests for the RPP parser functionality
"""

import os
import tempfile

import pytest

from rpp_editor import RPPParser, TrackInfo, compare_tracks


@pytest.fixture
def sample_rpp_content():
    """Create a minimal RPP file content for testing."""
    return """<REAPER_PROJECT 0.1 "7.51/win64" 1763106377
  RIPPLE 0 0
  GROUPOVERRIDE 0 0 0 0
  MASTER_VOLUME 1 0 -1 -1 1
  MASTER_PANMODE 3
  MASTER_FX 1
  MASTER_SEL 0
  <MASTERFXLIST
    WNDRECT 24 52 655 408
    SHOW 0
    LASTSEL 0
    DOCKED 0
    BYPASS 0 0 0
    <VST "VST: ReaEQ (Cockos)" reaeq.dll 0 "" 1919247729<56535472656571726561657100000000> ""
      Y2FsZhAAAAAIAAAA
    >
    PRESETNAME "Test Preset"
    FLOATPOS 0 0 0 0
    FXID {1DDC23AB-175A-448B-80E8-87404426DE3A}
    WAK 0 0
  >
  <TRACK {A858D602-18C1-491F-9352-37B286CF4C0D}
    NAME "Track1"
    PEAKCOL 16576
    BEAT -1
    AUTOMODE 0
    PANLAWFLAGS 3
    VOLPAN 1 0 -1 -1 1
    MUTESOLO 0 0 0
    IPHASE 0
    PLAYOFFS 0 1
    ISBUS 0 0
    BUSCOMP 0 0 0 0 0
    SHOWINMIX 1 0.6667 0.5 1 0.5 0 0 0 0
    SEL 1
    REC 0 0 1 0 0 0 0 0
    VU 2
    TRACKHEIGHT 0 0 0 0 0 0 0
    INQ 0 0 0 0.5 100 0 0 100
    NCHAN 2
    FX 1
    TRACKID {A858D602-18C1-491F-9352-37B286CF4C0D}
    PERF 0
    MIDIOUT -1
    MAINSEND 1 0
    <FXCHAIN
      WNDRECT 24 52 655 408
      SHOW 0
      LASTSEL 0
      DOCKED 0
      BYPASS 0 0 0
      <VST "VST: TestVST" testvst.dll 0 "" 1400128611<56535453744463646563617069746174> ""
        Y0R0U+5e7f4CAAAAAQAAAAAAAAACAAAAAAAAAAIAAAABAAAAAAAAAAIAAAAAAAAAYwIAAAEAAAAAAAAA
      >
      PRESETNAME Default
      FLOATPOS 0 0 0 0
      FXID {CBA383BD-5FD2-496D-B99B-DCBE859881DA}
      WAK 0 0
    >
  >
  <EXTENSIONS
  >
>"""


@pytest.fixture
def temp_rpp_file(sample_rpp_content):
    """Create a temporary RPP file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f:
        f.write(sample_rpp_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestRPPParser:
    """Test cases for the RPP parser."""

    def test_parser_initialization(self):
        """Test that parser initializes correctly."""
        parser = RPPParser()
        assert parser.file_path is None
        assert parser.project is None
        assert parser.tracks == []

    def test_load_file(self, temp_rpp_file):
        """Test loading an RPP file."""
        parser = RPPParser(temp_rpp_file)

        assert parser.file_path == temp_rpp_file
        assert parser.project is not None
        assert len(parser.tracks) >= 1  # At least master track

    def test_master_track_parsing(self, temp_rpp_file):
        """Test that master track is parsed correctly."""
        parser = RPPParser(temp_rpp_file)

        master_tracks = [t for t in parser.tracks if t.is_master]
        assert len(master_tracks) == 1

        master = master_tracks[0]
        assert master.name == "Master"
        assert master.track_id == "MASTER"
        assert master.volume == 1.0
        assert master.pan == 0.0
        assert len(master.effects) > 0

    def test_regular_track_parsing(self, temp_rpp_file):
        """Test that regular tracks are parsed correctly."""
        parser = RPPParser(temp_rpp_file)

        regular_tracks = [t for t in parser.tracks if not t.is_master]
        assert len(regular_tracks) >= 1

        track = regular_tracks[0]
        assert track.name == "Track1"
        assert not track.is_master
        assert track.volume == 1.0
        assert track.pan == 0.0

    def test_effects_parsing(self, temp_rpp_file):
        """Test that effects are parsed correctly."""
        parser = RPPParser(temp_rpp_file)

        # Test master effects
        master = next(t for t in parser.tracks if t.is_master)
        assert len(master.effects) > 0
        assert master.effects[0]["type"] == "VST"
        assert "reaeq.dll" in master.effects[0]["name"]

        # Test regular track effects
        regular_track = next(t for t in parser.tracks if not t.is_master)
        assert len(regular_track.effects) > 0
        assert regular_track.effects[0]["type"] == "VST"
        assert "testvst.dll" in regular_track.effects[0]["name"]

    def test_project_info(self, temp_rpp_file):
        """Test project information extraction."""
        parser = RPPParser(temp_rpp_file)
        info = parser.get_project_info()

        assert "version" in info
        assert "track_count" in info
        assert "total_track_count" in info
        assert "has_master_effects" in info
        assert info["has_master_effects"] is True
        assert info["total_track_count"] > info["track_count"]  # Master track included

    def test_find_track_by_name(self, temp_rpp_file):
        """Test finding tracks by name."""
        parser = RPPParser(temp_rpp_file)

        master = parser.get_track_by_name("Master")
        assert master is not None
        assert master.is_master

        track1 = parser.get_track_by_name("Track1")
        assert track1 is not None
        assert not track1.is_master

        nonexistent = parser.get_track_by_name("NonexistentTrack")
        assert nonexistent is None


class TestTrackComparison:
    """Test cases for track comparison functionality."""

    def test_compare_identical_tracks(self, temp_rpp_file):
        """Test comparing identical tracks."""
        parser = RPPParser(temp_rpp_file)
        track1 = parser.tracks[0]
        track2 = parser.tracks[0]  # Same track

        differences = compare_tracks(track1, track2)
        assert len(differences) == 0

    def test_compare_different_volumes(self, temp_rpp_file):
        """Test comparing tracks with different volumes."""
        parser = RPPParser(temp_rpp_file)
        track1 = parser.tracks[0]

        # Create a modified copy
        track2 = TrackInfo(
            track_id=track1.track_id,
            name=track1.name,
            volume=0.5,  # Different volume
            pan=track1.pan,
            mute=track1.mute,
            solo=track1.solo,
            effects=track1.effects,
            raw_element=track1.raw_element,
            is_master=track1.is_master,
        )

        differences = compare_tracks(track1, track2)
        assert "volume" in differences
        assert differences["volume"]["track1"] == track1.volume
        assert differences["volume"]["track2"] == track2.volume


class TestTrackCopying:
    """Test cases for track copying functionality."""

    def test_copy_between_regular_tracks(self, temp_rpp_file):
        """Test copying settings between regular tracks."""
        parser1 = RPPParser(temp_rpp_file)
        parser2 = RPPParser(temp_rpp_file)

        # Get regular tracks
        track1 = next(t for t in parser1.tracks if not t.is_master)
        track2 = next(t for t in parser2.tracks if not t.is_master)

        original_volume = track2.volume
        track1.volume = 0.5  # Modify source

        # Copy volume only
        parser2.copy_track_settings(
            track1, track2, copy_volume=True, copy_pan=False, copy_effects=False
        )

        assert track2.volume == 0.5
        assert track2.volume != original_volume

    def test_copy_master_to_regular(self, temp_rpp_file):
        """Test copying from master track to regular track."""
        parser1 = RPPParser(temp_rpp_file)
        parser2 = RPPParser(temp_rpp_file)

        master = next(t for t in parser1.tracks if t.is_master)
        regular = next(t for t in parser2.tracks if not t.is_master)

        master_effects = len(master.effects)

        # Copy effects from master to regular track
        parser2.copy_track_settings(
            master, regular, copy_effects=True, copy_volume=False, copy_pan=False
        )

        # Should have master's effects
        assert len(regular.effects) == master_effects
        assert regular.effects[0]["name"] == master.effects[0]["name"]

    def test_copy_regular_to_master(self, temp_rpp_file):
        """Test copying from regular track to master track."""
        parser1 = RPPParser(temp_rpp_file)
        parser2 = RPPParser(temp_rpp_file)

        regular = next(t for t in parser1.tracks if not t.is_master)
        master = next(t for t in parser2.tracks if t.is_master)

        original_effects = master.effects[0]["name"]
        regular_effects = regular.effects[0]["name"]

        # Copy effects from regular to master track
        parser2.copy_track_settings(
            regular, master, copy_effects=True, copy_volume=False, copy_pan=False
        )

        # Should have regular track's effects
        assert master.effects[0]["name"] == regular_effects
        assert master.effects[0]["name"] != original_effects


class TestFileSaving:
    """Test cases for file saving functionality."""

    def test_save_and_reload(self, temp_rpp_file):
        """Test saving and reloading a file."""
        # Load the file
        parser = RPPParser(temp_rpp_file)
        original_track_count = len(parser.tracks)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as temp_save:
            save_path = temp_save.name

        try:
            parser.save_file(save_path)

            # Reload and verify structure is preserved
            parser_reloaded = RPPParser(save_path)

            assert len(parser_reloaded.tracks) == original_track_count

            # Verify the master track is preserved
            master_original = next(t for t in parser.tracks if t.is_master)
            master_reloaded = next(t for t in parser_reloaded.tracks if t.is_master)
            assert master_original.name == master_reloaded.name
            assert master_original.volume == master_reloaded.volume

            # Verify regular tracks are preserved
            regular_original = next(t for t in parser.tracks if not t.is_master)
            regular_reloaded = next(t for t in parser_reloaded.tracks if not t.is_master)
            assert regular_original.name == regular_reloaded.name
            assert regular_original.volume == regular_reloaded.volume
        finally:
            if os.path.exists(save_path):
                os.unlink(save_path)
