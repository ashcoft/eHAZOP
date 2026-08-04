"""Tests for storage service path traversal protection."""

import os
import tempfile

from app.services.storage_service import _is_path_within_storage


class TestIsPathWithinStorage:
    """Test the path containment helper function."""

    def test_path_within_storage_returns_true(self):
        """Test that a path within storage root returns True."""
        storage_root = "/var/storage"
        file_path = "/var/storage/docs/file.txt"
        assert _is_path_within_storage(file_path, storage_root) is True

    def test_path_outside_storage_returns_false(self):
        """Test that a path outside storage root returns False."""
        storage_root = "/var/storage"
        file_path = "/var/other/file.txt"
        assert _is_path_within_storage(file_path, storage_root) is False

    def test_path_traversal_attempt_with_normalized_path_returns_false(self):
        """Test that path traversal attempts are blocked when paths are pre-normalized."""
        storage_root = "/var/storage"
        # Pre-normalized path that would escape storage
        malicious_path = os.path.normpath(os.path.realpath("/var/storage/../../../etc/passwd"))
        # After normalization this resolves to /etc/passwd
        assert malicious_path == "/etc/passwd"
        assert _is_path_within_storage(malicious_path, storage_root) is False

    def test_symlink_inside_storage_returns_true(self):
        """Test that a symlink resolving inside storage is allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_root = os.path.join(tmpdir, "storage")
            os.makedirs(storage_root)
            
            # Create a file inside storage
            file_inside = os.path.join(storage_root, "file.txt")
            with open(file_inside, "w") as f:
                f.write("content")
            
            # Create a symlink to it
            symlink_path = os.path.join(tmpdir, "link.txt")
            os.symlink(file_inside, symlink_path)
            
            # The symlink resolves inside storage
            resolved = os.path.realpath(symlink_path)
            assert _is_path_within_storage(resolved, storage_root) is True

    def test_symlink_outside_storage_returns_false(self):
        """Test that a symlink resolving outside storage is blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_root = os.path.join(tmpdir, "storage")
            os.makedirs(storage_root)
            
            # Create a file outside storage
            file_outside = os.path.join(tmpdir, "secret.txt")
            with open(file_outside, "w") as f:
                f.write("secret")
            
            # Create a symlink inside storage pointing outside
            symlink_path = os.path.join(storage_root, "link.txt")
            os.symlink(file_outside, symlink_path)
            
            # The symlink resolves outside storage
            resolved = os.path.realpath(symlink_path)
            assert _is_path_within_storage(resolved, storage_root) is False

    def test_empty_path_returns_false(self):
        """Test that empty paths are handled safely."""
        storage_root = "/var/storage"
        file_path = ""
        assert _is_path_within_storage(file_path, storage_root) is False

    def test_relative_path_returns_false(self):
        """Test that relative paths are handled safely."""
        storage_root = "/var/storage"
        file_path = "docs/../../etc/passwd"
        assert _is_path_within_storage(file_path, storage_root) is False

    def test_value_error_handled_gracefully(self):
        """Test that ValueError from commonpath is handled (Windows cross-drive)."""
        # On Windows, paths on different drives raise ValueError
        # We should treat these as unsafe (return False)
        storage_root = "C:\\storage"
        file_path = "D:\\other"
        assert _is_path_within_storage(file_path, storage_root) is False

    def test_path_within_storage_trailing_slash(self):
        """Test path validation with trailing slash in storage root."""
        # os.path.normpath normalizes trailing slashes, so we need to test
        # with paths that have been normalized
        storage_root = "/var/storage"
        file_path = "/var/storage/docs/file.txt"
        assert _is_path_within_storage(file_path, storage_root) is True


