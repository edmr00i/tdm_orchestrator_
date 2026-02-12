"""
Tests for file_utils - File and filename manipulation utilities.

Covers:
- sanitize_filename: Invalid character replacement and truncation
- sanitize_reference: Slash replacement for references
"""

import pytest

from .file_utils import sanitize_filename, sanitize_reference


# =====================
# sanitize_filename Tests
# =====================

class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_returns_unchanged_valid_filename(self, mocker):
        """Returns filename unchanged when no invalid characters."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/', '\\', '<', '>', ':', '"', '|', '?', '*']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("valid_filename.txt")
        
        assert result == "valid_filename.txt"

    def test_replaces_forward_slash_with_underscore(self, mocker):
        """Replaces forward slash with underscore."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("path/to/file.txt")
        
        assert result == "path_to_file.txt"

    def test_replaces_backslash_with_underscore(self, mocker):
        """Replaces backslash with underscore."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['\\']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("path\\to\\file.txt")
        
        assert result == "path_to_file.txt"

    def test_replaces_colon_with_underscore(self, mocker):
        """Replaces colon with underscore."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            [':']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("C:file.txt")
        
        assert result == "C_file.txt"

    def test_replaces_multiple_invalid_chars(self, mocker):
        """Replaces multiple different invalid characters."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/', '\\', '<', '>', ':']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file<name>with:invalid/chars\\here")
        
        assert result == "file_name_with_invalid_chars_here"

    def test_replaces_asterisk_with_underscore(self, mocker):
        """Replaces asterisk with underscore."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['*']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file*.txt")
        
        assert result == "file_.txt"

    def test_replaces_question_mark_with_underscore(self, mocker):
        """Replaces question mark with underscore."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['?']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file?.txt")
        
        assert result == "file_.txt"

    def test_replaces_double_quote_with_underscore(self, mocker):
        """Replaces double quote with underscore."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['"']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename('file"name.txt')
        
        assert result == "file_name.txt"

    def test_replaces_pipe_with_underscore(self, mocker):
        """Replaces pipe character with underscore."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['|']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file|name.txt")
        
        assert result == "file_name.txt"

    def test_replaces_angle_brackets_with_underscore(self, mocker):
        """Replaces angle brackets with underscores."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['<', '>']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file<tag>name.txt")
        
        assert result == "file_tag_name.txt"

    def test_truncates_to_max_length(self, mocker):
        """Truncates filename to MAX_FILENAME_LENGTH."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            []
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            10
        )
        
        result = sanitize_filename("verylongfilename.txt")
        
        assert result == "verylongfi"
        assert len(result) == 10

    def test_does_not_truncate_when_under_max_length(self, mocker):
        """Does not truncate when filename is under MAX_FILENAME_LENGTH."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            []
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            100
        )
        
        result = sanitize_filename("short.txt")
        
        assert result == "short.txt"

    def test_does_not_truncate_when_exactly_max_length(self, mocker):
        """Does not truncate when filename is exactly MAX_FILENAME_LENGTH."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            []
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            10
        )
        
        result = sanitize_filename("exactlyten")
        
        assert result == "exactlyten"
        assert len(result) == 10

    def test_sanitizes_then_truncates(self, mocker):
        """Sanitizes characters first, then truncates."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            10
        )
        
        result = sanitize_filename("a/b/c/d/e/f/g/h")
        
        # First replace / with _, then truncate
        assert result == "a_b_c_d_e_"
        assert len(result) == 10

    def test_handles_empty_string(self, mocker):
        """Handles empty string input."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("")
        
        assert result == ""

    def test_handles_only_invalid_chars(self, mocker):
        """Handles string with only invalid characters."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/', '\\']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("///\\\\\\")
        
        assert result == "______"

    def test_handles_unicode_characters(self, mocker):
        """Preserves unicode characters not in invalid list."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("日本語ファイル名.txt")
        
        assert result == "日本語ファイル名.txt"

    def test_handles_unicode_with_invalid_chars(self, mocker):
        """Handles unicode with invalid characters mixed in."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("日本語/ファイル/名.txt")
        
        assert result == "日本語_ファイル_名.txt"

    def test_handles_consecutive_invalid_chars(self, mocker):
        """Handles consecutive invalid characters."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/', '\\']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file//\\\\name.txt")
        
        assert result == "file____name.txt"

    def test_preserves_dots_and_hyphens(self, mocker):
        """Preserves dots, hyphens, and underscores."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/', '\\', '<', '>', ':', '"', '|', '?', '*']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file-name_v1.0.txt")
        
        assert result == "file-name_v1.0.txt"

    def test_preserves_spaces(self, mocker):
        """Preserves spaces in filename."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/', '\\']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file name with spaces.txt")
        
        assert result == "file name with spaces.txt"

    def test_handles_max_length_of_one(self, mocker):
        """Handles MAX_FILENAME_LENGTH of 1."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            []
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            1
        )
        
        result = sanitize_filename("longfilename.txt")
        
        assert result == "l"

    def test_handles_empty_invalid_chars_list(self, mocker):
        """Handles empty INVALID_FILENAME_CHARS list."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            []
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file/with\\special:chars.txt")
        
        # No replacements should occur
        assert result == "file/with\\special:chars.txt"


# =====================
# sanitize_reference Tests
# =====================

class TestSanitizeReference:
    """Tests for sanitize_reference function."""

    def test_returns_unchanged_valid_reference(self):
        """Returns reference unchanged when no slashes."""
        result = sanitize_reference("VALID_REF_001")
        
        assert result == "VALID_REF_001"

    def test_replaces_forward_slash_with_underscore(self):
        """Replaces forward slash with underscore."""
        result = sanitize_reference("REF/001/TEST")
        
        assert result == "REF_001_TEST"

    def test_replaces_backslash_with_underscore(self):
        """Replaces backslash with underscore."""
        result = sanitize_reference("REF\\001\\TEST")
        
        assert result == "REF_001_TEST"

    def test_replaces_mixed_slashes(self):
        """Replaces both forward and backward slashes."""
        result = sanitize_reference("REF/001\\TEST/002\\END")
        
        assert result == "REF_001_TEST_002_END"

    def test_handles_empty_string(self):
        """Handles empty string input."""
        result = sanitize_reference("")
        
        assert result == ""

    def test_handles_only_forward_slashes(self):
        """Handles string with only forward slashes."""
        result = sanitize_reference("///")
        
        assert result == "___"

    def test_handles_only_backslashes(self):
        """Handles string with only backslashes."""
        result = sanitize_reference("\\\\\\")
        
        assert result == "___"

    def test_handles_consecutive_forward_slashes(self):
        """Handles consecutive forward slashes."""
        result = sanitize_reference("REF//TEST")
        
        assert result == "REF__TEST"

    def test_handles_consecutive_backslashes(self):
        """Handles consecutive backslashes."""
        result = sanitize_reference("REF\\\\TEST")
        
        assert result == "REF__TEST"

    def test_handles_consecutive_mixed_slashes(self):
        """Handles consecutive mixed slashes."""
        result = sanitize_reference("REF/\\TEST")
        
        assert result == "REF__TEST"

    def test_preserves_other_special_characters(self):
        """Preserves other special characters."""
        result = sanitize_reference("REF-001_TEST:v2")
        
        assert result == "REF-001_TEST:v2"

    def test_preserves_unicode_characters(self):
        """Preserves unicode characters."""
        result = sanitize_reference("日本語REF/テスト")
        
        assert result == "日本語REF_テスト"

    def test_handles_slash_at_start(self):
        """Handles slash at start of reference."""
        result = sanitize_reference("/START")
        
        assert result == "_START"

    def test_handles_slash_at_end(self):
        """Handles slash at end of reference."""
        result = sanitize_reference("END/")
        
        assert result == "END_"

    def test_handles_backslash_at_start(self):
        """Handles backslash at start of reference."""
        result = sanitize_reference("\\START")
        
        assert result == "_START"

    def test_handles_backslash_at_end(self):
        """Handles backslash at end of reference."""
        result = sanitize_reference("END\\")
        
        assert result == "END_"

    def test_handles_windows_path_style(self):
        """Handles Windows-style path reference (only slashes replaced, not colon)."""
        result = sanitize_reference("C:\\Users\\Documents\\ref")
        
        # Note: sanitize_reference only replaces / and \, not :
        assert result == "C:_Users_Documents_ref"

    def test_handles_unix_path_style(self):
        """Handles Unix-style path reference."""
        result = sanitize_reference("/home/user/ref")
        
        assert result == "_home_user_ref"

    def test_preserves_numbers(self):
        """Preserves numeric characters."""
        result = sanitize_reference("REF123/456\\789")
        
        assert result == "REF123_456_789"

    def test_preserves_dots(self):
        """Preserves dots in reference."""
        result = sanitize_reference("REF.v1.0/TEST")
        
        assert result == "REF.v1.0_TEST"

    def test_preserves_spaces(self):
        """Preserves spaces in reference."""
        result = sanitize_reference("REF WITH SPACES/TEST")
        
        assert result == "REF WITH SPACES_TEST"

    def test_single_character_forward_slash(self):
        """Handles single forward slash."""
        result = sanitize_reference("/")
        
        assert result == "_"

    def test_single_character_backslash(self):
        """Handles single backslash."""
        result = sanitize_reference("\\")
        
        assert result == "_"

    def test_very_long_reference(self):
        """Handles very long reference without truncation."""
        long_ref = "A" * 500 + "/" + "B" * 500
        
        result = sanitize_reference(long_ref)
        
        expected = "A" * 500 + "_" + "B" * 500
        assert result == expected
        assert len(result) == 1001


# =====================
# Integration Tests
# =====================

class TestFileUtilsIntegration:
    """Integration tests for file_utils functions."""

    def test_sanitize_filename_then_reference_workflow(self, mocker):
        """Tests typical workflow of sanitizing both filename and reference."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/', '\\', '<', '>', ':', '"', '|', '?', '*']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            50
        )
        
        # Typical runner reference
        reference = "APP/MODULE/RUNNER_001"
        sanitized_ref = sanitize_reference(reference)
        
        # Use sanitized reference in filename
        filename = f"export_{sanitized_ref}.zip"
        sanitized_filename = sanitize_filename(filename)
        
        assert sanitized_ref == "APP_MODULE_RUNNER_001"
        assert sanitized_filename == "export_APP_MODULE_RUNNER_001.zip"

    def test_consistent_underscore_replacement(self, mocker):
        """Both functions use underscore for replacement consistently."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/', '\\']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        test_input = "path/to\\file"
        
        filename_result = sanitize_filename(test_input)
        reference_result = sanitize_reference(test_input)
        
        assert filename_result == "path_to_file"
        assert reference_result == "path_to_file"


# =====================
# Edge Cases
# =====================

class TestFileUtilsEdgeCases:
    """Edge case tests for file_utils functions."""

    def test_sanitize_filename_with_null_bytes(self, mocker):
        """Handles null bytes if in invalid chars list."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['\x00']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file\x00name.txt")
        
        assert result == "file_name.txt"

    def test_sanitize_filename_with_newlines(self, mocker):
        """Handles newlines if in invalid chars list."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['\n', '\r']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("file\nname\r.txt")
        
        assert result == "file_name_.txt"

    def test_sanitize_filename_preserves_emoji(self, mocker):
        """Preserves emoji characters not in invalid list."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            ['/']
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("🚀rocket_launch.txt")
        
        assert result == "🚀rocket_launch.txt"

    def test_sanitize_reference_preserves_emoji(self):
        """Preserves emoji characters in reference."""
        result = sanitize_reference("🚀ROCKET/LAUNCH")
        
        assert result == "🚀ROCKET_LAUNCH"

    def test_sanitize_filename_with_max_length_zero(self, mocker):
        """Handles MAX_FILENAME_LENGTH of 0."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            []
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            0
        )
        
        result = sanitize_filename("anyfilename.txt")
        
        assert result == ""

    def test_sanitize_filename_whitespace_only(self, mocker):
        """Handles whitespace-only filename."""
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.INVALID_FILENAME_CHARS',
            []
        )
        mocker.patch(
            'tdm_orchestrator.services.export.file_utils.MAX_FILENAME_LENGTH',
            255
        )
        
        result = sanitize_filename("   ")
        
        assert result == "   "

    def test_sanitize_reference_whitespace_only(self):
        """Handles whitespace-only reference."""
        result = sanitize_reference("   ")
        
        assert result == "   "


# =====================
# Summary of Covered Cases
# =====================
# sanitize_filename:
# - Returns unchanged valid filename
# - Replaces forward slash with underscore
# - Replaces backslash with underscore
# - Replaces colon with underscore
# - Replaces multiple invalid chars
# - Replaces asterisk, question mark, double quote, pipe
# - Replaces angle brackets
# - Truncates to MAX_FILENAME_LENGTH
# - Does not truncate when under/exactly max length
# - Sanitizes then truncates (order matters)
# - Handles empty string
# - Handles only invalid chars
# - Handles unicode characters
# - Handles unicode with invalid chars
# - Handles consecutive invalid chars
# - Preserves dots, hyphens, spaces
# - Handles max length of 1
# - Handles empty invalid chars list
#
# sanitize_reference:
# - Returns unchanged valid reference
# - Replaces forward slash with underscore
# - Replaces backslash with underscore
# - Replaces mixed slashes
# - Handles empty string
# - Handles only slashes
# - Handles consecutive slashes
# - Preserves other special characters
# - Preserves unicode characters
# - Handles slashes at start/end
# - Handles Windows/Unix path styles
# - Preserves numbers, dots, spaces
# - Handles single slash
# - Handles very long reference
#
# Integration:
# - Workflow of sanitizing both filename and reference
# - Consistent underscore replacement
#
# Edge cases:
# - Null bytes
# - Newlines
# - Emoji characters
# - Max length zero
# - Whitespace-only input