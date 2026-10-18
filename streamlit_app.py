import io
import math
from xml.sax.saxutils import escape

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generer_sammenfasning_pdf(
    station,
    bryder_id,
    u_nom,
    tolerance_vinkel,
    tolerance_volt,
    side_a_data,
    side_b_data,
    maalingstype,
    måle_sted_a,
    måle_sted_b,
    målepunkt_billeder=None,
):
    fase_navne = ["L1 (Blå)", "L2 (Gul)", "L3 (Rød)"]
    spændingspunkter = [
        "L1 A mod L1 B",
        "L1 A mod L2 B",
        "L2 A mod L2 B",
        "L2 A mod L3 B",
        "L3 A mod L3 B",
        "L3 A mod L1 B",
    ]
    data_tabel_rækker = []
    godkendt_samlet = True

    if maalingstype in ("Spændingsværdier", "Vinkel- og spændingsværdier"):
        if maalingstype == "Vinkel- og spændingsværdier":
            vinkel_data_a = side_a_data["vinkler"]
            vinkel_data_b = side_b_data["vinkler"]
            sammenligninger = [
                (
                    fase_navne[i],
                    vinkel_data_a[i][0],
                    vinkel_data_b[i][0],
                    vinkel_data_a[i][1],
                    vinkel_data_b[i][1],
                )
                for i in range(3)
            ]
            vinkler_a = [item[1] for item in vinkel_data_a]
            vinkler_b = [item[1] for item in vinkel_data_b]
        else:
            vinkler_a = [0.0, 120.0, 240.0]
            vinkler_b = [0.0, 120.0, 240.0]
        samme_fase_indeks = {0, 2, 4}
        for i, (label, spændingsforskel) in enumerate(
            zip(
                spændingspunkter,
                side_a_data
                if maalingstype == "Spændingsværdier"
                else side_a_data["spændinger"],
            )
        ):
            samme_fase = i in samme_fase_indeks
            spænding_ok = (
                spændingsforskel <= tolerance_volt
                if samme_fase
                else spændingsforskel > tolerance_volt
            )
            if spænding_ok and samme_fase:
                status = "I SAMMENFASE"
            elif spænding_ok and not samme_fase:
                status = "KORREKT KRYDSFASE"
            else:
                status = "AFVIGELSE"
            if not spænding_ok:
                godkendt_samlet = False
            data_tabel_rækker.append(
                [
                    label,
                    "",
                    "Samme fase" if samme_fase else "Krydsfase",
                    "",
                    f"{round(spændingsforskel, 2)} V",
                    status,
                ]
            )
    else:
        sammenligninger = [
            (
                fase_navne[i],
                side_a_data[i][0],
                side_b_data[i][0],
                side_a_data[i][1],
                side_b_data[i][1],
            )
            for i in range(3)
        ]

        vinkler_a = [item[3] for item in sammenligninger]
        vinkler_b = [item[4] for item in sammenligninger]

    if maalingstype in ("Vinkelværdier", "Vinkel- og spændingsværdier"):
        if maalingstype == "Vinkelværdier":
            sammenligninger = [
                (
                    fase_navne[i],
                    side_a_data[i][0],
                    side_b_data[i][0],
                    side_a_data[i][1],
                    side_b_data[i][1],
                )
                for i in range(3)
            ]
        for label, u_a, u_b, v_a, v_b in sammenligninger:

            vinkel_diff = (v_b - v_a) % 360
            if vinkel_diff > 180:
                vinkel_diff -= 360
            volt_diff = abs(u_a - u_b)
            vinkel_ok = abs(vinkel_diff) <= tolerance_vinkel
            volt_ok = True

            if vinkel_ok and volt_ok:
                status = "I SAMMENFASE"
            else:
                status = "AFVIGELSE"
                godkendt_samlet = False

            data_tabel_rækker.append(
                [
                    label,
                    f"{v_a}°",
                    f"{v_b}°",
                    f"{round(vinkel_diff, 1)}°",
                    "Ikke målt",
                    status,
                ]
            )

    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_direction(-1)
    ax.set_theta_zero_location("N")
    fase_farver = ["#2B6CB0", "#ECC94B", "#E53E3E"]

    for i in range(3):
        rad_a = math.radians(vinkler_a[i])
        rad_b = math.radians(vinkler_b[i])
        ax.annotate(
            "",
            xy=(rad_a, 0.95),
            xytext=(0, 0),
            arrowprops={
                "arrowstyle": "->",
                "linestyle": "--",
                "color": fase_farver[i],
                "lw": 1.5,
            },
        )
        ax.text(
            rad_a,
            1.15,
            f"L{i + 1} A",
            color=fase_farver[i],
            fontweight="bold",
            ha="center",
            va="center",
        )
        ax.annotate(
            "",
            xy=(rad_b, 0.85),
            xytext=(0, 0),
            arrowprops={
                "arrowstyle": "->",
                "linestyle": "-",
                "color": fase_farver[i],
                "lw": 3,
            },
        )
        ax.text(
            rad_b,
            0.72,
            f"L{i + 1} B",
            color=fase_farver[i],
            fontweight="bold",
            ha="center",
            va="center",
            bbox={
                "boxstyle": "square,pad=0.1",
                "fc": "white",
                "ec": fase_farver[i],
                "lw": 1,
                "alpha": 0.7,
            },
        )

    ax.set_ylim(0, 1.2)
    ax.set_yticklabels([])
    ax.set_xticks(np.deg2rad(np.arange(0, 360, 30)))
    ax.set_xticklabels([f"{angle}°" for angle in range(0, 360, 30)])
    ax.grid(True, color="#CBD5E0", linestyle=":")

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png", bbox_inches="tight", dpi=200)
    img_buf.seek(0)

    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "T1",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=15,
    )
    meta_style = ParagraphStyle(
        "M1",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#34495E"),
    )
    cell_style = ParagraphStyle(
        "C1", parent=styles["Normal"], fontSize=10, alignment=1
    )
    cell_hdr = ParagraphStyle(
        "CH",
        parent=styles["Normal"],
        fontSize=10,
        alignment=1,
        textColor=colors.white,
    )
    samlet_status_tekst = (
        "<font color='#27AE60'><b>GODKENDT - SYSTEMERNE ER I SAMMENFASE</b></font>"
        if godkendt_samlet
        else "<font color='#C0392B'><b>AFVIST - IKKE I SAMMENFASE</b></font>"
    )

    story = [
        Paragraph("SAMMENFASNINGS RAPPORT", title_style),
        Paragraph(
            f"<b>Målestation:</b> {escape(str(station))}<br/>"
            f"<b>Afbryder ID / Felt:</b> {escape(str(bryder_id))}<br/>"
            f"<b>Målingstype:</b> {escape(str(maalingstype))}<br/>"
            f"<b>Værdi A målt ved:</b> {escape(str(måle_sted_a))}<br/>"
            f"<b>Værdi B målt ved:</b> {escape(str(måle_sted_b))}<br/>"
            f"<b>Tilladt tolerance:</b> "
            f"{f'±{tolerance_vinkel}°' if maalingstype == 'Vinkelværdier' else f'{tolerance_volt} V' if maalingstype == 'Spændingsværdier' else f'±{tolerance_vinkel}° / {tolerance_volt} V'}<br/>"
            f"<b>Samlet Konklusion:</b> {samlet_status_tekst}",
            meta_style,
        ),
        Spacer(1, 15),
    ]
    if maalingstype == "Vinkelværdier":
        tabel_headers = [
            "Målepunkt",
            måle_sted_a,
            måle_sted_b,
            "Vinkel Diff.",
            "Status",
        ]
        tabel_bredder = [95, 125, 125, 85, 100]
    elif maalingstype == "Spændingsværdier":
        tabel_headers = ["Målepunkt", "Målingstype", "Spændings Diff.", "Status"]
        tabel_bredder = [145, 100, 105, 100]
    else:
        tabel_headers = [
            "Målepunkt",
            måle_sted_a,
            måle_sted_b,
            "Vinkel Diff.",
            "Spændings Diff.",
            "Status",
        ]
        tabel_bredder = [80, 105, 105, 75, 85, 80]

    tabel_data = [
        [Paragraph(escape(str(header)), cell_hdr) for header in tabel_headers]
    ]
    for række in data_tabel_rækker:
        status_farve = (
            "#27AE60"
            if række[5] in ("I SAMMENFASE", "KORREKT KRYDSFASE")
            else "#C0392B"
        )
        if maalingstype == "Vinkelværdier":
            række_data = [række[0], række[1], række[2], række[3], række[5]]
        elif maalingstype == "Spændingsværdier":
            række_data = [række[0], række[2], række[4], række[5]]
        else:
            række_data = række
        tabel_data.append(
            [
                Paragraph(f"<b>{række_data[0]}</b>", cell_style),
                *[Paragraph(værdi, cell_style) for værdi in række_data[1:-1]],
                Paragraph(
                    f"<font color='{status_farve}'><b>{række_data[-1]}</b></font>",
                    cell_style,
                ),
            ]
        )

    table = Table(tabel_data, colWidths=tabel_bredder)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ECF0F1")),
                ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#ECF0F1")),
            ]
        )
    )
    story.extend([table, Spacer(1, 20)])
    if målepunkt_billeder:
        story.append(Paragraph("Billeder til måleresultater", title_style))
        for målepunkt, billeder in målepunkt_billeder.items():
            if not billeder:
                continue
            story.append(Paragraph(f"<b>{escape(målepunkt)}</b>", meta_style))
            for billede in billeder:
                image = Image(
                    io.BytesIO(billede.getvalue()),
                    width=250,
                    height=180,
                    kind="proportional",
                )
                story.extend([image, Spacer(1, 8)])
            story.append(Spacer(1, 8))
    if maalingstype in ("Vinkelværdier", "Vinkel- og spændingsværdier"):
        story.extend(
            [
                Paragraph(
                    "<b>Grafisk Sammenligning</b>",
                    ParagraphStyle(
                        "Sub",
                        parent=styles["Heading2"],
                        fontSize=13,
                        textColor=colors.HexColor("#2980B9"),
                    ),
                ),
                Spacer(1, 5),
                KeepTogether([Image(img_buf, width=310, height=310)]),
                Spacer(1, 25),
            ]
        )
    story.append(
        Table(
            [
                [
                    Paragraph(
                        "<b>Test udført af:</b> _______________________", meta_style
                    ),
                    Paragraph("<b>Dato:</b> ____/____ - 20__", meta_style),
                ],
                [
                    Paragraph(
                        "<b>Godkendt af:</b> _______________________", meta_style
                    ),
                    Paragraph("<b>Signatur:</b> _______________________", meta_style),
                ],
            ],
            colWidths=[270, 260],
        )
    )
    doc.build(story)
    plt.close(fig)
    pdf_buf.seek(0)
    return pdf_buf.getvalue(), fig


