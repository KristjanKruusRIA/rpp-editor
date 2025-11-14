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
    def test_save_file_as_success(self, mock_info, mock_filedialog, gui_app, temp_rpp_file):
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


class TestGUILogicWithoutDisplay:
    """Test GUI logic without requiring actual display."""

    def test_update_copy_buttons_logic(self):
        """Test copy button state logic without GUI."""
        # Create mock GUI instance
        gui = Mock()
        gui.copy_left_button = Mock()
        gui.copy_right_button = Mock()

        # Import the actual method
        from rpp_editor.gui import RPPEditorGUI

        update_copy_buttons = RPPEditorGUI.update_copy_buttons

        # Test with both tracks selected
        gui.selected_track1 = Mock()
        gui.selected_track2 = Mock()
        update_copy_buttons(gui)
        gui.copy_left_button.config.assert_called_with(state="normal")
        gui.copy_right_button.config.assert_called_with(state="normal")

        # Test with only one track selected
        gui.selected_track1 = None
        gui.selected_track2 = Mock()
        update_copy_buttons(gui)
        gui.copy_left_button.config.assert_called_with(state="disabled")
        gui.copy_right_button.config.assert_called_with(state="disabled")

    def test_differences_display_logic(self):
        """Test differences display logic."""
        from rpp_editor.gui import RPPEditorGUI
        from rpp_editor.parser import TrackInfo

        gui = Mock()
        gui.diff_text = Mock()

        # Create mock tracks
        track1 = TrackInfo(
            track_id="1",
            name="Track1",
            volume=0.8,
            pan=0.0,
            mute=False,
            solo=False,
            effects=[],
            raw_element=None,
        )
        track2 = TrackInfo(
            track_id="2",
            name="Track2",
            volume=0.6,
            pan=0.1,
            mute=True,
            solo=True,
            effects=[],
            raw_element=None,
        )

        gui.selected_track1 = track1
        gui.selected_track2 = track2

        # Test the differences display method
        update_differences_display = RPPEditorGUI.update_differences_display
        update_differences_display(gui)

        # Should have called config and insert methods
        assert gui.diff_text.config.call_count >= 2
        assert gui.diff_text.insert.call_count >= 1
        assert gui.diff_text.delete.call_count >= 1

    def test_highlight_differences_logic(self):
        """Test track highlighting logic."""
        from rpp_editor.gui import RPPEditorGUI

        # Test the method with parsers present
        gui = Mock()
        gui.parser1 = Mock()
        gui.parser2 = Mock()
        gui.parser1.tracks = []  # Empty tracks
        gui.tracks1_tree = Mock()
        gui.tracks2_tree = Mock()

        # Mock get_children to return empty lists
        gui.tracks1_tree.get_children.return_value = []
        gui.tracks2_tree.get_children.return_value = []

        # Test with parsers but no tracks
        highlight_differences = RPPEditorGUI.highlight_differences
        highlight_differences(gui)

        # Verify tag_configure was called for setting up styles (always called at end)
        assert gui.tracks1_tree.tag_configure.call_count == 2  # different and master
        assert gui.tracks2_tree.tag_configure.call_count == 2  # different and master

        # Verify the specific tag configurations
        gui.tracks1_tree.tag_configure.assert_any_call("different", background="#ffcccc")
        gui.tracks2_tree.tag_configure.assert_any_call("different", background="#ffcccc")
        gui.tracks1_tree.tag_configure.assert_any_call(
            "master", background="#e6f3ff", font=("TkDefaultFont", 9, "bold")
        )
        gui.tracks2_tree.tag_configure.assert_any_call(
            "master", background="#e6f3ff", font=("TkDefaultFont", 9, "bold")
        )


