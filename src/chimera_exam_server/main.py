from contextlib import asynccontextmanager
from datetime import datetime
import json
from pathlib import Path
import os
import re
import socket
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn

from .discovery import (
    DISCOVERY_MAGIC,
    DISCOVERY_VERSION,
    SERVICE_TYPE,
    ZeroconfAdvertiser,
)
from .logsystem import configure_logging, logger, log_startup_info
from .pydanticmodels import (
    Finalise_Session_Detail,
    LC_Ans_bare,
    LC_Set,
    New_Session_Data,
    RR_Ans_bare,
    RR_Ans_Query,
    RR_Set,
)
from .serverconstants import SERVER_MAKE_PDF_REPORT
from .serverdb import chimera_server_db
from .serverreport import create_answer_pdf


db: chimera_server_db | None = None


def get_db() -> chimera_server_db:
    if db is None:
        raise RuntimeError("Database is not initialized")
    return db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global db

    log_file = configure_logging()
    log_startup_info(log_file)
    db = chimera_server_db(
        db_file="chimera_server.db",
        test_on_start=False,
        clean_start=False,
    )
    advertiser = ZeroconfAdvertiser()
    await advertiser.start()
    logger.info("LAN discovery advertising {service}", service=SERVICE_TYPE)
    try:
        yield
    finally:
        await advertiser.stop()
        if db is not None:
            db.connection.close()
            db = None
        logger.info("Chimera server stopped")

app = FastAPI(lifespan=lifespan)
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,64}\Z")


@app.exception_handler(RequestValidationError)
async def request_validation_error(request: Request, exc: RequestValidationError):
    if request.url.path == "/session/new/":
        raw_body = await request.body()
        try:
            payload = json.loads(raw_body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = raw_body.decode("utf-8", errors="replace")
        logger.warning(
            "Session request validation failed | payload={payload} errors={errors}",
            payload=payload,
            errors=exc.errors(),
        )

    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors())},
    )


@app.middleware("http")
async def log_request(request: Request, call_next):
    supplied_request_id = request.headers.get("X-Request-ID", "")
    request_id = (
        supplied_request_id
        if REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
        else uuid4().hex[:12]
    )
    client = request.client.host if request.client else "unknown"
    started_at = perf_counter()

    with logger.contextualize(request_id=request_id, client=client):
        logger.info(
            "Request started | method={method} path={path}",
            method=request.method,
            path=request.url.path,
        )
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - started_at) * 1000
            logger.exception(
                "Request failed | method={method} path={path} duration_ms={duration:.1f}",
                method=request.method,
                path=request.url.path,
                duration=duration_ms,
            )
            raise

        duration_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "Request complete | method={method} path={path} status={status} "
            "duration_ms={duration:.1f}",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration=duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response

# ########################################################################
# ----------------------------------------  POST RR CASE
@app.post("/answers/RR_CASE/")
async def store_RR_CASE(rr_case: RR_Ans_bare):
    result = get_db().store_rr_case(rr_case, uid=rr_case.uid)
    return {'db_msg': result}

# ----------------------------------------  GET RR CASE
@app.get("/answers/RR_CASE/")
async def get_RR_CASE(query: RR_Ans_Query):
    result = get_db().get_rr_case(uid=query.uid, case_n=query.case_n)
    return {'rr_case_content': result}

# ----------------------------------------  POST RR SET
@app.post("/answers/RR_SET/")
async def store_RR_SET(rr_set: RR_Set):
    result = get_db().store_rr_set(rr_set)
    # todo: Check the action was successful
    # todo: make this standard HTTP response code
    return {'db_msg': result}

# ########################################################################
# ----------------------------------------  POST LC CASE
@app.post("/answers/LC_CASE/")
async def store_LC_CASE(lc_case: LC_Ans_bare):
    get_db().store_lc_case(lc_case, uid=lc_case.uid)

    return {'db_msg': 'Completed'}


# ----------------------------------------  POST LC SET
@app.post("/answers/LC_SET/")
async def store_LC_SET(lc_set: LC_Set):
    get_db().store_lc_set(lc_set)

    return {'db_msg': 'Completed'}


# ########################################################################
# ########################      QUERIES       ############################
# ########################################################################
# ----------------------------------------  GET RR CASE
@app.get("/answers/q_open_sessions/")
async def q_open_sessions():
    results = get_db().query_open_sessions()
    return results

@app.get("/answers/q_closed_sessions/")
async def q_closed_sessions():
    results = get_db().query_closed_sessions()
    return results

@app.get("/answers/q_all_sessions/")
async def q_all_sessions():
    results = get_db().query_all_sessions()
    return results


# ########################################################################
# ########################################################################
# ########################################################################
# ----------------------------------------  New session/GET NEW UID
@app.post("/session/new/")
async def start_new_session(data: New_Session_Data):
    new_uid = get_db().create_session(username=data.username,
                                      set_type=data.set_type,
                                      set_name=data.set_name,
                                      device_name=data.device_name,
                                      start_dt=data.start_dt,
                                      )
    logger.info("Session created | type={type}", type=data.set_type)
    return {'uid': new_uid}




# ----------------------------------------  Finalise Session
@app.post("/session/finalise/")
async def finalise(sess: Finalise_Session_Detail):
    database = get_db()
    feedback = database.finalise_session(sess)
    logger.debug('[/session/finalise/] DB say: {txt}', txt=feedback)

    if SERVER_MAKE_PDF_REPORT:
        answers = database.get_answers_obj_by_uid(uid=sess.uid)
        report_fp = create_answer_pdf(answers=answers)
        if not report_fp or not Path(report_fp).is_file():
            raise RuntimeError('PDF creation did not produce a file')
        database.mark_pdf_created(sess.uid)
        logger.info('Written PDF to {fp}', fp=report_fp)
    else:
        logger.trace('PDF NOT made- SERVER_MAKE_PDF_REPORT is {smpr}', smpr=SERVER_MAKE_PDF_REPORT)

    logger.info("Session finalised | type={type}", type=sess.set_type)
 
    return 200  # {msg: result}


# ----------------------------------------  PING
@app.get("/discovery/identity")
async def discovery_identity():
    return {
        "service": DISCOVERY_MAGIC,
        "version": DISCOVERY_VERSION,
        "hostname": socket.gethostname(),
    }


@app.post("/ping/")
async def post_ping_me(request: Request):
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    client_host = request.client.host if request.client else "unknown"
    logger.trace('[pinged]\t\t({client_host})', client_host=client_host)
    return f'200 - Chimera ({ip_address}) says hello.'


# ----------------------------------------  DEBUG
@app.get("/debug/")
async def debug_info(request: Request):

    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    client_host = request.client.host if request.client else "unknown"
    client_url = dict(request.scope["headers"]).get(b"referer", b"").decode()
    logger.trace('[pinged]\t\t({client_host})', client_host=client_host)

    return {'server_name': hostname,
            'server_ip': ip_address,
            'client_url': client_url
            }


# ----------------------------------------  DATE-TIME
@app.get("/datetime/")
async def get_server_time():

    dt_now = datetime.now()
    logger.trace('Received date-time request. returned: {dt}',
                 dt=dt_now.isoformat("#", "auto"))

    return dt_now.isoformat("#", "auto")


def run_server() -> None:
    uvicorn.run(
        app,
        host=os.getenv("CHIMERA_HOST", "0.0.0.0"),
        port=int(os.getenv("CHIMERA_PORT", "8000")),
        timeout_keep_alive=15,
        access_log=False,
        log_level=os.getenv("CHIMERA_UVICORN_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    run_server()
