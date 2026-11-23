import os, sys, win32com.client as win32, pymupdf
path = os.path.abspath(sys.argv[1]); pdf = os.path.splitext(path)[0] + ".pdf"
app = win32.DispatchEx("PowerPoint.Application")
try:
    pr = app.Presentations.Open(path, WithWindow=False); pr.SaveAs(pdf, 32); pr.Close()
finally:
    app.Quit()
d = pymupdf.open(pdf); out = sys.argv[2]
for i, p in enumerate(d): p.get_pixmap(dpi=96).save(f"{out}/s{i+1:02d}.png")
print(len(d))