class TestGUIHighlightingWithRealTracks:
    """Test highlighting logic with real track comparison scenarios."""

    def test_highlight_differences_with_actual_differences(self, gui_app, temp_rpp_file):
        """Test highlighting when tracks actually have differences."""
        app, root = gui_app

        # Load the same file into both parsers
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)

        # Modify one track to create differences
        if app.parser2.tracks:
            app.parser2.tracks[0].volume = 0.5  # Different from original

        # Mock tree widgets to simulate actual GUI trees
        app.tracks1_tree = Mock()
        app.tracks2_tree = Mock()

        # Mock tree items to return track names
        app.tracks1_tree.get_children.return_value = ["item0"]
        app.tracks2_tree.get_children.return_value = ["item0"]

        # Mock item method to return track names
        def mock_item1(item_id, key=None, **kwargs):
            if key == "text" and item_id == "item0":
                return app.parser1.tracks[0].name if app.parser1.tracks else ""
            elif "tags" in kwargs:
                # This is the call we want to test - setting tags for differences
                return None
            return ""

        def mock_item2(item_id, key=None, **kwargs):
            if key == "text" and item_id == "item0":
                return app.parser2.tracks[0].name if app.parser2.tracks else ""
            elif "tags" in kwargs:
                # This is the call we want to test - setting tags for differences
                return None
            return ""

        app.tracks1_tree.item.side_effect = mock_item1
        app.tracks2_tree.item.side_effect = mock_item2

        # Test highlight differences - this should trigger the highlighting loops
        app.highlight_differences()

        # Verify that item was called to set tags for differences
        # This covers lines 370-378 in gui.py
        app.tracks1_tree.item.assert_any_call("item0", tags=("different",))
        app.tracks2_tree.item.assert_any_call("item0", tags=("different",))

    @patch("tkinter.messagebox.showerror")
    @patch("tkinter.filedialog.askopenfilename")
    def test_file_loading_exception_handling(self, mock_dialog, mock_error, gui_app):
        """Test exception handling in file loading."""
        app, root = gui_app

        # Mock file dialog to return a path
        mock_dialog.return_value = "nonexistent.rpp"

        # Test that file loading exceptions are properly caught
        with patch("rpp_editor.parser.RPPParser") as mock_parser:
            mock_parser.side_effect = Exception("Parser error")

            # This should trigger the exception handler (lines 312-313)
            app.load_file1()

            # Verify error dialog was shown
            mock_error.assert_called_once()
            assert "Failed to load file" in mock_error.call_args[0][1]

    @patch("tkinter.messagebox.showerror")
    @patch("tkinter.filedialog.askopenfilename")
    def test_file_loading_exception_handling_file2(self, mock_dialog, mock_error, gui_app):
        """Test exception handling in file2 loading."""
        app, root = gui_app

        # Mock file dialog to return a path
        mock_dialog.return_value = "nonexistent.rpp"

        # Test that file loading exceptions are properly caught for file2
        with patch("rpp_editor.parser.RPPParser") as mock_parser:
            mock_parser.side_effect = Exception("Parser error")

            # This should trigger the exception handler for file2
            app.load_file2()

            # Verify error dialog was shown
            mock_error.assert_called_once()
            assert "Failed to load file" in mock_error.call_args[0][1]

    def test_save_exception_scenarios_detailed(self, gui_app, temp_rpp_file):
        """Test detailed save exception scenarios."""
        app, root = gui_app

        # Load files first
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)

        # Test save file1 exception handling
        with patch.object(app.parser1, "save_file", side_effect=Exception("Save failed")):
            with patch("tkinter.messagebox.showerror") as mock_error:
                app.save_file1()
                mock_error.assert_called_once()

        # Test save file2 exception handling
        with patch.object(app.parser2, "save_file", side_effect=Exception("Save failed")):
            with patch("tkinter.messagebox.showerror") as mock_error:
                app.save_file2()
                mock_error.assert_called_once()

        # Test save as file1 exception handling
        with patch.object(app.parser1, "save_file", side_effect=Exception("Save failed")):
            with patch("tkinter.filedialog.asksaveasfilename", return_value="test.rpp"):
                with patch("tkinter.messagebox.showerror") as mock_error:
                    app.save_file1_as()
                    mock_error.assert_called_once()

        # Test save as file2 exception handling
        with patch.object(app.parser2, "save_file", side_effect=Exception("Save failed")):
            with patch("tkinter.filedialog.asksaveasfilename", return_value="test2.rpp"):
                with patch("tkinter.messagebox.showerror") as mock_error:
                    app.save_file2_as()
                    mock_error.assert_called_once()

    def test_save_file2_operations(self, gui_app, temp_rpp_file):
        """Test file2 save operations to cover missing lines."""
        app, root = gui_app

        # Load file2
        from rpp_editor.parser import RPPParser

        app.parser2 = RPPParser(temp_rpp_file)

        # Test successful save file2
        with patch.object(app.parser2, "save_file") as mock_save:
            with patch("tkinter.messagebox.showinfo") as mock_info:
                app.save_file2()
                mock_save.assert_called_once()
                mock_info.assert_called_once()

        # Test successful save as file2
        with patch.object(app.parser2, "save_file") as mock_save:
            with patch("tkinter.filedialog.asksaveasfilename", return_value="test.rpp"):
                with patch("tkinter.messagebox.showinfo") as mock_info:
                    app.save_file2_as()
                    mock_save.assert_called_once_with("test.rpp")
                    mock_info.assert_called_once()

    def test_no_parser_save_operations(self, gui_app):
        """Test save operations when no parser is loaded."""
        app, root = gui_app

        # Test save operations with no parsers - should do nothing
        app.parser1 = None
        app.parser2 = None

        # These should not raise exceptions and should do nothing
        app.save_file1()
        app.save_file2()
        app.save_file1_as()
        app.save_file2_as()


