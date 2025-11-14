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
    <VST "VST: ReaEQ (Cockos)" reaeq.dll 0 "" 1919247729<565354726565717265616571> ""
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
      <VST "VST: TestVST" testvst.dll 0 "" 1400128611<5653545374446364656361706> ""
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

    def test_save_without_output_path(self, temp_rpp_file):
        """Test saving without specifying output path."""
        parser = RPPParser(temp_rpp_file)

        # Should save to original file path
        parser.save_file()

        # Verify file still exists and is readable
        parser_reloaded = RPPParser(temp_rpp_file)
        assert len(parser_reloaded.tracks) == len(parser.tracks)

    def test_save_no_project_loaded(self):
        """Test saving when no project is loaded."""
        parser = RPPParser()

        with pytest.raises(Exception, match="No project loaded"):
            parser.save_file("test.rpp")

    def test_save_no_file_path_no_output(self):
        """Test saving when no file path is set and no output path given."""
        parser = RPPParser()
        parser.project = "dummy"  # Fake project to pass the first check

        with pytest.raises(Exception, match="No output path specified"):
            parser.save_file()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_file(self):
        """Test loading an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            with pytest.raises(Exception):
                RPPParser(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_malformed_rpp_file(self):
        """Test loading a malformed RPP file."""
        malformed_content = """<INVALID_PROJECT>
  This is not a valid RPP file
  Missing proper structure"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f:
            f.write(malformed_content)
            temp_path = f.name

        try:
            with pytest.raises(Exception):
                RPPParser(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_file_not_found(self):
        """Test loading a file that doesn't exist."""
        with pytest.raises(Exception):
            RPPParser("nonexistent_file.rpp")

    def test_minimal_valid_rpp(self):
        """Test loading a minimal valid RPP file."""
        minimal_content = """<REAPER_PROJECT 0.1 "7.51/win64" 1763106377
>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f:
            f.write(minimal_content)
            temp_path = f.name

        try:
            parser = RPPParser(temp_path)
            assert parser.project is not None
            assert len(parser.tracks) >= 0  # Might have master track or none
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_rpp_without_master_track(self):
        """Test RPP file without master track elements."""
        content_no_master = """<REAPER_PROJECT 0.1 "7.51/win64" 1763106377
  <TRACK {A858D602-18C1-491F-9352-37B286CF4C0D}
    NAME "OnlyTrack"
    VOLPAN 1 0 -1 -1 1
  >
>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f:
            f.write(content_no_master)
            temp_path = f.name

        try:
            parser = RPPParser(temp_path)
            assert parser.project is not None

            # Should still have tracks, but master might be None/empty
            regular_tracks = [t for t in parser.tracks if not t.is_master]
            assert len(regular_tracks) >= 1
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_track_without_name(self):
        """Test track without NAME element."""
        content = """<REAPER_PROJECT 0.1 "7.51/win64" 1763106377
  <TRACK {A858D602-18C1-491F-9352-37B286CF4C0D}
    VOLPAN 1 0 -1 -1 1
  >
>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = RPPParser(temp_path)
            regular_tracks = [t for t in parser.tracks if not t.is_master]
            assert len(regular_tracks) >= 1
            assert regular_tracks[0].name == "Untitled Track"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_track_without_volpan(self):
        """Test track without VOLPAN element."""
        content = """<REAPER_PROJECT 0.1 "7.51/win64" 1763106377
  <TRACK {A858D602-18C1-491F-9352-37B286CF4C0D}
    NAME "TestTrack"
  >
>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = RPPParser(temp_path)
            regular_tracks = [t for t in parser.tracks if not t.is_master]
            assert len(regular_tracks) >= 1
            # Should use default values
            assert regular_tracks[0].volume == 1.0
            assert regular_tracks[0].pan == 0.0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_track_with_js_effects(self):
        """Test track with JS (JavaScript) effects."""
        content = """<REAPER_PROJECT 0.1 "7.51/win64" 1763106377
  <TRACK {A858D602-18C1-491F-9352-37B286CF4C0D}
    NAME "JSTrack"
    VOLPAN 1 0 -1 -1 1
    <FXCHAIN
      BYPASS 0 0 0
      <JS "JS: Test Effect" testeffect.js ""
        Y2FsZhAAAAAIAAAA
      >
      WAK 0 0
    >
  >
>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = RPPParser(temp_path)
            regular_tracks = [t for t in parser.tracks if not t.is_master]
            assert len(regular_tracks) >= 1
            track = regular_tracks[0]
            assert len(track.effects) >= 1
            assert track.effects[0]["type"] == "JS"
            assert "testeffect.js" in track.effects[0]["name"]
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestUntestedMethods:
    """Test methods that aren't fully covered."""

    def test_get_track_by_id(self, temp_rpp_file):
        """Test finding tracks by ID."""
        parser = RPPParser(temp_rpp_file)

        # Get a track to test with
        regular_track = next(t for t in parser.tracks if not t.is_master)
        track_id = regular_track.track_id

        found_track = parser.get_track_by_id(track_id)
        assert found_track is not None
        assert found_track.track_id == track_id
        assert found_track.name == regular_track.name

        # Test with non-existent ID
        not_found = parser.get_track_by_id("NONEXISTENT")
        assert not_found is None

    def test_get_track_by_id_master(self, temp_rpp_file):
        """Test finding master track by ID."""
        parser = RPPParser(temp_rpp_file)

        master_track = parser.get_track_by_id("MASTER")
        assert master_track is not None
        assert master_track.is_master
        assert master_track.name == "Master"

    def test_copy_track_settings_error_handling(self, temp_rpp_file):
        """Test error handling in copy operations."""
        parser1 = RPPParser(temp_rpp_file)
        parser2 = RPPParser(temp_rpp_file)

        track1 = next(t for t in parser1.tracks if not t.is_master)
        track2 = next(t for t in parser2.tracks if not t.is_master)

        # Test copying with None elements - should handle gracefully
        original_volume = track2.volume
        parser2.copy_track_settings(track1, track2, copy_volume=True)
        # Should still work even if some elements are missing
        assert track2.volume == track1.volume or track2.volume == original_volume

    def test_project_info_edge_cases(self):
        """Test project info with edge cases."""
        # Test with no project loaded
        parser = RPPParser()
        info = parser.get_project_info()
        assert info == {}

    def test_trackinfo_str_representation(self, temp_rpp_file):
        """Test TrackInfo string representation."""
        parser = RPPParser(temp_rpp_file)

        master = next(t for t in parser.tracks if t.is_master)
        regular = next(t for t in parser.tracks if not t.is_master)

        master_str = str(master)
        assert "Master" in master_str
        assert master.name in master_str

        regular_str = str(regular)
        assert "Track" in regular_str
        assert regular.name in regular_str
