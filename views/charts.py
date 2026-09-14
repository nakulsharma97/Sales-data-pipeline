"""Chart builders shared by the demo and uploaded-data dashboards.

All charts use the project's coral/orange theme.

Note on titles: plotly express always renders a title object. Passing an
empty string makes the browser show the literal text "undefined" (px wraps
it as <b><b></b></b>). Titles are therefore optional and only applied when
a non-empty string is provided — the dashboard renders its own card
headers in HTML instead.
"""

import pandas as pd
import plotly.express as px

CORAL = "#F55036"
INK = "#111827"          # dark navy headline color
SLATE = "#6B7280"        # muted text
FONT_FAMILY = "'Source Sans Pro', sans-serif"

WARM_SEQUENCE = [
    "#F55036", "#F67A54", "#F89671", "#FAB28E",
    "#FCCEAC", "#FDE3D0", "#E04327", "#B93318",
]


def _apply_title(fig, title):
    """Only set a layout title when one is actually provided.

    plotly express creates a title object even when title="". If we set
    title=None or title_text=None, plotly.js still renders "undefined" for
    the empty <b>...</b> title object px created. The safe fix is to explicitly
    set the title text to an empty string with zero height/font.
    """
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=15, color=INK)))
    else:
        # Completely suppress the title — empty text avoids the "undefined" bug
        fig.update_layout(title=dict(text="", font=dict(size=1)))
    return fig


def _base_layout(fig):
    """Shared typography/margins so every chart behaves the same."""
    fig.update_layout(
        font=dict(family=FONT_FAMILY, size=12, color=INK),
        hoverlabel=dict(font=dict(family=FONT_FAMILY, size=12)),
        margin=dict(t=10, b=10, l=10, r=10),
    )
    return fig


def bar_chart(df, x, y, title, color_scale="Oranges", horizontal=False,
              height=None, hide_colorbar=False):
    orientation = "h" if horizontal else "v"
    fig = px.bar(
        df,
        x=y if horizontal else x,
        y=x if horizontal else y,
        orientation=orientation,
        labels={x: x.replace("_", " ").title(), y: y.replace("_", " ").title()},
        color=y,
        color_continuous_scale=color_scale,
    )
    # Currency hover, e.g. "$1,234.50"
    fig.update_traces(
        hovertemplate="%{y}: $%{x:,.2f}<extra></extra>"
        if horizontal else "%{x}: $%{y:,.2f}<extra></extra>"
    )
    _apply_title(fig, title)
    _base_layout(fig)
    fig.update_layout(showlegend=False)
    if height:
        fig.update_layout(height=height)
    if hide_colorbar:
        fig.update_coloraxes(showscale=False)
    if horizontal:
        # Value labels at the end of every bar (reference design). The x-range
        # is extended ~16% so the last label never clips, and both axes get
        # explicit titles ("Product" / "Revenue ($)") like the reference.
        fig.update_traces(
            texttemplate="$%{x:,.0f}", textposition="outside",
            textfont=dict(size=11, color=INK), cliponaxis=False,
        )
        x_max = float(pd.to_numeric(df[y], errors="coerce").max() or 0)
        fig.update_yaxes(autorange="reversed", automargin=True,
                         title_text="Product", tickfont=dict(size=11, color=INK))
        fig.update_xaxes(automargin=True, tickformat="$,.0f",
                         title_text="Revenue ($)",
                         range=[0, x_max * 1.16] if x_max else None,
                         tickfont=dict(size=11, color=SLATE))
    else:
        fig.update_xaxes(automargin=True, tickfont=dict(size=11, color=INK))
        fig.update_yaxes(automargin=True, tickformat="$,.0f",
                         tickfont=dict(size=11, color=SLATE))
    return fig


def line_chart(df, x, y, title):
    fig = px.line(
        df,
        x=x,
        y=y,
        markers=True,
        labels={x: "Date", y: "Revenue ($)"},
    )
    fig.update_traces(line_color=CORAL,
                      hovertemplate="%{x|%b %d, %Y}: $%{y:,.2f}<extra></extra>")
    _apply_title(fig, title)
    _base_layout(fig)
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(automargin=True, tickformat="$,.0f",
                     tickfont=dict(size=11, color=SLATE))
    fig.update_xaxes(automargin=True, tickfont=dict(size=11, color=SLATE))
    return fig


def category_chart(df, height=None, showlegend=None, textposition="inside"):
    fig = px.pie(
        df,
        names="category",
        values="revenue",
        hole=0.45,
        color_discrete_sequence=WARM_SEQUENCE,
    )
    fig.update_traces(
        textposition=textposition,
        textinfo="percent+label",
        textfont=dict(size=11, color=INK),
        hovertemplate="%{label}: $%{value:,.2f} (%{percent})<extra></extra>",
        automargin=True,
    )
    _apply_title(fig, None)
    _base_layout(fig)
    if height:
        fig.update_layout(height=height)
    if showlegend is not None:
        fig.update_layout(
            showlegend=showlegend,
            legend=dict(orientation="v", x=1.0, y=0.5, xanchor="left",
                        yanchor="middle", font=dict(size=11, color=INK))
            if showlegend else {},
        )
        if showlegend:
            fig.update_traces(textinfo="percent")
    return fig


def compute_category_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Group a raw sales DataFrame by category (for uploaded-data mode)."""
    return (
        df.groupby("category", as_index=False)["total"]
        .sum()
        .rename(columns={"total": "revenue"})
        .sort_values("revenue", ascending=False)
    )


def compute_product_revenue(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("product", as_index=False)["total"]
        .sum()
        .rename(columns={"total": "revenue"})
        .sort_values("revenue", ascending=False)
    )


def compute_revenue_by_date(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.assign(sale_date=df["date"].dt.date)
        .groupby("sale_date", as_index=False)["total"]
        .sum()
        .rename(columns={"total": "daily_revenue"})
        .sort_values("sale_date")
    )
    out["sale_date"] = pd.to_datetime(out["sale_date"])
    return out