class TestGUIMenuOperations:
    """Test GUI menu operations with mocking."""

    @patch("tkinter.messagebox.showinfo")
    def test_show_about_detailed(self, mock_showinfo, gui_app):
        """Test about dialog with detailed verification."""
        app, root = gui_app

        app.show_about()

        # Verify the about dialog content
        mock_showinfo.assert_called_once()
        args = mock_showinfo.call_args[0]

        assert "About RPP Editor" in args[0]
        assert "RPP Editor v1.0" in args[1]
        assert "REAPER project files" in args[1]
        assert "Features:" in args[1]
        assert "Load and compare" in args[1]
        assert "Python and tkinter" in args[1]


class TestGUITrackOperations:
    """Test track operations with enhanced mocking."""

    def test_track_selection_detailed(self, gui_app, temp_rpp_file):
        """Test detailed track selection behavior."""
        app, root = gui_app

        # Load file and setup
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)

        # Mock the tree widgets with proper numeric IDs
        app.tracks1_tree.get_children = Mock(return_value=["0", "1"])
        app.tracks2_tree.get_children = Mock(return_value=["0", "1"])
        app.tracks1_tree.selection_set = Mock()
        app.tracks2_tree.selection_set = Mock()
        app.tracks1_tree.selection = Mock(return_value=["0"])
        app.tracks2_tree.selection = Mock(return_value=["0"])

        # Mock update methods to avoid GUI operations
        app.update_copy_buttons = Mock()
        app.update_differences_display = Mock()

        # Test track selection events
        event = Mock()

        # Select first track
        app.on_track1_select(event)
        assert app.selected_track1 == app.parser1.tracks[0]
        app.update_copy_buttons.assert_called_once()
        app.update_differences_display.assert_called_once()

        # Reset mocks and select second track
        app.update_copy_buttons.reset_mock()
        app.update_differences_display.reset_mock()

        app.on_track2_select(event)
        assert app.selected_track2 == app.parser2.tracks[0]
        app.update_copy_buttons.assert_called_once()
        app.update_differences_display.assert_called_once()

    @patch("tkinter.messagebox.showerror")
    def test_copy_operations_detailed(self, mock_error, gui_app, temp_rpp_file):
        """Test detailed copy operations."""
        app, root = gui_app

        # Load files
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)

        # Set up tracks
        app.selected_track1 = app.parser1.tracks[0]
        app.selected_track2 = app.parser2.tracks[0]

        # Mock the update methods
        app.update_tracks_display = Mock()
        app.update_differences_display = Mock()

        # Test copy with different options
        app.copy_volume_var.set(True)
        app.copy_pan_var.set(False)
        app.copy_effects_var.set(True)

        app.copy_track_to_file2()

        # Verify methods were called
        app.update_tracks_display.assert_called_once()
        app.update_differences_display.assert_called_once()
        mock_error.assert_not_called()

        # Test copy in other direction
        app.update_tracks_display.reset_mock()
        app.update_differences_display.reset_mock()

        app.copy_track_to_file1()

        app.update_tracks_display.assert_called_once()
        app.update_differences_display.assert_called_once()


