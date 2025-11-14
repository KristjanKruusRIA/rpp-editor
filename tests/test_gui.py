"""
Tests for the RPP editor GUI functionality
"""

import os
import tempfile
import tkinter as tk
from unittest.mock import Mock, patch

import pytest

from rpp_editor.gui import RPPEditorGUI


@pytest.fixture
def sample_rpp_content():
    """Create a minimal RPP file content for testing."""
    return """<REAPER_PROJECT 0.1 "7.51/win64" 1763106377
  MASTER_VOLUME 1 0 -1 -1 1
  <MASTERFXLIST
    BYPASS 0 0 0
    <VST "VST: MasterEQ" mastereq.dll 0 "" 1919247729 ""
      Y2FsZhAAAAAIAAAA
    >
    WAK 0 0
  >
  <TRACK {A858D602-18C1-491F-9352-37B286CF4C0D}
    NAME "TestTrack"
    VOLPAN 0.8 0.2 -1 -1 1
    MUTESOLO 0 1 0
    <FXCHAIN
      BYPASS 0 0 0
      <VST "VST: TrackEQ" trackeq.dll 0 "" 987654321 ""
        Y2FsZhAAAAAIAAAA
      >
      WAK 0 0
    >
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


@pytest.fixture
def gui_app():
    """Create a GUI application for testing."""
    try:
        root = tk.Tk()
        app = RPPEditorGUI(root)
        yield app, root
        root.destroy()
    except tk.TclError:
        # Skip GUI tests if no display available (CI environment)
        pytest.skip("GUI tests require display - skipping in headless environment")


class TestGUIInitialization:
    """Test GUI initialization and basic functionality."""

    def test_gui_initialization(self, gui_app):
        """Test that GUI initializes correctly."""
        app, root = gui_app

        assert app.parser1 is None
        assert app.parser2 is None
        assert app.selected_track1 is None
        assert app.selected_track2 is None

        # Check that main widgets exist
        assert hasattr(app, "file1_var")
        assert hasattr(app, "file2_var")
        assert hasattr(app, "tracks1_tree")
        assert hasattr(app, "tracks2_tree")

    def test_initial_button_states(self, gui_app):
        """Test initial button states."""
        app, root = gui_app

        # Copy buttons should be disabled initially
        assert str(app.copy_left_button.cget("state")) == "disabled"
        assert str(app.copy_right_button.cget("state")) == "disabled"

    def test_initial_checkbox_states(self, gui_app):
        """Test initial checkbox states."""
        app, root = gui_app

        # Copy options should be enabled by default
        assert app.copy_volume_var.get() is True
        assert app.copy_pan_var.get() is True
        assert app.copy_effects_var.get() is True


class TestFileLoading:
    """Test file loading functionality."""

    @patch("tkinter.filedialog.askopenfilename")
    def test_load_file1_success(self, mock_filedialog, gui_app, temp_rpp_file):
        """Test successful loading of file 1."""
        app, root = gui_app
        mock_filedialog.return_value = temp_rpp_file

        app.load_file1()

        assert app.parser1 is not None
        assert app.file1_var.get() == os.path.basename(temp_rpp_file)
        assert "Version:" in app.file1_info_var.get()

    @patch("tkinter.filedialog.askopenfilename")
    def test_load_file2_success(self, mock_filedialog, gui_app, temp_rpp_file):
        """Test successful loading of file 2."""
        app, root = gui_app
        mock_filedialog.return_value = temp_rpp_file

        app.load_file2()

        assert app.parser2 is not None
        assert app.file2_var.get() == os.path.basename(temp_rpp_file)
        assert "Version:" in app.file2_info_var.get()

    @patch("tkinter.filedialog.askopenfilename")
    @patch("tkinter.messagebox.showerror")
    def test_load_file1_error(self, mock_messagebox, mock_filedialog, gui_app):
        """Test error handling when loading file 1."""
        app, root = gui_app
        mock_filedialog.return_value = "nonexistent_file.rpp"

        app.load_file1()

        # Should show error message
        mock_messagebox.assert_called_once()
        assert app.parser1 is None

    @patch("tkinter.filedialog.askopenfilename")
    def test_load_file_cancelled(self, mock_filedialog, gui_app):
        """Test when user cancels file dialog."""
        app, root = gui_app
        mock_filedialog.return_value = ""  # Empty string when cancelled

        app.load_file1()

        # Should not change anything
        assert app.parser1 is None
        assert app.file1_var.get() == ""


class TestTrackDisplay:
    """Test track display functionality."""

    def test_update_tracks_display_empty(self, gui_app):
        """Test updating tracks display with no files loaded."""
        app, root = gui_app

        app.update_tracks_display()

        # Should have no items in either tree
        assert len(app.tracks1_tree.get_children()) == 0
        assert len(app.tracks2_tree.get_children()) == 0

    def test_update_tracks_display_with_file(self, gui_app, temp_rpp_file):
        """Test updating tracks display with a loaded file."""
        app, root = gui_app

        # Load file manually
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)

        app.update_tracks_display()

        # Should have items in tree
        children = app.tracks1_tree.get_children()
        assert len(children) > 0

        # Check that master track is displayed with special formatting
        for child in children:
            text = app.tracks1_tree.item(child, "text")
            if "🎛️" in text:
                # This is the master track
                assert "Master" in text
                break

    def test_highlight_differences(self, gui_app, temp_rpp_file):
        """Test difference highlighting."""
        app, root = gui_app

        # Load same file in both parsers
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)

        app.update_tracks_display()

        # Since files are identical, no differences should be highlighted
        # This tests the highlighting mechanism
        app.highlight_differences()


class TestTrackSelection:
    """Test track selection functionality."""

    def test_track_selection_file1(self, gui_app, temp_rpp_file):
        """Test selecting a track in file 1."""
        app, root = gui_app

        # Load file and update display
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.update_tracks_display()

        # Simulate selection
        children = app.tracks1_tree.get_children()
        if children:
            # Create a mock event
            app.tracks1_tree.selection_set(children[0])
            event = Mock()
            app.on_track1_select(event)

            assert app.selected_track1 is not None

    def test_track_selection_enables_buttons(self, gui_app, temp_rpp_file):
        """Test that selecting tracks in both files enables copy buttons."""
        app, root = gui_app

        # Load files
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)
        app.update_tracks_display()

        # Select tracks
        children1 = app.tracks1_tree.get_children()
        children2 = app.tracks2_tree.get_children()

        if children1 and children2:
            app.tracks1_tree.selection_set(children1[0])
            app.tracks2_tree.selection_set(children2[0])

            # Simulate selections
            event = Mock()
            app.on_track1_select(event)
            app.on_track2_select(event)

            # Buttons should be enabled now
            assert str(app.copy_left_button.cget("state")) == "normal"
            assert str(app.copy_right_button.cget("state")) == "normal"


class TestTrackCopying:
    """Test track copying functionality."""

    @patch("tkinter.messagebox.showerror")
    def test_copy_track_to_file2_success(self, mock_messagebox, gui_app, temp_rpp_file):
        """Test successful copying from file 1 to file 2."""
        app, root = gui_app

        # Load files
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)
        app.update_tracks_display()

        # Set selections manually for testing
        app.selected_track1 = app.parser1.tracks[0]
        app.selected_track2 = app.parser2.tracks[0]

        # Mock the update methods to avoid GUI updates
        app.update_tracks_display = Mock()
        app.update_differences_display = Mock()

        app.copy_track_to_file2()

        # Should not show error
        mock_messagebox.assert_not_called()

        # Should update displays
        app.update_tracks_display.assert_called_once()
        app.update_differences_display.assert_called_once()

    @patch("tkinter.messagebox.showerror")
    def test_copy_track_to_file1_success(self, mock_messagebox, gui_app, temp_rpp_file):
        """Test successful copying from file 2 to file 1."""
        app, root = gui_app

        # Load files
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)

        # Set selections manually for testing
        app.selected_track1 = app.parser1.tracks[0]
        app.selected_track2 = app.parser2.tracks[0]

        # Mock the update methods
        app.update_tracks_display = Mock()
        app.update_differences_display = Mock()

        app.copy_track_to_file1()

        # Should not show error
        mock_messagebox.assert_not_called()

    def test_copy_track_no_selection(self, gui_app):
        """Test copying when no tracks are selected."""
        app, root = gui_app

        # No tracks selected
        app.selected_track1 = None
        app.selected_track2 = None

        # Should return early without error
        app.copy_track_to_file1()
        app.copy_track_to_file2()

    @patch("tkinter.messagebox.showerror")
    def test_copy_track_error_handling(self, mock_messagebox, gui_app, temp_rpp_file):
        """Test error handling in track copying."""
        app, root = gui_app

        # Load files
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)

        # Set up selection but break parser to cause error
        app.selected_track1 = app.parser1.tracks[0]
        app.selected_track2 = app.parser2.tracks[0]

        # Mock copy_track_settings to raise exception
        app.parser2.copy_track_settings = Mock(side_effect=Exception("Test error"))

        app.copy_track_to_file2()

        # Should show error message
        mock_messagebox.assert_called_once()


class TestFileSaving:
    """Test file saving functionality."""

    @patch("tkinter.messagebox.showinfo")
    @patch("tkinter.messagebox.showerror")
    def test_save_file1_success(self, mock_error, mock_info, gui_app, temp_rpp_file):
        """Test successful saving of file 1."""
        app, root = gui_app

        # Load file
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)

        app.save_file1()

        # Should show success message
        mock_info.assert_called_once()
        mock_error.assert_not_called()

    @patch("tkinter.messagebox.showinfo")
    @patch("tkinter.messagebox.showerror")
    def test_save_file1_error(self, mock_error, mock_info, gui_app, temp_rpp_file):
        """Test error handling in file saving."""
        app, root = gui_app

        # Load file but break save functionality
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser1.save_file = Mock(side_effect=Exception("Save error"))

        app.save_file1()

        # Should show error message
        mock_error.assert_called_once()
        mock_info.assert_not_called()

    def test_save_file_no_parser(self, gui_app):
        """Test saving when no parser is loaded."""
        app, root = gui_app

        # No parser loaded
        app.parser1 = None

        # Should return early without error
        app.save_file1()
        app.save_file2()

    @patch("tkinter.filedialog.asksaveasfilename")
    @patch("tkinter.messagebox.showinfo")
    def test_save_file_as_success(
        self, mock_info, mock_filedialog, gui_app, temp_rpp_file
    ):
        """Test save as functionality."""
        app, root = gui_app

        # Load file
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)

        # Mock file dialog
        with tempfile.NamedTemporaryFile(suffix=".rpp", delete=False) as temp:
            save_path = temp.name

        mock_filedialog.return_value = save_path

        try:
            app.save_file1_as()

            # Should show success message
            mock_info.assert_called_once()
        finally:
            if os.path.exists(save_path):
                os.unlink(save_path)

    @patch("tkinter.filedialog.asksaveasfilename")
    def test_save_file_as_cancelled(self, mock_filedialog, gui_app, temp_rpp_file):
        """Test save as when user cancels."""
        app, root = gui_app

        # Load file
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)

        # User cancels dialog
        mock_filedialog.return_value = ""

        app.save_file1_as()
        # Should return without error


class TestDifferencesDisplay:
    """Test differences display functionality."""

    def test_differences_display_no_selection(self, gui_app):
        """Test differences display with no tracks selected."""
        app, root = gui_app

        app.update_differences_display()

        # Should handle gracefully with no tracks selected
        # Text widget might be empty or disabled

    def test_differences_display_with_selection(self, gui_app, temp_rpp_file):
        """Test differences display with tracks selected."""
        app, root = gui_app

        # Load files
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)

        # Set selections
        app.selected_track1 = app.parser1.tracks[0]
        app.selected_track2 = app.parser2.tracks[0]

        app.update_differences_display()

        # Should display comparison info without error


class TestMenuFunctionality:
    """Test menu functionality."""

    @patch("tkinter.messagebox.showinfo")
    def test_show_about(self, mock_info, gui_app):
        """Test about dialog."""
        app, root = gui_app

        app.show_about()

        # Should show about dialog
        mock_info.assert_called_once()
        call_args = mock_info.call_args[0]
        assert "About RPP Editor" in call_args[0]
        assert "RPP Editor v1.0" in call_args[1]


class TestMainFunction:
    """Test main function and automatic file loading."""

    @patch("os.path.exists")
    def test_main_function_auto_load(self, mock_exists):
        """Test main function with automatic file loading."""
        # Mock that test files exist
        mock_exists.side_effect = lambda path: path in ["test1.rpp", "test2.rpp"]

        # Import and patch the main function
        from rpp_editor.gui import main

        with patch("tkinter.Tk") as mock_tk:
            mock_root = Mock()
            mock_tk.return_value = mock_root

            with patch("rpp_editor.gui.RPPEditorGUI") as mock_gui:
                mock_app = Mock()
                mock_gui.return_value = mock_app

                # Mock the parser creation to avoid actual file loading
                with patch("rpp_editor.gui.RPPParser") as mock_parser:
                    mock_parser_instance = Mock()
                    mock_parser_instance.get_project_info.return_value = {
                        "version": "0.1",
                        "track_count": 1,
                        "has_master_effects": True,
                        "tempo": 120,
                    }
                    mock_parser.return_value = mock_parser_instance

                    # Mock mainloop to prevent GUI from actually running
                    mock_root.mainloop = Mock()

                    main()

                    # Should have created GUI and attempted to load files
                    mock_gui.assert_called_once()
                    mock_root.mainloop.assert_called_once()
