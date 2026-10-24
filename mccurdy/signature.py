"""Fillable signature block. Opens in Adobe/Edge/Preview with typed fields; also prints cleanly
for wet ink, and uploads to DocuSign / PandaDoc / Dropbox Sign as-is for a legal e-signature trail."""
from reportlab.lib.units import inch
from reportlab.platypus import Flowable

from .pdfstyle import palette


class SignatureBlock(Flowable):
    def __init__(self, cfg, parties, width=7 * inch, field_prefix="sig"):
        """parties: list of (heading, fields) where fields is a list of labels e.g. ["Signature", "Printed name"]."""
        super().__init__()
        self.cfg = cfg
        self.parties = parties
        self.width = width
        self.prefix = field_prefix
        self.row_h = 0.42 * inch
        rows = max(len(f) for _, f in parties)
        self.height = 0.3 * inch + rows * self.row_h

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = palette(self.cfg)
        canv = self.canv
        col_w = self.width / len(self.parties)
        for i, (heading, fields) in enumerate(self.parties):
            x = i * col_w
            canv.setFont("Helvetica-Bold", 10)
            canv.setFillColor(c["blue"])
            canv.drawString(x, self.height - 0.18 * inch, heading)
            for j, label in enumerate(fields):
                y = self.height - 0.3 * inch - (j + 1) * self.row_h + 0.12 * inch
                line_w = col_w - 0.35 * inch
                canv.setStrokeColor(c["black"])
                canv.setLineWidth(0.6)
                canv.line(x, y, x + line_w, y)
                canv.setFont("Helvetica", 7)
                canv.setFillColor(c["gray"])
                canv.drawString(x, y - 9, label)
                name = f"{self.prefix}_{i}_{label.lower().replace(' ', '_')}"
                canv.acroForm.textfield(
                    name=name, tooltip=f"{heading}: {label}", x=x, y=y + 1, width=line_w, height=0.24 * inch,
                    borderWidth=0, fillColor=None, textColor=c["blue"], fontSize=11,
                    forceBorder=False, fieldFlags="",
                )
