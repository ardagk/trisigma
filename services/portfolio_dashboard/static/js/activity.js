import { app, pm_id } from './app.js';
import { createTable } from './util.js';
import { ref } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js'

var selectedAccount = ref(null);
var selectedStrategy = ref(null);
var traderMatch = ref([]);

export const ActivityOptions = {
    template: `
        <div class="rowflex fh justify-content-end" style="gap: 8px !important;">
            <dropdown-field :value="strategies[0]" :options="strategies" :key="strategies" @update="onSelection"/>
            <dropdown-field :value="accounts[0]" :options="accounts" :key="accounts" @update="onSelection"/>
        </div>
    `,
    data: function () {
        return {
            accounts: [],
            strategies: [],
            traders: [],
            selectedAccount: null,
            selectedStrategy: null,
        }
    },
    methods: {
        update () {
            let promise = axios.get('/portfolio/bots', {
                params: {portfolio_manager_id: pm_id}
            }).then(response => {
                this.bots = response.data;
                this.accounts = [...new Set(this.bots.map(item => item.account_id))];
                this.strategies = [...new Set(this.bots.map(item => item.strategy_uri))];
                this.selectedAccount = this.accounts[0];
                this.selectedStrategy = this.strategies[0];
                this.onSelection();
            });
            return promise;
        },

        onSelection () {
            selectedAccount.value = this.selectedAccount;
            selectedStrategy.value = this.selectedStrategy;
            //emit event global event
            if (this.selectedAccount === null || this.selectedStrategy === null) {
                return;
            }
            traderMatch.value = this.bots.filter(
                item => item.account_id == this.selectedAccount
                && item.strategy_uri == this.selectedStrategy
                )
        },
    },
    mounted: function () {
        this.$root.wait(this.update());
    },
};

export const ObservationsView = {
    template: `
        <div class="fh fw">
            <canvas id="activity-observations-chart"></canvas>
        </div>
    `,
    data: function () {
        return {
            botObservations: [],
            chartView: null,
        }
    },
    methods: {
        onSelection () {
            if (traderMatch.value.length === 0) {
                return;
            }
            const trader_id = traderMatch.value[0].trader_id;
            axios.get('/portfolio/observations', {params: {trader_id: trader_id}}).then(response => {
                this.botObservations = response.data;
                this.render();
            }).catch(errors => {
                console.log(errors);
            });
        },
        render () {
            if (this.chartView === null) {
                //observations schema [{'time': time, 'observations': {'indicator1': value1, 'indicator2': value2, ...}}, ...]
                let time = [];
                let data = {};
                let names = [];
                const null_value = undefined;
                for (let i = 0; i < this.botObservations.length; i++) {
                    if (i % 10 !== 0) {
                        continue;
                    }
                    time.push(new Date(parseInt(this.botObservations[i].time * 1000)));
                    let keys = Object.keys(this.botObservations[i].observations);
                    for (let j = 0; j < keys.length; j++) {
                        let k = keys[j];
                        if (!names.includes(k)) {
                            //if doesn't exist fill with nulls for previous times
                            names.push(k);
                            data[k] = [];
                            for (let j = 0; j < i; j++) data[k].push(null_value);
                        } 
                    }
                    for (let j = 0; j < names.length; j++) {
                        name = names[j];
                        if (this.botObservations[i].observations[name] === undefined) {
                            data[name].push(null_value);
                        } else {
                            data[name].push(this.botObservations[i].observations[name]);
                        }
                    }
                }
                let datasets = [];
                let colors = ['gray', 'cyan']
                for (let i = 0; i < names.length; i++) {
                    datasets.push({
                        label: names[i],
                        data: data[names[i]],
                        borderColor: colors[i % colors.length],
                    });
                }
                let ctx = document.getElementById('activity-observations-chart').getContext('2d');
                this.chartView = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: time,
                        datasets: datasets,
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        pointRadius: 0,
                        layout: {
                            padding: {
                                left: 10,
                                right: 13,
                            }
                        },
                        scales: {
                            x: {
                                //time cartesian axis
                                type: 'time',
                                time: {
                                    unit: 'hour',
                                    displayFormats: {
                                        hour: 'DD MMM HH:mm',
                                    },
                                },
                                ticks: {
                                    maxRotation: 0,
                                    minRotation: 0,
                                    autoSkip: true,
                                },
                                min: Date.now() - 1000*60*60*24,
                                max: time[time.length - 1],
                            },
                            y: {
                                type: 'linear',
                                min: function (context) {
                                    let chart = context.chart;
                                    let datasets = chart.data.datasets;
                                    let min = null;
                                    for(var i=0; i<datasets.length; i++) {
                                        let dataset=datasets[i]
                                        if(chart.data.datasets[i].hidden) {
                                            continue;
                                        }

                                        dataset.data.forEach(function(d) {
                                            if(d<min || min == null) {
                                                min = d
                                            }
                                        })
                                    }
                                    return min * 0.8;
                                },
                                max: function (context) {
                                    let chart = context.chart;
                                    let datasets = chart.data.datasets;
                                    let max = null;
                                    for(var i=0; i<datasets.length; i++) {
                                        let dataset=datasets[i]
                                        if(chart.data.datasets[i].hidden) {
                                            continue;
                                        }

                                        dataset.data.forEach(function(d) {
                                            if(d>max || max == null) {
                                                max = d
                                            }
                                        })
                                    }
                                    return max * 1.2;
                                },
                                    

                                ticks: {
                                    count: 10,
                                },
                            },
                        },
                        plugins: {
                            zoom: {
                                limits: {
                                    x: {min: time[0], max: time[time.length - 1], minRange: 1000*60*60*6, maxRange: 1000*60*60*24},
                                },
                                zoom: {
                                    wheel: {
                                        enabled: true,
                                    },
                                    pinch: {
                                        enabled: true,
                                    },
                                    mode: 'x',
                                },
                                pan: {
                                    enabled: true,
                                    mode: 'x',
                                },
                            },
                        },
                    }
                });
            } else {
                return;
                this.chartView.data.labels = time;
                this.chartView.data.datasets = datasets;
                this.chartView.update();
            }
        },

    },
    mounted: function () {
        this.$watch(() => traderMatch.value, this.onSelection);

    },
};

