"""Tests for storage service path traversal protection.

These tests exercise the real upload/download/delete code paths (including the
filesystem guards) against a temporary storage root. A minimal in-memory session
double stands in for the database, since path containment is independent of the
database and the SQLite schema used elsewhere in the suite cannot be created
(the models rely on Postgres-specific relationships).
"""

import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.rag_service import RAGService
from app.services.storage_service import (
    StorageService,
    _storage_boundary,
    _storage_root,
)


class _StubResult:
    """Result object exposing the single-document accessor the service calls."""

    def __init__(self, document):
        """Store the document the service will look up."""
        self._document = document

    def scalar_one_or_none(self):
        """Return the configured document."""
        return self._document


class _StubSession:
    """Minimal async session double: the storage service only needs CRUD calls."""

    def __init__(self, document=None):
        """Track the lookup document plus added and deleted records."""
        self._document = document
        self.added = []
        self.deleted = []

    def add(self, obj):
        """Record an added object."""
        self.added.append(obj)

    async def flush(self):
        """No-op flush."""

    async def refresh(self, obj):
        """No-op refresh."""

    async def execute(self, *args, **kwargs):
        """Return the prepared lookup result."""
        return _StubResult(self._document)

    async def delete(self, obj):
        """Record a deleted object."""
        self.deleted.append(obj)


@pytest.fixture
def storage_root(monkeypatch):
    """Point the service at a fresh temporary storage root.

    The root is a child of the managed temporary directory so that escape
    targets created next to it (siblings, parent-directory files) are cleaned
    up with it rather than persisting in the system temp directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = os.path.join(tmpdir, "storage")
        os.makedirs(root)
        monkeypatch.setattr(
            "app.services.storage_service.settings.STORAGE_LOCAL_PATH", root
        )
        yield os.path.realpath(root)


class _RecordedDocument:
    """Replacement for the ORM Document built during upload."""

    def __init__(self, **kwargs):
        """Record the constructor kwargs and assign a stable id."""
        self.__dict__.update(kwargs)
        self.id = "doc-1"


@pytest.fixture
def document_model_stub(monkeypatch):
    """Swap the ORM Document for a recording stub, for upload tests only.

    Instantiating the real ORM model currently fails during mapper configuration
    because of a pre-existing relationship definition unrelated to path handling
    (User.audit_logs has no matching foreign key). Only the ORM object is stubbed;
    the path guards under test are exercised for real.
    """
    monkeypatch.setattr("app.services.storage_service.Document", _RecordedDocument)


def _document(file_path):
    """Stand-in for a Document row; only the attributes the service reads.

    The real ORM model is avoided because mapper configuration currently fails on
    an unrelated pre-existing relationship definition, and path containment does
    not depend on it.
    """
    return SimpleNamespace(
        id="doc-1",
        storage_backend="local",
        file_path=file_path,
    )


class TestStorageRoot:
    def test_storage_root_is_resolved(self, storage_root):
        """The root is fully resolved (symlinks, trailing separators)."""
        assert _storage_root() == storage_root

    def test_boundary_rejects_sibling_prefix(self, storage_root):
        """A sibling directory sharing the root's name prefix is not inside it."""
        assert _storage_boundary() == storage_root + os.sep
        assert not f"{storage_root}-evil/file.txt".startswith(_storage_boundary())

    def test_boundary_handles_filesystem_root(self, monkeypatch):
        """At '/' the boundary must not collapse to '//'."""
        monkeypatch.setattr(
            "app.services.storage_service.settings.STORAGE_LOCAL_PATH", os.sep
        )
        assert _storage_boundary() == os.sep
        assert "/etc/passwd".startswith(_storage_boundary())


