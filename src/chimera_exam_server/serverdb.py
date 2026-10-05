from .serverconstants import (
    DB_PATH,
    RR_NORMAL,
    RR_ABNORMAL,
    RR_DESC
)
import sqlite3
from sqlite3 import Error
from . import serverreport as report
import uuid
import datetime

from .logsystem import logger

from .pydanticmodels import (
    RR_Ans_bare,
    RR_Set,
    LC_Set,
    Finalise_Session_Detail
)

# Manage the server DB interactions

class chimera_server_db():
    def __init__(self, db_file,
                 test_on_start=True,
                 clean_start=False):
        # Use SQL DB to store answers
        # 3 tables:
        # 1- Users & instances (start_time & UID)
        # 2- RR answers (key = UID)
        # 3- LC answers (key = UID)

        # Does the DB dir & file exist?
        if not DB_PATH.exists():
            DB_PATH.mkdir(parents=True, exist_ok=True)

        self.db_fp = DB_PATH.joinpath(db_file)

        # Delete the existing DB file if instructed on startup
        if clean_start and self.db_fp.exists():
            self.db_fp.unlink()

        if not self.db_fp.exists():
            logger.info(f'*** Server DB file does not exist: {self.db_fp}')
            logger.info('*** Creating DB file...')
            self.create_new_db(include_test_data=True)
            self.mount_db()

        else:
            logger.info(f'*** Found DB file: {self.db_fp}')
            self.mount_db()

        if test_on_start:
            self.populate_fake_data()


    def create_new_db(self, include_test_data=False):
        try:
            self.connection = sqlite3.connect(self.db_fp)
            mode = self.connection.execute('PRAGMA journal_mode=WAL;').fetchone()[0]
            if mode != 'wal':
                logger.warning(f'Failed to set journal mode to WAL. Current mode: {mode}')

            self.cursor = self.connection.cursor()
            logger.info(f'***[DB]*** Creating DB {self.db_fp}')

            logger.debug('\t\t *** Creating sessions table')
            # See the pydantic model in pydanticmodels.py
            SQL_create_sessions_table = ("CREATE TABLE sessions ("
                                        "id INTEGER PRIMARY KEY, "
                                        "uid TEXT NOT NULL, "
                                        "username TEXT NOT NULL, "
                                        "set_name INTEGER NOT NULL, "
                                        "set_type TEXT NOT NULL, "
                                        "device_name TEXT NOT NULL, "
                                        "start_dt TEXT NOT NULL,"
                                        "finalised INTEGER NOT NULL,"  # bool
                                        "final_dt TIMESTAMP NULL,"
                                        "pdf INTEGER NOT NULL DEFAULT 0,"
                                        "pdf_dt TIMESTAMP NULL"
                                        ");")
            self.cursor.execute(SQL_create_sessions_table)
    
            logger.debug('\t\t *** Creating rr table')
            # See the pydantic model in pydanticmodels.py
            SQL_create_rr_table = ("CREATE TABLE rr_answers ("
                                    "id INTEGER PRIMARY KEY, "
                                    "uid TEXT NOT NULL, "
                                    "case_number INTEGER NOT NULL, "
                                    "rr_normal INTEGER NOT NULL, "  # Bool
                                    "rr_abnormal INTEGER NOT NULL, "  # Bool
                                    "rr_desc TEXT NOT NULL, "
                                    "FOREIGN KEY (uid) REFERENCES sessions (uid)"
                                    ");")
            self.cursor.execute(SQL_create_rr_table)

            logger.debug('\t\t *** Creating lc table')
            # See the pydantic model in pydanticmodels.py
            SQL_create_lc_table = ("CREATE TABLE lc_answers ("
                                    "id INTEGER PRIMARY KEY, "
                                    "uid TEXT NOT NULL, "
                                    "case_number INTEGER NOT NULL, "
                                    "LC_OBS TEXT NOT NULL, "
                                    "LC_INT TEXT NOT NULL, "
                                    "LC_PDX TEXT NOT NULL, "
                                    "LC_DDX TEXT NOT NULL, "
                                    "LC_MX TEXT NOT NULL, "
                                    "FOREIGN KEY (uid) REFERENCES sessions (uid)"
                                    ");")
            self.cursor.execute(SQL_create_lc_table)
            logger.debug('\t\t *** Done creating tables')
            self.connection.commit()
            self.connection.close()

        except Error:
            logger.exception("Failed to create database schema")
            raise


    def mount_db(self):
        try:
            self.connection = sqlite3.connect(self.db_fp)
            self.cursor = self.connection.cursor()
            logger.info(f'***[DB]*** Connected to DB {self.db_fp}')
            mode = self.connection.execute('PRAGMA journal_mode=WAL;').fetchone()[0]
            if mode != 'wal':
                logger.warning(f'Failed to set journal mode to WAL. Current mode: {mode}')
            self._migrate_sessions_pdf_tracking()
            self._migrate_sessions_final_tracking()
            self._migrate_lookup_indexes()
        except Error as e:
            logger.error(f"The error '{e}' occurred")
        except Exception as e:
            logger.error(f"The Exception '{e}' occurred")

    def _migrate_sessions_pdf_tracking(self):
        """Add PDF tracking columns to databases created by older versions."""
        columns = {
            row[1] for row in self.connection.execute('PRAGMA table_info(sessions)')
        }
        if 'pdf' not in columns:
            self.connection.execute(
                'ALTER TABLE sessions ADD COLUMN pdf INTEGER NOT NULL DEFAULT 0'
            )
        if 'pdf_dt' not in columns:
            self.connection.execute(
                'ALTER TABLE sessions ADD COLUMN pdf_dt TIMESTAMP NULL'
            )
        self.connection.commit()

    def _migrate_sessions_final_tracking(self):
        """Add finalisation tracking to databases created by older versions."""
        columns = {
            row[1] for row in self.connection.execute('PRAGMA table_info(sessions)')
        }
        if 'final_dt' not in columns:
            self.connection.execute(
                'ALTER TABLE sessions ADD COLUMN final_dt TIMESTAMP NULL'
            )
        self.connection.commit()

    def _migrate_lookup_indexes(self):
        """Index the columns used by session and answer lookups."""
        tables = {
            row[0]
            for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        indexes = (
            ('sessions', 'idx_sessions_uid', 'uid'),
            ('rr_answers', 'idx_rr_answers_uid_case', 'uid, case_number'),
            ('lc_answers', 'idx_lc_answers_uid_case', 'uid, case_number'),
        )
        for table, index, columns in indexes:
            if table in tables:
                self.connection.execute(
                    f'CREATE INDEX IF NOT EXISTS {index} ON {table} ({columns})'
                )
        self.connection.commit()


    def populate_fake_data(self, rr_sets=1, lc_sets=1):
        # use the fake data generator in reports.py
        # populate this directly into the DB

        for rr_set in range(rr_sets):
            new_dt = report.get_rnd_dt()
            uid = self.create_session(username='TEST01',
                                      set_type="RR",
                                      set_name='RR SET 99',
                                      device_name='SURAFCE',
                                      start_dt=new_dt
                                      )

            rr_answers = report.generate_fake_rr_answers()
            rr_set_name = rr_answers['set_name']

            for casen in rr_answers['case'].keys():
                txt = f'---[DB Fake RR] set {rr_set} ({rr_set_name}) case {casen}'
                case = rr_answers['case'][casen]
                case['case_n'] = casen
                case['uid'] = uid

                rr_case_answer = RR_Ans_bare.model_validate(case)
                self.store_rr_case(rr_case=rr_case_answer, uid=uid, txt=txt)
                logger.trace('\t-Done creating RR case data.')
            logger.debug('\t-Done creating RR set data.')

    # ###################################################################
    # ########      Base Functions                               ########
    # ###################################################################


    def create_session(self,
                       username,
                       set_type,
                       set_name,
                       device_name,
                       start_dt,
                       uid=None
                       ):
        # Begin a NEW session
        if not uid:
            uid = f'{username}|{set_name}_{uuid.uuid4()}'
        logger.debug("Creating session | type={type}", type=set_type)

        
        SQL_NEW_SESSION = ("INSERT INTO sessions"
                           "(uid, username, set_type, set_name, device_name, start_dt, finalised) "
                           "VALUES "
                           "(?, ?, ?, ?, ?, ?, ?);")
        params = (uid, username, set_type, set_name, device_name, start_dt, 0)

        # self.execute_query(SQL_NEW_SESSION, txt='Creating Session')
        result = self.execute_param_query(
            SQL_NEW_SESSION, params, txt='Creating Session'
        )
        if isinstance(result, Exception):
            raise result
        return uid


    def finalise_session(self, sess: Finalise_Session_Detail):
        '''
        Take a finalise_session_detail object from the API
        'Close the session by setting the 'finalised' flag in sesions table.
        '''
        logger.debug('finalise_session')
        final_dt = datetime.datetime.now().isoformat(timespec='seconds')
        query = ("UPDATE sessions"
            " SET finalised=True, final_dt=?"
                " WHERE uid=?;")
        params = (final_dt, sess.uid)
        msg = 'Finalising session'

        db_response = self.execute_param_query(query, params=params, txt=msg)

        if isinstance(db_response, Exception):
            raise db_response
        if db_response.rowcount != 1:
            raise LookupError(f'Session not found while finalising: {sess.uid}')
        return 'No Error'

    def mark_pdf_created(self, uid: str, created_at: str | None = None) -> str:
        pdf_dt = created_at or datetime.datetime.now().isoformat(timespec='seconds')
        result = self.execute_param_query(
            'UPDATE sessions SET pdf=1, pdf_dt=? WHERE uid=?',
            (pdf_dt, uid),
            txt='Mark PDF created',
        )
        if isinstance(result, Exception):
            raise result
        if result.rowcount != 1:
            raise LookupError(f'Session not found while marking PDF: {uid}')
        return pdf_dt

    # ###################################################################
    # ########      RAPID REPORTING                              ########
    # ###################################################################


    def store_rr_case(self,
                      rr_case,
                      uid:str,
                      txt:str=None,
                      method:str=None
                      ):
        '''
        rr_ans (dict) must include all fields:
        { 'RR_Normal':   bool,
          'RR_Abnormal': bool,
          'RR_Desc':     str,
          'case_n':      INTEGER,
          'uid:          str
        }
        uid is needed to associate with the correct session
        '''
        if method is None:
            logger.trace('[store_rr_case] Checking existing cases')
            existing = self.get_rr_cases_by_uid(uid=uid)
            logger.trace('[store_rr_case] Existing case count={count}', count=len(existing))

            if rr_case.case_n not in existing:
                method = 'INSERT'
            else:
                method = 'UPDATE'
        elif method not in ['UPDATE', 'INSERT']:
            raise(ValueError(f"Unknown method value: {method}"))

        if method == 'INSERT':
            logger.trace('INSERT')
            new_rr_data =  ("INSERT INTO "
                            "rr_answers (uid, case_number, rr_normal, rr_abnormal, rr_desc) "
                            "VALUES (?, ?, ?, ?, ?);")
            params = (uid,
                      rr_case.case_n,
                      rr_case.RR_Normal,
                      rr_case.RR_Abnormal,
                      rr_case.RR_Desc
                      )

        elif method == 'UPDATE':
            logger.trace('UPDATE')
            new_rr_data = ("UPDATE rr_answers"
                           " SET rr_normal=?,"
                           "    rr_abnormal=?,"
                           "    rr_desc=?"
                           " WHERE uid=? AND case_number=?"
                        )
            params = (rr_case.RR_Normal,
                      rr_case.RR_Abnormal,
                      rr_case.RR_Desc,
                      uid,
                      rr_case.case_n)

        else:
            logger.error(f"Unknown method value: {method}")
            raise(ValueError(f"Unknown method value: {method}"))

        msg = '[Store RR Case]' + str(txt)
        db_response = self.execute_param_query(new_rr_data, params=params, txt=msg)

        if isinstance(db_response, Exception):
            raise db_response
        return 'Success'


    def exists_rr_case(self,
                      rr_case,
                      uid:str,
                      txt:str=None
                      ):
        '''
        Checks for the existance of a single case at a time
        True if exists in te DB
        '''
        cases_in_DB = self.get_rr_casen_by_uid(uid)
        if rr_case.case_n in cases_in_DB:
            return True
        else:
            return False


    def store_rr_set(self, rr_set:RR_Set):
        '''
        the rr set dict should be like this:

        '''
        uid = rr_set.uid
        candidateID = rr_set.candidateID
        device_name = rr_set.device_name
        start_time = rr_set.start_time
        set_name = rr_set.set_name
        cases = rr_set.case
        logger.debug('[store_rr_set] case_count={count}', count=len(cases))
        existing_cases = set(self.get_rr_cases_by_uid(uid=uid))
        insert_rows = []
        update_rows = []
        for case_number, rr_case in cases.items():
            if case_number in existing_cases:
                update_rows.append((
                    rr_case.RR_Normal,
                    rr_case.RR_Abnormal,
                    rr_case.RR_Desc,
                    uid,
                    rr_case.case_n,
                ))
            else:
                insert_rows.append((
                    uid,
                    rr_case.case_n,
                    rr_case.RR_Normal,
                    rr_case.RR_Abnormal,
                    rr_case.RR_Desc,
                ))

        return self._execute_case_batch(
            'INSERT INTO rr_answers '
            '(uid, case_number, rr_normal, rr_abnormal, rr_desc) '
            'VALUES (?, ?, ?, ?, ?)',
            'UPDATE rr_answers SET rr_normal=?, rr_abnormal=?, rr_desc=? '
            'WHERE uid=? AND case_number=?',
            insert_rows,
            update_rows,
            'Storing RR set',
        )

    # ###################################################################
    # ########      LONG CASES                                   ########
    # ###################################################################

    def store_lc_case(self,
                      lc_case,
                      uid:str,
                      txt:str=None,
                      method:str=None
                      ):
        '''
        lc_ans (dict) must include all fields:
        { 
            'uid:          str,
            'case_n':      INTEGER,
            'LC_OBS': str,
            'LC_INT': str,
            'LC_PDX': str,
            'LC_DDX': str,
            'LC_MX': str,
        }
        uid is needed to associate with the correct session
        '''
        if method is None:
            logger.trace('[store_lc_case] Checking existing cases')
            existing = self.get_lc_cases_by_uid(uid=uid)
            logger.trace('[store_lc_case] Existing case count={count}', count=len(existing))

            if lc_case.case_n not in existing:
                method = 'INSERT'
            else:
                method = 'UPDATE'
        elif method not in ['UPDATE', 'INSERT']:
            raise(ValueError(f"Unknown method value: {method}"))

        if method == 'INSERT':
            logger.trace('INSERT')
            new_lc_data =  ("INSERT INTO "
                            "lc_answers (uid, "
                            "case_number, "
                            "LC_OBS, "
                            "LC_INT, "
                            "LC_PDX, "
                            "LC_DDX, "
                            "LC_MX "
                            ") VALUES (?, ?, ?, ?, ?, ?, ?);")
            params = (uid,
                      lc_case.case_n,
                      lc_case.LC_OBS,
                      lc_case.LC_INT,
                      lc_case.LC_PDX,
                      lc_case.LC_DDX,
                      lc_case.LC_MX,
                      )

        elif method == 'UPDATE':
            logger.trace('UPDATE')
            new_lc_data = ("UPDATE lc_answers"
                           " SET "
                            "LC_OBS=?, "
                            "LC_INT=?, "
                            "LC_PDX=?, "
                            "LC_DDX=?, "
                            "LC_MX=? "
                           " WHERE uid=? AND case_number=?"
                        )
            params = (lc_case.LC_OBS,
                      lc_case.LC_INT,
                      lc_case.LC_PDX,
                      lc_case.LC_DDX,
                      lc_case.LC_MX,
                      uid,
                      lc_case.case_n)

        else:
            logger.error(f"Unknown method value: {method}")
            raise(ValueError(f"Unknown method value: {method}"))

        msg = '[Store LC Case] ' + str(txt)

        logger.debug(msg)

        db_response = self.execute_param_query(new_lc_data,
                                               params=params,
                                               txt=msg)

        if isinstance(db_response, Exception):
            raise db_response
        return 'Success'


    # ###################################################################

    def store_lc_set(self, lc_set:LC_Set):
        '''
        the lc set dict should be like this (very similar to rr_set):

        '''
        uid = lc_set.uid
        candidateID = lc_set.candidateID
        device_name = lc_set.device_name
        start_time = lc_set.start_time
        set_name = lc_set.set_name
        cases = lc_set.case
        logger.debug('[store_lc_set] case_count={count}', count=len(cases))

        existing_cases = set(self.get_lc_cases_by_uid(uid=uid))
        insert_rows = []
        update_rows = []
        for case_number, lc_case in cases.items():
            if case_number in existing_cases:
                update_rows.append((
                    lc_case.LC_OBS,
                    lc_case.LC_INT,
                    lc_case.LC_PDX,
                    lc_case.LC_DDX,
                    lc_case.LC_MX,
                    uid,
                    lc_case.case_n,
                ))
            else:
                insert_rows.append((
                    uid,
                    lc_case.case_n,
                    lc_case.LC_OBS,
                    lc_case.LC_INT,
                    lc_case.LC_PDX,
                    lc_case.LC_DDX,
                    lc_case.LC_MX,
                ))

        return self._execute_case_batch(
            'INSERT INTO lc_answers '
            '(uid, case_number, LC_OBS, LC_INT, LC_PDX, LC_DDX, LC_MX) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            'UPDATE lc_answers SET LC_OBS=?, LC_INT=?, LC_PDX=?, '
            'LC_DDX=?, LC_MX=? WHERE uid=? AND case_number=?',
            insert_rows,
            update_rows,
            'Storing LC set',
        )

    def _execute_case_batch(
        self,
        insert_sql: str,
        update_sql: str,
        insert_rows: list[tuple],
        update_rows: list[tuple],
        operation: str,
    ) -> str:
        try:
            with self.connection:
                if insert_rows:
                    self.cursor.executemany(insert_sql, insert_rows)
                if update_rows:
                    self.cursor.executemany(update_sql, update_rows)
        except sqlite3.Error as error:
            logger.exception(
                'Database operation failed | operation={operation}',
                operation=operation,
            )
            raise error
        logger.debug('{operation} committed', operation=operation)
        return 'Success'


    # ###################################################################
    # ###################################################################
    # ###################################################################

    def query_open_sessions(self):
        '''
        Returns a dict of open sessions
        '''
        query = '''
         SELECT uid, username, set_name, set_type, device_name, start_dt, finalised,
             final_dt, pdf, pdf_dt
        FROM sessions
        WHERE finalised=0
        '''
        reply = self.cursor.execute(query)
        results = self.fetch_all_as_dict(reply)
        return results

    def query_all_sessions(self):
        '''
        Returns a dict of all sessions
        '''
        query = '''
         SELECT uid, username, set_name, set_type, device_name, start_dt, finalised,
             final_dt, pdf, pdf_dt
        FROM sessions
        '''
        reply = self.cursor.execute(query)
        results = self.fetch_all_as_dict(reply)
        return results

    def query_closed_sessions(self):
        '''
        Returns a dict of closed sessions
        '''
        query = '''
         SELECT uid, username, set_name, set_type, device_name, start_dt, finalised,
             final_dt, pdf, pdf_dt
        FROM sessions
        WHERE finalised=1
        '''
        reply = self.cursor.execute(query)
        results = self.fetch_all_as_dict(reply)
        return results

    def get_answers_obj_by_uid(self,
                               uid
                               ):
        '''
        Check type - RR or LC
        get list of answers accordingly and populate the answers object
        '''
        logger.debug('Starting answer retrieval')
        # ### Query sessions table:
        query = ("SELECT set_type, finalised, set_name, username, device_name, start_dt"
                " FROM sessions"
                " WHERE uid=?"
                )
        params = (uid, )
        msg = 'Extracting session details'
 
        results = self.execute_param_query_fetch(query,
                                                 params,
                                                 txt=msg,
                                                 fetchall=True
                                                 )
        logger.debug('Session detail rows={count}', count=len(results))

        if not results:
            raise LookupError("Session not found while retrieving answers")

        answers = None
        for item in results:
            answers = {'type': item[0],
                'final': item[1],
                'set_id': 'SET-ID',
                'set_name': item[2],
                'candidateID': item[3],
                'device_name:': item[4],
                'start_time': item[5],
                'case': {}
            }
        logger.debug('Answers are for type: {type}', type=answers['type'])

        if answers['type'] == 'RR':
            logger.trace('Looking for Rapid Reporting answers')

            # ### Query rr_answers table:
            query = ("SELECT case_number, rr_normal, rr_abnormal, rr_desc"
                    " FROM rr_answers"
                    " WHERE uid=?"
                    " ORDER BY case_number ASC")
            params = (uid, )
            msg = 'Extracting RR answers'
            case_results = self.execute_param_query(query, params, txt=msg)

            for item in case_results:
                answers['case'][item[0]] = {
                    RR_NORMAL: item[1],
                    RR_ABNORMAL: item[2],
                    RR_DESC: item[3]
                }

        elif answers['type'] == 'LC':
            logger.trace('Looking for Long Case answers')

            # ### Query lc_answers table:
            query = ("SELECT case_number, LC_OBS, LC_INT, LC_PDX, LC_DDX, LC_MX "
                    "FROM lc_answers "
                    "WHERE uid=?")
            params = (uid, )
            msg = 'Extracting LC answers'
            case_results = self.execute_param_query(query, params, txt=msg)

            for item in case_results:
                answers['case'][item[0]] = {
                    'LC_OBS': item[1],
                    'LC_INT': item[2],
                    'LC_PDX': item[3],
                    'LC_DDX': item[4],
                    'LC_MX': item[5]
                }

        return answers

    def fetch_all_as_dict(self, cursor):
        # Get column names from the cursor description
        column_names = [description[0] for description in cursor.description]
        
        try:
            # Fetch all rows from the cursor
            rows = cursor.fetchall()
        except sqlite3.Error:
            logger.exception('Database row fetch failed')
            return []
        
        # Convert rows to list of dictionaries
        result = [dict(zip(column_names, row)) for row in rows]
        
        return result


    def execute_query(self,
                      query,
                      txt=''
                      ):
        try:
            results = self.cursor.execute(query)
            self.connection.commit()
            logger.debug(f"\t[DB SExecute] '{txt}' Query successful")
        except (sqlite3.Error, Error) as error:
            logger.exception("Database operation failed | operation={operation}", operation=txt)
            return error
        return results


    def execute_param_query(self,
                            query,
                            params,
                            txt=''
                            ):
        try:
            results = self.cursor.execute(query, params)
            self.connection.commit()
            logger.debug(f"\t[DB PExecute] '{txt}' Query successful")
        except Exception as error:
            logger.exception("Database operation failed | operation={operation}", operation=txt)
            return error
        return results


    def execute_param_query_fetch(self,
                            query,
                            params,
                            txt='',
                            fetchall=False
                            ):
        try:
            cursor = self.cursor.execute(query, params)
            results = cursor.fetchall() if fetchall else cursor
            logger.debug(f"\t[DB PExecute] '{txt}' Query successful")
        except Exception:
            logger.exception("Database fetch failed | operation={operation}", operation=txt)
            raise
        return results



    # ######################## HELPER FUNCTIONS  ########################
    def get_unique_uids(self, table='sessions'):
        '''
        Queries 'table' for unique UIDs based on type
        table can only be 'sessions', 'rr_answers' or 'lc_answers'
        '''
        allowed_tables = {'sessions', 'rr_answers', 'lc_answers'}
        if table not in allowed_tables:
            raise(ValueError(f"Unknown table: {table}"))
        query = f'SELECT DISTINCT uid FROM {table}'
        return [row[0] for row in self.cursor.execute(query)]

    def get_rr_cases_by_uid(self, uid):
        '''
        Returns a list of existing RR cases for a given UID
        '''
        query = '''
        SELECT case_number FROM rr_answers
        WHERE uid=?'''

        reply = self.cursor.execute(query, (uid,))
        return [row[0] for row in reply]

    def get_lc_cases_by_uid(self, uid):
        '''
        Returns a list of existing LC cases for a given UID
        '''
        query = '''
        SELECT case_number FROM lc_answers
        WHERE uid=?'''

        reply = self.cursor.execute(query, (uid,))
        return [row[0] for row in reply]


    def get_rr_case(self, uid, case_n):
        '''
        Specific single RR case lookup
        return the case as json
        '''
        query = '''
        SELECT case_number, rr_normal, rr_abnormal, rr_desc 
        FROM rr_answers
        WHERE uid=? AND case_number=?
        '''
        # params = {
        #     'uid': uid,
        #     'case_number': case_n
        # }
        dbreply = self.cursor.execute(query, (uid, case_n))
        n_list = []
        for item in dbreply:
            n_list.append(item)
        return n_list


def random_uid():
    return str(uuid.uuid4())


def get_current_dt_dict():
    dt = datetime.datetime.now()
    dt_dict = {
    'yyyy': dt.year,
    'mm': dt.month,
    'dd': dt.day,
    'HH': dt.hour,
    'MM': dt.minute,
    'SS': dt.second
    }
    return dt_dict


def get_current_dt_str():
    dt = datetime.datetime.now()
    dt_str = f'{dt.year:04}-{dt.month:02}-{dt.day:02} {dt.hour:02}:{dt.minute:02}:{dt.second:02}'
    return dt_str
