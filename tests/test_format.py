import json
import tempfile
from pathlib import Path

from llm_multi.format import parse_input, output_results


class TestParseInput:
    def test_parse_jsonl_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            jsonl_file = tmpdir_path / "test.jsonl"
            with open(jsonl_file, "w") as f:
                f.write('{"path": "file1.txt", "content": "content1"}\n')
                f.write('{"path": "file2.txt", "content": "content2"}\n')

            items = parse_input(str(jsonl_file), "jsonl")

            assert len(items) == 2
            assert items[0]["path"] == "file1.txt"
            assert items[0]["content"] == "content1"

    def test_parse_json_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            json_file = tmpdir_path / "test.json"
            data = {"file1.txt": "content1", "file2.txt": "content2"}
            with open(json_file, "w") as f:
                json.dump(data, f)

            items = parse_input(str(json_file), "json")

            assert len(items) == 2
            paths = [item["path"] for item in items]
            assert "file1.txt" in paths
            assert "file2.txt" in paths

    def test_parse_jsonarr_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            jsonarr_file = tmpdir_path / "test.json"
            data = ["content1", "content2"]
            with open(jsonarr_file, "w") as f:
                json.dump(data, f)

            items = parse_input(str(jsonarr_file), "jsonarr")

            assert len(items) == 2
            assert items[0]["path"] == "item_0"
            assert items[0]["content"] == "content1"
            assert items[1]["path"] == "item_1"
            assert items[1]["content"] == "content2"

    def test_parse_xml_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            xml_file = tmpdir_path / "test.xml"
            xml_content = "<file1_txt>Hello world</file1_txt><file2_py>&lt;em&gt;escaped&lt;/em&gt;</file2_py>"
            xml_file.write_text(xml_content)

            items = parse_input(str(xml_file), "xml")

            assert len(items) == 2
            assert items[0]["path"] == "file1.txt"
            assert items[0]["content"] == "Hello world"
            assert items[1]["path"] == "file2.py"
            assert items[1]["content"] == "<em>escaped</em>"

    def test_parse_xmlish_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            xml_file = tmpdir_path / "test.xml"
            xml_content = "<file1_txt>Hello world</file1_txt><file2_html><em>not escaped</em></file2_html>"
            xml_file.write_text(xml_content)

            items = parse_input(str(xml_file), "xmlish")

            assert len(items) == 2
            assert items[0]["path"] == "file1.txt"
            assert items[0]["content"] == "Hello world"
            assert items[1]["path"] == "file2.html"
            assert items[1]["content"] == "<em>not escaped</em>"


class TestOutputResults:
    def test_output_jsonl_format(self, capsys):
        results = [
            {"path": "file1.txt", "content": "Response1"},
            {"path": "file2.txt", "content": "Response2"},
        ]

        output_results(results, None, "jsonl")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        assert len(lines) == 2
        result1 = json.loads(lines[0])
        json.loads(lines[1])

        assert result1["path"] == "file1.txt"
        assert result1["content"] == "Response1"

    def test_output_json_format(self, capsys):
        results = [
            {"path": "file1.txt", "content": "Response1"},
            {"path": "file2.txt", "content": "Response2"},
        ]

        output_results(results, None, "json")

        captured = capsys.readouterr()
        result = json.loads(captured.out.strip())

        assert result["file1.txt"] == "Response1"
        assert result["file2.txt"] == "Response2"

    def test_output_jsonarr_format(self, capsys):
        results = [
            {"path": "file1.txt", "content": "Response1"},
            {"path": "file2.txt", "content": "Response2"},
        ]

        output_results(results, None, "jsonarr")

        captured = capsys.readouterr()
        result = json.loads(captured.out.strip())

        assert isinstance(result, list)
        assert result == ["Response1", "Response2"]

    def test_output_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            results = [{"path": "file1.txt", "content": "Response1"}]

            output_file = tmpdir_path / "output.jsonl"
            output_results(results, str(output_file), "jsonl")

            assert output_file.exists()
            result = json.loads(output_file.read_text())
            assert result["content"] == "Response1"

    def test_output_json_with_errors(self, capsys):
        results = [
            {"path": "file1.txt", "content": "Response1"},
            {"path": "file2.txt", "error": "API Error"},
        ]

        output_results(results, None, "json")

        captured = capsys.readouterr()
        result = json.loads(captured.out.strip())

        assert result["file1.txt"] == "Response1"
        assert result["file2.txt"]["error"] == "API Error"
