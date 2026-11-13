import io
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from models import CollegeSetting, AcademicClass, TimeSlot, TimetableEntry

def generate_pdf_timetable(class_id=None):
    buffer = io.BytesIO()
    # Landscape A4 for wide timetable grid
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15,
        leftMargin=15,
        topMargin=15,
        bottomMargin=15
    )
    
    elements = []
    styles = getSampleStyleSheet()

    setting = CollegeSetting.query.first()
    trust = setting.trust_name if setting else "Mahatma Gandhi Mission's"
    college = setting.college_name if setting else "COLLEGE OF ENGINEERING"
    addr = setting.address if setting else "Near Airport, Off Hingoli Road, Nanded-431605."
    dept = setting.department_name if setting else "DEPARTMENT OF ELECTRONICS AND TELECOMMUNICATION ENGINEERING"
    acad = setting.academic_year if setting else "ACADEMIC YEAR 2026-27 (SEMESTER-I) TIME TABLE"
    wef = setting.wef_date if setting else "17/08/2026"
    sem_start = setting.sem_start_date if setting else "10/08/2026"

    # Title styling
    title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, alignment=1, textColor=colors.HexColor('#0d233a'))
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, alignment=1, textColor=colors.HexColor('#333333'))
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, alignment=1, textColor=colors.HexColor('#800000'))
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=6.5, leading=7.5, alignment=1)

    elements.append(Paragraph(trust, sub_style))
    elements.append(Paragraph(college, title_style))
    elements.append(Paragraph(addr, sub_style))
    elements.append(Paragraph(f"<b>{dept}</b>", title_style))
    elements.append(Paragraph(f"<b>{acad}</b> &nbsp;&nbsp;|&nbsp;&nbsp; Sem Start: {sem_start} &nbsp;&nbsp;|&nbsp;&nbsp; WEF: {wef}", meta_style))
    elements.append(Spacer(1, 8))

    # Build timetable table
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slots = TimeSlot.query.order_by(TimeSlot.slot_index).all()
    classes = [AcademicClass.query.get(class_id)] if class_id else AcademicClass.query.order_by(AcademicClass.id).all()

    # Table Header
    header = ['DAY / TIME', 'CLASS']
    for s in slots:
        if s.is_recess:
            header.append('R\ne\nc\ne\ns\ns')
        else:
            # Short clean slot header
            header.append(s.slot_label.replace(' TO ', '\nTO\n').replace(' Or ', '\nOr\n'))

    table_data = [header]

    for day in days:
        first_row_for_day = True
        for cls in classes:
            row = []
            if first_row_for_day:
                row.append(day[:3].upper()) # MON, TUE...
            else:
                row.append('')
            row.append(cls.name)

            for s in slots:
                if s.is_recess:
                    row.append('R\nE\nC\nE\nS\nS')
                else:
                    # Find entries for day, slot, cls
                    entries = TimetableEntry.query.filter_by(day=day, slot_id=s.id, class_id=cls.id).all()
                    if not entries:
                        row.append('-')
                    else:
                        text_parts = []
                        for e in entries:
                            if e.custom_title:
                                text_parts.append(e.custom_title)
                            elif e.subject:
                                t_code = e.teacher.code if e.teacher else ''
                                r_code = e.room.name if e.room else ''
                                text_parts.append(f"{e.subject.code}\n{t_code} ({r_code})")
                        row.append(Paragraph("<br/>".join(text_parts), cell_style))

            table_data.append(row)
            first_row_for_day = False

    col_widths = [45, 55] + [70 if not s.is_recess else 22 for s in slots]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#4a5568')),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#edf2f7')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (0, -1), 8),
    ]))

    elements.append(t)
    elements.append(Spacer(1, 15))

    # Signatories
    sig_data = [
        [
            Paragraph(f"<b>{setting.tt_incharge if setting else 'Time Table Incharge'}</b><br/>Time Table Incharge", sub_style),
            Paragraph(f"<b>{setting.dept_coordinator if setting else 'Dept. Academic Coordinator'}</b><br/>Dept. Academic Coordinator", sub_style),
            Paragraph(f"<b>{setting.hod_name if setting else 'Prof. and Head'}</b><br/>Prof. and Head", sub_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[260, 260, 260])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
