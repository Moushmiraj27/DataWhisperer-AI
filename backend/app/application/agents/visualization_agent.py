from __future__ import annotations

import pandas as pd
import plotly.express as px

from backend.app.application.schemas.visualization import ChartType, VisualizationRequest, VisualizationResponse


class VisualizationAgentError(ValueError):
    """Raised when a visualization request cannot be rendered."""


class VisualizationAgent:
    def execute(self, request: VisualizationRequest) -> VisualizationResponse:
        dataframe = pd.DataFrame(request.records)
        if dataframe.empty:
            raise VisualizationAgentError("Visualization requires at least one data row.")

        self._require_columns(dataframe, [column for column in [request.x, request.y, request.color] if column])
        chart_type, reasoning = choose_chart_type(dataframe, request)
        figure = create_plotly_figure(dataframe, request, chart_type)
        figure.update_layout(template="plotly_dark")

        return VisualizationResponse(
            chart_type=chart_type,
            figure=figure.to_plotly_json(),
            reasoning=reasoning,
            warnings=build_warnings(dataframe, chart_type),
        )

    @staticmethod
    def _require_columns(dataframe: pd.DataFrame, columns: list[str]) -> None:
        missing = [column for column in columns if column not in dataframe.columns]
        if missing:
            raise VisualizationAgentError(f"Unknown column(s): {', '.join(missing)}")


def choose_chart_type(dataframe: pd.DataFrame, request: VisualizationRequest) -> tuple[ChartType, str]:
    if request.chart_type:
        return request.chart_type, f"Using requested chart type: {request.chart_type.value}."

    numeric_columns = list(dataframe.select_dtypes(include="number").columns)
    datetime_columns = list(dataframe.select_dtypes(include=["datetime", "datetimetz"]).columns)

    if len(numeric_columns) >= 2 and not request.x and not request.y:
        return ChartType.SCATTER, "Detected multiple numeric columns, so a scatter chart is suitable."

    if request.x and request.y:
        if request.x in datetime_columns:
            return ChartType.LINE, "Detected a time-like x-axis with a measure, so a line chart is suitable."
        if pd.api.types.is_numeric_dtype(dataframe[request.x]) and pd.api.types.is_numeric_dtype(dataframe[request.y]):
            return ChartType.SCATTER, "Detected two numeric columns, so a scatter chart is suitable."
        return ChartType.BAR, "Detected category and measure columns, so a bar chart is suitable."

    if request.x and pd.api.types.is_numeric_dtype(dataframe[request.x]):
        return ChartType.HISTOGRAM, "Detected one numeric column, so a histogram is suitable."

    if request.y and pd.api.types.is_numeric_dtype(dataframe[request.y]):
        return ChartType.BOXPLOT, "Detected one numeric measure, so a boxplot is suitable."

    if len(dataframe.columns) >= 2:
        return ChartType.BAR, "Defaulting to a bar chart for categorical comparison."

    return ChartType.HISTOGRAM, "Defaulting to a histogram for a single-column dataset."


def create_plotly_figure(dataframe: pd.DataFrame, request: VisualizationRequest, chart_type: ChartType):
    x = request.x or infer_x_column(dataframe, chart_type)
    y = request.y or infer_y_column(dataframe, chart_type, x)
    title = request.title or build_title(chart_type, x, y)

    if chart_type == ChartType.BAR:
        return px.bar(dataframe, x=x, y=y, color=request.color, title=title)
    if chart_type == ChartType.LINE:
        return px.line(dataframe, x=x, y=y, color=request.color, title=title)
    if chart_type == ChartType.SCATTER:
        return px.scatter(dataframe, x=x, y=y, color=request.color, title=title)
    if chart_type == ChartType.HISTOGRAM:
        return px.histogram(dataframe, x=x, color=request.color, title=title)
    if chart_type == ChartType.PIE:
        return px.pie(dataframe, names=x, values=y, title=title)
    if chart_type == ChartType.HEATMAP:
        return create_heatmap(dataframe, title)
    if chart_type == ChartType.BOXPLOT:
        return px.box(dataframe, x=x if request.x else None, y=y, color=request.color, title=title)

    raise VisualizationAgentError(f"Unsupported chart type: {chart_type}")


def create_heatmap(dataframe: pd.DataFrame, title: str):
    numeric_dataframe = dataframe.select_dtypes(include="number")
    if numeric_dataframe.shape[1] < 2:
        raise VisualizationAgentError("Heatmap requires at least two numeric columns.")
    correlation = numeric_dataframe.corr(numeric_only=True)
    return px.imshow(correlation, text_auto=True, aspect="auto", title=title, color_continuous_scale="RdBu_r")


def infer_x_column(dataframe: pd.DataFrame, chart_type: ChartType) -> str:
    if chart_type in {ChartType.HISTOGRAM, ChartType.BOXPLOT}:
        return first_numeric_column(dataframe)
    if chart_type == ChartType.PIE:
        return first_categorical_column(dataframe)
    if chart_type == ChartType.HEATMAP:
        return ""
    return first_categorical_column(dataframe) or str(dataframe.columns[0])


def infer_y_column(dataframe: pd.DataFrame, chart_type: ChartType, x: str | None) -> str:
    if chart_type in {ChartType.HISTOGRAM, ChartType.HEATMAP}:
        return ""
    if chart_type == ChartType.BOXPLOT:
        return first_numeric_column(dataframe)
    if chart_type == ChartType.PIE:
        numeric = first_numeric_column(dataframe)
        if not numeric:
            raise VisualizationAgentError("Pie chart requires a numeric values column.")
        return numeric

    numeric_columns = [str(column) for column in dataframe.select_dtypes(include="number").columns]
    for column in numeric_columns:
        if column != x:
            return column

    raise VisualizationAgentError(f"{chart_type.value} chart requires a numeric y column.")


def first_numeric_column(dataframe: pd.DataFrame) -> str:
    numeric_columns = [str(column) for column in dataframe.select_dtypes(include="number").columns]
    if not numeric_columns:
        raise VisualizationAgentError("No numeric columns are available for this chart.")
    return numeric_columns[0]


def first_categorical_column(dataframe: pd.DataFrame) -> str:
    categorical_columns = [
        str(column)
        for column in dataframe.columns
        if not pd.api.types.is_numeric_dtype(dataframe[column])
    ]
    return categorical_columns[0] if categorical_columns else str(dataframe.columns[0])


def build_title(chart_type: ChartType, x: str | None, y: str | None) -> str:
    if y:
        return f"{chart_type.value.title()} of {y} by {x}"
    if x:
        return f"{chart_type.value.title()} of {x}"
    return chart_type.value.title()


def build_warnings(dataframe: pd.DataFrame, chart_type: ChartType) -> list[str]:
    warnings: list[str] = []
    if len(dataframe) > 5000:
        warnings.append("Large datasets may render slowly; consider sampling or aggregation.")
    if chart_type == ChartType.PIE and len(dataframe) > 12:
        warnings.append("Pie charts are most readable with 12 or fewer categories.")
    return warnings
