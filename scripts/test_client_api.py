# Code to be shared with the client
# Also to be used for testing the API
import asyncio
import requests
from datetime import datetime, timezone
import random
import string
import os

import pprint

from chimera_exam_server.logsystem import logger
from chimera_exam_server import serverreport as report
from chimera_exam_server.formatting import (
    format_rr_answer_dict,
    format_lc_set_dict,
)
from chimera_exam_server.discovery import discover_server

pp = pprint.PrettyPrinter(indent=4, compact=True)
charslist = string.ascii_letters + string.digits
indent = 18

SERVER_IP = asyncio.run(discover_server())
DEVICE_NAME = "TEST_" + os.environ['COMPUTERNAME']

print('\nTesting Chimera Server')
print('============================\n:)\n')
print(f'@{SERVER_IP}')


repeats = 10
# ----------------------------------------  PING
# @app.post("/ping/")

route = "/ping/"

for i in range(repeats):
    response = requests.post(SERVER_IP + route)
    if response.status_code == 200:
        logger.info(f'{route:<{indent}}- [response ({i})] {response.text}')
    else:
        logger.error(f'{" ":<{indent}}- Request error- status code {response.status_code}')
        logger.error(response.text)
        raise requests.exceptions.HTTPError(response.text)


# print(timeit.timeit('requests.post("http://127.0.0.1:8000" + "/ping/")',
#               setup="import requests",
#               number=1000))

# ----------------------------------------  DEBUG
# @app.post("/debug/")

route = "/debug/"

for i in range(repeats):
    response = requests.get(SERVER_IP + route)
    if response.status_code == 200:
        logger.info(f'{route:<{indent}}- [response ({i})] {response.text}')
    else:
        logger.error(f'{route:<{indent}}- Request error- status code {response.status_code}')
        logger.error(response.text)
        raise requests.exceptions.HTTPError(response.text)

# ----------------------------------------  DATE-TIME
# @app.post("/datetime/")

route = "/datetime/"

for i in range(repeats):
    response = requests.get(SERVER_IP + route)
    if response.status_code == 200:
        logger.info(f'{route:<{indent}}- [response ({i})] {response.text}')
    else:
        logger.error(f'{route:<{indent}}- Request error- status code {response.status_code}')
        logger.error(response.text)
        raise requests.exceptions.HTTPError(response.text)

logger.info('*************  start Rapids CASES  **************')

# ----------------------------------------  New session/GET UID
# @app.post("/session/new/")
# Create new sesion by submitting session details.
# returns uid
route = "/session/new/"
start_dt = datetime.now()

test_RR_setname = "RR_test_set_" + "".join(random.choices(charslist, k=3))
username = "test_bot " + "".join(random.choices(charslist, k=3))

payload = {
  "username": username,
  "set_name": test_RR_setname,
  "set_type": "RR",
  "device_name": DEVICE_NAME,
  "start_dt": start_dt.isoformat("#", "auto")
}
logger.trace(f'{route:<{indent}}- [payload] {payload}')

response = requests.post(SERVER_IP + route, json=payload)
if response.status_code == 200:
    session_uid = response.json()['uid']
    logger.info(f'{route:<{indent}}- [response] {response.text}')
else:
    logger.error(f'{route:<{indent}}- Request error- status code {response.status_code}')
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)

# ----------------------------------------  POST RR CASE
# @app.post("/answers/RR_CASE/")
route = "/answers/RR_CASE/"

# The case number is outside the normal set size to
# prevent it being overwritten by the next test
case_n = random.randint(35, 40)

payload = {
  "uid": session_uid,  # Needs to be valid for DB ingestion
  "case_n": case_n,
  "RR_Normal": False,
  "RR_Abnormal": True,
  "RR_Desc": "[test text] Left big toe fracture"
}
logger.debug(f'{route:<{indent}}- [payload] {payload}')

# ---- test for SQL INSERT
response = requests.post(SERVER_IP + route, json=payload)
if response.status_code == 200:
    logger.info(f'{route:<{indent}}- [INSERT response] {response.text}')
else:
    logger.error(f'{route:<{indent}}- Request error- status code {response.status_code}')
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)


# ---- check DB contains the case
route = "/answers/RR_CASE/"
payload = {
    'uid': session_uid,
    'case_n': case_n
}
response = requests.get(SERVER_IP + route, json=payload)
logger.info(f"{route:<{indent}}- [Check change in DB] - response: {response.text}")


