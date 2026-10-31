from __future__ import annotations

from dataclasses import dataclass, field
from math import pi, sqrt
from typing import List, Optional


@dataclass
class MemberData:
    area_mm2: float
    iy_mm4: float
    iz_mm4: float
    wy_mm3: float
    wz_mm3: float
    length_y_mm: float
    length_z_mm: float
    ned_kn: float
    my_knm: float
    mz_knm: float
    ved_kn: float
    fy_mpa: float = 275.0
    gamma_m0: float = 1.0
    gamma_m1: float = 1.0


@dataclass
class ConnectionData:
    mode: str
    shear_kn: float
    bolt_count: int = 0
    bolt_diameter_mm: float = 0.0
    bolt_fu_mpa: float = 400.0
    plate_thickness_mm: float = 0.0
    plate_fu_mpa: float = 430.0
    edge_mm: float = 0.0
    pitch_mm: float = 0.0
    weld_length_mm: float = 0.0
    weld_throat_mm: float = 0.0
    weld_fu_mpa: float = 430.0


@dataclass
class Finding:
    title: str
    demand: float
    resistance: float
    unit: str
    explanation: str

    @property
    def utilization(self) -> float:
        return self.demand / self.resistance if self.resistance > 0 else float("inf")

    @property
    def passed(self) -> bool:
        return self.utilization <= 1


@dataclass
class Analysis:
    findings: List[Finding] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.findings) and all(f.passed for f in self.findings)


def _finding(title: str, demand: float, resistance: float, unit: str, explanation: str) -> Finding:
    return Finding(title, demand, resistance, unit, explanation)


def analyze(member: MemberData, connection: Optional[ConnectionData] = None) -> Analysis:
    positive = [
        member.area_mm2, member.iy_mm4, member.iz_mm4, member.wy_mm3,
        member.wz_mm3, member.length_y_mm, member.length_z_mm, member.fy_mpa
    ]
    if any(value <= 0 for value in positive):
        raise ValueError("جميع خصائص القطاع والأطوال و fy يجب أن تكون أكبر من صفر.")

    result = Analysis()
    npl = member.area_mm2 * member.fy_mpa / member.gamma_m0 / 1000
    result.findings.append(_finding(
        "مقاومة القوة المحورية", abs(member.ned_kn), npl, "kN",
        "مقارنة أولية بين NEd و A·fy/γM0 وفق EN 1993-1-1."
    ))

    euler_y = pi**2 * 210000 * member.iy_mm4 / member.length_y_mm**2 / 1000
    euler_z = pi**2 * 210000 * member.iz_mm4 / member.length_z_mm**2 / 1000
    ncr = min(euler_y, euler_z)
    lambda_bar = sqrt((member.area_mm2 * member.fy_mpa / 1000) / ncr)
    alpha = 0.49
    phi = 0.5 * (1 + alpha * (lambda_bar - 0.2) + lambda_bar**2)
    chi = min(1.0, 1 / (phi + sqrt(max(phi * phi - lambda_bar * lambda_bar, 0))))
    if member.ned_kn < 0:
        nb = chi * npl / member.gamma_m1
        result.findings.append(_finding(
            "الانبعاج العام", abs(member.ned_kn), nb, "kN",
            f"فحص أولي محافظ: λ̄={lambda_bar:.3f} و χ={chi:.3f}. المحور الحاكم "
            f"{'y' if euler_y < euler_z else 'z'}."
        ))

    my = member.wy_mm3 * member.fy_mpa / member.gamma_m0 / 1e6
    mz = member.wz_mm3 * member.fy_mpa / member.gamma_m0 / 1e6
    result.findings.extend([
        _finding("العزم My", abs(member.my_knm), my, "kN·m", "فحص مقاومة مقطع أولي."),
        _finding("العزم Mz", abs(member.mz_knm), mz, "kN·m", "فحص مقاومة مقطع أولي."),
        _finding("القص في العنصر", abs(member.ved_kn), 0.6 * member.area_mm2 *
                 member.fy_mpa / sqrt(3) / 1000, "kN",
                 "تقريب أولي؛ يلزم Av الفعلية للفحص النهائي."),
    ])

    if connection:
        if connection.mode in ("براغي", "براغي ولحام"):
            if connection.bolt_count <= 0 or connection.bolt_diameter_mm <= 0:
                result.missing.append("عدد البراغي وقطر البرغي")
            else:
                area = 0.6 * pi * connection.bolt_diameter_mm**2 / 4
                bolt_rd = connection.bolt_count * 0.6 * connection.bolt_fu_mpa * area / sqrt(3) / 1.25 / 1000
                result.findings.append(_finding(
                    "قص البراغي", connection.shear_kn, bolt_rd, "kN",
                    "فحص أولي وفق EN 1993-1-8؛ يجب التحقق من توزيع القوى ومجموعة البراغي."
                ))
                if connection.plate_thickness_mm <= 0 or connection.edge_mm <= 0:
                    result.missing.append("سمك الصفيحة والمسافة إلى الحافة")
                else:
                    c = min(connection.edge_mm, connection.pitch_mm - connection.bolt_diameter_mm / 2)
                    bearing = max(0.0, 2.5 * c * connection.plate_thickness_mm *
                                   connection.plate_fu_mpa / 1.25 / 1000)
                    result.findings.append(_finding(
                        "سحق الصفيحة عند البراغي", connection.shear_kn,
                        connection.bolt_count * bearing, "kN",
                        "تقريب أولي؛ يجب استخدام معاملات αb وk1 والمسافات الفعلية."
                    ))
        if connection.mode in ("لحام", "براغي ولحام"):
            if connection.weld_length_mm <= 0 or connection.weld_throat_mm <= 0:
                result.missing.append("طول اللحام وسمك الحلق الفعال")
            else:
                weld = connection.weld_length_mm * connection.weld_throat_mm * connection.weld_fu_mpa / sqrt(3) / 1.25 / 1000
                result.findings.append(_finding(
                    "مقاومة اللحام", connection.shear_kn, weld, "kN",
                    "فحص أولي للحام تحت القص؛ يلزم تحديد اتجاهات اللحام وأطوالها الفعالة."
                ))
    return result
