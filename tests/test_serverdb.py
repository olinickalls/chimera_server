import tempfile
import unittest
import sqlite3
import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from chimera_exam_server import serverdb
from chimera_exam_server.pydanticmodels import (
    Finalise_Session_Detail,
    LC_Ans_bare,
    LC_Set,
    RR_Ans_bare,
    RR_Set,
)


class AnswerReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path_patch = patch.object(
            serverdb, "DB_PATH", Path(self.temp_directory.name)
        )
        self.db_path_patch.start()
        self.database = serverdb.chimera_server_db(
            "test.db", test_on_start=False
        )

    def tearDown(self):
        self.database.connection.close()
        self.db_path_patch.stop()
        self.temp_directory.cleanup()

    def create_session(self, set_type: str) -> str:
        return self.database.create_session(
            username="candidate",
            set_type=set_type,
            set_name="test set",
            device_name="client",
            start_dt="2026-09-27",
        )

    def finalise(self, uid: str, set_type: str) -> None:
        result = self.database.finalise_session(
            Finalise_Session_Detail(
                uid=uid,
                username="candidate",
                set_name="test set",
                set_type=set_type,
                device_name="client",
            )
        )
        self.assertNotIsInstance(result, Exception)

    def test_finalised_rr_answers_are_reconstructed(self):
        uid = self.create_session("RR")
        self.database.store_rr_case(
            RR_Ans_bare(
                uid=uid,
                case_n=1,
                RR_Normal=False,
                RR_Abnormal=True,
                RR_Desc="finding",
            ),
            uid,
        )

        self.finalise(uid, "RR")
        answers = self.database.get_answers_obj_by_uid(uid)

        self.assertEqual(answers["type"], "RR")
        self.assertEqual(answers["case"][1]["RR_Desc"], "finding")

    def test_finalised_lc_answers_are_reconstructed(self):
        uid = self.create_session("LC")
        self.database.store_lc_case(
            LC_Ans_bare(
                uid=uid,
                case_n=1,
                LC_OBS="observation",
                LC_INT="interpretation",
                LC_PDX="diagnosis",
                LC_DDX="differential",
                LC_MX="management",
            ),
            uid,
        )

        self.finalise(uid, "LC")
        answers = self.database.get_answers_obj_by_uid(uid)

        self.assertEqual(answers["type"], "LC")
        self.assertEqual(answers["case"][1]["LC_OBS"], "observation")

    def test_missing_session_has_clear_error(self):
        with self.assertRaisesRegex(LookupError, "Session not found"):
            self.database.get_answers_obj_by_uid("missing")

    def test_existing_case_lookup_propagates_database_errors(self):
        failing_cursor = Mock()
        failing_cursor.execute.side_effect = sqlite3.OperationalError("database locked")
        with patch.object(self.database, "cursor", failing_cursor):
            for lookup in (
                self.database.get_rr_cases_by_uid,
                self.database.get_lc_cases_by_uid,
            ):
                with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                    lookup("session-1")

    def test_get_unique_uids_uses_only_known_table_names(self):
        uid = self.create_session("RR")

        self.assertEqual(self.database.get_unique_uids(), [uid])
        with self.assertRaisesRegex(ValueError, "Unknown table"):
            self.database.get_unique_uids("sessions; DROP TABLE sessions")

    def test_session_writes_propagate_database_errors(self):
        database_error = sqlite3.OperationalError("database is locked")
        with patch.object(
            self.database, "execute_param_query", return_value=database_error
        ):
            with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                self.database.create_session(
                    username="candidate",
                    set_type="RR",
                    set_name="test set",
                    device_name="client",
                    start_dt="2026-09-27",
                )

            with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                self.database.finalise_session(
                    Finalise_Session_Detail(
                        uid="missing",
                        username="candidate",
                        set_name="test set",
                        set_type="RR",
                        device_name="client",
                    )
                )

    def test_pdf_status_is_exposed_and_updated(self):
        uid = self.create_session("RR")

        session = next(row for row in self.database.query_all_sessions() if row["uid"] == uid)
        self.assertEqual(session["pdf"], 0)
        self.assertIsNone(session["pdf_dt"])

        pdf_dt = self.database.mark_pdf_created(uid, "2026-09-28T14:30:00")
        session = next(row for row in self.database.query_all_sessions() if row["uid"] == uid)
        self.assertEqual(pdf_dt, "2026-09-28T14:30:00")
        self.assertEqual(session["pdf"], 1)
        self.assertEqual(session["pdf_dt"], "2026-09-28T14:30:00")

        for query in (
            self.database.query_all_sessions,
            self.database.query_open_sessions,
        ):
            exposed = next(row for row in query() if row["uid"] == uid)
            self.assertIn("final_dt", exposed)
            self.assertIn("pdf", exposed)
            self.assertIn("pdf_dt", exposed)

    def test_finalise_session_records_second_precision_time(self):
        uid = self.create_session("RR")

        self.finalise(uid, "RR")

        session = next(
            row for row in self.database.query_closed_sessions() if row["uid"] == uid
        )
        final_dt = datetime.datetime.fromisoformat(session["final_dt"])
        self.assertEqual(final_dt.microsecond, 0)

    def test_mount_migrates_legacy_session_schema(self):
        self.database.connection.close()
        legacy_path = Path(self.temp_directory.name) / "legacy.db"
        connection = sqlite3.connect(legacy_path)
        connection.execute(
            """CREATE TABLE sessions (
                id INTEGER PRIMARY KEY,
                uid TEXT NOT NULL,
                username TEXT NOT NULL,
                set_name TEXT NOT NULL,
                set_type TEXT NOT NULL,
                device_name TEXT NOT NULL,
                start_dt TEXT NOT NULL,
                finalised INTEGER NOT NULL
            )"""
        )
        connection.commit()
        connection.close()

        migrated = serverdb.chimera_server_db("legacy.db", test_on_start=False)
        try:
            columns = {
                row[1]: row for row in migrated.connection.execute("PRAGMA table_info(sessions)")
            }
            self.assertIn("pdf", columns)
            self.assertEqual(columns["pdf"][3], 1)
            self.assertEqual(columns["pdf"][4], "0")
            self.assertIn("pdf_dt", columns)
            self.assertEqual(columns["pdf_dt"][2], "TIMESTAMP")
            self.assertEqual(columns["pdf_dt"][3], 0)
            self.assertIn("final_dt", columns)
            self.assertEqual(columns["final_dt"][2], "TIMESTAMP")
            self.assertEqual(columns["final_dt"][3], 0)
        finally:
            migrated.connection.close()

    def test_lookup_indexes_are_created_for_existing_tables(self):
        expected = {
            "sessions": "idx_sessions_uid",
            "rr_answers": "idx_rr_answers_uid_case",
            "lc_answers": "idx_lc_answers_uid_case",
        }
        for table, index in expected.items():
            indexes = {
                row[1]
                for row in self.database.connection.execute(
                    f"PRAGMA index_list({table})"
                )
            }
            self.assertIn(index, indexes)

    def test_rr_and_lc_sets_commit_once_each(self):
        rr_uid = self.create_session("RR")
        self.database.store_rr_case(
            RR_Ans_bare(
                uid=rr_uid,
                case_n=1,
                RR_Normal=True,
                RR_Abnormal=False,
                RR_Desc="existing RR case",
            ),
            rr_uid,
        )
        rr_set = RR_Set(
            uid=rr_uid,
            candidateID="candidate",
            device_name="client",
            start_time="2026-09-27",
            set_name="RR set",
            set_id=1,
            type="RR",
            case={
                1: RR_Ans_bare(
                    uid=rr_uid,
                    case_n=1,
                    RR_Normal=False,
                    RR_Abnormal=True,
                    RR_Desc="updated RR case",
                ),
                2: RR_Ans_bare(
                    uid=rr_uid,
                    case_n=2,
                    RR_Normal=True,
                    RR_Abnormal=False,
                    RR_Desc="new RR case",
                ),
            },
        )
        rr_statements = []
        self.database.connection.set_trace_callback(rr_statements.append)
        try:
            self.assertEqual(self.database.store_rr_set(rr_set), "Success")
        finally:
            self.database.connection.set_trace_callback(None)
        rr_commits = [
            statement for statement in rr_statements
            if statement.strip().upper() == "COMMIT"
        ]
        self.assertEqual(len(rr_commits), 1)
        self.assertEqual(
            self.database.get_rr_case(rr_uid, 1)[0][3], "updated RR case"
        )
        self.assertEqual(len(self.database.get_rr_case(rr_uid, 2)), 1)

        lc_uid = self.create_session("LC")
        lc_set = LC_Set(
            uid=lc_uid,
            candidateID="candidate",
            device_name="client",
            start_time="2026-09-27",
            set_name="LC set",
            set_id=1,
            type="LC",
            case={
                case_n: LC_Ans_bare(
                    uid=lc_uid,
                    case_n=case_n,
                    LC_OBS="observation",
                    LC_INT="interpretation",
                    LC_PDX="primary diagnosis",
                    LC_DDX="differential",
                    LC_MX="management",
                )
                for case_n in (1, 2)
            },
        )
        lc_statements = []
        self.database.connection.set_trace_callback(lc_statements.append)
        try:
            self.assertEqual(self.database.store_lc_set(lc_set), "Success")
        finally:
            self.database.connection.set_trace_callback(None)
        lc_commits = [
            statement for statement in lc_statements
            if statement.strip().upper() == "COMMIT"
        ]
        self.assertEqual(len(lc_commits), 1)
        self.assertEqual(self.database.get_lc_cases_by_uid(lc_uid), [1, 2])


if __name__ == "__main__":
    unittest.main()
