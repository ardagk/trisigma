import { app } from './app.js';
import { pm_id } from './app.js';
import { createLineChart } from './util.js';

export const KeyStatsView = {
    template: `
    <div class="keystats-wrapper">
        <div class="keystats-interval-wrapper">
            <button class="keystats-interval-button" @click="renderView('1d')">1d</button>
            <button class="keystats-interval-button" @click="renderView('1w')">1w</button>
            <button class="keystats-interval-button" @click="renderView('4w')">4w</button>
            <button class="keystats-interval-button" @click="renderView('12w')">12w</button>
            <button class="keystats-interval-button" @click="renderView('SE')">SE</button>
        </div>
        <div class="keystats-returnchart-wrapper">
                <canvas class="line-chart-canvas" id="keystats-return-chart"></canvas>
        </div>
        <div class="keystats-table-wrapper">
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
            selectedInterval: '1d',
            availableIntervals: ['1d', '1w', '4w', '12w', 'SE']
        };
    },
    methods: {
        update () {
            for (let interval of this.availableIntervals) {
                const req1 = axios.get('/portfolio/returnchart', {
                    params: { portfolio_manager_id: pm_id, interval: interval }
                })
                const req2 = axios.get('/portfolio/keystats', {
                    params: { portfolio_manager_id: pm_id, interval: interval }
                })
                axios.all([req1, req2]).then(axios.spread((returnchart, keystats) => {
                    this.historicReturn[interval] = returnchart.data;
                    this.keyStats[interval] = keystats.data;
                    if (interval === this.selectedInterval) {
                        this.renderView(interval);
                    }
                }))
            }
        },
        renderView (newInterval) {
            this.selectedInterval = newInterval;
        
            createLineChart(
                'keystats-return-chart',
                'Return',
                this.historicReturn[this.selectedInterval].time,
                this.historicReturn[this.selectedInterval].returns);
        }
    },
    mounted () {
        this.update();
    },
};

export const OverallWorthView = {
    template: `
    <div class="performance-worth-view-wrapper">
        <div class="performance-worth-box">
            <p class="performance-worth-title">Overall Worth</p>
            <p class="performance-worth-value">{{ overallWorth }}</p>
            <p class="performance-worth-change">{{ overallWorthChange }}</p>
        </div>
        <div class="performance-worth-details">
            <table class="list-table">
                <tbody>
                    <tr>
                        <td class="list-table-key" style="width: 30%;">Capital: </td>
                        <td class="list-table-value">{{ capitalWorth }}</td>
                    </tr>
                    <tr>
                        <td class="list-table-key" style="width: 30%;">Security: </td>
                        <td class="list-table-value">{{ securityWorth }}</td>
                    </tr>
                </tbody>
            </table>
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
            axios.get('/portfolio/position', {
                params: { portfolio_manager_id: pm_id }
            }).then(response => {
                let capitalWorth = 0;
                let securityWorth = 0;
                let position = response.data;
                for (let asset in position) {
                    if (asset === 'USD') {
                        capitalWorth += position[asset].value;
                    } else {
                        securityWorth += position[asset].value;
                    }
                }
                this.overallWorth = capitalWorth + securityWorth;
                this.capitalWorth = capitalWorth;
                this.securityWorth = securityWorth;
            }).catch(error => {
                console.log(error);
            });
        }
    },
    mounted () {
        this.update();
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
            axios.get('/portfolio/bots', {
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
                axios.all(requests).then(axios.spread((...responses) => {
                    for (let response in responses) {
                        let strategy = this.bots[response].strategy_uri.split('?')[0];
                        if (this.nTrades[strategy] === undefined) {
                            this.nTrades[strategy] = 0;
                        }
                        this.nTrades[strategy] = responses[response].data.length;
                    }
                })).catch(errors => {
                    console.log(errors);
                });
            }).catch(error => {
                console.log(error);
            });
        }
    },
    mounted () {
        this.update();
    },
};

app.component('keystatsview', KeyStatsView);
app.component('overallworthview', OverallWorthView);
app.component('strategyresultview', StrategyResultView);