class TestUploadPathTraversal:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "malicious_name",
        [
            "../../../etc/passwd",
            "/etc/passwd",
            "foo/../bar/../../etc/passwd",
            "..",
            ".",
            "",
            "../\x00evil",
        ],
    )
    async def test_traversal_filenames_are_written_inside_root(
        self, storage_root, document_model_stub, malicious_name
    ):
        """Traversal filenames land inside the storage root."""
        session = _StubSession()
        service = StorageService(session)

        result = await service.upload_file(
            content=b"payload",
            filename=malicious_name,
            file_type="text/plain",
            uploaded_by_id="11111111-1111-1111-1111-111111111111",
        )

        written = result["file_path"]
        assert written.startswith(storage_root + os.sep)
        assert os.path.isfile(written)
        assert Path(written).read_bytes() == b"payload"

    @pytest.mark.asyncio
    async def test_normal_filename_is_preserved(
        self, storage_root, document_model_stub
    ):
        """A normal filename keeps its name and lands in the root."""
        session = _StubSession()
        service = StorageService(session)

        result = await service.upload_file(
            content=b"report",
            filename="quarterly-report.pdf",
            file_type="application/pdf",
            uploaded_by_id="11111111-1111-1111-1111-111111111111",
        )

        assert result["file_path"].endswith("_quarterly-report.pdf")
        assert result["file_path"].startswith(storage_root + os.sep)

    @pytest.mark.asyncio
    async def test_upload_rejects_file_path_escaping_root(
        self, storage_root, document_model_stub, monkeypatch
    ):
        """Pin the file-path guard itself, not just the filename sanitizer.

        Filenames reaching the guard are already sanitized, so the guard is
        unreachable through the public API. Simulate a broken upstream invariant
        by returning a traversal fragment from uuid4; the guard must reject it.
        """
        monkeypatch.setattr(
            "app.services.storage_service.uuid.uuid4", lambda: "../../../../evil"
        )
        service = StorageService(_StubSession())

        with pytest.raises(ValueError, match="Invalid file path"):
            await service.upload_file(
                content=b"payload",
                filename="ok.pdf",
                file_type="application/pdf",
                uploaded_by_id="11111111-1111-1111-1111-111111111111",
            )

    @pytest.mark.asyncio
    async def test_upload_rejects_storage_path_escaping_root(
        self, storage_root, document_model_stub, monkeypatch
    ):
        """Pin the directory guard with a date component that escapes the root."""

        class _EscapingDate:
            @staticmethod
            def strftime(_fmt):
                """Return a traversal fragment in place of a date component."""
                return "../../.."

        class _EscapingDateTime:
            @staticmethod
            def now(_tz):
                """Return the escaping date double."""
                return _EscapingDate()

        monkeypatch.setattr(
            "app.services.storage_service.datetime", _EscapingDateTime
        )
        service = StorageService(_StubSession())

        with pytest.raises(ValueError, match="Invalid storage path"):
            await service.upload_file(
                content=b"payload",
                filename="ok.pdf",
                file_type="application/pdf",
                uploaded_by_id="11111111-1111-1111-1111-111111111111",
            )


class TestDownloadPathTraversal:
    @pytest.mark.asyncio
    async def test_download_rejects_file_outside_root(self, storage_root):
        """A file outside the root is not served."""
        with tempfile.NamedTemporaryFile(delete=False) as secret:
            secret.write(b"top secret")
            secret_path = secret.name
        try:
            document = _document(secret_path)
            service = StorageService(_StubSession(document))

            assert await service.download_file(document.id) is None
        finally:
            os.remove(secret_path)

    @pytest.mark.asyncio
    async def test_download_allows_file_inside_root(self, storage_root):
        """A file inside the root is served."""
        inside_path = os.path.join(storage_root, "docs", "report.txt")
        os.makedirs(os.path.dirname(inside_path))
        Path(inside_path).write_bytes(b"report body")

        document = _document(inside_path)
        service = StorageService(_StubSession(document))

        assert await service.download_file(document.id) == b"report body"

    @pytest.mark.asyncio
    async def test_download_rejects_sibling_prefix_path(self, storage_root):
        """A '<root>-evil' sibling must not pass a bare startswith(root) check."""
        sibling_dir = storage_root + "-evil"
        os.makedirs(sibling_dir, exist_ok=True)
        sibling_file = os.path.join(sibling_dir, "loot.txt")
        Path(sibling_file).write_bytes(b"loot")

        document = _document(sibling_file)
        service = StorageService(_StubSession(document))

        assert await service.download_file(document.id) is None

    @pytest.mark.asyncio
    async def test_download_rejects_symlink_escape(self, storage_root):
        """A symlink inside the root that points outside is rejected."""
        with tempfile.TemporaryDirectory() as outside_dir:
            secret = os.path.join(outside_dir, "secret.txt")
            Path(secret).write_bytes(b"secret")
            link = os.path.join(storage_root, "escape")
            os.symlink(outside_dir, link)

            document = _document(os.path.join(link, "secret.txt"))
            service = StorageService(_StubSession(document))

            assert await service.download_file(document.id) is None

    @pytest.mark.asyncio
    async def test_download_rejects_traversal_path(self, storage_root):
        """A stored path using '..' is rejected."""
        outside = os.path.join(os.path.dirname(storage_root), "outside.txt")
        Path(outside).write_bytes(b"outside")

        document = _document(f"{storage_root}/../outside.txt")
        service = StorageService(_StubSession(document))

        assert await service.download_file(document.id) is None


