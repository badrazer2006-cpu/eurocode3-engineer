from __future__ import annotations

from dataclasses import dataclass, field
from math import pi, sqrt
from typing import Dict, List


@dataclass
class DesignInput:
    project: str
    member: str
    steel_grade: str
    fy_mpa: float
    fu_mpa: float
    area_mm2: float
    iy_mm4: float
    iz_mm4: float
    wy_mm3: float
    wz_mm3: float
    length_y_mm: float
    length_z_mm: float
    ky: float
    kz: float
    ned_kn: float = 0.0
    my_ed_knm: float = 0.0
    mz_ed_knm: float = 0.0
    ved_kn: float = 0.0
    gamma_m0: float = 1.0
    gamma_m1: float = 1.0
    gamma_m2: float = 1.25


@dataclass
class CheckResult:
    name: str
    utilization: float
    resistance: float
    demand: float
    unit: str
    passed: bool
    note: str


@dataclass
class DesignReport:
    inputs: DesignInput
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.checks)


def _result(name: str, demand: float, resistance: float, unit: str, note: str = "") -> CheckResult:
    utilization = demand / resistance if resistance > 0 else float("inf")
    return CheckResult(name, utilization, resistance, demand, unit, utilization <= 1.0, note)


def _buckling_curve(steel_grade: str, section_axis: str) -> str:
    # Conservative default curves for a preliminary check when section type is unknown.
    if steel_grade.upper().startswith("S"):
        return "b"
    return "c"


def _buckling_reduction(lambda_bar: float, curve: str) -> float:
    alpha = {"a": 0.21, "b": 0.34, "c": 0.49, "d": 0.76}[curve]
    phi = 0.5 * (1 + alpha * (lambda_bar - 0.2) + lambda_bar**2)
    return min(1.0, 1 / (phi + sqrt(max(phi**2 - lambda_bar**2, 0))))


def run_checks(data: DesignInput) -> DesignReport:
    if min(data.area_mm2, data.iy_mm4, data.iz_mm4, data.wy_mm3, data.wz_mm3) <= 0:
        raise ValueError("خصائص القطاع يجب أن تكون أكبر من صفر.")
    if min(data.length_y_mm, data.length_z_mm, data.gamma_m0, data.gamma_m1) <= 0:
        raise ValueError("الأطوال ومعاملات الأمان يجب أن تكون أكبر من صفر.")

    report = DesignReport(data)
    fy = data.fy_mpa
    area = data.area_mm2

    # EN 1993-1-1 6.2.3: N_pl,Rd = A fy / gamma_M0.
    n_pl_rd = area * fy / data.gamma_m0 / 1000
    if data.ned_kn >= 0:
        report.checks.append(_result("الشد / المقاومة البلاستيكية", data.ned_kn, n_pl_rd, "kN"))
    else:
        report.checks.append(_result("الضغط / المقاومة البلاستيكية", abs(data.ned_kn), n_pl_rd, "kN"))

    # EN 1993-1-1 6.3.1: Euler loads and reduction factor.
    euler_y = pi**2 * 210000 * data.iy_mm4 / (data.ky * data.length_y_mm) ** 2 / 1000
    euler_z = pi**2 * 210000 * data.iz_mm4 / (data.kz * data.length_z_mm) ** 2 / 1000
    ncr = min(euler_y, euler_z)
    lambda_bar = sqrt((area * fy / 1000) / ncr)
    axis = "y" if euler_y <= euler_z else "z"
    chi = _buckling_reduction(lambda_bar, _buckling_curve(data.steel_grade, axis))
    n_b_rd = chi * n_pl_rd / data.gamma_m1
    if data.ned_kn < 0:
        report.checks.append(
            _result("الانبعاج العام بالضغط", abs(data.ned_kn), n_b_rd, "kN",
                    f"المحور الحاكم {axis}، λ̄={lambda_bar:.3f}، χ={chi:.3f}")
        )

    my_rd = data.wy_mm3 * fy / data.gamma_m0 / 1e6
    mz_rd = data.wz_mm3 * fy / data.gamma_m0 / 1e6
    report.checks.append(_result("العزم حول y", abs(data.my_ed_knm), my_rd, "kN·m"))
    report.checks.append(_result("العزم حول z", abs(data.mz_ed_knm), mz_rd, "kN·m"))

    shear_area = 0.6 * area
    v_rd = shear_area * fy / sqrt(3) / data.gamma_m0 / 1000
    report.checks.append(_result("القص", abs(data.ved_kn), v_rd, "kN",
                                 "تقريب أولي لمساحة القص؛ أدخل Av الفعلية للتصميم النهائي."))

    n_ratio = abs(data.ned_kn) / n_b_rd if data.ned_kn < 0 else abs(data.ned_kn) / n_pl_rd
    interaction = n_ratio + abs(data.my_ed_knm) / my_rd + abs(data.mz_ed_knm) / mz_rd
    report.checks.append(_result("تفاعل N + My + Mz", interaction, 1.0, "-",
                                 "تفاعل خطي محافظ للفحص الأولي، وليس بديلاً عن فحص 6.3.3 الكامل."))
    return report
