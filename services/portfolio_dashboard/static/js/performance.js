import { app } from './app.js';
import { pm_id } from './app.js';
import { shallowRef } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js'

export const KeyStatsView = {
    template: `
    <div class="colflex">
        <div class="flexitem" style="flex-basis: 5%">
            <button class="interval-button" @click="renderView('1w')">1w</button>
            <button class="interval-button" @click="renderView('4w')">4w</button>
            <button class="interval-button" @click="renderView('12w')">12w</button>
            <button class="interval-button" @click="renderView('SE')">SE</button>
        </div>
        <div class="flexitem fw" style="flex-basis: 45%;">
            <canvas class="line-chart-canvas fw fh" id="keystats-return-chart"></canvas>
        </div>
        <div class="flexitem" style="flex-basis: 50%;">
            <div id="keystats-table">
                <table class="list-table">
                <thead>
                <tr>
                </tr>
                </thead>
                <tbody>
                <tr v-for="(value, key) in keyStats[selectedInterval]" :key="key">
                    <td class="list-table-key" style="width: 30%;">{{ key }}</td>
                    <td class="list-table-value">{{ value }}</td>
                </tr>
                </tbody>
            </table>
            </div>
        </div>
    </div>
    `,
    data: function() {
        return {
            historicReturn: {},
            keyStats: {},
            keyStatsSelection: {},
            selectedInterval: '1w',
            availableIntervals: ['1w', '4w', '12w', 'SE'],
            chart: null,
        };
    },
    methods: {
        update () {
            const promises = [];
            for (let interval of this.availableIntervals) {
                const req1 = axios.get('/portfolio/returnchart', {
                    params: { portfolio_manager_id: pm_id, interval: interval }
                })
                const req2 = axios.get('/portfolio/keystats', {
                    params: { portfolio_manager_id: pm_id, interval: interval }
                })
                const p = axios.all([req1, req2]).then(axios.spread((returnchart, keystats) => {
                    for (let i = 0; i < returnchart.data.time.length; i++) {
                        returnchart.data.time[i] *= 1000;
                        returnchart.data.time[i] = new Date(returnchart.data.time[i]);
                        //format to YYYY-MM-DD
                        returnchart.data.time[i] = returnchart.data.time[i].toISOString().slice(0, 10);
                    }
                    this.historicReturn[interval] = returnchart.data;
                    this.keyStats[interval] = {};
                    //this.keyStats[interval] = keystats.data;
                    this.keyStats[interval] = {
                        'Return': "3.21%",
                        'Benchmark': "2.12%",
                        'Sharpe Ratio': "1.23",
                        'Volatility': "2.34%",
                        'Max Drawdown': "3.45%",
                        'Total Trades': "123",
                        'Win Rate': "45.67%",
                        'Avg. Win': "1.23%",
                        'Avg. Loss': "2.34%",
                        'Avg. Hold': "3.45 days",
                        'Avg. Profit': "4.56%",
                        'Avg. Loss': "5.67%",
                    }
                    if (interval === this.selectedInterval) {
                        this.renderView(interval);
                    }
                }))
                promises.push(p);
            }
            return Promise.all(promises);
        },
        renderView (newInterval) {
            this.selectedInterval = newInterval;
            if (this.chart == null) {
                const rootStyles = getComputedStyle(document.documentElement);
                const returnColor = 'hsl(160, 30%, 30%)'
                const benchmarkColor = 'rgba(200, 0, 0, 0.5)'
                let ctx = document.getElementById('keystats-return-chart').getContext('2d');
                let chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        datasets: [
                            {label: 'Return', data: [], borderColor: returnColor},
                            {label: 'Benchmark', data: [], borderColor: benchmarkColor, borderDash: [5, 5]} ],
                    },
                    options: {
                        //set background color
                        scales: { x: { type: 'time', time: { unit: 'day', tooltipFormat: 'MMM DD YYYY' } } },
                        animation: { duration: 0 }, elements: { point: { radius: 0 } },
                        responsive: false, aspectRatio: 3, maintainAspectRatio: false} });
                this.chart = shallowRef(chart);
            }
            this.chart.data.labels = this.historicReturn[this.selectedInterval].time;
            this.chart.data.datasets[0].data = this.historicReturn[this.selectedInterval].portfolio;
            this.chart.data.datasets[1].data = this.historicReturn[this.selectedInterval].benchmark;
            this.chart.update();
        }
    },
    mounted () {
        this.$root.wait(this.update());
    },
};

