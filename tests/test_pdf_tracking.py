import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from chimera_exam_server import main, serverreport
import pytest
from pypdf import PdfReader
from chimera_exam_server.pydanticmodels import Finalise_Session_Detail


class FinalisePdfTrackingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = Finalise_Session_Detail(
            uid="session-1",
            username="candidate",
            set_name="set",
            set_type="RR",
            device_name="device",
        )
        self.database = Mock()
        self.database.finalise_session.return_value = "No Error"
        self.database.get_answers_obj_by_uid.return_value = {"type": "RR"}

    async def test_successful_pdf_creation_updates_status(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.pdf"
            report_path.write_bytes(b"%PDF")
            with (
                patch.object(main, "get_db", return_value=self.database),
                patch.object(main, "SERVER_MAKE_PDF_REPORT", True),
                patch.object(main, "create_answer_pdf", return_value=report_path),
            ):
                await main.finalise(self.session)

        self.database.mark_pdf_created.assert_called_once_with("session-1")

    async def test_failed_pdf_creation_does_not_update_status(self):
        with (
            patch.object(main, "get_db", return_value=self.database),
            patch.object(main, "SERVER_MAKE_PDF_REPORT", True),
            patch.object(main, "create_answer_pdf", return_value=None),
        ):
            with self.assertRaisesRegex(RuntimeError, "did not produce a file"):
                await main.finalise(self.session)

        self.database.mark_pdf_created.assert_not_called()

    async def test_finalise_skips_answer_retrieval_when_pdf_is_disabled(self):
        with (
            patch.object(main, "get_db", return_value=self.database),
            patch.object(main, "SERVER_MAKE_PDF_REPORT", False),
        ):
            await main.finalise(self.session)

        self.database.get_answers_obj_by_uid.assert_not_called()
        self.database.mark_pdf_created.assert_not_called()

    async def test_session_api_exposes_pdf_fields(self):
        self.database.query_all_sessions.return_value = [
            {
                "uid": "session-1",
                "final_dt": "2026-09-28T14:15:00",
                "pdf": 1,
                "pdf_dt": "2026-09-28T14:30:00",
            }
        ]
        with patch.object(main, "get_db", return_value=self.database):
            response = await main.q_all_sessions()

        self.assertEqual(response[0]["final_dt"], "2026-09-28T14:15:00")
        self.assertEqual(response[0]["pdf"], 1)
        self.assertEqual(response[0]["pdf_dt"], "2026-09-28T14:30:00")


@pytest.mark.parametrize(
    ("set_type", "case", "submitted_text"),
    [
        (
            "RR",
            {
                1: {
                    "RR_Normal": False,
                    "RR_Abnormal": True,
                    "RR_Desc": "RR_TEXT_MARKER <acute> & cardiac murmur",
                },
            },
            ("RR_TEXT_MARKER <acute> & cardiac murmur",),
        ),
        (
            "LC",
            {
                1: {
                    "LC_OBS": "LC_OBS_MARKER Patient <remains> clinically stable & safe.",
                    "LC_INT": "LC_INT_MARKER Findings indicate gradual improvement.",
                    "LC_PDX": "LC_PDX_MARKER Primary diagnosis is confirmed.",
                    "LC_DDX": "LC_DDX_MARKER Consider the alternative diagnosis.",
                    "LC_MX": "LC_MX_MARKER Continue treatment and follow-up.",
                },
            },
            (
                "LC_OBS_MARKER Patient <remains> clinically stable & safe.",
                "LC_INT_MARKER Findings indicate gradual improvement.",
                "LC_PDX_MARKER Primary diagnosis is confirmed.",
                "LC_DDX_MARKER Consider the alternative diagnosis.",
                "LC_MX_MARKER Continue treatment and follow-up.",
            ),
        ),
    ],
)
def test_generated_pdf_contains_submitted_answer_text(
    tmp_path, monkeypatch, set_type, case, submitted_text
):
    monkeypatch.setattr(serverreport, "REPORT_PATH", str(tmp_path))
    answers = {
        "type": set_type,
        "set_id": 1,
        "set_name": f"{set_type}_PDF_text_test",
        "candidateID": "PDF_text_test_candidate",
        "case": case,
    }

    pdf_path = serverreport.create_answer_pdf(answers)
    extracted_text = " ".join(
        page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages
    )
    normalized_text = " ".join(extracted_text.split())

    for text in submitted_text:
        assert text in normalized_text


if __name__ == "__main__":
    unittest.main()