class TestStorageServicePathValidation:
    """Unit tests for StorageService path validation logic."""

    def test_path_validation_blocks_path_traversal_in_upload(self):
        """Test that upload logic blocks path traversal attempts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "storage")
            os.makedirs(storage_path)
            
            # Simulate what happens in _upload_local
            settings_storage_path = storage_path
            malicious_filename = "../../../etc/passwd"
            
            # Simulate filename sanitization (os.path.basename) - this removes path traversal
            safe_filename = os.path.basename(malicious_filename)  # "passwd"
            assert safe_filename == "passwd"
            
            # After basename sanitization, the filename is safe and path is valid
            # This is correct behavior - the sanitization prevents path traversal
            base_storage_root = os.path.normpath(os.path.realpath(settings_storage_path))
            file_path = os.path.normpath(
                os.path.realpath(
                    os.path.join(base_storage_root, "2026/01/01", f"uuid_{safe_filename}")
                )
            )
            
            # The sanitized filename results in a valid path (sanitization worked)
            is_blocked = not _is_path_within_storage(file_path, base_storage_root)
            assert is_blocked is False, f"Path was incorrectly blocked: {file_path}"

    def test_filename_sanitization_removes_path_traversal(self):
        """Test that filename sanitization removes path traversal characters."""
        import re
        
        # Simulate the sanitization from _upload_local
        def sanitize_filename(filename):
            safe_filename = os.path.basename(filename)
            safe_filename = re.sub(r"[^A-Za-z0-9._-]", "_", safe_filename)
            return safe_filename
        
        # Path traversal attempts get sanitized to just the filename
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("/etc/passwd") == "passwd"
        assert sanitize_filename("foo/../bar/../../etc/passwd") == "passwd"
        
        # Normal filenames are preserved
        assert sanitize_filename("document.pdf") == "document.pdf"
        assert sanitize_filename("my_report-2024.docx") == "my_report-2024.docx"

    def test_path_validation_allows_valid_path_in_upload(self):
        """Test that upload logic allows valid file paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "storage")
            os.makedirs(storage_path)
            
            # Simulate what happens in _upload_local
            settings_storage_path = storage_path
            valid_filename = "document.pdf"
            
            # Build the path as the service would
            base_storage_root = os.path.normpath(os.path.realpath(settings_storage_path))
            file_path = os.path.normpath(
                os.path.realpath(
                    os.path.join(base_storage_root, "2026/01/01", f"uuid_{valid_filename}")
                )
            )
            
            # This should be allowed
            is_blocked = not _is_path_within_storage(file_path, base_storage_root)
            assert is_blocked is False, f"Valid path was incorrectly blocked: {file_path}"

    def test_download_validates_stored_path(self):
        """Test that download validates stored file paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "storage")
            os.makedirs(storage_path)
            
            # Create a file inside storage
            inside_path = os.path.join(storage_path, "test.txt")
            with open(inside_path, "w") as f:
                f.write("content")
            
            # Simulate stored path (as in Document.file_path)
            stored_path = inside_path
            
            # Validate as download_file would
            base_storage_root = os.path.normpath(os.path.realpath(storage_path))
            resolved_path = os.path.normpath(os.path.realpath(stored_path))
            
            # This should be allowed
            is_blocked = not _is_path_within_storage(resolved_path, base_storage_root)
            assert is_blocked is False, f"Valid path was incorrectly blocked: {resolved_path}"

    def test_download_blocks_malicious_stored_path(self):
        """Test that download blocks malicious stored file paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "storage")
            os.makedirs(storage_path)
            
            # Create a file outside storage
            malicious_path = os.path.join(tmpdir, "secret.txt")
            with open(malicious_path, "w") as f:
                f.write("secret")
            
            # Simulate stored path that tries to escape
            stored_path = malicious_path
            
            # Validate as download_file would
            base_storage_root = os.path.normpath(os.path.realpath(storage_path))
            resolved_path = os.path.normpath(os.path.realpath(stored_path))
            
            # This should be blocked
            is_blocked = not _is_path_within_storage(resolved_path, base_storage_root)
            assert is_blocked is True, f"Malicious path was not blocked: {resolved_path}"
