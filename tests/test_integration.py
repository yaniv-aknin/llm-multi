import json
import pytest
import tempfile
import os
import subprocess
from pathlib import Path
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_files(tmp_path):
    """Create temporary test files."""
    file1 = tmp_path / "test1.txt"
    file1.write_text("Hello world from file 1")

    file2 = tmp_path / "test2.py"
    file2.write_text('def hello():\n    return "Hello from Python"')

    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file3 = subdir / "nested.txt"
    file3.write_text("Nested file content")

    yield {"dir": tmp_path, "file1": file1, "file2": file2, "file3": file3}


class TestIntegration:
    def test_archive_create_jsonl_format(self, temp_files):
        """Test archive command creates JSONL format correctly."""
        files = [str(temp_files["file1"]), str(temp_files["file2"])]

        result = subprocess.run(
            ["llm", "archive", "--basename"] + files,
            capture_output=True,
            text=True,
            cwd=str(temp_files["dir"]),
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2

        item1 = json.loads(lines[0])
        item2 = json.loads(lines[1])

        assert item1["path"] == "test1.txt"
        assert item2["path"] == "test2.py"
        assert item1["content"] == "Hello world from file 1"

    def test_archive_create_json_format(self, temp_files):
        """Test archive command creates JSON format correctly."""
        files = [str(temp_files["file1"]), str(temp_files["file2"])]

        result = subprocess.run(
            ["llm", "archive", "--basename", "--format", "json"] + files,
            capture_output=True,
            text=True,
            cwd=str(temp_files["dir"]),
        )

        assert result.returncode == 0
        data = json.loads(result.stdout.strip())

        assert "test1.txt" in data
        assert "test2.py" in data
        assert data["test1.txt"] == "Hello world from file 1"

    def test_archive_create_jsonarr_format(self, temp_files):
        """Test archive command creates JSON array format correctly."""
        files = [str(temp_files["file1"]), str(temp_files["file2"])]

        result = subprocess.run(
            ["llm", "archive", "--format", "jsonarr"] + files,
            capture_output=True,
            text=True,
            cwd=str(temp_files["dir"]),
        )

        assert result.returncode == 0
        data = json.loads(result.stdout.strip())

        assert isinstance(data, list)
        assert len(data) == 2
        assert "Hello world from file 1" in data

    def test_archive_extract_workflow(self, temp_files):
        """Test complete archive create -> extract workflow."""
        with tempfile.TemporaryDirectory() as work_dir:
            work_path = Path(work_dir)

            files = [str(temp_files["file1"]), str(temp_files["file2"])]

            create_result = subprocess.run(
                ["llm", "archive", "--basename"] + files,
                capture_output=True,
                text=True,
                cwd=str(work_path),
            )

            assert create_result.returncode == 0

            archive_file = work_path / "test.jsonl"
            with open(archive_file, "w") as f:
                f.write(create_result.stdout)

            extract_dir = work_path / "extracted"
            extract_dir.mkdir()

            old_cwd = os.getcwd()
            try:
                os.chdir(str(extract_dir))

                extract_result = subprocess.run(
                    ["llm", "archive", "--extract", str(archive_file)],
                    capture_output=True,
                    text=True,
                )

                assert extract_result.returncode == 0
                assert (extract_dir / "test1.txt").exists()
                assert (extract_dir / "test2.py").exists()
                assert (
                    extract_dir / "test1.txt"
                ).read_text() == "Hello world from file 1"
            finally:
                os.chdir(old_cwd)

    def test_archive_json_extract_workflow(self, temp_files):
        """Test JSON format create -> extract workflow."""
        with tempfile.TemporaryDirectory() as work_dir:
            work_path = Path(work_dir)

            files = [str(temp_files["file1"]), str(temp_files["file2"])]

            create_result = subprocess.run(
                ["llm", "archive", "--basename", "--format", "json"] + files,
                capture_output=True,
                text=True,
                cwd=str(work_path),
            )

            assert create_result.returncode == 0

            archive_file = work_path / "test.json"
            with open(archive_file, "w") as f:
                f.write(create_result.stdout)

            extract_dir = work_path / "extracted"
            extract_dir.mkdir()

            old_cwd = os.getcwd()
            try:
                os.chdir(str(extract_dir))

                extract_result = subprocess.run(
                    [
                        "llm",
                        "archive",
                        "--extract",
                        "--format",
                        "json",
                        str(archive_file),
                    ],
                    capture_output=True,
                    text=True,
                )

                assert extract_result.returncode == 0
                assert (extract_dir / "test1.txt").exists()
                assert (extract_dir / "test2.py").exists()
            finally:
                os.chdir(old_cwd)

    def test_validation_errors(self):
        """Test CLI validation errors."""
        result = subprocess.run(
            ["llm", "archive", "--create", "--extract"], capture_output=True, text=True
        )

        assert result.returncode != 0
        assert "Cannot use both --create and --extract" in result.stderr

    def test_format_validation_error(self):
        """Test format validation errors."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"path": "test", "content": "data"}\n')
            temp_file = f.name

        try:
            result = subprocess.run(
                [
                    "llm",
                    "map",
                    "--input",
                    "--oformat",
                    "json",
                    temp_file,
                    "test prompt",
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode != 0
            assert (
                "Cannot use --input with --json or --jsonarr output formats"
                in result.stderr
            )
        finally:
            os.unlink(temp_file)

    def test_archive_create_xml_format(self, temp_files):
        """Test archive command creates XML format correctly."""
        files = [str(temp_files["file1"]), str(temp_files["file2"])]

        result = subprocess.run(
            ["llm", "archive", "--basename", "--format", "xml"] + files,
            capture_output=True,
            text=True,
            cwd=str(temp_files["dir"]),
        )

        assert result.returncode == 0
        output = result.stdout.strip()
        assert "<test1_txt>\nHello world from file 1\n</test1_txt>" in output
        assert "<test2_py>" in output

    def test_archive_create_xmlish_format(self, temp_files):
        """Test archive command creates XMLish format correctly."""
        files = [str(temp_files["file1"]), str(temp_files["file2"])]

        result = subprocess.run(
            ["llm", "archive", "--basename", "--format", "xmlish"] + files,
            capture_output=True,
            text=True,
            cwd=str(temp_files["dir"]),
        )

        assert result.returncode == 0
        output = result.stdout.strip()
        assert "<test1_txt>\nHello world from file 1\n</test1_txt>" in output
        assert "<test2_py>" in output

    def test_archive_xml_extract_workflow(self, temp_files):
        """Test XML format create -> extract workflow."""
        with tempfile.TemporaryDirectory() as work_dir:
            work_path = Path(work_dir)

            files = [str(temp_files["file1"]), str(temp_files["file2"])]

            create_result = subprocess.run(
                ["llm", "archive", "--basename", "--format", "xml"] + files,
                capture_output=True,
                text=True,
                cwd=str(work_path),
            )

            assert create_result.returncode == 0

            archive_file = work_path / "test.xml"
            with open(archive_file, "w") as f:
                f.write(create_result.stdout)

            extract_dir = work_path / "extracted"
            extract_dir.mkdir()

            old_cwd = os.getcwd()
            try:
                os.chdir(str(extract_dir))

                extract_result = subprocess.run(
                    [
                        "llm",
                        "archive",
                        "--extract",
                        "--format",
                        "xml",
                        str(archive_file),
                    ],
                    capture_output=True,
                    text=True,
                )

                assert extract_result.returncode == 0
                assert (extract_dir / "test1.txt").exists()
                assert (extract_dir / "test2.py").exists()
                assert (
                    extract_dir / "test1.txt"
                ).read_text() == "Hello world from file 1"
            finally:
                os.chdir(old_cwd)
