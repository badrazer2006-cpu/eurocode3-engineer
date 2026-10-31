from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from eurocode3.checks import DesignInput, run_checks
from eurocode3.report import pdf_bytes


st.set_page_config(page_title="Eurocode 3 Engineer", layout="wide")
st.title("Eurocode 3 Engineer")
st.caption("أداة محلية أولية للفحص؛ يجب اعتماد النتائج من مهندس إنشائي مختص.")

with st.sidebar:
    st.header("بيانات المشروع")
    project = st.text_input("اسم المشروع", "مشروع تجريبي")
    member = st.text_input("العنصر", "Beam-1")
    steel_grade = st.text_input("درجة الفولاذ", "S275")
    fy = st.number_input("fy (MPa)", min_value=1.0, value=275.0)
    fu = st.number_input("fu (MPa)", min_value=1.0, value=430.0)
    st.header("خصائص القطاع")
    area = st.number_input("A (mm²)", min_value=1.0, value=5000.0)
    iy = st.number_input("Iy (mm⁴)", min_value=1.0, value=8.0e7, format="%.1f")
    iz = st.number_input("Iz (mm⁴)", min_value=1.0, value=2.0e7, format="%.1f")
    wy = st.number_input("Wy (mm³)", min_value=1.0, value=4.0e5)
    wz = st.number_input("Wz (mm³)", min_value=1.0, value=1.5e5)
    length_y = st.number_input("Lcr,y (mm)", min_value=1.0, value=3000.0)
    length_z = st.number_input("Lcr,z (mm)", min_value=1.0, value=3000.0)
    ky = st.number_input("kᵧ", min_value=0.01, value=1.0)
    kz = st.number_input("k𝓏", min_value=0.01, value=1.0)
    st.header("التأثيرات التصميمية")
    ned = st.number_input("NEd (kN) - ضغط سالب", value=-100.0)
    my = st.number_input("My,Ed (kN·m)", value=20.0)
    mz = st.number_input("Mz,Ed (kN·m)", value=5.0)
    ved = st.number_input("VEd (kN)", value=15.0)

uploaded = st.file_uploader("ارفع ملفًا أو صورة للمرجع (لاستخراج المعلومات يدويًا)", type=["pdf", "png", "jpg", "jpeg"])
if uploaded:
    Path("uploads").mkdir(exist_ok=True)
    (Path("uploads") / uploaded.name).write_bytes(uploaded.getvalue())
    st.info(f"تم حفظ الملف المرجعي: {uploaded.name}. راجع البيانات وأدخلها يدويًا.")

data = DesignInput(project, member, steel_grade, fy, fu, area, iy, iz, wy, wz,
                   length_y, length_z, ky, kz, ned, my, mz, ved)

if st.button("إجراء الفحوصات", type="primary"):
    try:
        report = run_checks(data)
    except ValueError as error:
        st.error(str(error))
    else:
        st.subheader("النتائج")
        st.metric("الحالة العامة", "مقبول مبدئيًا" if report.passed else "غير مقبول")
        st.dataframe(
            [{"الفحص": item.name, "الاستغلال": f"{item.utilization:.3f}",
              "المقاومة": f"{item.resistance:.3f} {item.unit}",
              "الطلب": f"{item.demand:.3f} {item.unit}",
              "الحالة": "PASS" if item.passed else "FAIL",
              "ملاحظات": item.note} for item in report.checks
            ],
            use_container_width=True,
        )
        st.download_button("تنزيل تقرير PDF", pdf_bytes(report),
                           "eurocode3_report.pdf", "application/pdf")
        st.download_button("تنزيل مدخلات JSON", json.dumps(data.__dict__, indent=2).encode(),
                           "eurocode3_input.json", "application/json")