# ---- _re_test for SQL UPDATE
payload = {
  "uid": session_uid,  # Needs to be valid for DB ingestion
  "case_n": case_n,
  "RR_Normal": False,
  "RR_Abnormal": True,
  "RR_Desc": "[SQL UPDATE test] Left big toe fracture"
}

response = requests.post(SERVER_IP + route, json=payload)
if response.status_code == 200:
    logger.info(f'{" ":<{indent}}- [response] {response.text}')
else:
    logger.error(f'{" ":<{indent}}- Request error- status code {response.status_code}')
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)
# ----------------------------------------  POST RR SET
# @app.post("/answers/RR_SET/")
route = "/answers/RR_SET/"

# auto-generate & update test RR answers
rr_set = 2  # arbitrary integer

rr_answers = report.generate_fake_rr_answers()
rr_answers['uid'] = session_uid
rr_answers['candidateID'] = username
rr_answers['device_name'] = DEVICE_NAME
rr_answers['start_time'] = start_dt.isoformat("#", "auto")
rr_answers['set_name'] = test_RR_setname
rr_answers['set_id'] = rr_set

for case_n in rr_answers['case'].keys():
    # txt = f'---[DB Fake RR] set {rr_set} ({test_RR_setname}) case {case_n}'
    case = rr_answers['case'][case_n]
    case['case_n'] = case_n
    case['uid'] = session_uid

logger.info(f'{route:<{indent}}- [payload]:')  # {rr_answers}')
# pp.pprint(rr_answers)
logger.debug(format_rr_answer_dict(rr_answers))

# ---- test for  RR_SET  SQL INSERT
response = requests.post(SERVER_IP + route, json=rr_answers)
if response.status_code == 200:
    logger.info(f'{" ":<{indent}}- Test RR is in DB [response] {response.text}')

else:
    logger.error(f'{" ":<{indent}}- Request error- status code {response.status_code}')
    # print(response.text)
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)


# ---- _re_test for  RR_SET  SQL UPDATE 
response = requests.post(SERVER_IP + route, json=rr_answers)
if response.status_code == 200:
    logger.info(f'{" ":<{indent}}- re-test [response] {response.text}')

else:
    print(f'{" ":<{indent}}- re-test Request error- status code {response.status_code}')
    # print(response.text)
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)


# ----------------------------------------  Finalise Session
# @app.post("/session/finalise/")

route = "/session/finalise/"
payload = {
  "uid": session_uid,
  "username": username,
  "set_name": test_RR_setname,
  "set_type": "RR",
  "device_name": DEVICE_NAME
}

logger.info(f'{route:<{indent}}- [payload] {payload}')

response = requests.post(SERVER_IP + route, json=payload)
if response.status_code == 200:
    logger.info(f'{" ":<{indent}}- [response] {response.text}')

else:
    logger.error(f'{" ":<{indent}}- Request error- status code {response.status_code}')
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)


logger.info('*************  start LONG CASES  **************')

# ======================
# ======================
# ======================
# ----------------------  New LC session/GET UID
# ======================
# ======================
# @app.post("/session/new/")
# Create new sesion by submitting session details.
# returns uid
route = "/session/new/"
start_dt = datetime.now()

test_LC_setname = "LC_test_set_" + "".join(random.choices(charslist, k=3))
username = "test_bot_" + "".join(random.choices(charslist, k=3))

payload = {
  "username": username,
  "set_name": test_LC_setname,
  "set_type": "LC",
  "device_name": DEVICE_NAME,
  "start_dt": start_dt.isoformat("#", "auto")
}
logger.info(f'{route:<{indent}}- [payload] {payload}')

response = requests.post(SERVER_IP + route, json=payload)
if response.status_code == 200:
    session_uid = response.json()['uid']
    logger.info(f'{" ":<{indent}}- [response] {response.text}\n')
else:
    logger.error(f'{" ":<{indent}}- Request error- status code {response.status_code}')
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)

# --------------------------  POST LC CASE -- INSERT
# @app.post("/answers/LC_CASE/")
route = "/answers/LC_CASE/"

# The case number is outside the normal set size to
# prevent it being overwritten by the next test
case_no = random.randint(8, 10)

