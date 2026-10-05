Chimera Server ToDo list
========================

## Basic Features

- [x] prevent cursor object being sent back by server

### Supporting functionality

- [x] Create new session

- [ ] 'External' API test code
- [ ] Separate API call code into an api.py


### PDF output

- [ ] Test server-side PDF print
    BUG [x] RR 'answer' not populating in PDF
    BUG [x] RR (?LC too?) answers sorted by DB order, not case no. order.
        mitigation [x] results from DB ordered by case_number

    BUG [x] LC answers sorted by DB order, not case no. order.
        mitigation [x] results from DB ordered by case_number

- [x] Add a 'pdf_filepath' column to ?session table
- [ ] Set 'pdf_filepath' to local PDF fp when PDF exported

- [ ] Create all 30 RR or 5 LC answers on session creation for performance??
- [x] 'pretty print' formatting functions for logging whole answers

### Rapid Reporting (old style)

- [x] Store RR Case
- [x] Store RR Whole 
- [x] Finalise RR

### Long Case Reporting

- [x] Create LC Case pydantic model
- [x] Create LC Set pydantic model

- [x] Make LC case pydantic model keys match in-client dict keys

- [x] Store LC Case
  BUG - [x] only INSERT method used. Does not UPDATE.
- [x] Store LC Whole 
- [x] Finalise LC

### BUG 01:
    Test RR qn 37 added. Then rest of Questions 1-30 aded. When savibg to PDF, they are only saved in dict order & otherwise ignoring actual question number values in the answers dict.  Should record actual **question number** and in order.
- [x] Make sure RR & LC answers are sorted in order.
- [x] ? print _actual_ question number in PDF, not _assumed_ value
