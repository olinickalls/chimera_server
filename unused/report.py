from reportlab.platypus import (
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    SimpleDocTemplate,
    PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT
)
from random import choice, randint
from datetime import datetime
from server-constants import (
    DEBUG_REPORT,
    REPORT_PATH,
    RR_NORMAL,
    RR_ABNORMAL,
    RR_DESC,
    LC_OBS,
    LC_INT,
    LC_PDX,
    LC_DDX,
    LC_MX,
    ANS_BLANK,
    LC_OBS_TITLE,
    LC_INT_TITLE,
    LC_PDX_TITLE,
    LC_DDX_TITLE,
    LC_MX_TITLE
)
from pathlib import Path
from utils import get_safe_filename
import os


def reformat(strtxt: str):
    '''
    Convert the Python '/n' to <br/> which report lab understands
    '''
    return strtxt.replace('\n', '<br/>\n')


def create_answer_pdf(answers, draft_status=False):
    '''
    Supply the .answers dict from answer sheet widget.
    Prototype (from Answer_sheet_widget() class def.)
        self.answers = {'type': self.parent.current_set_type,
                        'set_id': c_set_id,
                        'set_name': set_name,
                        'candidateID': 'Candidate X',
                        'case': {}
                        }    '''
    if DEBUG_REPORT:
        print("[create_answer_pdf]")
        print(f"\tType:{answers['type']}")
        print(f"\tset_id:{answers['set_id']}")
        print(f"\tset_name:{answers['set_name']}")
        print(f"\tcandidate_ID:{answers['candidateID']}")
        print(f"\tNo. Cases:{len(answers['case'])}")

    if answers['type'] == 'RR':
        pathPDF = create_rapids_pdf(answers, draft_status)
    elif answers['type'] == 'LC':
        pathPDF = create_longcase_pdf(answers, draft_status)
    else:
        print('[create_answer_pdf] Unknown set_id type: {answers["type"]}')
        return None
    return pathPDF


def get_filename(fname: str = '', draft: bool = False):
    '''
    Adjust filename to make unique draft names to prevent clash'''
    now = datetime.now()
    if draft:
        dt_str = now.strftime("(%Y-%m-%d_%H-%M-%S.%f)")
        new_fname = fname + '_' + dt_str + '_draft.pdf'
        return new_fname

    else:
        dt_str = now.strftime("(%H-%M-%S.%f)")
        new_fname = fname + '_' + dt_str + '.pdf'
        return new_fname


def get_filepath(candID: str,
                 set_name: str,
                 draft: bool
                 ):
    '''
    Generate appropriate report filename for RR/LC and draft/final
    '''
    # ########## Report PATH ##########

    if REPORT_PATH is None:
        report_path = Path(os.getcwd())
    else:
        report_path = Path(REPORT_PATH)

    dt = datetime.now()
    report_path /= Path(dt.strftime("%Y-%m-%d %A"))

    if draft:
        report_path = report_path / Path('Drafts')
    else:
        report_path = report_path / Path('Final')

    # ########## Report Filename ##########

    base = get_safe_filename(f'{candID}-{set_name}')
    if draft:
        fname = get_filename(base, draft=True)
    else:
        fname = get_filename(base, draft=False)

    report_fp = report_path / Path(fname)
    report_fp.parent.mkdir(parents=True, exist_ok=True)
    return report_fp


