"""
Research-specific template implementations.

This module provides template classes and supporting data models for generating
various types of research documents including:
- Research reports
- Executive summaries
- Technical analysis reports
- Data visualizations
"""
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from datetime import datetime, date, timedelta
from enum import Enum
import re
from urllib.parse import urlparse
from pydantic import BaseModel, Field, validator, HttpUrl, conint, confloat

from .document_interface import DocumentFormat
from .templates import BaseTemplate, BaseTemplateMetadata, TemplateSection

# Base Enums
class ResearchMethodology(str, Enum):
    """Research methodology types."""
    QUALITATIVE = "qualitative"
    QUANTITATIVE = "quantitative"
    MIXED_METHODS = "mixed_methods"
    CASE_STUDY = "case_study"
    EXPERIMENTAL = "experimental"
    OBSERVATIONAL = "observational"

class SummaryLevel(str, Enum):
    """Executive summary detail levels."""
    TECHNICAL = "technical"
    BUSINESS = "business"
    GENERAL = "general"

class TargetAudience(str, Enum):
    """Target audience categories."""
    EXECUTIVE = "executive"
    MANAGEMENT = "management"
    STAKEHOLDER = "stakeholder"
    TECHNICAL = "technical"

class BusinessImpact(str, Enum):
    """Business impact ratings."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class PriorityLevel(str, Enum):
    """Priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Visualization Enums
class VisualizationType(str, Enum):
    """Types of data visualizations."""
    CHART = "chart"
    GRAPH = "graph"
    PLOT = "plot"
    MAP = "map"
    HEATMAP = "heatmap"
    DASHBOARD = "dashboard"
    INFOGRAPHIC = "infographic"

class DataFormat(str, Enum):
    """Supported data formats."""
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    EXCEL = "excel"
    GEOJSON = "geojson"
    SQL = "sql"
    AVRO = "avro"

class ChartType(str, Enum):
    """Types of charts."""
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    AREA = "area"
    BUBBLE = "bubble"
    RADAR = "radar"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"

class ColorScheme(str, Enum):
    """Color scheme types."""
    SEQUENTIAL = "sequential"
    DIVERGING = "diverging"
    QUALITATIVE = "qualitative"
    MONOCHROME = "monochrome"
    CUSTOM = "custom"

class UpdateFrequency(str, Enum):
    """Data update frequency."""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    STATIC = "static"

# Data Models
class DataSource(BaseModel):
    """Model for data source information."""
    name: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    url: HttpUrl
    access_date: Optional[date] = None
    reliability_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None

class ResearchReportMetadata(BaseTemplateMetadata):
    """Metadata specific to research reports."""
    research_period_start: date
    research_period_end: date
    methodology: ResearchMethodology
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    data_sources: List[DataSource] = Field(default_factory=list)
    
    @validator('research_period_end')
    def validate_research_period(cls, v, values):
        """Ensure research period end is after start."""
        if 'research_period_start' in values and v < values['research_period_start']:
            raise ValueError('research_period_end must be after research_period_start')
        return v

class ExecutiveSummaryMetadata(BaseTemplateMetadata):
    """Metadata specific to executive summaries."""
    summary_level: SummaryLevel
    target_audience: List[TargetAudience]
    business_impact: BusinessImpact
    priority_level: PriorityLevel
    presentation_time: Optional[int] = Field(None, gt=0)
    key_stakeholders: List[str] = Field(default_factory=list)
    
    @validator('target_audience')
    def validate_target_audience(cls, v):
        """Ensure target audience list has unique values."""
        return list(set(v))

class DatasetMetrics(BaseModel):
    """Metrics about the dataset."""
    rows: conint(ge=0)
    columns: conint(ge=0)
    size_bytes: conint(ge=0)
    last_updated: datetime
    update_frequency: UpdateFrequency
    completeness_score: confloat(ge=0.0, le=1.0)

class VisualizationConfig(BaseModel):
    """Configuration for a single visualization."""
    type: VisualizationType
    chart_type: Optional[ChartType] = None
    color_scheme: ColorScheme
    interactive: bool = True
    data_format: DataFormat
    accessibility_features: List[str] = Field(
        default_factory=list,
        description="List of implemented accessibility features"
    )
    
    @validator('chart_type')
    def validate_chart_type(cls, v, values):
        """Ensure chart_type is provided for charts."""
        if values.get('type') == VisualizationType.CHART and not v:
            raise ValueError("chart_type is required for chart visualizations")
        return v

    @validator('accessibility_features')
    def validate_accessibility_features(cls, v):
        """Ensure required accessibility features are included."""
        required_features = {
            "alt_text",
            "aria_labels",
            "color_contrast_ratio",
            "keyboard_navigation"
        }
        if not required_features.issubset(set(v)):
            raise ValueError(f"Missing required accessibility features: {required_features - set(v)}")
        return v

class DataVisualizationMetadata(BaseTemplateMetadata):
    """Metadata specific to data visualization templates."""
    data_sources: List[DataSource]
    visualizations: List[VisualizationConfig]
    dataset_metrics: DatasetMetrics
    supports_interactivity: bool = True
    supports_responsiveness: bool = True
    min_update_interval: timedelta = Field(default=timedelta(hours=24))
    accessibility_standards: List[str] = Field(
        default_factory=lambda: ["WCAG 2.1", "Section 508"]
    )
    
    @validator('data_sources')
    def validate_data_sources(cls, v):
        """Ensure data sources are unique."""
        names = [ds.name for ds in v]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate data source names are not allowed")
        return v

    @validator('visualizations')
    def validate_visualizations(cls, v):
        """Ensure at least one visualization is defined."""
        if not v:
            raise ValueError("At least one visualization must be defined")
        return v

