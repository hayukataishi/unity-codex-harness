from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract_imagegen_result.py"
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)
PNG_B64 = base64.b64encode(PNG_BYTES).decode("ascii")


class ExtractImagegenResultTests(unittest.TestCase):
    def write_jsonl(self, path: Path, records: list[object]) -> None:
        path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )

    def run_script(self, session: Path, call_id: str, output: Path):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--session-jsonl",
                str(session),
                "--call-id",
                call_id,
                "--output",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_extracts_png_for_matching_call_id(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            session = root / "session.jsonl"
            output = root / "out" / "sprite.png"
            self.write_jsonl(
                session,
                [
                    {
                        "payload": {
                            "type": "image_generation_end",
                            "call_id": "call_other",
                            "result": PNG_B64,
                        }
                    },
                    {
                        "payload": {
                            "type": "image_generation_end",
                            "call_id": "call_target",
                            "result": {"b64_json": PNG_B64},
                        }
                    },
                ],
            )

            completed = self.run_script(session, "call_target", output)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(output.read_bytes(), PNG_BYTES)
            self.assertIn("1x1", completed.stdout)

    def test_rejects_missing_call_id(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            session = root / "session.jsonl"
            output = root / "sprite.png"
            self.write_jsonl(
                session,
                [
                    {
                        "payload": {
                            "type": "image_generation_end",
                            "call_id": "call_other",
                            "result": PNG_B64,
                        }
                    }
                ],
            )

            completed = self.run_script(session, "call_target", output)

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("no image_generation_end", completed.stderr)
            self.assertFalse(output.exists())

    def test_rejects_non_png_payload(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            session = root / "session.jsonl"
            output = root / "sprite.png"
            self.write_jsonl(
                session,
                [
                    {
                        "payload": {
                            "type": "image_generation_end",
                            "call_id": "call_target",
                            "result": base64.b64encode(b"not a png").decode(
                                "ascii"
                            ),
                        }
                    }
                ],
            )

            completed = self.run_script(session, "call_target", output)

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("did not contain a PNG", completed.stderr)
            self.assertFalse(output.exists())

    def test_rejects_existing_output_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            session = root / "session.jsonl"
            output = root / "sprite.png"
            output.write_bytes(b"existing")
            self.write_jsonl(
                session,
                [
                    {
                        "payload": {
                            "type": "image_generation_end",
                            "call_id": "call_target",
                            "result": PNG_B64,
                        }
                    }
                ],
            )

            completed = self.run_script(session, "call_target", output)

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("output already exists", completed.stderr)
            self.assertEqual(output.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
