from plotly import graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot
from dash import dcc

class EpaComparisonChart:

    RENDER_OPTIONS = ['div', 'html', 'figure', 'dcc']

    def __init__(
            self, real_trades, backtest_trades,
            backtest_data, renderer='figure'):
        assert renderer in self.RENDER_OPTIONS, \
            'Invalid renderer: {}'.format(renderer)
        self.real_trades = real_trades
        self.backtest_trades = backtest_trades
        self.backtest_data = backtest_data
        self.renderer = renderer

    def render(self):
        fig = self._get_epa_fig(
            self.real_trades,
            self.backtest_trades,
            self.backtest_data)
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

    def _get_epa_fig(self, real_trades, backtest_trades, backtest_data):
        increasing_color = '#51ad51'
        decreasing_color = '#e63737'
        showlegend = True
        reserve_line = dict(color='rgba(130,130,160,0.4)', width=2.5)
        wma_line = dict(color='rgba(255,165,0,0.4)', width=3)
        r_buy_marker = dict(color='rgba(0,180,0,1)', size=11, line={'width': 2, 'color': 'rgba(0,0,0,1)'})
        r_sell_marker = dict(color='rgba(180,0,0,1)', size=11, line={'width': 2, 'color': 'rgba(0,0,0,1)'})
        b_buy_marker = dict(color=f'rgba(0,200,0,0.4)', size=20, line={'width': 2, 'color': 'rgba(0,0,0,0.8)'})
        b_sell_marker = dict(color=f'rgba(200,0,0,0.4)', size=20, line={'width': 2, 'color': 'rgba(0,0,0,0.8)'})
        resistance_line_color = 'rgba(247,37,37,0.4)'
        support_line_color = 'rgba(70,161,47,0.4)'
        resistance_fill_color = 'rgba(247,37,37,0.0)'
        support_fill_color = 'rgba(70,161,47,0.0)'
        sr_width = 2
        sr_dash = 'dash'

        sr_df = backtest_data.copy()
        subfig = make_subplots(specs=[[{"secondary_y": True}]])
        subfig.update_yaxes(showgrid=False, zeroline=False)
        subfig.update_xaxes(showgrid=False, zeroline=False)
        BG_COLOR = "#21211f"
        OPT_BG_COLOR = "#363632"
        FONT_COLOR = "gray"
        layout = go.Layout(
            showlegend=showlegend,
            updatemenus=[dict(buttons=[])],
            xaxis=dict(title="Time",showgrid=False),
            yaxis=dict(title="Price", showgrid=False),
            xaxis_rangeslider_visible=False,
            height=550,
            plot_bgcolor=BG_COLOR,
            paper_bgcolor=BG_COLOR,
            yaxis_gridcolor=BG_COLOR,
            xaxis_gridcolor=BG_COLOR,
            yaxis_tickcolor="white",
            xaxis_tickcolor="white",
            font=dict(color=FONT_COLOR),
        )
        subfig.update_layout(layout)
        gdata = sr_df.copy()
        mins = 15
        dvalue = mins * 60 * 1000  # 30min * 60sec/min * 1000msec/sec
        df_resample = gdata[[]].resample("15T").max()
        merged_index = gdata.index.append(df_resample.index)
        timegap = merged_index[~merged_index.duplicated(keep=False)]
        subfig.add_trace(
            go.Candlestick(
                x=gdata.index,
                open=gdata.open,
                high=gdata.high,
                low=gdata.low,
                close=gdata.close,
                increasing=dict(
                    line=dict(color=increasing_color),
                    fillcolor=increasing_color),
                decreasing=dict(
                    line=dict(color=decreasing_color),
                    fillcolor=decreasing_color)),
            secondary_y=False)

        subfig.add_trace(
            go.Scatter(
                x=gdata.index,
                y=gdata.R3,
                line=dict(
                    color=resistance_line_color,
                    width=sr_width,
                    dash=sr_dash),
                name='R3'),
            secondary_y=False)

        subfig.add_trace(
            go.Scatter(
                x=gdata.index,
                y= gdata.R4,
                line=dict(
                    color=resistance_line_color,
                    width=sr_width, dash=sr_dash),
                name='R4',
                fill='tonexty',
                fillcolor=resistance_fill_color),
            secondary_y=False)

        subfig.add_trace(
            go.Scatter(
                x=gdata.index,
                y= gdata.S3,
                line=dict(
                    color=support_line_color,
                    width=sr_width, dash=sr_dash),
                name='S3'),
            secondary_y=False)
        subfig.add_trace(
            go.Scatter(
                x=gdata.index,
                y= gdata.S4,
                line=dict(
                    color=support_line_color,
                    width=sr_width,
                    dash=sr_dash),
                name='S4',
                fill='tonexty',
                fillcolor=support_fill_color),
            secondary_y=False)
        subfig.add_trace(
            go.Scatter(
                x=gdata.index,
                y= gdata.reserve,
                line=reserve_line,
                name='reserve'),
            secondary_y=True)
        subfig.update_xaxes(
            rangebreaks=[
                dict(values=timegap, dvalue=dvalue)
            ])
        subfig.add_trace(
            go.Scatter(x=gdata.index, y=gdata.WMA,
                line=wma_line,
                name='WMA'),
            secondary_y=False)
        if len(backtest_trades) != 0:
            b_buys = backtest_trades[backtest_trades['side']=='BUY']
            subfig.add_scatter(
                x=b_buys.index, y=b_buys['price'],
                mode="markers", name="backtest buy", marker=b_buy_marker,
                hovertext=b_buys['label'], connectgaps=True)
            b_sells = backtest_trades[backtest_trades['side']=='SELL']
            subfig.add_scatter(
                x=b_sells.index, y=b_sells['price'],
                mode="markers", name="backtest sell", marker=b_sell_marker,
                hovertext=b_sells['label'], connectgaps=True)
        if len(real_trades) != 0:
            r_buys = real_trades[real_trades['side']=='BUY']
            subfig.add_scatter(
                x=r_buys.index, y=r_buys['price'],
                mode="markers", name="real buy", marker=r_buy_marker,
                hovertext=r_buys['label'], connectgaps=True)
            r_sells = real_trades[real_trades['side']=='SELL']
            subfig.add_scatter(
                x=r_sells.index, y=r_sells['price'],
                mode="markers", name="real sell", marker=r_sell_marker,
                hovertext=r_sells['label'], connectgaps=True)
        return subfig

