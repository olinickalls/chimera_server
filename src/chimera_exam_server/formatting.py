from .pydanticmodels import RR_Set


def format_rr_answer(ans: RR_Set, indent=4):
    '''
    Pretty Format out a RR answer pydantic object
    '''
    indent = " " * indent
    
    txt = f"{indent}         uid: {ans.uid}\n"
    txt += f"{indent} candidateID: {ans.candidateID}\n"
    txt += f"{indent} device_name: {ans.device_name}\n"
    txt += f"{indent}  start_time: {ans.start_time}\n"
    txt += f"{indent}    set_name: {ans.set_name}\n"

    cases = ans.case

    for i, case_n in enumerate(cases.keys()):
        prefix = f"{indent + (8*' ')}case {case_n:>2} :"
        if cases[case_n].RR_Normal:
            rr_n = 'Normal'
        else:
            rr_n = 'Abnormal'
        if cases[case_n].RR_Abnormal:
            rr_abn = 'Normal'
        else:
            rr_abn = 'Abnormal'
        rr_desc = cases[case_n].RR_Desc

        txt += f"{prefix} {rr_n:>10} {rr_abn:>10} - '{rr_desc}'\n"
    return txt


def format_rr_answer_dict(ans: dict, indent=4):
    '''
    Pretty Format a RR answer _dict_
    '''
    indent = " " * indent
    
    txt = f"{indent}         uid: {ans['uid']}\n"
    txt += f"{indent} candidateID: {ans['candidateID']}\n"
    txt += f"{indent} device_name: {ans['device_name']}\n"
    txt += f"{indent}  start_time: {ans['start_time']}\n"
    txt += f"{indent}    set_name: {ans['set_name']}\n"

    cases = ans['case']

    for i, case_n in enumerate(cases.keys()):
        prefix = f"{indent + (8*' ')}case {case_n:>2} :"
        if cases[case_n]['RR_Normal']:
            rr_n = 'Normal'
        else:
            rr_n = 'Abnormal'
        if cases[case_n]['RR_Abnormal']:
            rr_abn = 'Normal'
        else:
            rr_abn = 'Abnormal'
        rr_desc = cases[case_n]['RR_Desc']

        txt += f"{prefix} {rr_n:>10} {rr_abn:>10} - '{rr_desc}'\n"
    return txt


def format_lc_set_dict(ans: dict, indent=4):
    '''
    Pretty Format a RR answer _dict_
    '''
    indent = " " * indent

    txt = f"{indent}        type: {ans['type']}\n"
    txt += f"{indent}      set_id: {ans['set_id']}\n"
    txt += f"{indent}    set_name: {ans['set_name']}\n"
    txt += f"{indent} candidateID: {ans['candidateID']}\n"
    txt += f"{indent} device_name: {ans['device_name']}\n"
    txt += f"{indent}  start_time: {ans['start_time']}\n"
    txt += f"{indent}         uid: {ans['uid']}\n"

    cases = ans['case']

    case_indent = indent + (18*' ')
    for i, case_n in enumerate(cases.keys()):
        txt += f"{indent + (8*' ')}case {case_n:>2} :\n"
        for field in cases[case_n].keys():
            if field in ('case_n', 'uid'):
                continue
            txt += f"{case_indent} {field}: {cases[case_n][field]}\n"

    return txt

def format_lc_set(ans: dict, indent=4):
    '''
    Pretty Format a RR answer _dict_
    '''
    indent = " " * indent

    txt = f"{indent}        type: {ans.type}\n"
    txt += f"{indent}      set_id: {ans.set_id}\n"
    txt += f"{indent}    set_name: {ans.set_name}\n"
    txt += f"{indent} candidateID: {ans.candidateID}\n"
    txt += f"{indent} device_name: {ans.device_name}\n"
    txt += f"{indent}  start_time: {ans.start_time}\n"
    txt += f"{indent}         uid: {ans.uid}\n"

    cases = ans.case

    case_indent = indent + (18*' ')
    for i, case_n in enumerate(cases.keys()):
        txt += f"{indent + (8*' ')}case {case_n:>2} :\n"

        txt += f"{case_indent} {i}"
        txt += f"{case_indent} LC_OBS: {cases[case_n].LC_OBS}\n"
        txt += f"{case_indent} LC_INT: {cases[case_n].LC_INT}\n"
        txt += f"{case_indent} LC_PDX: {cases[case_n].LC_PDX}\n"
        txt += f"{case_indent} LC_DDX: {cases[case_n].LC_DDX}\n"
        txt += f"{case_indent} LC_MX: {cases[case_n].LC_MX}\n"

    return txt