st.set_page_config(page_title="Sammenfasnings Rapport", layout="wide")
st.title("🔗 Sammenfasnings Kontrol & Rapport")
st.subheader("Måling over åben afbryder inden indkobling (Lagging / Mod uret)")

col1, col2 = st.columns(2)
with col1:
    st.header("1. Stamdata & Tolerancer")
    station_navn = st.text_input("Stationsnavn")
    bryder_navn = st.text_input("Afbryder ID / Feltnummer")
    sted_a, sted_b = st.columns(2)
    with sted_a:
        måle_sted_a = st.text_input("Hvor er Værdi A målt?")
    with sted_b:
        måle_sted_b = st.text_input("Hvor er Værdi B målt?")
    u_nom = st.number_input("Nominel spænding (V)", value=None, step=1.0)
    c_tol1, c_tol2 = st.columns(2)
    with c_tol1:
        tol_vinkel = st.number_input(
            "Tilladt vinkelafvigelse (±°)", value=None, step=0.5
        )
    with c_tol2:
        tol_volt = st.number_input(
            "Tilladt spændingsafvigelse (V)", value=None, step=0.5
        )

    st.header("2. Måleresultater")
    maalingstype = st.radio(
        "Vælg hvilke værdier der skal indtastes",
        [
            "Vinkelværdier",
            "Spændingsværdier",
            "Vinkel- og spændingsværdier",
        ],
        horizontal=True,
    )
    if maalingstype in ("Spændingsværdier", "Vinkel- og spændingsværdier"):
        st.markdown("### **Spændingsmålinger mellem de to sider**")
        ca1, ca2, ca3 = st.columns(3)
        with ca1:
            u_a1 = st.number_input("L1 A mod L1 B (V)", value=None, key="ua1")
            u_a2 = st.number_input("L1 A mod L2 B (V)", value=None, key="ua2")
        with ca2:
            u_a3 = st.number_input("L2 A mod L2 B (V)", value=None, key="ua3")
            u_a4 = st.number_input("L2 A mod L3 B (V)", value=None, key="ua4")
        with ca3:
            u_a5 = st.number_input("L3 A mod L3 B (V)", value=None, key="ua5")
            u_a6 = st.number_input("L3 A mod L1 B (V)", value=None, key="ua6")
        spændingsdata = [u_a1, u_a2, u_a3, u_a4, u_a5, u_a6]
        if maalingstype == "Spændingsværdier":
            v_a1, v_a2, v_a3 = 0.0, 120.0, 240.0
        else:
            st.markdown("### **Vinkelmålinger**")
            angle_a = st.columns(3)
            with angle_a[0]:
                v_a1 = st.number_input("L1 Vinkel (°)", value=None, key="va1_begge")
            with angle_a[1]:
                v_a2 = st.number_input("L2 Vinkel (°)", value=None, key="va2_begge")
            with angle_a[2]:
                v_a3 = st.number_input("L3 Vinkel (°)", value=None, key="va3_begge")
    else:
        st.markdown("### **Side A (F.eks. Skinne / Reference)**")
        ca1_v, ca2_v, ca3_v = st.columns(3)
        with ca1_v:
            v_a1 = st.number_input("L1 Vinkel (°)", value=None, key="va1")
        with ca2_v:
            v_a2 = st.number_input("L2 Vinkel (°)", value=None, key="va2")
        with ca3_v:
            v_a3 = st.number_input("L3 Vinkel (°)", value=None, key="va3")
        u_a1, u_a2, u_a3 = 0.0, 0.0, 0.0

    if maalingstype in ("Spændingsværdier", "Vinkel- og spændingsværdier"):
        st.caption("Målingerne udføres mellem de angivne faser på de to sider.")
        side_b_data = []
        if maalingstype == "Spændingsværdier":
            v_b1, v_b2, v_b3 = 0.0, 120.0, 240.0
        else:
            angle_b = st.columns(3)
            with angle_b[0]:
                v_b1 = st.number_input("L1 Vinkel (°)", value=None, key="vb1_begge")
            with angle_b[1]:
                v_b2 = st.number_input("L2 Vinkel (°)", value=None, key="vb2_begge")
            with angle_b[2]:
                v_b3 = st.number_input("L3 Vinkel (°)", value=None, key="vb3_begge")
    else:
        st.markdown("### **Side B (F.eks. Transformer / Ny linje)**")
        cb1_v, cb2_v, cb3_v = st.columns(3)
        with cb1_v:
            v_b1 = st.number_input("L1 Vinkel (°)", value=None, key="vb1")
        with cb2_v:
            v_b2 = st.number_input("L2 Vinkel (°)", value=None, key="vb2")
        with cb3_v:
            v_b3 = st.number_input("L3 Vinkel (°)", value=None, key="vb3")
        side_b_data = [(0.0, v_b1), (0.0, v_b2), (0.0, v_b3)]

    if maalingstype == "Vinkelværdier":
        side_a_data = [(0.0, v_a1), (0.0, v_a2), (0.0, v_a3)]
        side_b_data = [(0.0, v_b1), (0.0, v_b2), (0.0, v_b3)]
    elif maalingstype == "Spændingsværdier":
        side_a_data = spændingsdata
    else:
        side_a_data = {
            "vinkler": [(0.0, v_a1), (0.0, v_a2), (0.0, v_a3)],
            "spændinger": spændingsdata,
        }
        side_b_data = {
            "vinkler": [(0.0, v_b1), (0.0, v_b2), (0.0, v_b3)],
            "spændinger": [],
        }

    st.markdown("### Billeder til måleresultater (valgfrit)")
    if maalingstype == "Vinkelværdier":
        målepunkter = [
            f"L{fase} {side} side"
            for fase in range(1, 4)
            for side in ("A", "B")
        ]
    elif maalingstype == "Spændingsværdier":
        målepunkter = [
            "L1 A mod L1 B",
            "L1 A mod L2 B",
            "L2 A mod L2 B",
            "L2 A mod L3 B",
            "L3 A mod L3 B",
            "L3 A mod L1 B",
        ]
    else:
        målepunkter = [
            "L1 A mod L1 B",
            "L1 A mod L2 B",
            "L2 A mod L2 B",
            "L2 A mod L3 B",
            "L3 A mod L3 B",
            "L3 A mod L1 B",
            *[
                f"L{fase} {side} side"
                for fase in range(1, 4)
                for side in ("A", "B")
            ],
        ]
    målepunkt_billeder = {}
    for indeks, målepunkt in enumerate(målepunkter):
        billeder = st.file_uploader(
            f"Billeder: {målepunkt}",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key=f"målepunkt_billeder_{maalingstype}_{indeks}",
        )
        if billeder:
            målepunkt_billeder[målepunkt] = billeder