def create_rapids_pdf(answers, draft=False, show_PDF=False):
    set_name = answers['set_name']  # string - set number != c_set_id
    candidate_ID = answers['candidateID']  # string

    report_fp = get_filepath(candID=answers['candidateID'],  # string,
                             set_name=answers['set_name'],  # string - set number != c_set_id,
                             draft=draft
                             )

    # DT for in-report use
    now = datetime.now()
    dt_str = now.strftime("%d %B, %Y")
    # dt_file_str = now.strftime("%d-%B-%Y")

    # if REPORT_PATH is not None:
    #     report_path = Path(REPORT_PATH)
    # else:
    #     report_path = Path(os.getcwd())
    # fname = get_safe_filename(f'{set_name}-{candidate_ID}')
    # if draft:
    #     fname = get_draft_filename(fname)
    # fname += '.pdf'

    # report_fp = report_path / Path(dt_file_str) / Path(fname)
    # report_fp.parent.mkdir(parents=True, exist_ok=True)

    # Header style
    styleSheet = getSampleStyleSheet()
    h3 = styleSheet['Heading3']
    h3.spaceBefore = 0
    h3.spaceAfter = 0

    # Paragraph style in-table
    PARA_STYLE = styleSheet['Normal']
    PARA_STYLE.spaceBefore = 0
    PARA_STYLE.spaceAfter = 0
    PARA_STYLE.leading = 10
    PARA_STYLE.fontSize = 8

    # Data creation - one row per RR case answer
    data = []
    for i, rr_case_key in enumerate(answers['case'], start=1):
        row = []
        row.append(f'{i}.')
        rr_case = answers['case'][rr_case_key]
        if rr_case[RR_NORMAL] is True and rr_case[RR_ABNORMAL] is False:
            row.append(Paragraph('<b>N</b>ormal', PARA_STYLE))
        elif rr_case[RR_ABNORMAL] is True and rr_case[RR_NORMAL] is False:
            row.append(Paragraph('<b>Ab</b>normal', PARA_STYLE))
        else:  # both are False
            row.append(Paragraph('Not answered', PARA_STYLE))

        row.append(Paragraph(reformat(rr_case[RR_DESC]), PARA_STYLE))
        row.append(10 * ' ')
        data.append(row)

    t = Table(data,
              colWidths=[0.3*inch, 0.9*inch, 5.7*inch, 0.5*inch],
              style=[  # ALL cells grey border
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    # case number Align Left
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ]
              )

    story = []
    story.append(Paragraph(f"""Rapids Marksheet {dt_str}<br/>
                            Set: {set_name}\t\tUser: {candidate_ID}""", h3))
    story.append(t)

    SimpleDocTemplate(str(report_fp),
                      pagesize=A4,
                      showBoundary=0
                      ).build(story)
    # Expand this with header/Footer from:
    # https://stackoverflow.com/questions/67702808
    if show_PDF:
        os.system(f'start {report_fp}')

    return report_fp


