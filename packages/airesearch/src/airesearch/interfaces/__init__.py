"""Document interface module initialization."""
from .document_interface import DocumentFormat, DocumentTemplate, DocumentInterface
from .templates import BaseTemplate, BaseTemplateMetadata, TemplateSection
from .research_templates import (
    ResearchReportTemplate,
    ResearchReportMetadata,
    ResearchMethodology,
    DataSource,
    ExecutiveSummaryTemplate,
    ExecutiveSummaryMetadata,
    SummaryLevel,
    TargetAudience,
    BusinessImpact,
    PriorityLevel,
    DataVisualizationTemplate,
    DataVisualizationMetadata,
    VisualizationType,
    DataFormat,
    ChartType,
    ColorScheme,
    UpdateFrequency,
    DatasetMetrics,
    VisualizationConfig
)

__all__ = [
    'DocumentFormat',
    'DocumentTemplate',
    'DocumentInterface',
    'BaseTemplate',
    'BaseTemplateMetadata',
    'TemplateSection',
    'ResearchReportTemplate',
    'ResearchReportMetadata',
    'ResearchMethodology',
    'DataSource',
    'ExecutiveSummaryTemplate',
    'ExecutiveSummaryMetadata',
    'SummaryLevel',
    'TargetAudience',
    'BusinessImpact',
    'PriorityLevel',
    'DataVisualizationTemplate',
    'DataVisualizationMetadata',
    'VisualizationType',
    'DataFormat',
    'ChartType',
    'ColorScheme',
    'UpdateFrequency',
    'DatasetMetrics',
    'VisualizationConfig'
]