payload = {
  "uid": session_uid,  # Needs to be valid for DB ingestion
  "case_n": case_no,
  "LC_OBS": "my observations text.",
  "LC_INT": "my observations text.",
  "LC_PDX": "my primary diagnosis text.",
  "LC_DDX": "my differentials text.",
  "LC_MX": "my management text."
}
logger.debug(f'{route:<{indent}}- [INSERT payload] {payload}')

response = requests.post(SERVER_IP + route, json=payload)
if response.status_code == 200:
    logger.info(f'{" ":<{indent}}- [INSERT response] {response.text}')
else:
    logger.error(f'{" ":<{indent}}- Request error- status code {response.status_code}')
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)


# ------------------  POST LC CASE - UPDATE
# @app.post("/answers/LC_CASE/")
route = "/answers/LC_CASE/"

payload = {
  "uid": session_uid,  # Needs to be valid for DB ingestion
  "case_n": case_no,  # recycle the same case number to overwrite entry
  "LC_OBS": "my observations text. [UPDATE METHOD]",
  "LC_INT": "my observations text. [UPDATE METHOD]",
  "LC_PDX": "my primary diagnosis text. [UPDATE METHOD]",
  "LC_DDX": "my differentials text. [UPDATE METHOD]",
  "LC_MX": "my management text. [UPDATE METHOD]"
}
logger.debug(f'{route:<{indent}}- [UPDATE payload] {payload}')

response = requests.post(SERVER_IP + route, json=payload)
if response.status_code == 200:
    logger.info(f'{route:<{indent}}- [UPDATE response] {response.text}')
else:
    logger.error(f'{route:<{indent}}- Request error- status code {response.status_code}')
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)


# ------------------  POST LC SET (INSERT)
# @app.post("/answers/LC_SET/")
route = "/answers/LC_SET/"

lc_answers = report.generate_fake_lc_answers()

# Prepare additional info to match pydantic LC_ANS model
lc_answers['uid'] = session_uid

# Fix missing data in the fake case data
for case_n in lc_answers['case'].keys():
    # case = lc_answers['case'][case_n]
    lc_answers['case'][case_n]['case_n'] = case_n
    lc_answers['case'][case_n]['uid'] = session_uid

logger.trace(f'{route:<{indent}}- [payload] \n{format_lc_set_dict(lc_answers)}')

response = requests.post(SERVER_IP + route, json=lc_answers)
if response.status_code == 200:
    logger.info(f'{route:<{indent}}- [INSERT response] {response.text}')
else:
    logger.error(f'{route:<{indent}}- Request error- status code {response.status_code}')
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)

# ------------------  RE-POST LC SET (UPDATE)

# Fix missing data in the fake case data
for case_n in lc_answers['case'].keys():
    # case = lc_answers['case'][case_n]
    lc_answers['case'][case_n]['LC_OBS'] += '-UPDATE'
    lc_answers['case'][case_n]['LC_INT'] += '-UPDATE'
    lc_answers['case'][case_n]['LC_PDX'] += '-UPDATE'
    lc_answers['case'][case_n]['LC_DDX'] += '-UPDATE'
    lc_answers['case'][case_n]['LC_MX'] += '-UPDATE'

logger.trace(f'{route:<{indent}}- [payload] \n{format_lc_set_dict(lc_answers)}')

response = requests.post(SERVER_IP + route, json=lc_answers)
if response.status_code == 200:
    logger.info(f'{route:<{indent}}- [UPDATE response] {response.text}')
else:
    logger.error(f'{route:<{indent}}- Request error- status code {response.status_code}')
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)


# ----------------------------------------  Finalise Session
# @app.post("/session/finalise/")

route = "/session/finalise/"
payload = {
  "uid": lc_answers['uid'],
  "username": lc_answers['candidateID'],
  "set_name": lc_answers['set_name'],
  "set_type": lc_answers['type'],
  "device_name": lc_answers['device_name']
}

logger.debug(f'{route:<{indent}}- [payload] {payload}')

response = requests.post(SERVER_IP + route, json=payload)
if response.status_code == 200:
    logger.info(f'{route:<{indent}}- Finalise [response] {response.text}')

else:
    logger.error(f'{route:<{indent}}- Request error- status code {response.status_code}')
    logger.error(response.text)
    raise requests.exceptions.HTTPError(response.text)