from __future__ import annotations

import streamlit as st

from eurocode3_teacher.engine import ConnectionData, MemberData, analyze

st.set_page_config(page_title="Eurocode 3 Teacher Engineer", layout="wide")
st.title("Eurocode 3 — الأستاذ المهندس")
st.warning("هذه أداة تعليمية وفحوصات أولية فقط، وليست اعتمادًا نهائيًا للتنفيذ.")

st.write("ارفع صورة الوصلة أو المخطط، وسأعرضها لك وأطلب القياسات اللازمة. "
         "الصورة لا تكفي وحدها لاستخراج أبعاد موثوقة.")
image = st.file_uploader("صورة أو PDF", type=["png", "jpg", "jpeg", "pdf"])
if image and image.type.startswith("image/"):
    st.image(image, caption="الصورة المرجعية", use_container_width=True)

with st.sidebar:
    st.header("بيانات العنصر")
    area = st.number_input("A (mm²)", 1.0, value=5000.0)
    iy = st.number_input("Iy (mm⁴)", 1.0, value=8e7, format="%.1f")
    iz = st.number_input("Iz (mm⁴)", 1.0, value=2e7, format="%.1f")
    wy = st.number_input("Wy (mm³)", 1.0, value=4e5)
    wz = st.number_input("Wz (mm³)", 1.0, value=1.5e5)
    ly = st.number_input("Lcr,y (mm)", 1.0, value=3000.0)
    lz = st.number_input("Lcr,z (mm)", 1.0, value=3000.0)
    fy = st.number_input("fy (MPa)", 1.0, value=275.0)
    ned = st.number_input("NEd (kN، الضغط سالب)", value=-100.0)
    my = st.number_input("My,Ed (kN·m)", value=20.0)
    mz = st.number_input("Mz,Ed (kN·m)", value=5.0)
    ved = st.number_input("VEd (kN)", value=15.0)
    st.header("بيانات الوصلة")
    mode = st.selectbox("نوع الوصلة", ["براغي", "لحام", "براغي ولحام"])
    shear = st.number_input("قص الوصلة (kN)", min_value=0.0, value=15.0)
    bolts = st.number_input("عدد البراغي", min_value=0, value=4)
    diameter = st.number_input("قطر البرغي (mm)", min_value=0.0, value=16.0)
    thickness = st.number_input("سمك الصفيحة (mm)", min_value=0.0, value=10.0)
    edge = st.number_input("المسافة للحافة (mm)", min_value=0.0, value=40.0)
    pitch = st.number_input("المسافة بين البراغي (mm)", min_value=0.0, value=70.0)
    weld_length = st.number_input("طول اللحام (mm)", min_value=0.0, value=0.0)
    weld_throat = st.number_input("سمك حلق اللحام a (mm)", min_value=0.0, value=0.0)

if st.button("حلّل واشرح لي", type="primary"):
    member = MemberData(area, iy, iz, wy, wz, ly, lz, ned, my, mz, ved, fy)
    connection = ConnectionData(mode, shear, int(bolts), diameter, plate_thickness_mm=thickness,
                                edge_mm=edge, pitch_mm=pitch, weld_length_mm=weld_length,
                                weld_throat_mm=weld_throat)
    try:
        result = analyze(member, connection)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.subheader("شرح الأستاذ")
        st.write("الاستغلال = الطلب ÷ المقاومة. إذا كان أقل من 1.00 فالفحص ينجح مبدئيًا.")
        if result.passed:
            st.success("الفحوصات المدخلة ناجحة مبدئيًا. راجع الفرضيات والكود الوطني.")
        else:
            st.error("هناك فحص أو أكثر غير ناجح؛ لا تعتمد الوصلة قبل تعديلها ومراجعتها.")
        st.dataframe([
            {"الفحص": f.title, "الطلب": f"{f.demand:.2f} {f.unit}",
             "المقاومة": f"{f.resistance:.2f} {f.unit}",
             "الاستغلال": f"{f.utilization:.3f}",
             "الحالة": "ناجح" if f.passed else "غير ناجح",
             "الشرح": f.explanation}
            for f in result.findings
        ], use_container_width=True)
        if result.missing:
            st.info("المعطيات الناقصة قبل دراسة نهائية: " + "، ".join(result.missing))
        st.subheader("حلول تعليمية عند عدم النجاح")
        st.write("جرّب زيادة عدد أو قطر البراغي، زيادة سمك الصفيحة، زيادة طول/حلق اللحام، "
                 "أو تقليل طول الانبعاج. يجب أن يوافق مهندس مختص على الحل.")
