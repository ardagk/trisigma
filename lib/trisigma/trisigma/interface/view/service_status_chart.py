from plotly import graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot
from dash import dcc
import plotly.express as px
import pandas as pd

class ServiceStatusChart:

    RENDER_OPTIONS = ['div', 'html', 'figure', 'dcc']

    def __init__(self, status_reports,renderer='figure'):
        assert renderer in self.RENDER_OPTIONS, \
            'Invalid renderer: {}'.format(renderer)
        self.status_reports = status_reports
        self.renderer = renderer

    def render(self):
        fig = self._get_epa_fig(self.status_reports)
        if self.renderer == 'div':
            return plot({"data": fig}, output_type='div')
        elif self.renderer == 'html':
            return fig.to_html(full_html=True)
        elif self.renderer == 'figure':
            return fig
        elif self.renderer == 'dcc':
            return dcc.Graph(figure=fig)
        else:
            raise Exception('<!> Invalid renderer: {}'.format(self.renderer))

    def _get_epa_fig(self, dfs):
        BG_COLOR = "#21211f"
        OPT_BG_COLOR = "#363632"
        FONT_COLOR = "gray"
        bar_edge_width = 3
        bar_width = 0.6

        layout = go.Layout(
            showlegend=False,
            updatemenus=[dict(buttons=[])],
            xaxis=dict(showgrid=False),
            #update distance between y ticks
            yaxis=dict(title="", showgrid=False, tickangle=0, showticklabels=True),
            height=550,
            plot_bgcolor=BG_COLOR,
            paper_bgcolor=BG_COLOR,
            yaxis_gridcolor=BG_COLOR,
            xaxis_gridcolor=BG_COLOR,
            yaxis_tickcolor="white",
            xaxis_tickcolor="white",
            font=dict(color=FONT_COLOR),
        )
        df = pd.concat(dfs)
        df['status'] = df['value'].apply(lambda x: 'Healthy' if x else 'Unhealthy')
        colors = {'Healthy': 'green', 'Unhealthy': 'red'}
        fig = px.timeline(df, x_start="start", x_end="end", y="title", color_discrete_map=colors, color='status', opacity=0.8,)
        fig.update_traces(marker=dict(line=dict(color=BG_COLOR, width=bar_edge_width)))
        fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
        fig.update_traces(width=bar_width)
        fig.update_layout(layout)
        fig.update_yaxes(fixedrange=True)
        return fig

