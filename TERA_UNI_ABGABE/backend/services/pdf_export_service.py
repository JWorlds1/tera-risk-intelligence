import io
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, black
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

@dataclass
class ReportConfig:
    title: str = "TERA Risk Intelligence Report"
    subtitle: str = "Topographical Earth Risk Assessment"
    color_primary: str = "#00ffff"
    color_accent: str = "#ff4444"

class PDFExportService:
    def __init__(self, config=None):
        self.config = config or ReportConfig()
        self.styles = None
        if REPORTLAB_AVAILABLE:
            self._setup_styles()
    
    def _setup_styles(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name="ReportTitle", fontSize=24, leading=28, alignment=TA_CENTER, textColor=HexColor(self.config.color_primary), spaceAfter=12))
        self.styles.add(ParagraphStyle(name="ReportSubtitle", fontSize=14, leading=18, alignment=TA_CENTER, textColor=HexColor("#888888"), spaceAfter=24))
        self.styles.add(ParagraphStyle(name="SectionHeader", fontSize=16, leading=20, textColor=HexColor(self.config.color_primary), spaceBefore=20, spaceAfter=10))
    
    def _get_risk_color(self, score):
        if score >= 0.7: return "#ff4444"
        elif score >= 0.5: return "#ff8c00"
        elif score >= 0.3: return "#eab308"
        return "#22c55e"
    
    async def generate_report(self, city, country, analysis_data, year=2026, scenario="SSP2-4.5"):
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab not installed")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        story = []
        
        story.append(Paragraph(self.config.title, self.styles["ReportTitle"]))
        story.append(Paragraph(self.config.subtitle, self.styles["ReportSubtitle"]))
        story.append(HRFlowable(width="100%", thickness=2, color=HexColor(self.config.color_primary)))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("STANDORT", self.styles["SectionHeader"]))
        location_data = [["Stadt:", city], ["Land:", country], ["Jahr:", str(year)], ["Szenario:", scenario]]
        location_table = Table(location_data, colWidths=[4*cm, 10*cm])
        story.append(location_table)
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("RISIKO-UEBERSICHT", self.styles["SectionHeader"]))
        total_risk = analysis_data.get("total_risk", {}).get("mean", 0.25)
        risk_style = ParagraphStyle("RiskScore", fontSize=48, leading=52, alignment=TA_CENTER, textColor=HexColor(self._get_risk_color(total_risk)))
        story.append(Paragraph(f"{int(total_risk * 100)}%", risk_style))
        story.append(Paragraph("Gesamtrisiko-Index", self.styles["ReportSubtitle"]))
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        logger.info(f"PDF generated: {len(pdf_bytes)} bytes")
        return pdf_bytes
    
    def _interpret_risk(self, score):
        if score >= 0.7: return "Kritisch"
        elif score >= 0.5: return "Hoch"
        elif score >= 0.3: return "Moderat"
        return "Niedrig"

pdf_service = PDFExportService()