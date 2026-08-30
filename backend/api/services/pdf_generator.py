import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generate_analysis_pdf(analysis_data: dict, syllabus_title: str = "General Syllabus", section_title: str = "All Topics") -> bytes:
    """
    Generates a publication-quality PDF summary report for RecoMind Notes Analysis,
    including detailed predictions, placement guidance, exam paragraphs, refined notes draft, and full summary.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    PRIMARY_BLUE = colors.HexColor("#4361ee")
    TEXT_DARK = colors.HexColor("#1e293b")
    GREEN_COLOR = colors.HexColor("#047857")
    AMBER_COLOR = colors.HexColor("#b45309")
    RED_COLOR = colors.HexColor("#b91c1c")
    BG_LIGHT = colors.HexColor("#f8fafc")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=PRIMARY_BLUE,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        fontName='Helvetica',
        spaceAfter=10
    )

    h2_style = ParagraphStyle(
        'H2Header',
        parent=styles['Heading2'],
        fontSize=11.5,
        leading=15,
        textColor=PRIMARY_BLUE,
        fontName='Helvetica-Bold',
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        fontName='Helvetica'
    )

    code_style = ParagraphStyle(
        'CodeTextCustom',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#f8fafc"),
        fontName='Courier'
    )

    story = []

    # Title & Header
    story.append(Paragraph("RECOMMIND - AI NOTES & SYLLABUS ANALYSIS REPORT", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y - %I:%M %p')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_BLUE, spaceBefore=2, spaceAfter=10))

    # Metadata & Score Table
    coverage_pct = analysis_data.get('coverage_percentage', 0.0)
    domain_name = analysis_data.get('domain', 'General Education')

    meta_data = [
        [
            Paragraph(f"<b>Syllabus:</b> {syllabus_title}", body_style),
            Paragraph(f"<b>Overall Coverage:</b> <font color='{PRIMARY_BLUE.hexval()}'><b>{coverage_pct}%</b></font>", body_style)
        ],
        [
            Paragraph(f"<b>Section:</b> {section_title}", body_style),
            Paragraph(f"<b>Predicted Domain:</b> {domain_name}", body_style)
        ]
    ]

    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Topic Breakdown Section
    story.append(Paragraph("SYLLABUS TOPIC COVERAGE BREAKDOWN", h2_style))
    
    topics = analysis_data.get('topics', {})
    covered = topics.get('covered', [])
    partially_covered = topics.get('partially_covered', [])
    missing = topics.get('missing', [])

    topic_rows = []
    if covered:
        for t in covered:
            topic_rows.append([Paragraph(f"<font color='{GREEN_COLOR.hexval()}'><b>[COVERED]</b></font> {t}", body_style)])
    if partially_covered:
        for t in partially_covered:
            topic_rows.append([Paragraph(f"<font color='{AMBER_COLOR.hexval()}'><b>[NEEDS IMPROVEMENT]</b></font> {t}", body_style)])
    if missing:
        for t in missing:
            topic_rows.append([Paragraph(f"<font color='{RED_COLOR.hexval()}'><b>[MISSING]</b></font> {t}", body_style)])

    if not topic_rows:
        topic_rows.append([Paragraph("No topic breakdown available.", body_style)])

    topic_table = Table(topic_rows, colWidths=[540])
    topic_table.setStyle(TableStyle([
        ('PADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
    ]))
    story.append(topic_table)
    story.append(Spacer(1, 10))

    # Detailed Recommendations & Placement Guidance
    recs = analysis_data.get('recommendations', [])
    if recs:
        story.append(Paragraph("DETAILED PREDICTIONS & REFINED EXAM PARAGRAPHS", h2_style))
        for r in recs:
            prio = r.get('priority', 'MEDIUM')
            t_name = r.get('topic', '')
            action = r.get('recommendation', '')
            placement = r.get('placement_guidance', '')
            paragraph_text = r.get('suggested_paragraph', '')

            p_color = RED_COLOR if prio == 'HIGH' else AMBER_COLOR

            rec_content = [
                Paragraph(f"<font color='{p_color.hexval()}'><b>[{prio} PRIORITY] {t_name}</b></font>", body_style),
                Paragraph(f"<b>Placement Guidance:</b> {placement}", body_style) if placement else Paragraph("", body_style),
                Paragraph(f"<b>Suggested Exam Paragraph:</b> {paragraph_text}", body_style) if paragraph_text else Paragraph(action, body_style)
            ]

            r_table = Table([[c] for c in rec_content if c.text], colWidths=[540])
            r_table.setStyle(TableStyle([
                ('PADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fffdf5")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#fde68a")),
            ]))
            story.append(r_table)
            story.append(Spacer(1, 6))

        story.append(Spacer(1, 8))

    # Refined Notes Draft
    refined_draft = analysis_data.get('refined_notes_draft', '')
    if refined_draft:
        story.append(Paragraph("REFINED & COMPLETED NOTES DRAFT", h2_style))
        draft_lines = refined_draft.split('\n')
        draft_p_list = [Paragraph(line.replace('<', '&lt;').replace('>', '&gt;'), body_style) for line in draft_lines if line.strip()]
        
        draft_table = Table([[p] for p in draft_p_list[:25]], colWidths=[540]) # limit length for PDF spacing
        draft_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(draft_table)
        story.append(Spacer(1, 10))

    # Full Comprehensive Notes Summary
    full_summary = analysis_data.get('full_summary', {})
    if full_summary and full_summary.get('overview'):
        story.append(Paragraph("COMPREHENSIVE FULL NOTES SUMMARY", h2_style))
        story.append(Paragraph(f"<b>Executive Overview:</b> {full_summary.get('overview')}", body_style))
        story.append(Spacer(1, 6))

    # Footer Notice
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=10, spaceAfter=8))
    story.append(Paragraph("RecoMind Universal Educational Notes Analysis System - Generated automatically.", subtitle_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