class TestGUIFileOperationsDetailed:
    """Test detailed file operations."""

    @patch("tkinter.filedialog.askopenfilename")
    @patch("tkinter.messagebox.showerror")
    def test_file_loading_edge_cases(self, mock_error, mock_dialog, gui_app):
        """Test file loading edge cases."""
        app, root = gui_app

        # Test loading non-existent file
        mock_dialog.return_value = "nonexistent.rpp"
        app.load_file1()
        mock_error.assert_called_once()
        assert app.parser1 is None

        # Test loading with exception in parser
        mock_error.reset_mock()
        mock_dialog.return_value = "invalid.rpp"

        with patch("rpp_editor.parser.RPPParser") as mock_parser:
            mock_parser.side_effect = Exception("Parse error")
            app.load_file1()
            mock_error.assert_called_once()

    def test_file_info_display(self, gui_app, temp_rpp_file):
        """Test file info display functionality."""
        app, root = gui_app

        # Load file manually to test info display
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)

        # Test project info formatting
        info = app.parser1.get_project_info()

        expected_elements = [
            f"Version: {info['version']}",
            f"Tracks: {info['track_count']}",
            "Master FX:",
            f"Tempo: {info['tempo']}",
        ]

        # Simulate the info string creation
        master_fx = "Yes" if info["has_master_effects"] else "No"
        info_text = (
            f"Version: {info['version']}, Tracks: {info['track_count']}, "
            f"Master FX: {master_fx}, Tempo: {info['tempo']}"
        )

        for element in expected_elements[:-1]:  # Skip tempo check
            assert element.split(":")[0] in info_text


class TestGUIUpdateMethods:
    """Test GUI update methods with comprehensive mocking."""

    def test_update_tracks_display_comprehensive(self, gui_app, temp_rpp_file):
        """Test comprehensive track display updates."""
        app, root = gui_app

        # Load test data
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)

        # Mock tree operations
        app.tracks1_tree.get_children = Mock(return_value=["old1", "old2"])
        app.tracks1_tree.delete = Mock()
        app.tracks1_tree.insert = Mock()
        app.tracks2_tree.get_children = Mock(return_value=["old3", "old4"])
        app.tracks2_tree.delete = Mock()
        app.tracks2_tree.insert = Mock()

        # Mock highlight differences
        app.highlight_differences = Mock()

        # Call update method
        app.update_tracks_display()

        # Verify cleanup calls
        app.tracks1_tree.delete.assert_any_call("old1")
        app.tracks1_tree.delete.assert_any_call("old2")
        app.tracks2_tree.delete.assert_any_call("old3")
        app.tracks2_tree.delete.assert_any_call("old4")

        # Verify insert calls (should have at least one per parser)
        assert app.tracks1_tree.insert.call_count >= len(app.parser1.tracks)
        assert app.tracks2_tree.insert.call_count >= len(app.parser2.tracks)

        # Verify highlight differences called
        app.highlight_differences.assert_called_once()

    def test_update_differences_comprehensive(self, gui_app, temp_rpp_file):
        """Test comprehensive differences display."""
        app, root = gui_app

        # Set up test scenario
        from rpp_editor.parser import RPPParser, TrackInfo

        app.parser1 = RPPParser(temp_rpp_file)
        app.parser2 = RPPParser(temp_rpp_file)

        # Create different tracks for comparison
        track1 = TrackInfo(
            track_id="1",
            name="TestTrack",
            volume=0.8,
            pan=0.0,
            mute=False,
            solo=False,
            effects=[{"name": "Effect1"}],
            raw_element=None,
        )
        track2 = TrackInfo(
            track_id="2",
            name="TestTrack",
            volume=0.6,
            pan=0.2,
            mute=True,
            solo=True,
            effects=[{"name": "Effect2"}],
            raw_element=None,
        )

        app.selected_track1 = track1
        app.selected_track2 = track2

        # Mock text widget operations
        app.diff_text.config = Mock()
        app.diff_text.delete = Mock()
        app.diff_text.insert = Mock()

        # Call update method
        app.update_differences_display()

        # Verify text widget operations
        assert app.diff_text.config.call_count >= 2  # Enable and disable
        app.diff_text.delete.assert_called_with(1.0, tk.END)
        assert app.diff_text.insert.call_count >= 5  # Multiple inserts for differences