export const JournalView = {
    template: `
        <div class="fh fw">
            <div class="fh fw">
                <div id="activity-journal-table">
                </div>
            </div>
        </div>
    `,
    data: function () {
        return {
            botJournal: [],
            journalTable: null,
            lookback: 10,
        }
    },
    methods: {
        onSelection () {
            if (traderMatch.value.length === 0) {
                return;
            }
            const trader_id = traderMatch.value[0].trader_id;
            const start_time = Math.floor(Date.now() / 1000) - (this.lookback * 24 * 60 * 60);
            axios.get('/portfolio/journal', {
                params: {trader_id: trader_id, start_time: start_time}}
                ).then(response => {
                    this.botJournal = response.data;
                    for (let i = 0; i < response.data.length; i++) {
                        response.data[i].time = new Date(parseInt(response.data[i].time * 1000)).toLocaleString();
                    }
                    for (let i = 0; i < 10; i++) {
                        this.botJournal.push(response.data[i]);
                    }

                    this.render();
                }).catch(errors => {
                    console.log(errors);
            });
        },
        render () {
            //create a table for the journal using gridjs
            this.journalTable = createTable('activity-journal-table', {
                records: this.botJournal,
            }); 
        },

    },
    mounted: function () {
        this.$watch(() => traderMatch.value, this.onSelection);

    },
};

export const TransactionsView = {
    template: `
        <div class="fh fw">
            <div class="fw fh">
                <div id="activity-transactions-table">
                </div>
            </div>
        </div>
    `,
    data: function () {
        return {
            botTransactions: [],
            transactionsTable: null,
        }
    },
    methods: {
        onSelection () {
            if (traderMatch.value.length === 0) {
                return;
            }
            const trader_id = traderMatch.value[0].trader_id;
            let transactionsRequest = axios.get('/portfolio/transactions', {
                params: {trader_id: trader_id}}
                ).then(response => {
                    this.botTransactions = response.data;
                    this.render();
                }).catch(errors => {
                    console.log(errors);
            });
        },
        render () {
            //create a table for the journal using gridjs
            this.transactionsTable = createTable('activity-transactions-table', {
                records: this.botTransactions,
            }); 
        },
    },
    mounted: function () {
        this.$watch(() => traderMatch.value, this.onSelection);
    }

};

export const OpenOrdersView = {
    template: `
        <div id=""/>
    `,
    mounted: function () {
        const table = createTable('testtable', {
            records: [
                {id: 1, name: 'John', age: 21},
                {id: 2, name: 'Jane', age: 22},
                {id: 3, name: 'Susan', age: 23},
            ]
        });
        table.update();
    }
};


app.component('activityoptions', ActivityOptions);
app.component('journalview', JournalView);
app.component('observationsview', ObservationsView);
app.component('transactionsview', TransactionsView);
app.component('openordersview', OpenOrdersView);
