"""
pdf_report.py
-------------
ReportLab se professional PDF report generate karo.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing, Circle, String
from reportlab.graphics import renderPDF
import io
from datetime import datetime


# ── COLORS ───────────────────────────────────────────────────
COLOR_BG        = colors.HexColor('#080B14')
COLOR_ACCENT    = colors.HexColor('#AAFF45')
COLOR_SAFE      = colors.HexColor('#00E676')
COLOR_MODERATE  = colors.HexColor('#FFB800')
COLOR_HARMFUL   = colors.HexColor('#FF3D5A')
COLOR_UNKNOWN   = colors.HexColor('#8B95A8')
COLOR_WHITE     = colors.white
COLOR_DARK      = colors.HexColor('#1C2030')
COLOR_TEXT      = colors.HexColor('#E8ECF4')
COLOR_DIM       = colors.HexColor('#8B95A8')


def get_score_color(score: int):
    if score >= 80: return COLOR_SAFE
    if score >= 60: return colors.HexColor('#00E5FF')
    if score >= 40: return COLOR_MODERATE
    return COLOR_HARMFUL


def generate_pdf_report(
    product_name: str,
    ingredients_list: list,
    classified: list,
    counts: dict,
    health_score: dict,
    personalisation: dict,
    user_name: str = "",
) -> bytes:
    """
    Full PDF report generate karo — bytes return karta hai.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── CUSTOM STYLES ─────────────────────────────────────────
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=28,
        textColor=COLOR_WHITE,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=COLOR_DIM,
        fontName='Helvetica',
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontSize=13,
        textColor=COLOR_ACCENT,
        fontName='Helvetica-Bold',
        spaceBefore=16,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        'Normal2',
        parent=styles['Normal'],
        fontSize=10,
        textColor=COLOR_TEXT,
        fontName='Helvetica',
        spaceAfter=4,
    )

    warning_style = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXT,
        fontName='Helvetica',
        spaceAfter=3,
        leftIndent=8,
    )

    # ── HEADER ────────────────────────────────────────────────
    story.append(Paragraph("⬡ LabelLens", title_style))
    story.append(Paragraph("AI Ingredient Transparency Report", subtitle_style))
    story.append(Spacer(1, 0.2*cm))

    # Date + User
    date_str = datetime.now().strftime("%d %B %Y, %I:%M %p")
    meta_text = f"Generated on {date_str}"
    if user_name:
        meta_text = f"Report for {user_name}  •  {date_str}"
    story.append(Paragraph(meta_text, subtitle_style))
    story.append(Spacer(1, 0.3*cm))

    # Divider
    story.append(HRFlowable(
        width="100%", thickness=2,
        color=COLOR_ACCENT, spaceAfter=0.4*cm
    ))

    # ── PRODUCT INFO ──────────────────────────────────────────
    story.append(Paragraph("📦 Product Information", section_heading))

    product_data = [
        ['Product Name', product_name or 'Unknown Product'],
        ['Scan Date', date_str],
        ['Total Ingredients', str(len(ingredients_list))],
    ]

    product_table = Table(product_data, colWidths=[5*cm, 12*cm])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), COLOR_DARK),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#13161E')),
        ('TEXTCOLOR', (0, 0), (0, -1), COLOR_ACCENT),
        ('TEXTCOLOR', (1, 0), (1, -1), COLOR_TEXT),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1),
         [COLOR_DARK, colors.HexColor('#13161E')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#2A2F42')),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    story.append(product_table)

    # ── HEALTH SCORE ──────────────────────────────────────────
    story.append(Paragraph("🏆 Health Score", section_heading))

    score = health_score.get('normalised', 0)
    grade = health_score.get('grade', 'N/A')
    verdict = health_score.get('verdict', '')
    score_color = get_score_color(score)

    score_data = [
        [
            Paragraph(
                f'<font size="36" color="{score_color.hexval()}">'
                f'<b>{score}</b></font><br/>'
                f'<font size="12" color="#8B95A8">out of 100</font>',
                ParagraphStyle('sc', alignment=TA_CENTER,
                               textColor=COLOR_TEXT, fontSize=10)
            ),
            Paragraph(
                f'<font size="28" color="{score_color.hexval()}">'
                f'<b>Grade {grade}</b></font><br/><br/>'
                f'<font size="11" color="#E8ECF4">{verdict}</font>',
                ParagraphStyle('gr', alignment=TA_LEFT,
                               textColor=COLOR_TEXT, fontSize=10,
                               leftIndent=12)
            ),
        ]
    ]

    score_table = Table(score_data, colWidths=[6*cm, 11*cm])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_DARK),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#2A2F42')),
        ('PADDING', (0, 0), (-1, -1), 16),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.3*cm))

    # Count chips
    count_data = [[
        Paragraph(
            f'<font color="#00E676"><b>{counts.get("safe", 0)}</b></font><br/>'
            f'<font size="8" color="#8B95A8">SAFE</font>',
            ParagraphStyle('ct', alignment=TA_CENTER, fontSize=18)
        ),
        Paragraph(
            f'<font color="#FFB800"><b>{counts.get("moderate", 0)}</b></font><br/>'
            f'<font size="8" color="#8B95A8">MODERATE</font>',
            ParagraphStyle('ct2', alignment=TA_CENTER, fontSize=18)
        ),
        Paragraph(
            f'<font color="#FF3D5A"><b>{counts.get("harmful", 0)}</b></font><br/>'
            f'<font size="8" color="#8B95A8">HARMFUL</font>',
            ParagraphStyle('ct3', alignment=TA_CENTER, fontSize=18)
        ),
        Paragraph(
            f'<font color="#8B95A8"><b>{counts.get("unknown", 0)}</b></font><br/>'
            f'<font size="8" color="#8B95A8">UNKNOWN</font>',
            ParagraphStyle('ct4', alignment=TA_CENTER, fontSize=18)
        ),
    ]]

    count_table = Table(count_data, colWidths=[4.25*cm]*4)
    count_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#003322')),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#332200')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#330011')),
        ('BACKGROUND', (3, 0), (3, -1), COLOR_DARK),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#2A2F42')),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(count_table)

    # ── INGREDIENT BREAKDOWN ──────────────────────────────────
    story.append(Paragraph("🧬 Ingredient Breakdown", section_heading))

    if classified:
        ing_data = [['Ingredient', 'Category']]
        for item in classified:
            cat = item.get('category', 'unknown')
            cat_color = {
                'safe': '#00E676',
                'moderate': '#FFB800',
                'harmful': '#FF3D5A',
                'unknown': '#8B95A8',
            }.get(cat, '#8B95A8')

            ing_data.append([
                Paragraph(
                    f'<font color="#E8ECF4">{item["name"].title()}</font>',
                    normal_style
                ),
                Paragraph(
                    f'<font color="{cat_color}"><b>{cat.upper()}</b></font>',
                    ParagraphStyle('cat', fontSize=9, fontName='Helvetica-Bold')
                ),
            ])

        ing_table = Table(ing_data, colWidths=[13*cm, 4*cm])
        ing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_ACCENT),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_BG),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [COLOR_DARK, colors.HexColor('#13161E')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#2A2F42')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(ing_table)

    # ── PERSONALIZED WARNINGS ─────────────────────────────────
    all_warnings = (
        personalisation.get('allergy_warnings', []) +
        personalisation.get('diabetic_warnings', []) +
        personalisation.get('harmful_warnings', [])
    )

    if all_warnings:
        story.append(Paragraph("⚠️ Personalised Warnings", section_heading))

        for warning in all_warnings:
            warn_color = COLOR_HARMFUL
            if '⚠️' in warning:
                warn_color = COLOR_MODERATE
            elif '🚨' in warning:
                warn_color = COLOR_HARMFUL

            warn_data = [[
                Paragraph(
                    f'<font color="{warn_color.hexval()}">{warning}</font>',
                    warning_style
                )
            ]]
            warn_table = Table(warn_data, colWidths=[17*cm])
            warn_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), COLOR_DARK),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEBEFOREWIDTH', (0, 0), (0, -1), 3),
                ('LINEBEFORE', (0, 0), (0, -1), 3, warn_color),
                ('GRID', (0, 0), (-1, -1), 0.3,
                 colors.HexColor('#2A2F42')),
            ]))
            story.append(warn_table)
            story.append(Spacer(1, 0.15*cm))

    # General advice
    advice = personalisation.get('general_advice', '')
    if advice:
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            f'<font color="#AAFF45"><b>General Advice:</b></font> '
            f'<font color="#E8ECF4">{advice}</font>',
            normal_style
        ))

    # ── FOOTER ────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor('#2A2F42'), spaceAfter=0.3*cm
    ))
    story.append(Paragraph(
        'Generated by LabelLens • AI Ingredient Transparency System • '
        'For informational purposes only',
        ParagraphStyle(
            'footer', fontSize=8, textColor=COLOR_DIM,
            alignment=TA_CENTER, fontName='Helvetica'
        )
    ))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.read()