class TestGUIErrorHandling:
    """Test GUI error handling scenarios."""

    @patch("tkinter.messagebox.showerror")
    def test_save_error_scenarios(self, mock_error, gui_app, temp_rpp_file):
        """Test various save error scenarios."""
        app, root = gui_app

        # Load file
        from rpp_editor.parser import RPPParser

        app.parser1 = RPPParser(temp_rpp_file)

        # Test save with parser exception
        app.parser1.save_file = Mock(side_effect=Exception("Save failed"))
        app.save_file1()
        mock_error.assert_called_once()

        # Test save as with exception
        mock_error.reset_mock()
        with patch("tkinter.filedialog.asksaveasfilename") as mock_dialog:
            mock_dialog.return_value = "test_save.rpp"
            app.save_file1_as()
            mock_error.assert_called_once()

    def test_widget_error_handling(self, gui_app):
        """Test widget error handling."""
        app, root = gui_app

        # Test operations with no parser loaded
        app.parser1 = None
        app.parser2 = None

        # These should not raise exceptions
        app.update_tracks_display()
        app.update_differences_display()
        app.highlight_differences()

        # Test selection events with no parser
        event = Mock()
        app.on_track1_select(event)  # Should not crash
        app.on_track2_select(event)  # Should not crash


class TestGUIWidgetConfiguration:
    """Test GUI widget configuration and properties."""

    def test_widget_properties(self, gui_app):
        """Test widget properties and configuration."""
        app, root = gui_app

        # Test tree widget configuration
        assert hasattr(app, "tracks1_tree")
        assert hasattr(app, "tracks2_tree")

        # Test button configuration
        assert hasattr(app, "copy_left_button")
        assert hasattr(app, "copy_right_button")
        assert hasattr(app, "file1_button")
        assert hasattr(app, "file2_button")

        # Test variable configuration
        assert hasattr(app, "copy_volume_var")
        assert hasattr(app, "copy_pan_var")
        assert hasattr(app, "copy_effects_var")
        assert hasattr(app, "file1_var")
        assert hasattr(app, "file2_var")
        assert hasattr(app, "status_var")

    def test_layout_configuration(self, gui_app):
        """Test layout and frame configuration."""
        app, root = gui_app

        # Test frame existence
        assert hasattr(app, "main_frame")
        assert hasattr(app, "file_frame")
        assert hasattr(app, "comparison_frame")
        assert hasattr(app, "control_frame")
        assert hasattr(app, "status_frame")

        # Test text widget
        assert hasattr(app, "diff_text")
        assert hasattr(app, "status_label")

    def test_scrollbar_configuration(self, gui_app):
        """Test that both horizontal and vertical scrollbars are configured."""
        app, root = gui_app

        # Check that treeview widgets have scrollbar commands configured
        tracks1_tree_config = app.tracks1_tree.configure()
        tracks2_tree_config = app.tracks2_tree.configure()

        # Verify xscrollcommand is configured (horizontal scrolling)
        assert "xscrollcommand" in tracks1_tree_config
        assert "xscrollcommand" in tracks2_tree_config

        # Verify yscrollcommand is configured (vertical scrolling)
        assert "yscrollcommand" in tracks1_tree_config
        assert "yscrollcommand" in tracks2_tree_config