def create_longcase_pdf(answers, draft=False, show_PDF=False):
    set_name = answers['set_name']  # string - set number != c_set_id
    candidate_ID = answers['candidateID']  # string

    report_fp = get_filepath(candID=answers['candidateID'],  # string,
                             set_name=answers['set_name'],  # string - set number != c_set_id,
                             draft=draft
                             )
    now = datetime.now()
    dt_str = now.strftime("%d %B, %Y")
    dt_file_str = now.strftime("%d-%B-%Y")

    # if REPORT_PATH is not None:
    #     report_path = Path(REPORT_PATH)
    # else:
    #     report_path = Path(os.getcwd())
    # fname = get_safe_filename(f'{set_name}-{candidate_ID}')
    # if draft:
    #     fname = get_draft_filename(fname)
    # fname += '.pdf'

    # report_fp = report_path / Path(dt_file_str) / Path(fname)
    # report_fp.parent.mkdir(parents=True, exist_ok=True)

    # Header style
    styleSheet = getSampleStyleSheet()

    title = styleSheet['title']
    title.spaceBefore = 0
    title.spaceAfter = 6

    subtitle = styleSheet['Heading1']
    subtitle.spaceBefore = 0
    subtitle.spaceAfter = 6
    subtitle.fontSize = 12
    subtitle.alignment = TA_CENTER

    head_sty = styleSheet['Heading3']
    head_sty.spaceBefore = 12
    head_sty.spaceAfter = 8

    # Paragraph styles
    ans_sty = styleSheet['Normal']
    ans_sty.spaceBefore = 6
    ans_sty.spaceAfter = 6
    ans_sty.leftIndent = 10
    ans_sty.leading = 10
    ans_sty.fontSize = 8
    ans_sty.borderColor = '#808080'
    ans_sty.borderPadding = (5, 10, 5, 10)
    ans_sty.borderWidth = 0.5

    story = []

    # Paragraph creation - one Para per LC answer segment.
    # Titles and Section Headers
    top = Paragraph(f'Long Case Answer Sheet {dt_str}', style=title)
    top_data = Paragraph(f'Set: {set_name}\t\tUser: {candidate_ID}', subtitle)

    for case_n, case_id in enumerate(answers['case'], start=1):
        obs_head = Paragraph(f'{case_n}.1 {LC_OBS_TITLE}', head_sty)
        int_head = Paragraph(f'{case_n}.2 {LC_INT_TITLE}', head_sty)
        pdx_head = Paragraph(f'{case_n}.3 {LC_PDX_TITLE}', head_sty)
        ddx_head = Paragraph(f'{case_n}.4 {LC_DDX_TITLE}', head_sty)
        mx_head = Paragraph(f'{case_n}.5 {LC_MX_TITLE}', head_sty)

        case = answers['case'][case_id]
        case_title = Paragraph(f'Case {case_n}', subtitle)
        obs_ans = Paragraph(reformat(case[LC_OBS]), ans_sty)
        int_ans = Paragraph(reformat(case[LC_INT]), ans_sty)
        pdx_ans = Paragraph(reformat(case[LC_PDX]), ans_sty)
        ddx_ans = Paragraph(reformat(case[LC_DDX]), ans_sty)
        mx_ans = Paragraph(reformat(case[LC_MX]), ans_sty)

        # Answer Title and Demographics
        story.append(top)
        story.append(top_data)
        story.append(case_title)

        # Answer Headers & Text
        story.append(obs_head)
        story.append(obs_ans)

        story.append(int_head)
        story.append(int_ans)

        story.append(pdx_head)
        story.append(pdx_ans)

        story.append(ddx_head)
        story.append(ddx_ans)

        story.append(mx_head)
        story.append(mx_ans)

        story.append(PageBreak())

    SimpleDocTemplate(str(report_fp),
                      pagesize=A4,
                      showBoundary=0
                      ).build(story)
    # Expand this with header/Footer from:
    # https://stackoverflow.com/questions/67702808
    if show_PDF:
        os.system(f'start {report_fp}')
    
    return report_fp


def get_rr_case_answer(norm=None, abn=None, desc=''):
    '''
    # Used only in TESTING (generate_fake_rr_answers)
    answer as defined in displayclasses.py

    ans[RR_NORMAL] = False
    ans[RR_ABNORMAL] = False
    ans[RR_DESC] = ''
    '''
    case_dict = {
        RR_NORMAL: norm,
        RR_ABNORMAL: abn,
        RR_DESC: desc
    }
    return case_dict


def generate_fake_rr_answers():
    '''
    Makes 30 fake RR answers
    '''
    answers = {'type': 'RR',
               'set_id': randint(0, 100),
               'set_name': f'RR_set_{randint(1,100)}',
               'candidateID': choice(fake_names),  # part of uid
               'device_name:': choice(['mac1', 'mac3', 'mac7', 'mac9']),  # part of uid
               'start_time': get_rnd_dt(),  # part of uid
               'case': {}
               }

    answers['case'][1] = get_rr_case_answer(norm=True, abn=False)
    answers['case'][2] = get_rr_case_answer(norm=False,
                                            abn=True,
                                            desc='Some fracture'
                                            )
    answers['case'][3] = get_rr_case_answer(norm=False, abn=False, desc='')
    for i in range(4, 31):
        if choice([True, False]) is True:
            norm = True
            abn = False
            desc_txt = ''
        else:
            norm = False
            abn = True
            desc_txt = (f"{choice(['left', 'right'])} sided " +
                        f"{choice(['fracture', 'dislocation', 'FB'])}")
        answers['case'][i] = get_rr_case_answer(norm, abn, desc_txt)

    return answers