export const OverallWorthView = {
    template: `
        <div class="fh fw" style="position: relative">
            <div class="rowflex fw" style="gap: 30px; justify-content: space-around; padding: 30px;">
                <div class="valuebox flexitem">
                    <h5 class="bold">Overall Worth</h5>
                    <h1 class="bold">\${{ overallWorth }}</h1>
                    <h5 class="bold" style="text-align: right">{{ overallWorthChange }}</h5>
                </div>
                <ul class="flexitem">
                    <li> Capital: \${{ capitalWorth }} </li>
                    <li> Security: \${{ securityWorth }} </li>
                </ul>
            </div>
        </div>
    `,
    data: function() {
        return {
            overallWorth: 0,
            overallWorthChange: 0,
            capitalWorth: 0,
            securityWorth: 0,
        };
    },
    methods: {
        update () {
            let promise = axios.get('/portfolio/position', {
                params: { portfolio_manager_id: pm_id }
            }).then(response => {
                let capitalWorth = 0;
                let securityWorth = 0;
                let position = response.data;
                for (let asset in position) {
                    if (asset === 'USD') {
                        //round to 2 decimal
                        capitalWorth += position[asset].value;
                    } else {
                        securityWorth += position[asset].value;
                    }
                }
                this.overallWorth = Math.round((capitalWorth + securityWorth) * 100) / 100;
                this.capitalWorth = Math.round(capitalWorth * 100) / 100;
                this.securityWorth = Math.round(securityWorth * 100) / 100;
            }).catch(error => {
                console.log(error);
            });
            return promise;
        }
    },
    mounted () {
        this.$root.wait(this.update());
    },

};

export const StrategyResultView = {
    template: `
    <div class="performance-strategy-wrapper">
        <div class="performance-strategy-chart-wrapper">
            <canvas class="line-chart-canvas" id="performance-strategy-chart"></canvas>
        </div>
        <div class="performance-strategy-details-wrapper">
            <div id="performance-strategy-table">
                <table class="list-table">
                    <tbody>
                        <tr v-for="(value, key) in nTrades" :key="key">
                            <td class="list-table-key" style="width: 30%;">{{ key }}</td>
                            <td class="list-table-value">{{ value }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    `,
    data: function() {
        return {
            nTrades: {},
            bots: {},
        };
    },
    methods: {
        update () {
            const promises = [];
            promises.push(axios.get('/portfolio/bots', {
                params: { portfolio_manager_id: pm_id }
            }).then(response => {
                this.bots = response.data;
                let requests = [];
                let today = new Date();
                today.setHours(0,0,0,0);
                today = today.getTime();
                today = Math.floor(today / 1000);
                today = parseInt(today);
                //response is a list of bots
                for (let bot in this.bots) {
                    requests.push(axios.get('/portfolio/transactions', {
                        params: {
                            trader_id: this.bots[bot].trader_id,
                            start_time: today,
                        }
                    }));
                }
                promises.push(axios.all(requests).then(axios.spread((...responses) => {
                    for (let response in responses) {
                        let strategy = this.bots[response].strategy_uri.split('?')[0];
                        if (this.nTrades[strategy] === undefined) {
                            this.nTrades[strategy] = 0;
                        }
                        this.nTrades[strategy] = responses[response].data.length;
                    }
                })).catch(errors => {
                    console.log(errors);
                }));
            }).catch(error => {
                console.log(error);
            }));
            return Promise.all(promises);
        }
    },
    mounted () {
        this.$root.wait(this.update());
    },
};

app.component('keystatsview', KeyStatsView);
app.component('overallworthview', OverallWorthView);
app.component('strategyresultview', StrategyResultView);
