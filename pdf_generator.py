import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#333333"))
        
        # Draw header band (Tricolor Accent)
        self.setStrokeColor(colors.HexColor("#FF9933")) # Saffron
        self.setLineWidth(3)
        self.line(54, 750, 558, 750)
        self.setStrokeColor(colors.HexColor("#000080")) # Navy Blue
        self.line(54, 747, 558, 747)
        self.setStrokeColor(colors.HexColor("#138808")) # Green
        self.line(54, 744, 558, 744)

        # Header Text
        self.drawString(54, 758, "PRAGATI Digital Public Infrastructure Audit Engine")
        
        # Footer Line
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 50, 558, 50)
        
        # Footer Text
        self.drawString(54, 38, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Confidential Auditor Copy")
        self.drawRightString(558, 38, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def generate_audit_pdf(lgd_code: str, ward_name: str, grievances: list, budget: dict, output_dir: str) -> str:
    """
    Generates a beautifully structured PDF summary brief for state auditors.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"PRAGATI_Audit_Brief_{lgd_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=80,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#000080"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#FF9933"),
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#138808"),
        spaceBefore=10,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#222222")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    table_body_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#333333")
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("GOVERNMENT OF INDIA", subtitle_style))
    story.append(Paragraph("PRAGATI Infrastructure Audit Brief", title_style))
    story.append(Paragraph(f"Jurisdiction/Panchayat: {ward_name} (LGD Code: {lgd_code})", body_style))
    story.append(Spacer(1, 15))

    # Calculate metrics
    total_tickets = len(grievances)
    completed_tickets = sum(1 for g in grievances if g.get("status") == "Completed")
    disbursed_tickets = sum(1 for g in grievances if g.get("status") == "Disbursed")
    logged_tickets = sum(1 for g in grievances if g.get("status") == "Logged")
    
    closure_rate = (completed_tickets / total_tickets * 100) if total_tickets > 0 else 0.0
    
    total_collected = budget.get("total_collected", 0.0)
    total_disbursed = budget.get("total_disbursed", 0.0)
    remaining_balance = total_collected - total_disbursed

    # Financial & Grievance Metric KPI Table
    metric_data = [
        [
            Paragraph("<b>Total Collected Grant:</b>", body_style), Paragraph(f"INR {total_collected:,.2f}", body_style),
            Paragraph("<b>Total Tickets Logged:</b>", body_style), Paragraph(str(total_tickets), body_style)
        ],
        [
            Paragraph("<b>Total Disbursed:</b>", body_style), Paragraph(f"INR {total_disbursed:,.2f}", body_style),
            Paragraph("<b>Completed & Verified:</b>", body_style), Paragraph(f"{completed_tickets} ({closure_rate:.1f}%)", body_style)
        ],
        [
            Paragraph("<b>Remaining Balance:</b>", body_style), Paragraph(f"INR {remaining_balance:,.2f}", body_style),
            Paragraph("<b>Under Execution:</b>", body_style), Paragraph(str(disbursed_tickets + logged_tickets), body_style)
        ]
    ]

    metric_table = Table(metric_data, colWidths=[130, 120, 130, 120])
    metric_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F9F9F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(Paragraph("Executive Summary & KPI Dashboard", section_style))
    story.append(metric_table)
    story.append(Spacer(1, 20))

    # Grievance Logs Section
    story.append(Paragraph("Grievance Status Ledger", section_style))
    
    # Table headers
    headers = [
        Paragraph("Ticket ID", table_header_style),
        Paragraph("Category", table_header_style),
        Paragraph("Description", table_header_style),
        Paragraph("Status", table_header_style),
        Paragraph("Upvotes", table_header_style)
    ]
    
    table_rows = [headers]
    
    for g in grievances:
        # Wrap status in dynamic color formatting
        status = g.get("status", "Logged")
        status_color = "#FF9933"  # Saffron / Yellow-ish
        if status == "Completed":
            status_color = "#138808"  # Green
        elif status == "Logged":
            status_color = "#D32F2F"  # Red
            
        status_para = Paragraph(f"<font color='{status_color}'><b>{status}</b></font>", table_body_style)
        
        table_rows.append([
            Paragraph(f"TKT-{g.get('ticket_id')}", table_body_style),
            Paragraph(g.get("category", ""), table_body_style),
            Paragraph(g.get("description", "")[:40] + ("..." if len(g.get("description", "")) > 40 else ""), table_body_style),
            status_para,
            Paragraph(str(g.get("upvote_count", 1)), table_body_style)
        ])

    # Fallback if no grievances exist
    if len(grievances) == 0:
        table_rows.append([Paragraph("No grievances reported in this jurisdiction.", table_body_style), "", "", "", ""])

    grievance_table = Table(table_rows, colWidths=[70, 90, 200, 90, 50])
    grievance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#000080")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(grievance_table)
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    return filepath
