"""Open the .docx in Word, update all fields (TOC, lists), save, and export a PDF."""
import os, sys, win32com.client as win32
path = os.path.abspath(sys.argv[1])
pdf = os.path.splitext(path)[0] + ".pdf"
word = win32.DispatchEx("Word.Application"); word.Visible = False; word.DisplayAlerts = 0
try:
    d = word.Documents.Open(path)
    for sid, ind in ((-20, 0), (-21, 18)):
        st = d.Styles(sid); pf = st.ParagraphFormat
        pf.LineSpacingRule = 0; pf.FirstLineIndent = 0; pf.LeftIndent = ind; pf.SpaceAfter = 6; pf.SpaceBefore = 0
        st.Font.Name = "Times New Roman"; st.Font.Size = 12
    d.Fields.Update()
    for i in range(1, d.TablesOfContents.Count + 1):
        d.TablesOfContents(i).Update()
    d.Repaginate()
    for i in range(1, d.TablesOfContents.Count + 1):
        d.TablesOfContents(i).UpdatePageNumbers()
    d.Save()
    d.ExportAsFixedFormat(pdf, 17)
    print("pages", d.ComputeStatistics(2))
    d.Close(False)
finally:
    word.Quit()
print("pdf", pdf)
