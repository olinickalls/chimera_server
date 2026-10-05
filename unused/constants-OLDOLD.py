# constants.py
# Copyright Oliver Nickalls, March 2021
try:
    from PySide6.QtGui import QFont
except ModuleNotFoundError:
    from PySide2.QtGui import QFont
from pathlib import Path

SERVER_IP = 'http://192.168.50.76:8000'

DEBUG = True
DEBUG_SIDEBAR = False
DEBUG_SERIES = False
DEBUG_CATALOG = False
DEBUG_LOAD = True

DEBUG_ICONS = False
DEBUG_THUMBS = False
DEBUG_TOOLBAR = False

DEBUG_MOUSE = False
DEBUG_DICOM = True
DEBUG_DICOM_LOAD = True
DEBUG_DICOMPIXEL = True
DEBUG_IMGWIDGET = False
DEBUG_LEVELS = False

DEBUG_ANS = False
DEBUG_REPORT = False
DEBUG_SERVER = False
DEBUG_SUBMIT = False
DEBUG_ENTER_ID = False

DEBUG_BUTTONS = False  # show the buttons used for debugging

# Identify the computer name
import socket
DEVICE_NAME = socket.gethostname()

# SERVER OPTIONS #############################################################
SERVER_ENABLED = False  # if false, prevents all server communication.

# submit when changing cases
SUBMIT_ON_NEW_RR_CASE = False
SUBMIT_ON_NEW_LC_CASE = False


# LOCAL DB OPTIONS #############################################################
# Local SQLite DB
LOCAL_DB_DIR = 'HISTORY'
LOCAL_DB_FILE = 'local_data.db'
LOCAL_DB_FP = Path(LOCAL_DB_DIR) / Path(LOCAL_DB_FILE)

# IMAGE VIEW OPTIONS #############################################################
# vispy :   "VISPY"
# pyqtgraph "PYQTGRAPH"
IMG_DISPLAY_METHOD = "PYQTGRAPH"
DEBUG_VISPY = False

# Methods to load DICOM files ################################################
# Allowed values: ITK      - Use _fast_ ITK library (buggy?)
#                 ORIGINAL - Use my PYDICOM method (slower)
#                 MEDIO    - Probably the best choice but experimental
# NB- ITK pre-windows the volumes using in-file values.
DCM_VOL_METHOD = 'ITK'
DEBUG_DICOM_LOAD = True

# Attempt to verify SimpleITK is present
try:
    import SimpleITK as sitk
    print(f'Loaded SimpleITK v{sitk.__version__}')
    SITK_AVAILABLE = True
except Exception as e:
    if DEBUG or DEBUG_DICOM or DEBUG_DICOMPIXEL:
        print(e)
    SITK_AVAILABLE = False

if not SITK_AVAILABLE and DCM_VOL_METHOD == 'ITK':
    print('*** import SimpleITK failed. Failing over to ORIGINAL method.')
    DCM_VOL_METHOD = 'ORIGINAL'


# RR/LC DISPLAY OPTIONS ######################################################
DEFAULT_HX = 'No history provided.'


# RR/LC SRC DIR OPTIONS ######################################################
RRSET_PREFIX = 'RRSET'
LCSET_PREFIX = 'LONGSET'
VVSET_PREFIX = 'VIVASET'

RRCASE_PREFIX = 'RR'
LCCASE_PREFIX = 'LONGCASE'
VVCASE_PREFIX = 'VIVACASE'

RRSERIES_PREFIX = 'RR'
LCSERIES_PREFIX = ''
VVSERIES_PREFIX = ''

LC_CASE_NAME_STRICT = False


# Converted to a Path object.
# Is relative to current dir unless explicitly otherwise.
REPORT_PATH = 'REPORTS'


# Sort LC series by name - method
# seriesclass.py Series.get_custom_series_n()
# Options:
#     'LAST2DIGITS' If DIRs end with 2 digit numbers then use those.
#     'DICOMDT' Use DICOM AcquisitionDate & Time of 1st DICOM file
#     'ALPHABETICAL' DIR list by Alphabetical sort [DEFAULT]

LC_SERIES_SORT_METHOD = 'DICOMDT'

# ###################  UI Constants  ######################

# Toolbar buttons:
SHOW_RESET_IMAGE = True
SHOW_INVERT_IMAGE = False
SHOW_WINDOW_BRAIN = True
SHOW_WINDOW_BONE = True
SHOW_WINDOW_LUNG = True
SHOW_WINDOW_ABDOMEN = True
SHOW_FLIP_LR = False
SHOW_FLIP_CC = False
SHOW_ROTATE_CCW = True
SHOW_ROTATE_CW = True


FORCE_PWD = False  # Require a pwd in the Cand ID entry popup.

# End Exam options
ENDEXAM_SHOW_DISCARD = True

TOOL_SIZE = 44
THUMBNAIL_SIZE = 120
THUMBNAIL_SPACING = 15

# Fonts used
LIST_FONT = QFont()
# LIST_FONT.setFamily("Corbel")
LIST_FONT.setFamily("Calibri")
LIST_FONT.setPointSize(14)
LIST_FONT.setWeight(QFont.Normal)

GEN_FONT = 'Calibri'
GEN_FONT_WEIGHT = 'Normal'
GEN_FONT_SIZE = '14pt'

STYLE_NAV = """
"""

STYLE_DIAG = """
"""
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
# from webpage: icon col #aeb1ba
#              TB BG col #303d4d


# Yellow/dark blues
# BG_COL = COL_prussian_blue
# TXT_COL = COL_half_spanish_white
# ITEM_BG_COL = COL_light_cornflower_blue
# ITEM_BG_ALT_COL = COL_blue_green
# ITEM_TXT_COL = COL_half_spanish_white
# ITEM_BG_HL_COL = COL_orange
# ITEM_BG_SEL_COL = COL_orange

# BORDER_COL = COL_wedgewood
# BORDER_HL_COL = COL_terra_cotta
# BTN_BG_COL = COL_prussian_blue
# BTN_BG_SEL_COL = COL_honey_yellow
# BTN_TXT_COL = COL_wedgewood

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

# Read Accepted Users List
CAND_LIST_FILE = Path('userslist.txt')
CAND_LIST = []
if CAND_LIST_FILE.exists():
    CAND_LIST_ENABLED = True

    with open(CAND_LIST_FILE) as users_file:
        CAND_LIST = users_file.readlines()
        CAND_LIST = [item.strip(' \n\r') for item in CAND_LIST]

else:
    CAND_LIST_ENABLED = False

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
