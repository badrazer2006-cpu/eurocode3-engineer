from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .checks import DesignReport


def pdf_bytes(report: DesignReport) -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    y = height - 45
    pdf.setTitle(f"Eurocode 3 - {report.inputs.project}")

    def line(text: str, size: int = 10) -> None:
        nonlocal y
        if y < 45:
            pdf.showPage()
            y = height - 45
        pdf.setFont("Helvetica", size)
        pdf.drawString(40, y, text[:120])
        y -= 16

    line("Eurocode 3 - Preliminary Steel Member Check", 14)
    line(f"Project: {report.inputs.project}")
    line(f"Member: {report.inputs.member}")
    line(f"Steel: {report.inputs.steel_grade}, fy={report.inputs.fy_mpa:.1f} MPa")
    line("Units: mm, kN, kN.m, MPa")
    line("")
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        line(f"[{status}] {check.name}: demand={check.demand:.3f} {check.unit}, "
             f"resistance={check.resistance:.3f} {check.unit}, utilization={check.utilization:.3f}")
        if check.note:
            line(f"  {check.note}", 9)
    line("")
    line("WARNING: Preliminary engineering aid only. Verify loads, section class, "
         "buckling curves, connections, fire and national annex requirements.")
    pdf.save()
    return output.getvalue()
