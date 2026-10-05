# server_constants.py
# server-side
import os
import platform
from pathlib import Path
import socket

DATA_DIR = os.getenv("CHIMERA_DATA_DIR")

SERVER_IP = 'http://localhost:8000'

DEBUG = True
DEBUG_RR_CASE = False
DEBUG_RR_SET = True
DEBUG_LC_CASE = True
DEBUG_LC_SET = True
DEBUG_REPORT = False
DEBUG_FINALISE = True
DEBUG_NEW_SESSION = True

# Identify the computer name
DEVICE_NAME = socket.gethostname()

# SERVER OPTIONS #############################################################
SERVER_ENABLED = False  # if false, prevents all server communication.

# SERVER_MAKE_PDF_REPORT ---- if true, creates a PDF report for each
# session on session finalisation. This is a bottleneck to performance,
# so should generally be false unless the examAdmin UI is not working.
SERVER_MAKE_PDF_REPORT = False  

DB_RELATIVE_PATH = 'DB'

# Performace is MUCH improved with the SQLite DB on SSD
servername = platform.node()
if DATA_DIR:
    HOME_PATH = Path(DATA_DIR).expanduser()
elif servername == 'berg':
    HOME_PATH = Path(r'C:\Users\oli_n\CHIMERA_DB')
else:
    HOME_PATH = Path.cwd()
DB_PATH = HOME_PATH.joinpath(DB_RELATIVE_PATH)


# Converted to a Path object.
# Is relative to current dir unless explicitly otherwise.
REPORT_PATH = 'REPORTS'
DEBUG_REPORT = False

# ****************************
#        Report Options
# ****************************
# Converted to a Path object.
# Is relative to current dir unless explicitly otherwise.
REPORT_PATH = 'REPORTS'


# ****************************
#          UI Options
# ****************************
AS_LC_TITLE_TXT = 'RS Case '
AS_RR_TITLE_TXT = 'RRS Case '
AS_LC_HX_TXT = 'History:'
AS_LC_OBS_TXT = 'Observations:'
AS_LC_INT_TXT = 'Interpretation:'
AS_LC_PDX_TXT = 'Principle Diagnosis:'
AS_LC_DDX_TXT = 'Differential Diagnosis:'
AS_LC_MX_TXT = 'Management (if applicable):'
AS_RR_ABN_TXT = 'Abnormal?'
AS_RR_DESC_TXT = 'Description of Abnormality'

# answer dict keys:
RR_NORMAL = 'RR_Normal'
RR_ABNORMAL = 'RR_Abnormal'
RR_DESC = 'RR_Desc'
LC_OBS = 'LC_OBS'
LC_INT = 'LC_INT'
LC_PDX = 'LC_PDX'
LC_DDX = 'LC_DDX'
LC_MX = 'LC_MX'

LC_OBS_TITLE = 'Observations'
LC_INT_TITLE = 'Interpretation'
LC_PDX_TITLE = 'Primary Differential Diagnosis'
LC_DDX_TITLE = 'Differential Diagnoses'
LC_MX_TITLE = 'Management'

ANS_BLANK = '-- left blank --'

# ****************************
COL_midnight_blue = '#294052'
COL_wedgewood = '#447294'
COL_morning_glory = '#8FBCDB'
COL_half_spanish_white = '#FEF1E1'
COL_peach = '#FEF9F5'
COL_bittersweet = '#FA7268'

COL_eggshell = '#F4F1DE'
COL_terra_cotta = '#E07A5F'
COL_independence = '#3D405B'
COL_greensheen = '#81B29A'
COL_deep_champagne = '#F2CC8F'

COL_light_cornflower_blue = '#8ecae6'
COL_blue_green = '#219EBC'
COL_prussian_blue = '#023047'
COL_honey_yellow = '#FFB703'
COL_orange = '#FB8500'

COL_white = '#FFFFFF'
COL_dark_teal = '#30707C'
COL_cool_mint = '#74C8D2'
COL_tangerine = '#FFB259'
COL_v_light_mint = '#F6FAFA'