if maalingstype == "Vinkelværdier":
    nødvendige_værdier = [
        u_nom,
        tol_vinkel,
        tol_volt,
        v_a1,
        v_a2,
        v_a3,
        v_b1,
        v_b2,
        v_b3,
    ]
elif maalingstype == "Spændingsværdier":
    nødvendige_værdier = [u_nom, tol_vinkel, tol_volt, *spændingsdata]
else:
    nødvendige_værdier = [
        u_nom,
        tol_vinkel,
        tol_volt,
        *spændingsdata,
        v_a1,
        v_a2,
        v_a3,
        v_b1,
        v_b2,
        v_b3,
    ]

alle_felter_udfyldt = bool(
    station_navn.strip()
    and bryder_navn.strip()
    and måle_sted_a.strip()
    and måle_sted_b.strip()
) and all(
    værdi is not None for værdi in nødvendige_værdier
)

if alle_felter_udfyldt:
    pdf_data, diagram_fig = generer_sammenfasning_pdf(
        station_navn,
        bryder_navn,
        u_nom,
        tol_vinkel,
        tol_volt,
        side_a_data,
        side_b_data,
        maalingstype,
        måle_sted_a,
        måle_sted_b,
        målepunkt_billeder,
    )
else:
    pdf_data, diagram_fig = None, None

with col2:
    st.header("3. Live Sammenligning")
    if alle_felter_udfyldt:
        st.pyplot(diagram_fig)
        st.caption(
            "Diagram: CW-visning | Målinger: Lagging / mod uret | "
            "Stiplet = A, fuldt optrukket = B"
        )
        st.header("4. Download Dokumentation")
        st.download_button(
            label="📥 DOWNLOAD SAMMENFASNINGSRAPPORT (PDF)",
            data=bytes(pdf_data),
            file_name=(
                f"Sammenfasning_{station_navn.replace(' ', '_')}_"
                f"{bryder_navn.replace(' ', '_')}.pdf"
            ),
            mime="application/pdf",
            on_click="ignore",
        )
    else:
        st.info("Udfyld alle felter for at generere diagram og PDF-rapport.")
