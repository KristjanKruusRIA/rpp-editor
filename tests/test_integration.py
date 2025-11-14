"""
Integration tests for the complete RPP editor functionality
"""

import tempfile
import os

from rpp_editor import RPPParser


class TestIntegration:
    """Integration tests for the complete application."""

    def test_end_to_end_workflow(self):
        """Test a complete end-to-end workflow."""
        # Create two simple RPP files
        rpp_content_1 = """<REAPER_PROJECT 0.1 "7.51/win64" 1763106377
  MASTER_VOLUME 1 0 -1 -1 1
  <MASTERFXLIST
    BYPASS 0 0 0
    <VST "VST: Effect1" effect1.dll 0 "" 123456789 ""
      Y2FsZhAAAAAIAAAA
    >
    WAK 0 0
  >
  <TRACK {A858D602-18C1-491F-9352-37B286CF4C0D}
    NAME "TestTrack"
    VOLPAN 0.8 0 -1 -1 1
    <FXCHAIN
      BYPASS 0 0 0
      <VST "VST: TrackEffect1" trackeffect1.dll 0 "" 987654321 ""
        Y2FsZhAAAAAIAAAA
      >
      WAK 0 0
    >
  >
>"""

        rpp_content_2 = """<REAPER_PROJECT 0.1 "7.51/win64" 1763106377
  MASTER_VOLUME 1 0 -1 -1 1
  <MASTERFXLIST
    BYPASS 0 0 0
    <VST "VST: Effect2" effect2.dll 0 "" 111111111 ""
      Y2FsZhAAAAAIAAAA
    >
    WAK 0 0
  >
  <TRACK {A858D602-18C1-491F-9352-37B286CF4C0D}
    NAME "TestTrack"
    VOLPAN 0.6 0.2 -1 -1 1
    <FXCHAIN
      BYPASS 0 0 0
      <VST "VST: TrackEffect2" trackeffect2.dll 0 "" 222222222 ""
        Y2FsZhAAAAAIAAAA
      >
      WAK 0 0
    >
  >
>"""

        # Create temporary files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f1:
            f1.write(rpp_content_1)
            file1_path = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f2:
            f2.write(rpp_content_2)
            file2_path = f2.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rpp", delete=False) as f3:
            output_path = f3.name

        try:
            # Load both files
            parser1 = RPPParser(file1_path)
            parser2 = RPPParser(file2_path)

            # Verify initial state
            assert len(parser1.tracks) == 2  # Master + 1 regular
            assert len(parser2.tracks) == 2  # Master + 1 regular

            master1 = next(t for t in parser1.tracks if t.is_master)
            master2 = next(t for t in parser2.tracks if t.is_master)
            track1 = next(t for t in parser1.tracks if not t.is_master)
            track2 = next(t for t in parser2.tracks if not t.is_master)

            # Verify different effects
            assert master1.effects[0]["name"] != master2.effects[0]["name"]
            assert track1.effects[0]["name"] != track2.effects[0]["name"]
            assert track1.volume != track2.volume

            # Copy master effects from file1 to file2
            parser2.copy_track_settings(master1, master2, copy_effects=True)

            # Copy track settings from file1 to file2
            parser2.copy_track_settings(
                track1, track2, copy_volume=True, copy_effects=True
            )

            # Verify changes
            assert master2.effects[0]["name"] == master1.effects[0]["name"]
            assert track2.effects[0]["name"] == track1.effects[0]["name"]
            assert track2.volume == track1.volume

            # Save the modified file
            parser2.save_file(output_path)

            # Reload and verify persistence
            parser_verify = RPPParser(output_path)
            master_verify = next(t for t in parser_verify.tracks if t.is_master)
            track_verify = next(t for t in parser_verify.tracks if not t.is_master)

            assert master_verify.effects[0]["name"] == master1.effects[0]["name"]
            assert track_verify.effects[0]["name"] == track1.effects[0]["name"]
            assert track_verify.volume == track1.volume

        finally:
            # Cleanup
            for path in [file1_path, file2_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)