# Colours from https://dribbble.com/shots/8296286-Desktop-App-Dashboard-Dark-Mode
COL_highlight_green = '#23a64f'
COL_highlight_blue = '#0678ff'
COL_grey_0 = '#18212a'
COL_grey_1 = '#1d2833'
COL_grey_2 = '#263242'
COL_grey_3 = '#2f3d4c'
COL_l_grey_0 = '#abacb2'
COL_l_grey_1 = '#c4c7d0'

BG_grey = '#273645'

BG_COL = COL_grey_0
TXT_COL = COL_l_grey_1
LINEEDIT_BG = BG_grey
PB_BG_COL = BG_grey
ITEM_BG_COL = COL_grey_1
ITEM_BG_ALT_COL = COL_grey_0
ITEM_TXT_COL = COL_l_grey_1
ITEM_BG_HL_COL = COL_highlight_blue
ITEM_BG_SEL_COL = COL_highlight_blue

BORDER_COL = COL_l_grey_1
BORDER_HL_COL = COL_highlight_blue

BTN_BORDER_COL = BG_COL
BTN_BORDER_HL_COL = COL_highlight_blue

BTN_BG_COL = COL_grey_3
BTN_BG_SEL_COL = COL_highlight_blue
BTN_TXT_COL = COL_l_grey_1

BTN_NEXT_FONT_SIZE = 24

ANS_TXT_FONT_SIZE = 16
ANS_TXT_FONT_COL = COL_l_grey_1
ANS_TXT_BG_COL = COL_grey_2
ANS_TXT_BORDER_COL = ANS_TXT_BG_COL
ANS_TXT_BORDER_HL_COL = COL_tangerine

TOOLBAR_BG_COL = BG_COL
TB_BTN_BORDER_HL_COL = COL_tangerine


STYLESHEET_NAV = """
        QListView {
            show-decoration-selected: 1; /* make the selection span the entire width of the view */
            border-style: solid;
            border-width: 4px;
            border-radius: 10px;
            border-color: """ + BORDER_COL + """;
        }

        QListView::item{
            background: """ + ITEM_BG_COL + """;
            color: """ + ITEM_TXT_COL + """;
        }

        QListView::item:alternate {
            background: """ + ITEM_BG_ALT_COL + """;
            color: """ + ITEM_TXT_COL + """;
        }

        QListView::item:selected:!active {
            background: """ + ITEM_BG_HL_COL + """;
            color: """ + ITEM_TXT_COL + """;
        }

        QListView::item:selected:active {
            background: """ + ITEM_BG_SEL_COL + """;
            color: """ + ITEM_TXT_COL + """;
        }

        QListView::item:hover {
            background: """ + ITEM_BG_HL_COL + """;
            color: """ + ITEM_TXT_COL + """;
        }
        """

STYLESHEET_DLG = '''
            LoginPopup {
                background: ''' + BG_COL + ''';
            }
            QWidget#container {
                border: 4px solid ''' + BORDER_HL_COL + ''';
                border-radius: 10px;
                background: ''' + BG_COL + ''';
            }
            QWidget#container > QLabel {
                color: ''' + ITEM_TXT_COL + ''';
            }
            QLabel#title {
                font-size: 24pt;
            }
            QLabel#subtitle {
                font-size: 18pt;
            }
            QLabel#details {
                font-size: 12pt;
            }
            QPushButton#close {
                color: ''' + ITEM_TXT_COL + ''';
                font-weight: bold;
                font-size: 12pt;
                background: none;
                border: 1px solid gray;
            }
            QPushButton#button {
                color: ''' + BTN_TXT_COL + ''';
                font-weight: bold;
                font-size: 36;
                background: ''' + BTN_BG_COL + ''';
                border: 2px solid gray;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
                margin-top: 30px;
            }
        '''



# SOFTWARE BANNER ############################################################
BANNER_TXT = 'Chimera EV'
BANNER_HTML = '''<p style="font-size:144pt;color: #D76213;background-color:#1D2833;">
                ''' + BANNER_TXT + '''</p>'''
BANNER_CSS = '''
            QLabel#banner {
                color: #347FDB;
                background-color: #1D2833;
                font-size: 144pt;
            }
            '''