def get_lc_case_answer(OBStxt: str = None,
                       INTtxt: str = None,
                       PDXtxt: str = None,
                       DDXtxt: str = None,
                       MXtxt: str = None):
    '''
    answer as defined in displayclasses.py

    ans[RR_NORMAL] = False
    ans[RR_ABNORMAL] = False
    ans[RR_DESC] = ''
    '''
    if OBStxt is None:
        OBStxt = ANS_BLANK
    if INTtxt is None:
        INTtxt = ANS_BLANK
    if PDXtxt is None:
        PDXtxt = ANS_BLANK
    if DDXtxt is None:
        DDXtxt = ANS_BLANK
    if MXtxt is None:
        MXtxt = ANS_BLANK

    if OBStxt.strip() == '':
        OBStxt = ANS_BLANK
    if INTtxt.strip() == '':
        INTtxt = ANS_BLANK
    if PDXtxt.strip() == '':
        PDXtxt = ANS_BLANK
    if DDXtxt.strip() == '':
        DDXtxt = ANS_BLANK
    if MXtxt.strip() == '':
        MXtxt = ANS_BLANK

    case_dict = {
        LC_OBS: OBStxt,
        LC_INT: INTtxt,
        LC_PDX: PDXtxt,
        LC_DDX: DDXtxt,
        LC_MX: MXtxt
    }
    return case_dict


def generate_fake_lc_answers(n: int = 6):
    '''
    Makes n (default 6) fake LC answers
    '''
    answers = {'type': 'LC',
               'set_id': randint(0, 100),
               'set_name': f'RR_set_{randint(1,100)}',
               'candidateID': choice(fake_names),  # part of uid
               'device_name:': choice(['mac1', 'mac3', 'mac7', 'mac9']),  # part of uid
               'start_time': get_rnd_dt(),  # part of uid
               'case': {}
               }

    answers['case'][1] = get_lc_case_answer('These are my observations',
                                            'My interpretation...',
                                            'Prime Differential::',
                                            'Other differentials...',
                                            'Further Management goes here.')
    answers['case'][2] = get_lc_case_answer(OBStxt='--Intentionally Blank--')
    for i in range(3, n + 1):
        OBStxt = (f"{choice(['left', 'right'])} sided " +
                  f"{choice(['fracture', 'dislocation', 'FB'])}")
        INTtxt = choice(['MCA CVA', 'Intestinal Obstruction', 'Foreign Body'])
        PDXtxt = choice(['Malig Obstruction.', 'SDH', 'Pathologic Fracture'])
        DDXtxt = '1. Infarct\n2. IO\n3.Malignancy'
        MXtxt = ('1. Call someone.\n2. MDM\n3. Surgical referal (urgent)' +
                 '4. CT/MRI follow up.\n5. Onc ref.\n6. Neuro ref for tremor.')
        answers['case'][i] = get_lc_case_answer(OBStxt, INTtxt, PDXtxt, DDXtxt, MXtxt)

    return answers


def get_rnd_dt():
    rnd_dt = "20220123-"
    rnd_dt += str(randint(0, 23))
    rnd_dt += str(randint(0, 59))
    rnd_dt += str(randint(0, 59)) + '.'
    rnd_dt += str(randint(0, 999999))
    return rnd_dt


fake_names = ['Ray Burch',
              'Douglas Durham',
              'Darius Ramsey',
              'Chance Meza',
              'Kiana Harvey',
              'Julio Ellis',
              'Jaelynn Lynn',
              'Caleb Solis',
              'Destiney Houston',
              'Dominique Sharp',
              'Mara Holder',
              'Casey Pierce',
              'Nadia Reynolds',
              'Lawson Barton',
              'Moses Spence',
              'Cali Cardenas',
              'Lyla Payne',
              'Rodolfo Bowers',
              'Sidney Banks',
              'Malaki Fuller',
              'Savanna Underwood',
              'Brent Ponce',
              'Zara Dorsey',
              'Bridget Mendez',
              'Marco Stephenson',
              'Gaven Jones',
              'Jayvon Valenzuela',
              'Leonel Mack',
              'Wayne Simon',
              'Greyson Fuentes',
              ]
