import json
import pytest
import tempfile
import os
import io
from pathlib import Path

from llm_multi.archive import create_archive, extract_archive


@pytest.fixture
def temp_files():
    """Create temporary test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        file1 = tmpdir_path / "test1.txt"
        file1.write_text("Hello world from file 1")

        file2 = tmpdir_path / "test2.py"
        file2.write_text('def hello():\n    return "Hello from Python"')

        subdir = tmpdir_path / "subdir"
        subdir.mkdir()
        file3 = subdir / "nested.txt"
        file3.write_text("Nested file content")

        yield {"dir": tmpdir_path, "file1": file1, "file2": file2, "file3": file3}


@pytest.fixture
def sample_jsonl():
    """Create sample JSONL content."""
    return [
        {"path": "test1.txt", "content": "Hello world"},
        {"path": "test2.py", "content": "print('hello')"},
        {"path": "nested/file.txt", "content": "Nested content"},
    ]


class TestCreateBall:
    def test_create_archive_jsonl_format(self, temp_files, capsys):
        files = [str(temp_files["file1"]), str(temp_files["file2"])]
        create_archive(files, basename=False, basedir=None, format="jsonl")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        assert len(lines) == 2

        item1 = json.loads(lines[0])
        item2 = json.loads(lines[1])

        assert item1["content"] == "Hello world from file 1"
        assert item2["content"] == 'def hello():\n    return "Hello from Python"'
        assert str(temp_files["file1"]) in item1["path"]
        assert str(temp_files["file2"]) in item2["path"]

    def test_create_archive_json_format(self, temp_files, capsys):
        files = [str(temp_files["file1"]), str(temp_files["file2"])]
        create_archive(files, basename=True, basedir=None, format="json")

        captured = capsys.readouterr()
        result = json.loads(captured.out.strip())

        assert "test1.txt" in result
        assert "test2.py" in result
        assert result["test1.txt"] == "Hello world from file 1"
        assert result["test2.py"] == 'def hello():\n    return "Hello from Python"'

    def test_create_archive_jsonarr_format(self, temp_files, capsys):
        files = [str(temp_files["file1"]), str(temp_files["file2"])]
        create_archive(files, basename=False, basedir=None, format="jsonarr")

        captured = capsys.readouterr()
        result = json.loads(captured.out.strip())

        assert isinstance(result, list)
        assert len(result) == 2
        assert "Hello world from file 1" in result
        assert 'def hello():\n    return "Hello from Python"' in result

    def test_create_archive_basename(self, temp_files, capsys):
        files = [str(temp_files["file1"]), str(temp_files["file2"])]
        create_archive(files, basename=True, basedir=None, format="jsonl")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        item1 = json.loads(lines[0])
        item2 = json.loads(lines[1])

        assert item1["path"] == "test1.txt"
        assert item2["path"] == "test2.py"

    def test_create_archive_basedir(self, temp_files, capsys):
        files = [str(temp_files["file1"]), str(temp_files["file3"])]
        create_archive(
            files, basename=False, basedir=str(temp_files["dir"]), format="jsonl"
        )

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        item1 = json.loads(lines[0])
        item2 = json.loads(lines[1])

        assert item1["path"] == "test1.txt"
        assert item2["path"] == "subdir/nested.txt"

    def test_create_archive_basedir_warning(self, temp_files, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("external content")
            external_file = f.name

        try:
            files = [str(temp_files["file1"]), external_file]
            create_archive(
                files, basename=False, basedir=str(temp_files["dir"]), format="jsonl"
            )

            captured = capsys.readouterr()
            lines = captured.out.strip().split("\n") if captured.out.strip() else []

            assert "Warning:" in captured.err
            assert "does not have prefix" in captured.err
            assert len(lines) == 1
        finally:
            os.unlink(external_file)

    def test_create_archive_xml_format(self, temp_files, capsys):
        files = [str(temp_files["file1"]), str(temp_files["file2"])]
        create_archive(files, basename=True, basedir=None, format="xml")

        captured = capsys.readouterr()
        output = captured.out.strip()

        assert "<test1_txt>\nHello world from file 1\n</test1_txt>" in output
        assert (
            "&lt;em&gt;" not in output
        )  # Should not have HTML escaping for plain text

    def test_create_archive_xml_format_with_html(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            html_file = tmpdir_path / "test.html"
            html_file.write_text("<em>I am cool</em>")

            create_archive([str(html_file)], basename=True, basedir=None, format="xml")

            captured = capsys.readouterr()
            output = captured.out.strip()

            assert "<test_html>\n&lt;em&gt;I am cool&lt;/em&gt;\n</test_html>" in output

    def test_create_archive_xmlish_format(self, temp_files, capsys):
        files = [str(temp_files["file1"]), str(temp_files["file2"])]
        create_archive(files, basename=True, basedir=None, format="xmlish")

        captured = capsys.readouterr()
        output = captured.out.strip()

        assert "<test1_txt>\nHello world from file 1\n</test1_txt>" in output

    def test_create_archive_xmlish_format_with_html(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            html_file = tmpdir_path / "test.html"
            html_file.write_text("<em>I am cool</em>")

            create_archive(
                [str(html_file)], basename=True, basedir=None, format="xmlish"
            )

            captured = capsys.readouterr()
            output = captured.out.strip()

            assert "<test_html>\n<em>I am cool</em>\n</test_html>" in output

    def test_create_archive_empty_files_jsonl(self, capsys):
        create_archive([], basename=False, basedir=None, format="jsonl")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_create_archive_empty_files_json(self, capsys):
        create_archive([], basename=False, basedir=None, format="json")
        captured = capsys.readouterr()
        assert captured.out.strip() == "{}"

    def test_create_archive_empty_files_jsonarr(self, capsys):
        create_archive([], basename=False, basedir=None, format="jsonarr")
        captured = capsys.readouterr()
        assert captured.out.strip() == "[]"

    def test_create_archive_empty_files_xml(self, capsys):
        create_archive([], basename=False, basedir=None, format="xml")
        captured = capsys.readouterr()
        assert captured.out == ""


class TestExtractBall:
    def test_extract_archive_jsonl_format(self, sample_jsonl):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            jsonl_file = tmpdir_path / "test.jsonl"
            with open(jsonl_file, "w") as f:
                for item in sample_jsonl:
                    f.write(json.dumps(item) + "\n")

            extract_dir = tmpdir_path / "extract"
            extract_dir.mkdir()
            old_cwd = os.getcwd()

            try:
                os.chdir(str(extract_dir))
                with open(jsonl_file, "r") as f:
                    extract_archive(f, basename=False, basedir=None, format="jsonl")

                assert (extract_dir / "test1.txt").exists()
                assert (extract_dir / "test2.py").exists()
                assert (extract_dir / "nested" / "file.txt").exists()

                assert (extract_dir / "test1.txt").read_text() == "Hello world"
                assert (extract_dir / "test2.py").read_text() == "print('hello')"
            finally:
                os.chdir(old_cwd)

    def test_extract_archive_json_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            json_file = tmpdir_path / "test.json"
            data = {"test1.txt": "Hello world", "test2.py": "print('hello')"}
            with open(json_file, "w") as f:
                json.dump(data, f)

            extract_dir = tmpdir_path / "extract"
            extract_dir.mkdir()
            old_cwd = os.getcwd()

            try:
                os.chdir(str(extract_dir))
                with open(json_file, "r") as f:
                    extract_archive(f, basename=False, basedir=None, format="json")

                assert (extract_dir / "test1.txt").exists()
                assert (extract_dir / "test2.py").exists()
                assert (extract_dir / "test1.txt").read_text() == "Hello world"
                assert (extract_dir / "test2.py").read_text() == "print('hello')"
            finally:
                os.chdir(old_cwd)

    def test_extract_archive_jsonarr_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            jsonarr_file = tmpdir_path / "test.json"
            data = ["Hello world", "print('hello')", "more content"]
            with open(jsonarr_file, "w") as f:
                json.dump(data, f)

            extract_dir = tmpdir_path / "extract"
            extract_dir.mkdir()
            old_cwd = os.getcwd()

            try:
                os.chdir(str(extract_dir))
                with open(jsonarr_file, "r") as f:
                    extract_archive(f, basename=False, basedir=None, format="jsonarr")

                assert (extract_dir / "item_0.txt").exists()
                assert (extract_dir / "item_1.txt").exists()
                assert (extract_dir / "item_2.txt").exists()
                assert (extract_dir / "item_0.txt").read_text() == "Hello world"
                assert (extract_dir / "item_1.txt").read_text() == "print('hello')"
            finally:
                os.chdir(old_cwd)

    def test_extract_archive_basename(self, sample_jsonl):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            jsonl_file = tmpdir_path / "test.jsonl"
            with open(jsonl_file, "w") as f:
                for item in sample_jsonl:
                    f.write(json.dumps(item) + "\n")

            extract_dir = tmpdir_path / "extract"
            extract_dir.mkdir()
            old_cwd = os.getcwd()

            try:
                os.chdir(str(extract_dir))
                with open(jsonl_file, "r") as f:
                    extract_archive(f, basename=True, basedir=None, format="jsonl")

                assert (extract_dir / "test1.txt").exists()
                assert (extract_dir / "test2.py").exists()
                assert (extract_dir / "file.txt").exists()
                assert not (extract_dir / "nested" / "file.txt").exists()
            finally:
                os.chdir(old_cwd)

    def test_extract_archive_basedir(self, sample_jsonl):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            jsonl_file = tmpdir_path / "test.jsonl"
            with open(jsonl_file, "w") as f:
                for item in sample_jsonl:
                    f.write(json.dumps(item) + "\n")

            extract_dir = tmpdir_path / "extract"
            extract_dir.mkdir()
            old_cwd = os.getcwd()

            try:
                os.chdir(str(extract_dir))
                with open(jsonl_file, "r") as f:
                    extract_archive(f, basename=False, basedir="output", format="jsonl")

                assert (extract_dir / "output" / "test1.txt").exists()
                assert (extract_dir / "output" / "test2.py").exists()
                assert (extract_dir / "output" / "nested" / "file.txt").exists()
            finally:
                os.chdir(old_cwd)

    def test_extract_archive_xml_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            xml_file = tmpdir_path / "test.xml"
            xml_content = "<test1_txt>Hello world</test1_txt><test2_py>&lt;em&gt;I am cool&lt;/em&gt;</test2_py>"
            xml_file.write_text(xml_content)

            extract_dir = tmpdir_path / "extract"
            extract_dir.mkdir()
            old_cwd = os.getcwd()

            try:
                os.chdir(str(extract_dir))
                with open(xml_file, "r") as f:
                    extract_archive(f, basename=False, basedir=None, format="xml")

                assert (extract_dir / "test1.txt").exists()
                assert (extract_dir / "test2.py").exists()
                assert (extract_dir / "test1.txt").read_text() == "Hello world"
                assert (extract_dir / "test2.py").read_text() == "<em>I am cool</em>"
            finally:
                os.chdir(old_cwd)

    def test_extract_archive_xmlish_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            xml_file = tmpdir_path / "test.xml"
            xml_content = "<test1_txt>Hello world</test1_txt><test2_html><em>I am cool</em></test2_html>"
            xml_file.write_text(xml_content)

            extract_dir = tmpdir_path / "extract"
            extract_dir.mkdir()
            old_cwd = os.getcwd()

            try:
                os.chdir(str(extract_dir))
                with open(xml_file, "r") as f:
                    extract_archive(f, basename=False, basedir=None, format="xmlish")

                assert (extract_dir / "test1.txt").exists()
                assert (extract_dir / "test2.html").exists()
                assert (extract_dir / "test1.txt").read_text() == "Hello world"
                assert (extract_dir / "test2.html").read_text() == "<em>I am cool</em>"
            finally:
                os.chdir(old_cwd)

    def test_extract_archive_from_stdin(self, sample_jsonl):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            extract_dir = tmpdir_path / "extract"
            extract_dir.mkdir()
            old_cwd = os.getcwd()

            jsonl_content = "\n".join(json.dumps(item) for item in sample_jsonl)
            stdin_obj = io.StringIO(jsonl_content)

            try:
                os.chdir(str(extract_dir))
                extract_archive(stdin_obj, basename=False, basedir=None, format="jsonl")

                assert (extract_dir / "test1.txt").exists()
                assert (extract_dir / "test2.py").exists()
                assert (extract_dir / "nested" / "file.txt").exists()

                assert (extract_dir / "test1.txt").read_text() == "Hello world"
                assert (extract_dir / "test2.py").read_text() == "print('hello')"
            finally:
                os.chdir(old_cwd)
