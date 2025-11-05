import os
import hashlib
import sys
import types

sys.path.append(str(os.path.dirname(os.path.dirname(__file__))))
PyPDF2 = types.ModuleType("PyPDF2")
PyPDF2.PdfReader = object
sys.modules["PyPDF2"] = PyPDF2

import file_organizer
from file_organizer import compute_hash, handle_duplicates, categorize_file


def test_compute_hash_small_file(tmp_path):
    file_path = tmp_path / "sample.txt"
    content = b"hello world"
    file_path.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert compute_hash(str(file_path)) == expected


def test_compute_hash_large_file(tmp_path):
    file_path = tmp_path / "large.bin"
    size = 11 * 1024 * 1024  # 11 MB
    content = b"a" * size
    file_path.write_bytes(content)
    expected_hash = hashlib.sha256()
    expected_hash.update(content[:8192])
    expected_hash.update(content[-8192:])
    assert compute_hash(str(file_path)) == expected_hash.hexdigest()


def test_handle_duplicates(tmp_path):
    duplicates_dir = tmp_path / "duplicates"
    duplicates_dir.mkdir()

    content = b"duplicate content"
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_bytes(content)
    file2.write_bytes(content)

    hash_value = compute_hash(str(file1))

    handle_duplicates(str(file1), str(duplicates_dir))
    assert not file1.exists()
    assert (duplicates_dir / hash_value / "file1.txt").exists()

    handle_duplicates(str(file2), str(duplicates_dir))
    assert not file2.exists()
    duplicate_path = duplicates_dir / hash_value[:2] / hash_value[2:4] / hash_value / "file2.txt"
    assert duplicate_path.exists()


def test_categorize_file(monkeypatch):
    class DummyVectorizer:
        def transform(self, texts):
            return texts

    class DummyModel:
        def predict(self, vectors):
            return ["academic"]

    monkeypatch.setattr(file_organizer, "vectorizer", DummyVectorizer())
    monkeypatch.setattr(file_organizer, "model", DummyModel())
    monkeypatch.setattr(file_organizer, "word_tokenize", lambda text: text.lower().split())

    result = categorize_file("doc.txt", "This research paper studies AI.")
    assert result == "academic"
