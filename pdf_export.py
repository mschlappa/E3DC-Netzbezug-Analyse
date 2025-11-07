from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from io import BytesIO
import tempfile
import os
import subprocess

try:
    chromium_path = subprocess.check_output(['which', 'chromium'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
    if chromium_path:
        os.environ['BROWSER_PATH'] = chromium_path
except Exception:
    pass

def create_pdf_report(analysis_df, total_0_5, total_5_24, total_gesamt, 
                     kosten_0_5, kosten_5_24, kosten_gesamt,
                     preis_0_5, preis_5_24,
                     start_date, end_date,
                     fig_bar, fig_pie, fig_kosten):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          rightMargin=2*cm, leftMargin=2*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    title = Paragraph("E3DC Netzbezug Analyse", title_style)
    elements.append(title)
    
    date_text = f"Auswertungszeitraum: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
    date_para = Paragraph(date_text, styles['Normal'])
    elements.append(date_para)
    
    generated_text = f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    generated_para = Paragraph(generated_text, styles['Normal'])
    elements.append(generated_para)
    elements.append(Spacer(1, 0.5*cm))
    
    heading = Paragraph("Zusammenfassung Netzbezug", heading_style)
    elements.append(heading)
    
    summary_data = [
        ['Zeitintervall', 'Netzbezug (kWh)', 'Preis (Cent/kWh)', 'Kosten (€)'],
        ['0-5 Uhr', f'{total_0_5:.2f}', f'{preis_0_5:.2f}', f'{kosten_0_5:.2f}'],
        ['5-24 Uhr', f'{total_5_24:.2f}', f'{preis_5_24:.2f}', f'{kosten_5_24:.2f}'],
        ['Gesamt', f'{total_gesamt:.2f}', '-', f'{kosten_gesamt:.2f}']
    ]
    
    summary_table = Table(summary_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e0e0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey])
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 1*cm))
    
    heading = Paragraph("Detaillierte Tagesauswertung", heading_style)
    elements.append(heading)
    
    analysis_reset = analysis_df.reset_index()
    
    index_name = analysis_df.index.name if analysis_df.index.name else 'index'
    
    table_data = [['Datum'] + list(analysis_df.columns)]
    
    for _, row in analysis_reset.iterrows():
        datum_val = row[index_name]
        datum_str = datum_val.strftime('%d.%m.%Y') if hasattr(datum_val, 'strftime') else str(datum_val)
        row_data = [datum_str]
        for col in analysis_df.columns:
            row_data.append(f"{row[col]:.2f}")
        table_data.append(row_data)
    
    detail_table = Table(table_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    elements.append(detail_table)
    
    elements.append(PageBreak())
    
    heading = Paragraph("Visualisierungen", heading_style)
    elements.append(heading)
    elements.append(Spacer(1, 0.5*cm))
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_bar:
        fig_bar.write_image(tmp_bar.name, width=800, height=500, scale=2)
        img_bar = Image(tmp_bar.name, width=16*cm, height=10*cm)
        elements.append(img_bar)
        elements.append(Spacer(1, 0.5*cm))
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_pie:
        fig_pie.write_image(tmp_pie.name, width=800, height=500, scale=2)
        img_pie = Image(tmp_pie.name, width=16*cm, height=10*cm)
        elements.append(img_pie)
        elements.append(Spacer(1, 0.5*cm))
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_kosten:
        fig_kosten.write_image(tmp_kosten.name, width=800, height=500, scale=2)
        img_kosten = Image(tmp_kosten.name, width=16*cm, height=10*cm)
        elements.append(img_kosten)
    
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
