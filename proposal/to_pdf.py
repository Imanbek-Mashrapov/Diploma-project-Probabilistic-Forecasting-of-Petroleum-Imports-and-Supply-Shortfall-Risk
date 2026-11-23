import os, sys, win32com.client as win32
p=os.path.abspath(sys.argv[1]); w=win32.DispatchEx("Word.Application"); w.Visible=False
try:
    d=w.Documents.Open(p); d.ExportAsFixedFormat(os.path.splitext(p)[0]+".pdf",17); print("pages",d.ComputeStatistics(2)); d.Close(False)
finally: w.Quit()
