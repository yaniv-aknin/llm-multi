import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from llm_multi.map import map_items


class TestMapJsonl:
    @patch("llm.get_model")
    def test_map_jsonl_basic(self, mock_get_model, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text.return_value = "This is Python code"
            mock_model.prompt.return_value = mock_response
            mock_get_model.return_value = mock_model

            jsonl_file = tmpdir_path / "test.jsonl"
            with open(jsonl_file, "w") as f:
                f.write('{"path": "test.py", "content": "print(\'hello\')"}\n')

            map_items(
                str(jsonl_file),
                "Describe this: {item}",
                "mock",
                0.0,
                100,
                1,
                None,
                1,
                False,
                "jsonl",
                "jsonl",
            )

            captured = capsys.readouterr()
            result = json.loads(captured.out.strip())

            assert result["path"] == "test.py"
            assert result["content"] == "This is Python code"
            assert "input" not in result

            mock_model.prompt.assert_called_once()
            call_args = mock_model.prompt.call_args[0][0]
            assert call_args == "Describe this: print('hello')"

    @patch("llm.get_model")
    def test_map_jsonl_with_content_flag(self, mock_get_model, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text.return_value = "This is Python code"
            mock_model.prompt.return_value = mock_response
            mock_get_model.return_value = mock_model

            jsonl_file = tmpdir_path / "test.jsonl"
            with open(jsonl_file, "w") as f:
                f.write('{"path": "test.py", "content": "print(\'hello\')"}\n')

            map_items(
                str(jsonl_file),
                "Describe this: {item}",
                "mock",
                0.0,
                100,
                1,
                None,
                1,
                True,
                "jsonl",
                "jsonl",
            )

            captured = capsys.readouterr()
            result = json.loads(captured.out.strip())

            assert result["path"] == "test.py"
            assert result["content"] == "This is Python code"
            assert result["input"] == "print('hello')"

    @patch("llm.get_model")
    def test_map_jsonl_no_item_placeholder(self, mock_get_model, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text.return_value = "Response"
            mock_model.prompt.return_value = mock_response
            mock_get_model.return_value = mock_model

            jsonl_file = tmpdir_path / "test.jsonl"
            with open(jsonl_file, "w") as f:
                f.write('{"path": "file.txt", "content": "data"}\n')

            map_items(
                str(jsonl_file),
                "Analyze this",
                "mock",
                0.0,
                100,
                1,
                None,
                1,
                False,
                "jsonl",
                "jsonl",
            )

            call_args = mock_model.prompt.call_args[0][0]
            assert call_args == "Analyze this\ndata"

    @patch("llm.get_model")
    def test_map_jsonl_with_output_file(self, mock_get_model):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text.return_value = "Response"
            mock_model.prompt.return_value = mock_response
            mock_get_model.return_value = mock_model

            jsonl_file = tmpdir_path / "test.jsonl"
            output_file = tmpdir_path / "output.jsonl"

            with open(jsonl_file, "w") as f:
                f.write('{"path": "file.txt", "content": "data"}\n')

            map_items(
                str(jsonl_file),
                "Process: {item}",
                "mock",
                0.0,
                100,
                1,
                str(output_file),
                1,
                False,
                "jsonl",
                "jsonl",
            )

            assert output_file.exists()
            result = json.loads(output_file.read_text())
            assert result["content"] == "Response"
            assert result["path"] == "file.txt"

    @patch("llm.get_model")
    def test_map_jsonl_error_handling(self, mock_get_model, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            mock_model = MagicMock()
            mock_model.prompt.side_effect = Exception("API Error")
            mock_get_model.return_value = mock_model

            jsonl_file = tmpdir_path / "test.jsonl"
            with open(jsonl_file, "w") as f:
                f.write('{"path": "file.txt", "content": "data"}\n')

            map_items(
                str(jsonl_file),
                "Process: {item}",
                "mock",
                0.0,
                100,
                1,
                None,
                1,
                False,
                "jsonl",
                "jsonl",
            )

            captured = capsys.readouterr()
            result = json.loads(captured.out.strip())

            assert "error" in result
            assert result["error"] == "API Error"
            assert result["path"] == "file.txt"

    @patch("llm.get_model")
    def test_map_json_input_format(self, mock_get_model, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text.return_value = "Response"
            mock_model.prompt.return_value = mock_response
            mock_get_model.return_value = mock_model

            json_file = tmpdir_path / "test.json"
            data = {"file1.txt": "content1", "file2.txt": "content2"}
            with open(json_file, "w") as f:
                json.dump(data, f)

            map_items(
                str(json_file),
                "Process: {item}",
                "mock",
                0.0,
                100,
                1,
                None,
                1,
                False,
                "json",
                "jsonl",
            )

            assert mock_model.prompt.call_count == 2

            captured = capsys.readouterr()
            lines = captured.out.strip().split("\n")
            assert len(lines) == 2

    @patch("llm.get_model")
    def test_map_jsonarr_input_format(self, mock_get_model, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text.return_value = "Response"
            mock_model.prompt.return_value = mock_response
            mock_get_model.return_value = mock_model

            jsonarr_file = tmpdir_path / "test.json"
            data = ["content1", "content2"]
            with open(jsonarr_file, "w") as f:
                json.dump(data, f)

            map_items(
                str(jsonarr_file),
                "Process: {item}",
                "mock",
                0.0,
                100,
                1,
                None,
                1,
                False,
                "jsonarr",
                "jsonl",
            )

            assert mock_model.prompt.call_count == 2

    @patch("llm.get_model")
    def test_map_json_output_format(self, mock_get_model, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text.return_value = "Response"
            mock_model.prompt.return_value = mock_response
            mock_get_model.return_value = mock_model

            jsonl_file = tmpdir_path / "test.jsonl"
            with open(jsonl_file, "w") as f:
                f.write('{"path": "file.txt", "content": "data"}\n')

            map_items(
                str(jsonl_file),
                "Process: {item}",
                "mock",
                0.0,
                100,
                1,
                None,
                1,
                False,
                "jsonl",
                "json",
            )

            captured = capsys.readouterr()
            result = json.loads(captured.out.strip())

            assert result["file.txt"] == "Response"

    @patch("llm.get_model")
    def test_map_jsonarr_output_format(self, mock_get_model, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text.return_value = "Response"
            mock_model.prompt.return_value = mock_response
            mock_get_model.return_value = mock_model

            jsonl_file = tmpdir_path / "test.jsonl"
            with open(jsonl_file, "w") as f:
                f.write('{"path": "file.txt", "content": "data"}\n')

            map_items(
                str(jsonl_file),
                "Process: {item}",
                "mock",
                0.0,
                100,
                1,
                None,
                1,
                False,
                "jsonl",
                "jsonarr",
            )

            captured = capsys.readouterr()
            result = json.loads(captured.out.strip())

            assert isinstance(result, list)
            assert result[0] == "Response"