# Template Classes
class ResearchReportTemplate(BaseTemplate):
    """Template for comprehensive research reports."""
    
    def __init__(
        self,
        name: str,
        format: DocumentFormat,
        metadata: Optional[ResearchReportMetadata] = None
    ):
        """Initialize research report template."""
        super().__init__(name, format, metadata)
        if not isinstance(self.metadata, ResearchReportMetadata):
            raise ValueError("metadata must be instance of ResearchReportMetadata")

    def _initialize_sections(self) -> None:
        """Initialize research report sections."""
        self.add_section(TemplateSection(
            name="executive_summary",
            required=True,
            order=0,
            content_type="text",
            metadata={
                "description": "Brief overview of research findings",
                "max_length": 1000
            }
        ))
        
        self.add_section(TemplateSection(
            name="methodology",
            required=True,
            order=1,
            content_type="text"
        ))
        
        self.add_section(TemplateSection(
            name="findings",
            required=True,
            order=2,
            content_type="text"
        ))
        
        self.add_section(TemplateSection(
            name="analysis",
            required=True,
            order=3,
            content_type="text"
        ))
        
        self.add_section(TemplateSection(
            name="recommendations",
            required=True,
            order=4,
            content_type="text"
        ))

    async def format_content(self, content: Dict[str, Any]) -> str:
        """Format content according to template."""
        if self.format == DocumentFormat.MARKDOWN:
            return self._format_markdown(content)
        elif self.format == DocumentFormat.HTML:
            return self._format_html(content)
        elif self.format == DocumentFormat.PDF:
            return self._format_pdf(content)
        else:
            raise ValueError(f"Unsupported format: {self.format}")

    def _format_markdown(self, content: Dict[str, Any]) -> str:
        """Format content for Markdown output."""
        sections = []
        sections.append(f"# {self.metadata.title}\n")
        
        for section in self.get_ordered_sections():
            if section.name in content:
                title = section.name.replace('_', ' ').title()
                sections.append(f"## {title}")
                sections.append(content[section.name])
                sections.append("")
        
        return "\n".join(sections)

    def _format_pdf(self, content: Dict[str, Any]) -> str:
        """
        Format content for PDF output.
        
        Note: This returns LaTeX-formatted content that can be converted to PDF
        using a LaTeX processor.
        """
        sections = []
        
        # Add LaTeX preamble with required packages
        sections.append("\\documentclass[11pt]{article}")
        sections.append("\\usepackage[utf8]{inputenc}")
        sections.append("\\usepackage[T1]{fontenc}")
        sections.append("\\usepackage{geometry}")
        sections.append("\\usepackage{graphicx}")
        sections.append("\\usepackage{booktabs}")
        sections.append("\\usepackage{siunitx}")
        sections.append("\\usepackage{pgfplots}")
        sections.append("\\usepackage{tikz}")
        sections.append("\\usepackage{listings}")
        sections.append("\\usepackage{xcolor}")
        sections.append("\\usepackage{amsmath}")
        sections.append("\\usepackage{hyperref}")
        sections.append("\\usepackage{caption}")
        sections.append("\\usepackage{subcaption}")
        sections.append("\\usepackage{float}")
        
        # Configure packages
        sections.append("\\geometry{margin=1in}")
        sections.append("\\pgfplotsset{compat=newest}")
        sections.append("\\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue}")
        sections.append("\\lstset{basicstyle=\\ttfamily\\small, breaklines=true}")
        
        # Start document
        sections.append("\\begin{document}")
        
        # Add title
        sections.append("\\title{%")
        sections.append(f"{self.metadata.title}\\\\")
        sections.append("\\large Data Visualization Report}")
        sections.append("\\author{" + self.metadata.author + "}")
        sections.append("\\date{\\today}")
        sections.append("\\maketitle")
        
        # Add data overview section
        sections.append("\\section{Data Overview}")
        
        # Add data sources
        sections.append("\\subsection{Data Sources}")
        sections.append("\\begin{itemize}")
        for source in self.metadata.data_sources:
            sections.append(f"\\item \\textbf{{{source.name}}} ({source.type})")
            sections.append("  \\begin{itemize}")
            sections.append(f"  \\item URL: \\url{{{source.url}}}")
            sections.append(f"  \\item Last Updated: {self.metadata.dataset_metrics.last_updated}")
            sections.append("  \\end{itemize}")
        sections.append("\\end{itemize}")
        
        # Add dataset metrics
        sections.append("\\subsection{Dataset Statistics}")
        sections.append("\\begin{table}[H]")
        sections.append("\\centering")
        sections.append("\\begin{tabular}{lr}")
        sections.append("\\toprule")
        metrics = self.metadata.dataset_metrics
        sections.append(f"Total Rows & {metrics.rows:,} \\\\")
        sections.append(f"Total Columns & {metrics.columns} \\\\")
        sections.append(f"Dataset Size & \\SI{{{metrics.size_bytes / 1024 / 1024:.2f}}}{{MB}} \\\\")
        sections.append(f"Completeness Score & {metrics.completeness_score:.1%} \\\\")
        sections.append(f"Update Frequency & {metrics.update_frequency.value} \\\\")
        sections.append("\\bottomrule")
        sections.append("\\end{tabular}")
        sections.append("\\caption{Dataset Metrics}")
        sections.append("\\end{table}")
        
        # Add visualizations section
        if "charts_and_graphs" in content:
            sections.append("\\section{Visualizations}")
            for viz in self.metadata.visualizations:
                sections.append(f"\\subsection{{{viz.type.value.title()}}}")
                if viz.type == VisualizationType.CHART:
                    sections.append(f"\\textbf{{Type:}} {viz.chart_type.value}")
                    sections.append(f"\\textbf{{Color Scheme:}} {viz.color_scheme.value}")
                sections.append("\\begin{figure}[H]")
                sections.append("\\centering")
                viz_content = content["charts_and_graphs"].get(viz.type.value, "")
                sections.append(viz_content)
                sections.append("\\caption{" + viz.type.value.title() + " Visualization}")
                sections.append("\\end{figure}")
        
        # Add statistical analysis section
        if "statistical_analysis" in content:
            sections.append("\\section{Statistical Analysis}")
            sections.append("\\begin{itemize}")
            sections.append("\\item \\textbf{Summary Statistics}")
            sections.append("\\begin{lstlisting}")
            sections.append(content["statistical_analysis"])
            sections.append("\\end{lstlisting}")
            sections.append("\\end{itemize}")
        
        # Add interpretation guide
        if "interpretation_guide" in content:
            sections.append("\\section{Interpretation Guide}")
            sections.append(content["interpretation_guide"])
        
        # Add accessibility information
        sections.append("\\section{Accessibility Information}")
        sections.append("This document follows these accessibility standards:")
        sections.append("\\begin{itemize}")
        for standard in self.metadata.accessibility_standards:
            sections.append(f"\\item {standard}")
        sections.append("\\end{itemize}")
        
        if "accessibility_notes" in content:
            sections.append("\\subsection{Additional Accessibility Notes}")
            sections.append("\\begin{itemize}")
            sections.append("\\item \\textbf{Alternative Text:} All visualizations include detailed descriptions")
            sections.append("\\item \\textbf{Color Schemes:} Selected for maximum contrast and readability")
            sections.append("\\item \\textbf{PDF Tags:} Document is tagged for screen reader compatibility")
            sections.append("\\end{itemize}")
            sections.append(content["accessibility_notes"])
        
        # Add PDF/A compliance metadata
        sections.append("""
            \\pdfinfo{
                /Title (\""" + self.metadata.title + """\")
                /Author (\""" + self.metadata.author + """\")
                /Subject (Data Visualization Report)
                /Keywords (data visualization, accessibility, analysis)
                /Producer (LaTeX with hyperref)
                /Trapped /False
            }
        """)
        
        sections.append("\\end{document}")
        return "\n".join(sections)

    def _format_html(self, content: Dict[str, Any]) -> str:
        """Format content for HTML output."""
        sections = []
        sections.append("<!DOCTYPE html>")
        sections.append("<html><head>")
        sections.append(f"<title>{self.metadata.title}</title>")
        sections.append("</head><body>")
        sections.append(f"<h1>{self.metadata.title}</h1>")
        
        for section in self.get_ordered_sections():
            if section.name in content:
                title = section.name.replace('_', ' ').title()
                sections.append(f"<h2>{title}</h2>")
                sections.append(f"<div>{content[section.name]}</div>")
        
        sections.append("</body></html>")
        return "\n".join(sections)

    def _format_pdf(self, content: Dict[str, Any]) -> str:
        """
        Format content for PDF output.
        
        Note: This returns LaTeX-formatted content that can be converted to PDF
        using a LaTeX processor.
        """
        sections = []
        
        # Add LaTeX preamble with required packages
        sections.append("\\documentclass[11pt]{article}")
        sections.append("\\usepackage[utf8]{inputenc}")
        sections.append("\\usepackage[T1]{fontenc}")
        sections.append("\\usepackage{geometry}")
        sections.append("\\usepackage{graphicx}")
        sections.append("\\usepackage{booktabs}")
        sections.append("\\usepackage{siunitx}")
        sections.append("\\usepackage{pgfplots}")
        sections.append("\\usepackage{tikz}")
        sections.append("\\usepackage{float}")
        sections.append("\\usepackage{caption}")
        sections.append("\\usepackage{subcaption}")
        sections.append("\\usepackage{listings}")
        sections.append("\\usepackage{xcolor}")
        sections.append("\\usepackage{amsmath}")
        sections.append("\\usepackage{hyperref}")
        sections.append("\\usepackage{pdfcomment}")
        sections.append("\\usepackage{tagpdf}")
        
        # Configure packages for accessibility
        sections.append("\\geometry{margin=1in}")
        sections.append("\\pgfplotsset{compat=newest}")
        sections.append("\\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue}")
        sections.append("\\tagpdfsetup{tabsorder=structure, activate-all}")
        
        # Start document
        sections.append("\\begin{document}")
        
        # Add title
        sections.append("\\title{%")
        sections.append(f"{self.metadata.title}\\\\")
        sections.append("\\large Data Visualization Report}")
        sections.append("\\author{" + self.metadata.author + "}")
        sections.append("\\date{\\today}")
        sections.append("\\maketitle")
        
        # Add data overview section
        sections.append("\\section{Data Overview}")
        
        # Add data sources
        sections.append("\\subsection{Data Sources}")
        sections.append("\\begin{itemize}")
        for source in self.metadata.data_sources:
            sections.append(f"\\item \\textbf{{{source.name}}} ({source.type})")
            sections.append("  \\begin{itemize}")
            sections.append(f"  \\item URL: \\url{{{source.url}}}")
            sections.append(f"  \\item Last Updated: {self.metadata.dataset_metrics.last_updated}")
            sections.append("  \\end{itemize}")
        sections.append("\\end{itemize}")
        
        # Add dataset metrics with proper formatting
        sections.append("\\subsection{Dataset Statistics}")
        sections.append("\\begin{table}[H]")
        sections.append("\\centering")
        sections.append("\\begin{tabular}{lr}")
        sections.append("\\toprule")
        metrics = self.metadata.dataset_metrics
        sections.append(f"Total Rows & \\num{{{metrics.rows:,}}} \\\\")
        sections.append(f"Total Columns & \\num{{{metrics.columns}}} \\\\")
        sections.append(f"Dataset Size & \\SI{{{metrics.size_bytes / 1024 / 1024:.2f}}}{{MB}} \\\\")
        sections.append(f"Completeness Score & \\SI{{{metrics.completeness_score * 100}}}{{\\percent}} \\\\")
        sections.append(f"Update Frequency & {metrics.update_frequency.value} \\\\")
        sections.append("\\bottomrule")
        sections.append("\\end{tabular}")
        sections.append("\\caption{Dataset Metrics}")
        sections.append("\\label{tab:metrics}")
        sections.append("\\end{table}")
        
        # Add visualizations section with proper formatting
        if "charts_and_graphs" in content:
            sections.append("\\section{Visualizations}")
            for viz in self.metadata.visualizations:
                sections.append(f"\\subsection{{{viz.type.value.title()}}}")
                
                # Add visualization metadata
                sections.append("\\begin{description}")
                if viz.type == VisualizationType.CHART:
                    sections.append(f"\\item[Type] {viz.chart_type.value}")
                sections.append(f"\\item[Color Scheme] {viz.color_scheme.value}")
                if viz.interactive:
                    sections.append("\\item[Interactivity] Supported in HTML format")
                sections.append("\\end{description}")
                
                # Add visualization content
                sections.append("\\begin{figure}[H]")
                sections.append("\\centering")
                viz_content = content["charts_and_graphs"].get(viz.type.value, "")
                sections.append(viz_content)
                
                # Add accessibility info for screen readers
                alt_text = content["charts_and_graphs"].get("alt_text", "")
                if alt_text:
                    sections.append(f"\\pdftooltip{{\\caption{{{viz.type.value.title()} Visualization}}}}{{{alt_text}}}")
                else:
                    sections.append(f"\\caption{{{viz.type.value.title()} Visualization}}")
                
                sections.append("\\label{fig:" + viz.type.value.lower() + "}")
                sections.append("\\end{figure}")
        
        # Add statistical analysis section with math support
        if "statistical_analysis" in content:
            sections.append("\\section{Statistical Analysis}")
            sections.append("\\begin{itemize}")
            sections.append("\\item \\textbf{Summary Statistics}")
            sections.append("\\begin{lstlisting}[language=Python, numbers=left, frame=single]")
            sections.append(content["statistical_analysis"])
            sections.append("\\end{lstlisting}")
            sections.append("\\end{itemize}")
        
        # Add interpretation guide
        if "interpretation_guide" in content:
            sections.append("\\section{Interpretation Guide}")
            sections.append(content["interpretation_guide"])
        
        # Add accessibility information
        sections.append("\\section{Accessibility Information}")
        sections.append("This document follows these accessibility standards:")
        sections.append("\\begin{itemize}")
        for standard in self.metadata.accessibility_standards:
            sections.append(f"\\item {standard}")
        sections.append("\\end{itemize}")
        
        if "accessibility_notes" in content:
            sections.append("\\subsection{Additional Accessibility Notes}")
            sections.append("\\begin{itemize}")
            sections.append("\\item \\textbf{Alternative Text:} All visualizations include detailed descriptions")
            sections.append("\\item \\textbf{Color Schemes:} Selected for maximum contrast and readability")
            sections.append("\\item \\textbf{PDF Tags:} Document is tagged for screen reader compatibility")
            sections.append("\\item \\textbf{Navigation:} Document includes proper sectioning and cross-references")
            sections.append("\\end{itemize}")
            sections.append(content["accessibility_notes"])
        
        # Add PDF/A compliance metadata
        sections.append("""
            \\pdfinfo{
                /Title (\""" + self.metadata.title + """\")
                /Author (\""" + self.metadata.author + """\")
                /Subject (Data Visualization Report)
                /Keywords (data visualization, accessibility, analysis)
                /Producer (LaTeX with hyperref and tagpdf)
                /Trapped /False
            }
        """)
        
        sections.append("\\end{document}")
        return "\n".join(sections)

    def _format_pdf(self, content: Dict[str, Any]) -> str:
        """
        Format content for PDF output.
        
        Note: This returns LaTeX-formatted content that can be converted to PDF
        using a LaTeX processor.
        """
        sections = []
        
        # Add LaTeX preamble with required packages
        sections.append("\\documentclass[11pt]{article}")
        sections.append("\\usepackage[utf8]{inputenc}")
        sections.append("\\usepackage[T1]{fontenc}")
        sections.append("\\usepackage{geometry}")
        sections.append("\\usepackage{graphicx}")
        sections.append("\\usepackage{booktabs}")
        sections.append("\\usepackage{siunitx}")
        sections.append("\\usepackage{pgfplots}")
        sections.append("\\usepackage{tikz}")
        sections.append("\\usepackage{float}")
        sections.append("\\usepackage{caption}")
        sections.append("\\usepackage{subcaption}")
        sections.append("\\usepackage{listings}")
        sections.append("\\usepackage{xcolor}")
        sections.append("\\usepackage{amsmath}")
        sections.append("\\usepackage{hyperref}")
        sections.append("\\usepackage{pdfcomment}")
        sections.append("\\usepackage{tagpdf}")
        
        # Configure packages for accessibility
        sections.append("\\geometry{margin=1in}")
        sections.append("\\pgfplotsset{compat=newest}")
        sections.append("\\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue}")
        sections.append("\\tagpdfsetup{tabsorder=structure, activate-all}")
        
        # Start document
        sections.append("\\begin{document}")
        
        # Add title
        sections.append("\\title{%")
        sections.append(f"{self.metadata.title}\\\\")
        sections.append("\\large Data Visualization Report}")
        sections.append("\\author{" + self.metadata.author + "}")
        sections.append("\\date{\\today}")
        sections.append("\\maketitle")
        
        # Add data overview section
        sections.append("\\section{Data Overview}")
        
        # Add data sources
        sections.append("\\subsection{Data Sources}")
        sections.append("\\begin{itemize}")
        for source in self.metadata.data_sources:
            sections.append(f"\\item \\textbf{{{source.name}}} ({source.type})")
            sections.append("  \\begin{itemize}")
            sections.append(f"  \\item URL: \\url{{{source.url}}}")
            sections.append(f"  \\item Last Updated: {self.metadata.dataset_metrics.last_updated}")
            sections.append("  \\end{itemize}")
        sections.append("\\end{itemize}")
        
        # Add dataset metrics with proper formatting
        sections.append("\\subsection{Dataset Statistics}")
        sections.append("\\begin{table}[H]")
        sections.append("\\centering")
        sections.append("\\begin{tabular}{lr}")
        sections.append("\\toprule")
        metrics = self.metadata.dataset_metrics
        sections.append(f"Total Rows & \\num{{{metrics.rows:,}}} \\\\")
        sections.append(f"Total Columns & \\num{{{metrics.columns}}} \\\\")
        sections.append(f"Dataset Size & \\SI{{{metrics.size_bytes / 1024 / 1024:.2f}}}{{MB}} \\\\")
        sections.append(f"Completeness Score & \\SI{{{metrics.completeness_score * 100}}}{{\\percent}} \\\\")
        sections.append(f"Update Frequency & {metrics.update_frequency.value} \\\\")
        sections.append("\\bottomrule")
        sections.append("\\end{tabular}")
        sections.append("\\caption{Dataset Metrics}")
        sections.append("\\label{tab:metrics}")
        sections.append("\\end{table}")
        
        # Add visualizations section with proper formatting
        if "charts_and_graphs" in content:
            sections.append("\\section{Visualizations}")
            for viz in self.metadata.visualizations:
                sections.append(f"\\subsection{{{viz.type.value.title()}}}")
                
                # Add visualization metadata
                sections.append("\\begin{description}")
                if viz.type == VisualizationType.CHART:
                    sections.append(f"\\item[Type] {viz.chart_type.value}")
                sections.append(f"\\item[Color Scheme] {viz.color_scheme.value}")
                if viz.interactive:
                    sections.append("\\item[Interactivity] Supported in HTML format")
                sections.append("\\end{description}")
                
                # Add visualization content
                sections.append("\\begin{figure}[H]")
                sections.append("\\centering")
                viz_content = content["charts_and_graphs"].get(viz.type.value, "")
                sections.append(viz_content)
                
                # Add accessibility info for screen readers
                alt_text = content["charts_and_graphs"].get("alt_text", "")
                if alt_text:
                    sections.append(f"\\pdftooltip{{\\caption{{{viz.type.value.title()} Visualization}}}}{{{alt_text}}}")
                else:
                    sections.append(f"\\caption{{{viz.type.value.title()} Visualization}}")
                
                sections.append("\\label{fig:" + viz.type.value.lower() + "}")
                sections.append("\\end{figure}")
        
        # Add statistical analysis section with math support
        if "statistical_analysis" in content:
            sections.append("\\section{Statistical Analysis}")
            sections.append("\\begin{itemize}")
            sections.append("\\item \\textbf{Summary Statistics}")
            sections.append("\\begin{lstlisting}[language=Python, numbers=left, frame=single]")
            sections.append(content["statistical_analysis"])
            sections.append("\\end{lstlisting}")
            sections.append("\\end{itemize}")
        
        # Add interpretation guide
        if "interpretation_guide" in content:
            sections.append("\\section{Interpretation Guide}")
            sections.append(content["interpretation_guide"])
        
        # Add accessibility information
        sections.append("\\section{Accessibility Information}")
        sections.append("This document follows these accessibility standards:")
        sections.append("\\begin{itemize}")
        for standard in self.metadata.accessibility_standards:
            sections.append(f"\\item {standard}")
        sections.append("\\end{itemize}")
        
        if "accessibility_notes" in content:
            sections.append("\\subsection{Additional Accessibility Notes}")
            sections.append("\\begin{itemize}")
            sections.append("\\item \\textbf{Alternative Text:} All visualizations include detailed descriptions")
            sections.append("\\item \\textbf{Color Schemes:} Selected for maximum contrast and readability")
            sections.append("\\item \\textbf{PDF Tags:} Document is tagged for screen reader compatibility")
            sections.append("\\item \\textbf{Navigation:} Document includes proper sectioning and cross-references")
            sections.append("\\end{itemize}")
            sections.append(content["accessibility_notes"])
        
        # Add PDF/A compliance metadata
        sections.append("""
            \\pdfinfo{
                /Title (\""" + self.metadata.title + """\")
                /Author (\""" + self.metadata.author + """\")
                /Subject (Data Visualization Report)
                /Keywords (data visualization, accessibility, analysis)
                /Producer (LaTeX with hyperref and tagpdf)
                /Trapped /False
            }
        """)
        
        sections.append("\\end{document}")
        return "\n".join(sections)






class ExecutiveSummaryTemplate(BaseTemplate):
    """Template for executive summaries."""
    
    def __init__(
        self,
        name: str,
        format: DocumentFormat,
        metadata: Optional[ExecutiveSummaryMetadata] = None
    ):
        """Initialize executive summary template."""
        super().__init__(name, format, metadata)
        if not isinstance(self.metadata, ExecutiveSummaryMetadata):
            raise ValueError("metadata must be instance of ExecutiveSummaryMetadata")

    def _initialize_sections(self) -> None:
        """Initialize executive summary sections."""
        self.add_section(TemplateSection(
            name="key_findings",
            required=True,
            order=0,
            content_type="text",
            metadata={
                "description": "Key research findings",
                "max_length": 500
            }
        ))
        
        self.add_section(TemplateSection(
            name="insights",
            required=True,
            order=1,
            content_type="text",
            metadata={
                "description": "Business insights",
                "max_length": 300
            }
        ))
        
        self.add_section(TemplateSection(
            name="recommendations",
            required=True,
            order=2,
            content_type="text",
            metadata={
                "description": "Actionable recommendations",
                "max_length": 300
            }
        ))
        
        self.add_section(TemplateSection(
            name="next_steps",
            required=True,
            order=3,
            content_type="text",
            metadata={
                "description": "Proposed next steps",
                "max_length": 200
            }
        ))

    async def format_content(self, content: Dict[str, Any]) -> str:
        """Format content according to template."""
        if self.format == DocumentFormat.MARKDOWN:
            return self._format_markdown(content)
        elif self.format == DocumentFormat.HTML:
            return self._format_html(content)
        elif self.format == DocumentFormat.PDF:
            return self._format_pdf(content)
        else:
            raise ValueError(f"Unsupported format: {self.format}")

    def _format_markdown(self, content: Dict[str, Any]) -> str:
        """Format content for Markdown output."""
        sections = []
        sections.append(f"# Executive Summary: {self.metadata.title}\n")
        
        sections.append("## Summary Information")
        sections.append(f"* **Priority Level:** {self.metadata.priority_level.value.title()}")
        sections.append(f"* **Business Impact:** {self.metadata.business_impact.value.title()}")
        sections.append(f"* **Target Audience:** {', '.join(a.value.title() for a in self.metadata.target_audience)}")
        
        for section in self.get_ordered_sections():
            if section.name in content:
                title = section.name.replace('_', ' ').title()
                sections.append(f"\n## {title}")
                sections.append(content[section.name])
        
        return "\n".join(sections)

    def _format_html(self, content: Dict[str, Any]) -> str:
        """Format content for HTML output."""
        sections = []
        sections.append("<!DOCTYPE html>")
        sections.append("<html><head>")
        sections.append(f"<title>Executive Summary: {self.metadata.title}</title>")
        sections.append("<style>")
        sections.append("""
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .summary-info {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
            }
        """)
        sections.append("</style>")
        sections.append("</head><body>")
        
        sections.append(f"<h1>Executive Summary: {self.metadata.title}</h1>")
        
        sections.append('<div class="summary-info">')
        sections.append("<h2>Summary Information</h2>")
        sections.append("<ul>")
        sections.append(f"<li><strong>Priority Level:</strong> {self.metadata.priority_level.value.title()}</li>")
        sections.append(f"<li><strong>Business Impact:</strong> {self.metadata.business_impact.value.title()}</li>")
        sections.append(f"<li><strong>Target Audience:</strong> {', '.join(a.value.title() for a in self.metadata.target_audience)}</li>")
        sections.append("</ul>")
        sections.append("</div>")
        
        for section in self.get_ordered_sections():
            if section.name in content:
                title = section.name.replace('_', ' ').title()
                sections.append(f"<h2>{title}</h2>")
                sections.append(f"<div>{content[section.name]}</div>")
        
        sections.append("</body></html>")
        return "\n".join(sections)

    def _format_pdf(self, content: Dict[str, Any]) -> str:
        """Format content for PDF output."""
        sections = []
        sections.append("\\documentclass{article}")
        sections.append("\\usepackage{geometry}")
        sections.append("\\geometry{margin=1in}")
        
        sections.append("\\begin{document}")
        sections.append(f"\\title{{Executive Summary: {self.metadata.title}}}")
        sections.append("\\maketitle")
        
        sections.append("\\section*{Summary Information}")
        sections.append("\\begin{itemize}")
        sections.append(f"\\item Priority Level: {self.metadata.priority_level.value.title()}")
        sections.append(f"\\item Business Impact: {self.metadata.business_impact.value.title()}")
        sections.append(f"\\item Target Audience: {', '.join(a.value.title() for a in self.metadata.target_audience)}")
        sections.append("\\end{itemize}")
        
        for section in self.get_ordered_sections():
            if section.name in content:
                title = section.name.replace('_', ' ').title()
                sections.append(f"\\section{{{title}}}")
                sections.append(content[section.name])
        
        sections.append("\\end{document}")
        return "\n".join(sections)

class TechnicalAnalysisTemplate(BaseTemplate):
    """Template for technical analysis reports."""
    
    def __init__(
        self,
        name: str,
        format: DocumentFormat,
        metadata: Optional[BaseTemplateMetadata] = None
    ):
        """Initialize technical analysis template."""
        super().__init__(name, format, metadata)

    def _initialize_sections(self) -> None:
        """Initialize technical analysis sections."""
        self.add_section(TemplateSection(
            name="system_architecture",
            required=True,
            order=0,
            content_type="text"
        ))
        
        self.add_section(TemplateSection(
            name="technical_specifications",
            required=True,
            order=1,
            content_type="text"
        ))
        
        self.add_section(TemplateSection(
            name="implementation_details",
            required=True,
            order=2,
            content_type="text"
        ))
        
        self.add_section(TemplateSection(
            name="performance_metrics",
            required=True,
            order=3,
            content_type="text"
        ))
        
        self.add_section(TemplateSection(
            name="dependencies",
            required=True,
            order=4,
            content_type="text"
        ))
        
        self.add_section(TemplateSection(
            name="api_documentation",
            required=True,
            order=5,
            content_type="text"
        ))
        
        self.add_section(TemplateSection(
            name="deployment_guide",
            required=True,
            order=6,
            content_type="text"
        ))

    def validate_performance_metrics(self, metrics: Dict[str, float]) -> bool:
        """Validate performance metrics."""
        return all(value >= 0 for value in metrics.values())

    def validate_system_requirements(self, requirements: Dict[str, Any]) -> bool:
        """Validate system requirements."""
        valid_types = {"cpu", "memory", "storage"}
        return all(req in valid_types for req in requirements.keys())

    async def format_content(self, content: Dict[str, Any]) -> str:
        """Format content according to template."""
        if "performance_metrics" in content:
            if not self.validate_performance_metrics(content["performance_metrics"]):
                raise ValueError("Invalid performance metrics")
        
        if self.format == DocumentFormat.MARKDOWN:
            return self._format_markdown(content)
        elif self.format == DocumentFormat.HTML:
            return self._format_html(content)
        elif self.format == DocumentFormat.PDF:
            return self._format_pdf(content)
        else:
            raise ValueError(f"Unsupported format: {self.format}")

    def _format_markdown(self, content: Dict[str, Any]) -> str:
        """Format content for Markdown output."""
        sections = []
        sections.append(f"# {self.metadata.title}\n")
        
        for section in self.get_ordered_sections():
            if section.name in content:
                title = section.name.replace('_', ' ').title()
                sections.append(f"## {title}")
                sections.append(content[section.name])
                sections.append("")
        
        return "\n".join(sections)

    def _format_html(self, content: Dict[str, Any]) -> str:
        """Format content for HTML output."""
        sections = []
        sections.append("<!DOCTYPE html>")
        sections.append("<html><head>")
        sections.append(f"<title>{self.metadata.title}</title>")
        sections.append("</head><body>")
        
        sections.append(f"<h1>{self.metadata.title}</h1>")
        
        for section in self.get_ordered_sections():
            if section.name in content:
                title = section.name.replace('_', ' ').title()
                sections.append(f"<h2>{title}</h2>")
                sections.append(f"<div>{content[section.name]}</div>")
        
        sections.append("</body></html>")
        return "\n".join(sections)

    def _format_pdf(self, content: Dict[str, Any]) -> str:
        """Format content for PDF output."""
        sections = []
        sections.append("\\documentclass{article}")
        sections.append("\\usepackage{listings}")
        sections.append("\\begin{document}")
        sections.append(f"\\title{{{self.metadata.title}}}")
        sections.append("\\maketitle")
        
        for section in self.get_ordered_sections():
            if section.name in content:
                title = section.name.replace('_', ' ').title()
                sections.append(f"\\section{{{title}}}")
                sections.append(content[section.name])
        
        sections.append("\\end{document}")
        return "\n".join(sections)

class DataVisualizationTemplate(BaseTemplate):
    """Template for data visualization reports."""
    
    def __init__(
        self,
        name: str,
        format: DocumentFormat,
        metadata: Optional[DataVisualizationMetadata] = None
    ):
        """Initialize data visualization template."""
        super().__init__(name, format, metadata)
        if not isinstance(self.metadata, DataVisualizationMetadata):
            raise ValueError("metadata must be instance of DataVisualizationMetadata")

    def _initialize_sections(self) -> None:
        """Initialize visualization sections."""
        self.add_section(TemplateSection(
            name="data_overview",
            required=True,
            order=0,
            content_type="text",
            metadata={
                "description": "Overview of the dataset and data sources",
                "required_elements": [
                    "data sources description",
                    "dataset statistics",
                    "data quality metrics",
                    "update frequency"
                ]
            }
        ))
        
        self.add_section(TemplateSection(
            name="charts_and_graphs",
            required=True,
            order=1,
            content_type="visualization",
            metadata={
                "description": "Visual representations of the data",
                "supported_types": [vt.value for vt in VisualizationType],
                "interactive_support": self.metadata.supports_interactivity,
                "responsive_support": self.metadata.supports_responsiveness
            }
        ))
        
        self.add_section(TemplateSection(
            name="statistical_analysis",
            required=True,
            order=2,
            content_type="analysis",
            metadata={
                "description": "Statistical analysis of the data",
                "required_elements": [
                    "summary statistics",
                    "correlation analysis",
                    "trend analysis",
                    "outlier detection"
                ]
            }
        ))
        
        self.add_section(TemplateSection(
            name="interpretation_guide",
            required=True,
            order=3,
            content_type="text",
            metadata={
                "description": "Guide for interpreting the visualizations",
                "required_elements": [
                    "key insights",
                    "interpretation methods",
                    "limitations and caveats",
                    "recommendations"
                ]
            }
        ))
        
        self.add_section(TemplateSection(
            name="accessibility_notes",
            required=True,
            order=4,
            content_type="text",
            metadata={
                "description": "Accessibility information and alternative formats",
                "required_elements": [
                    "accessibility features",
                    "alternative text descriptions",
                    "keyboard navigation support",
                    "color contrast information"
                ]
            }
        ))

    def validate_visualization(
        self,
        viz_config: VisualizationConfig,
        content: Dict[str, Any]
    ) -> bool:
        """Validate visualization configuration and content."""
        required_fields = {
            "data": True,
            "type": True,
            "title": True,
            "description": True,
            "alt_text": viz_config.type != VisualizationType.MAP
        }
        
        return all(
            not required or key in content
            for key, required in required_fields.items()
        )

    def validate_accessibility(self, content: Dict[str, Any]) -> bool:
        """Validate accessibility requirements."""
        required_features = {
            "alt_text",
            "aria_labels",
            "color_contrast_ratio",
            "keyboard_navigation"
        }
        
        if "accessibility_features" not in content:
            return False
            
        provided_features = set(content["accessibility_features"])
        return required_features.issubset(provided_features)

    async def format_content(self, content: Dict[str, Any]) -> str:
        """Format content according to template."""
        # Validate visualizations if present
        if "charts_and_graphs" in content:
            for viz in self.metadata.visualizations:
                if not self.validate_visualization(viz, content["charts_and_graphs"]):
                    raise ValueError(
                        f"Invalid visualization configuration for {viz.type.value}"
                    )
        
        # Validate accessibility features
        if not self.validate_accessibility(content):
            raise ValueError("Required accessibility features are missing")
        
        if self.format == DocumentFormat.MARKDOWN:
            return self._format_markdown(content)
        elif self.format == DocumentFormat.HTML:
            return self._format_html(content)
        elif self.format == DocumentFormat.PDF:
            return self._format_pdf(content)
        else:
            raise ValueError(f"Unsupported format: {self.format}")

    def _format_markdown(self, content: Dict[str, Any]) -> str:
        """Format content for Markdown output."""
        sections = []
        sections.append(f"# {self.metadata.title}\n")
        
        # Add data overview
        sections.append("## Data Overview")
        sections.append("\n### Data Sources")
        for source in self.metadata.data_sources:
            sections.append(f"* **{source.name}** ({source.type})")
            sections.append(f"  * URL: {source.url}")
            sections.append(f"  * Last Updated: {self.metadata.dataset_metrics.last_updated}")
        
        # Add dataset metrics
        sections.append("\n### Dataset Statistics")
        metrics = self.metadata.dataset_metrics
        sections.append(f"* Rows: {metrics.rows:,}")
        sections.append(f"* Columns: {metrics.columns}")
        sections.append(f"* Size: {metrics.size_bytes / 1024 / 1024:.2f} MB")
        sections.append(f"* Completeness: {metrics.completeness_score:.1%}")
        
        # Add visualizations
        if "charts_and_graphs" in content:
            sections.append("\n## Visualizations")
            for viz in self.metadata.visualizations:
                sections.append(f"\n### {viz.type.value.title()}")
                if viz.type == VisualizationType.CHART:
                    sections.append(f"Type: {viz.chart_type.value}")
                sections.append(content["charts_and_graphs"].get(viz.type.value, ""))
        
        # Add remaining sections
        for section in self.get_ordered_sections():
            if section.name in content and section.name not in ["data_overview", "charts_and_graphs"]:
                title = section.name.replace('_', ' ').title()
                sections.append(f"\n## {title}")
                sections.append(content[section.name])
        
        return "\n".join(sections)

    def _format_html(self, content: Dict[str, Any]) -> str:
        """Format content for HTML output."""
        sections = []
        sections.append("<!DOCTYPE html>")
        sections.append("<html lang='en'><head>")
        sections.append(f"<title>{self.metadata.title}</title>")
        sections.append("<style>")
        sections.append("""
            body {
                font-family: 'Roboto', sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }
            .visualization {
                margin: 20px 0;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .chart-container {
                width: 100%;
                height: 400px;
            }
            @media (max-width: 768px) {
                .chart-container {
                    height: 300px;
                }
            }
            .accessibility-info {
                background: #f8f9fa;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }
            .data-metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .metric-card {
                background: white;
                padding: 15px;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        """)
        sections.append("</style>")
        
        # Add visualization libraries if interactive
        if self.metadata.supports_interactivity:
            sections.append("""
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <script src="https://d3js.org/d3.v7.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
                <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
                <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
            """)
        
        sections.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        sections.append('<meta name="description" content="Data visualization report">')
        sections.append("</head>")
        sections.append('<body role="document">')
        
        # Add title and overview
        sections.append(f'<h1 id="title">{self.metadata.title}</h1>')
        
        # Add data overview section
        sections.append('<section aria-labelledby="data-overview" class="data-section">')
        sections.append('<h2 id="data-overview">Data Overview</h2>')
        
        # Add data sources
        sections.append('<div class="data-sources">')
        sections.append('<h3>Data Sources</h3>')
        sections.append('<ul>')
        for source in self.metadata.data_sources:
            sections.append(f'<li><strong>{source.name}</strong> ({source.type})')
            sections.append('<ul>')
            sections.append(f'<li>URL: <a href="{source.url}">{source.url}</a></li>')
            sections.append(f'<li>Last Updated: {self.metadata.dataset_metrics.last_updated}</li>')
            sections.append('</ul>')
            sections.append('</li>')
        sections.append('</ul>')
        sections.append('</div>')
        
        # Add dataset metrics
        metrics = self.metadata.dataset_metrics
        sections.append('<div class="data-metrics">')
        sections.append('<h3>Dataset Statistics</h3>')
        sections.append('<div class="metric-grid">')
        sections.append('<div class="metric-card" role="region" aria-label="Dataset Size">')
        sections.append('<h4>Dataset Size</h4>')
        sections.append(f'<p>{metrics.rows:,} rows</p>')
        sections.append(f'<p>{metrics.columns} columns</p>')
        sections.append(f'<p>{metrics.size_bytes / 1024 / 1024:.2f} MB</p>')
        sections.append('</div>')
        sections.append('<div class="metric-card" role="region" aria-label="Data Quality">')
        sections.append('<h4>Data Quality</h4>')
        sections.append(f'<p>Completeness: {metrics.completeness_score:.1%}</p>')
        sections.append(f'<p>Update Frequency: {metrics.update_frequency.value}</p>')
        sections.append('</div>')
        sections.append('</div>')
        sections.append('</div>')
        sections.append('</section>')
        
        # Add visualizations section
        if "charts_and_graphs" in content:
            sections.append('<section aria-labelledby="visualizations" class="visualization-section">')
            sections.append('<h2 id="visualizations">Visualizations</h2>')
            for viz in self.metadata.visualizations:
                sections.append(f'<div class="visualization" role="figure" aria-labelledby="viz-{viz.type.value}-title">')
                sections.append(f'<h3 id="viz-{viz.type.value}-title">{viz.type.value.title()}</h3>')
                if viz.interactive:
                    sections.append(f'<div class="chart-container" id="viz-{viz.type.value}" tabindex="0">')
                    sections.append(content["charts_and_graphs"].get(viz.type.value, ""))
                    sections.append('</div>')
                else:
                    sections.append(content["charts_and_graphs"].get(viz.type.value, ""))
                sections.append('</div>')
            sections.append('</section>')
        
        # Add statistical analysis section
        if "statistical_analysis" in content:
            sections.append('<section aria-labelledby="analysis" class="analysis-section">')
            sections.append('<h2 id="analysis">Statistical Analysis</h2>')
            sections.append('<div class="analysis-content">')
            sections.append(content["statistical_analysis"])
            sections.append('</div>')
            sections.append('</section>')
        
        # Add interpretation guide section
        if "interpretation_guide" in content:
            sections.append('<section aria-labelledby="interpretation" class="interpretation-section">')
            sections.append('<h2 id="interpretation">Interpretation Guide</h2>')
            sections.append('<div class="interpretation-content">')
            sections.append(content["interpretation_guide"])
            sections.append('</div>')
            sections.append('</section>')
        
        # Add accessibility information
        sections.append('<section aria-labelledby="accessibility" class="accessibility-info">')
        sections.append('<h2 id="accessibility">Accessibility Information</h2>')
        sections.append('<p>This document follows these accessibility standards:</p>')
        sections.append('<ul>')
        for standard in self.metadata.accessibility_standards:
            sections.append(f'<li>{standard}</li>')
        sections.append('</ul>')
        
        if "accessibility_notes" in content:
            sections.append('<div class="accessibility-notes">')
            sections.append('<h3>Additional Accessibility Notes</h3>')
            sections.append(content["accessibility_notes"])
            sections.append('</div>')
        sections.append('</section>')
        
        # Add keyboard navigation support
        sections.append("""
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                // Add keyboard navigation for interactive elements
                const interactiveElements = document.querySelectorAll('.chart-container');
                interactiveElements.forEach(element => {
                    element.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            // Trigger interaction on Enter key
                            element.click();
                        }
                    });
                });
            });
            </script>
        """)
        
        sections.append("</body></html>")
        return "\n".join(sections)

