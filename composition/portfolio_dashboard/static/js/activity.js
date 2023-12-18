import { app, pm_id } from './app.js';
import { createTable } from './util.js';
import { ref } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js'
import 'https://cdnjs.cloudflare.com/ajax/libs/gridjs/6.0.6/gridjs.production.min.js'

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
            axios.get('/portfolio/bots', {
                params: {portfolio_manager_id: pm_id}
            }).then(response => {
                this.bots = response.data;
                this.accounts = [...new Set(this.bots.map(item => item.account_id))];
                this.strategies = [...new Set(this.bots.map(item => item.strategy_uri))];
                this.selectedAccount = this.accounts[0];
                this.selectedStrategy = this.strategies[0];
                this.onSelection();
            });
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
        this.update();
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
            let observationRequest = axios.get('/portfolio/observations', {params: {trader_id: trader_id}});
            let journalRequest = axios.get('/portfolio/journal', {params: {trader_id: trader_id}});
            axios.all([observationRequest, journalRequest]).then(axios.spread((...responses) => {
                this.botObservations = responses[0].data;
                this.botJournal = responses[1].data;
                this.render();
            })).catch(errors => {
                console.log(errors);
            });
        },
        render () {
            if (this.chartView === null) {
                //observations schema [{'time': time, 'observations': {'indicator1': value1, 'indicator2': value2, ...}}, ...]
                let time = [];
                let data = [];
                for (let i = 0; i < this.botObservations.length; i++) {
                    let entry = this.botObservations[i];
                    time.push(entry.time);
                    data.push(entry.observation);
                }
                let indicators = Object.keys(data[0]);
                let datasets = [];
                for (let i = 0; i < indicators.length; i++) {
                    let indicatorData = [];
                    for (let j = 0; j < data.length; j++) {
                        indicatorData.push(data[j][indicators[i]]);
                    }
                    datasets.push({
                        label: indicators[i],
                        data: indicatorData,
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
        }
    },
    methods: {
        onSelection () {
            if (traderMatch.value.length === 0) {
                return;
            }
            const trader_id = traderMatch.value[0].trader_id;
            axios.get('/portfolio/journal', {
                params: {trader_id: trader_id}}
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
            console.log(this.botTransactions);
            this.transactionsTable = createTable('activity-transactions-table', {
                records: this.botTransactions,
            }); 
        },
    },
    mounted: function () {
        this.$watch(() => traderMatch.value, this.onSelection);
        console.log('mounted');
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