class TestDeletePathTraversal:
    @pytest.mark.asyncio
    async def test_delete_refuses_to_unlink_outside_root(self, storage_root):
        """A file outside the root is not unlinked."""
        with tempfile.NamedTemporaryFile(delete=False) as secret:
            secret.write(b"keep me")
            secret_path = secret.name

        document = _document(secret_path)
        session = _StubSession(document)
        service = StorageService(session)

        assert await service.delete_file(document.id) is True
        assert os.path.exists(secret_path)
        assert document in session.deleted

        os.remove(secret_path)

    @pytest.mark.asyncio
    async def test_delete_refuses_sibling_prefix_path(self, storage_root):
        """A '<root>-evil' sibling must not be unlinked."""
        sibling_dir = storage_root + "-evil"
        os.makedirs(sibling_dir, exist_ok=True)
        sibling_file = os.path.join(sibling_dir, "keep.txt")
        Path(sibling_file).write_bytes(b"keep")

        document = _document(sibling_file)
        session = _StubSession(document)
        service = StorageService(session)

        assert await service.delete_file(document.id) is True
        assert os.path.exists(sibling_file)

    @pytest.mark.asyncio
    async def test_delete_removes_file_inside_root(self, storage_root):
        """A file inside the root is unlinked."""
        inside_path = os.path.join(storage_root, "gone.txt")
        Path(inside_path).write_bytes(b"bye")

        document = _document(inside_path)
        session = _StubSession(document)
        service = StorageService(session)

        assert await service.delete_file(document.id) is True
        assert not os.path.exists(inside_path)


class TestRagDocumentRead:
    """The RAG read sink previously had no containment check at all."""

    @pytest.mark.asyncio
    async def test_reads_document_inside_root(self, storage_root):
        """An in-root document is read."""
        inside_path = os.path.join(storage_root, "notes.txt")
        Path(inside_path).write_text("ingest me", encoding="utf-8")

        service = RAGService(_StubSession())
        assert await service._read_document_content(_document(inside_path)) == "ingest me"

    @pytest.mark.asyncio
    async def test_refuses_document_outside_root(self, storage_root):
        """An out-of-root document returns no content."""
        outside = os.path.join(os.path.dirname(storage_root), "secret.txt")
        Path(outside).write_text("top secret", encoding="utf-8")

        service = RAGService(_StubSession())
        assert await service._read_document_content(_document(outside)) == ""

    @pytest.mark.asyncio
    async def test_refuses_symlink_escape(self, storage_root):
        """A symlink pointing outside the root returns no content."""
        with tempfile.TemporaryDirectory() as outside_dir:
            Path(os.path.join(outside_dir, "secret.txt")).write_text(
                "secret", encoding="utf-8"
            )
            link = os.path.join(storage_root, "escape")
            os.symlink(outside_dir, link)

            service = RAGService(_StubSession())
            target = os.path.join(link, "secret.txt")
            assert await service._read_document_content(_document(target)) == ""

    @pytest.mark.asyncio
    async def test_refuses_traversal_document(self, storage_root):
        """A traversal document path returns no content."""
        outside = os.path.join(os.path.dirname(storage_root), "traversal.txt")
        Path(outside).write_text("nope", encoding="utf-8")

        service = RAGService(_StubSession())
        traversal = f"{storage_root}/../traversal.txt"
        assert await service._read_document_content(_document(traversal)) == ""
