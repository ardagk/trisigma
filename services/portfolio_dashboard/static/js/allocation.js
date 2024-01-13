import { app } from './app.js';
import { pm_id } from './app.js';
import { toRaw } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js'
import { shallowRef } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js'

// Allocator Views
export const AllocatorView = {
    template: `
    <div class="rowflex fh">
        <div class="flexitem" style="flex-basis: 60%">
            <canvas class="line-chart-canvas" ref="pieChart"></canvas>
        </div>
        <div class="flexitem colflex" style="flex-basis: 40%">
            <div v-if="focus()" class="colflex fw" :key="activeStrategyConfig.qualifiedName + activeStrategyConfig.strategy">
                <dropdown-field :value="activeStrategyConfig.strategy" :options="Object.keys(availableStrategies)"\
                 @update="strategyTypeChange"/>
                <model-form :options="genericParams" @update="genericParamChange"/>
                <model-form :options="strategyParams" :key="counter" @update="strategyParamChange"/>
                <div>
                    <button type="button" @click="onRemoveStrategy">Remove</button>
                    <button :disabled="activeStrategyConfig.new" type="button" @click="onRevertStrategy">Revert</button>
                </div>
            </div>
            <div v-else class="fw rowflex justify-content-center" style="flex-basis: 8%;">
                <button class="flexitem" type="button" @click="onNewStrategy" style="font-size: 1.3em; flex-basis: 70%;\
                 flex-grow: 0; margin-top: 10px">Add New Strategy</button>
            </div>
            <div class="rowflex justify-content-end fw padding-bottom: 20px;">
                <button type="button" @click="saveStrategyAllocation" style="font-size: 1.3em">Save</button>
            </div>
        </div>
    </div>
    `,
    data: function() {
        return {
            dropdownSelection: null,
            existingStrategies: [],
            availableStrategies: {},
            activeStrategyConfig: {},
            originalStrategyConfig: {},
            availableAssets: ['AAPL', 'SPY', 'TSLA', 'MSFT'],
            chart: null,
            freeAllocation: 0,
            paramsVerified: true,
            genericParams: {
                name: { type: 'text', banned: [], default: '', value: ''},
                allocation: { type: 'range', min: 0, max: 100, step: 1, available: 100, value: 0},
            },
            strategyParams: {},
            counter: 0,
        };
    },
    methods: {
        focus() {
            return Object.keys(this.activeStrategyConfig).length !== 0;
        },
        update () {
            const req1 = axios.get('/strategy/definition')
            const req2 = axios.get('/portfolio/allocation', {
                params: { portfolio_manager_id: pm_id }
            })
            let promise = axios.all([req1, req2]).then(axios.spread((definitionResp, allocationResp) => {
                this.availableStrategies = this._processStrategyDefinition(definitionResp.data);
                this.existingStrategies = this._processStrategyAllocation(allocationResp.data);
                this.originalStrategies = JSON.parse(JSON.stringify(this.existingStrategies));
                let totAlloc = Object.values(this.existingStrategies
                    ).reduce((a, b) => a + b.allocation, 0);
                this.freeAllocation = 100 - totAlloc;
                this.renderView();
            })).catch(error => {
                console.log(error);
            });
            return promise;
        },
        _processStrategyAllocation(resp) {
            const strategyConfigs = [];
            for (let [slotId, details] of Object.entries(resp)) {
                const strategyName = details.strategy;
                const name = details.name;
                const allocation = details.allocation;
                const options = JSON.parse(JSON.stringify(
                    this.availableStrategies[strategyName].options));
                for (let k of Object.keys(options)) {
                    options[k].value = details.config[k];
                }
                strategyConfigs.push({
                    name: name,
                    qualifiedName: name,
                    new: false,
                    strategy: strategyName,
                    options: options,
                    allocation: allocation * 100
                });
            }
            return strategyConfigs;
        },
        _processStrategyDefinition(resp) {
            const availableStrategies = {};
            for (let strategy of resp) {
                availableStrategies[strategy.name] = {};
                for (let param of Object.values(strategy.options)) {
                    switch (param.type) {

                        case '$asset':
                            param.type = 'dropdown';
                            if (param.exclude === undefined) param.exclude = [];
                            if (param.include === undefined) param.include = [];
                            param.options = this.availableAssets.slice();
                            param.options = param.options.concat(param.include);
                            param.options = param.options.filter(asset => {
                                return !param.exclude.includes(asset);
                            });
                        case 'dropdown':
                            if (param.default === undefined) {
                                param.default = param.options[0];
                            }
                            param.value = param.default;
                            break;
                        case 'rangeint':
                            param.type = 'range';
                            param.min = parseInt(param.min);
                            param.max = parseInt(param.max);
                            param.step = 1;
                            if (param.default === undefined) param.default = param.min;
                            else param.default = parseInt(param.default);
                            param.value = param.default;
                            break;
                            
                        case 'range':
                            param.min = parseInt(param.min);
                            param.max = parseInt(param.max);
                            if (param.step === undefined) param.step = 0.01;
                            else param.step = parseFloat(param.step);
                            if (param.default === undefined) param.default = param.min;
                            param.value = param.default;
                            break;
                    }
                }
                availableStrategies[strategy.name] = strategy;
            }
            return availableStrategies;
        },
        saveStrategyAllocation() {
            const finalAlloc = {};
            for (let i = 0; i < this.existingStrategies.length; i++) {
                const value = JSON.parse(JSON.stringify(this.existingStrategies[i]));
                value.config = {};
                for (let [cKey, cVal] of Object.entries(value.options)) {
                    value.config[cKey] = cVal.value;
                }
                delete value.options;
                delete value.new;
                delete value.qualifiedName;
                finalAlloc[value.name] = value;
            }
            axios.post('/portfolio/allocation', {
                portfolio_manager_id: pm_id,
                allocation: finalAlloc
            }).then(resp => {
                console.log(resp);
                this.update();
            }).catch(error => {
                console.log(error);
            });
        },
        //updater
        renderView () {
            //use strategyAllocation to create pie chart. keys are names and values are weights 0 to 1.0
            this.updateFreeAllocation();
            let label = this.existingStrategies.map(strategy => strategy.name);
            label.push('free');
            let data = this.existingStrategies.map(strategy => strategy.allocation);
            let labelDisp = label.slice();
            for (let i = 0; i < label.length; i++)
                if (label[i].length > 10)
                    labelDisp[i] = labelDisp[i].slice(0, 10) + '...'; 
            data = this.existingStrategies.map(strategy => strategy.allocation);
            data.push(this.freeAllocation);
            //create a color family
            let colors = [];
            let steps = 5;
            let hueFrom = 140;
            let hueTo = 220;
            let saturation = 80;
            let lightness = 15;
            for (let i = 0; i < label.length-1; i++)
                colors.splice(0,0,'hsl(' + (hueFrom + i * (hueTo - hueFrom) / steps) + ', ' + saturation + '%, ' + lightness + '%)');
            colors.push('hsl(180, 10%, 12%)');
            if (this.chart == null) {
                let ctx = this.$refs.pieChart.getContext('2d');
                let chart = new Chart(ctx, {
                    type: 'pie',
                    data: { labels: labelDisp, datasets: [{label: label, data: data, backgroundColor: colors}]},
                    options: {animation: false,
                         responsive: true, maintainAspectRatio: false,
                        layout: {padding: {top: 10, bottom: 10, left: 10, right: 10}}},
                });
                chart.legend.options.position = 'right';
                chart.legend.options.align = 'start';
                chart.legend.options.labels.fontSize = 10;
                chart.update();
                //Object.seal(chart);
                this.chart = shallowRef(chart);
                chart.options.onClick = (evt, item) => {
                    if (!this.paramsVerified) return;
                    if (item.length === 0) return;
                    const label = this.chart.data.datasets[0].label[item[0].index];
                    this.onStrategySelection(label);
                }
            }
            this.chart.data.datasets[0].data = data;
            this.chart.data.datasets[0].label = label;
            this.chart.data.datasets[0].backgroundColor = colors;
            this.chart.data.labels = labelDisp;
            if (this.focus()){
                const labelIndex = this.chart.data.datasets[0].label.indexOf(this.activeStrategyConfig.name);
                var name = this.activeStrategyConfig.name;
                if (name.length > 10)
                    name =  name.slice(0, 10) + '...';
                this.chart.data.labels[labelIndex] = name;
                const freeIndex = this.chart.data.labels.indexOf('free');
                this.chart.data.datasets[0].data[labelIndex] = this.activeStrategyConfig.allocation;
                this.chart.data.datasets[0].data[freeIndex] = this.freeAllocation;
                this.chart.update();
                //this.chart.getDatasetMeta(0).data[freeIndex].outerRadius -= 10;
                //this.chart.getDatasetMeta(0).data[labelIndex].outerRadius += 10;
            } else {
                const freeIndex = this.chart.data.labels.indexOf('free');
                this.chart.update();
                //this.chart.getDatasetMeta(0).data[freeIndex].outerRadius -= 10;
            }
        },
        updateFreeAllocation() {
            let totAlloc = this.existingStrategies.reduce((a, b) => a + b.allocation, 0);
            this.freeAllocation = 100 - totAlloc;
        },
        //command handlers
        onNewStrategy () {
            const alloc = parseInt(this.freeAllocation * 0.5);
            // strategy is the first strategy in the availableStrategy object
            const strategy = this.availableStrategies[Object.keys(this.availableStrategies)[0]];
            var name = 'New Strategy #' + Math.floor(Math.random() * 1000);
            while (this.existingStrategies.map(strategy => strategy.qualifiedName).includes(name)
                || this.existingStrategies.map(strategy => strategy.name).includes(name)) {
                name = 'New Strategy #' + Math.floor(Math.random() * 1000);
            }
            const newStrategyConfig = {
                name: name,
                qualifiedName: name,
                new: true,
                strategy: strategy.name,
                options: JSON.parse(JSON.stringify(strategy.options)),
                allocation: alloc
            };
            this.existingStrategies.splice(0, 0, newStrategyConfig);
            this.onStrategySelection(name);
        },
        onRevertStrategy () {
            let name = this.activeStrategyConfig.qualifiedName;
            for (let value of Object.values(this.originalStrategies)) {
                if (value.qualifiedName === name) {
                    this.activeStrategyConfig.options = JSON.parse(JSON.stringify(value.options));
                    this.activeStrategyConfig.strategy = value.strategy;
                    this.strategyParams = {}
                    this.strategyParams = JSON.parse(JSON.stringify(this.activeStrategyConfig.options));
                    this.counter += 1;
                    this.renderView();
                }
            }
        },
        onRemoveStrategy () {
            let name = this.activeStrategyConfig.qualifiedName;
            this.existingStrategies = this.existingStrategies.filter(
                strategy => strategy.qualifiedName != name).map(
                strategy => toRaw(strategy));
            this.activeStrategyConfig = {};
            this.renderView();
        },
        //form change handlers
        onStrategySelection(name) {
            if (name == 'free') {
                this.activeStrategyConfig = {};
            } else {
                this.activeStrategyConfig = this.existingStrategies.filter(
                    strategy => strategy.name === name)[0]; 
                this.updateFreeAllocation();
                this.genericParams.name.value = this.activeStrategyConfig.name;
                const bannedNames = [];
                for (let strategy of this.existingStrategies)
                    if (strategy.name != name)
                        bannedNames.push(strategy.name);
                this.genericParams.name.banned = bannedNames;
                this.genericParams.allocation.value = this.activeStrategyConfig.allocation;
                this.genericParams.allocation.available = this.freeAllocation + this.activeStrategyConfig.allocation;
                this.strategyParams = JSON.parse(JSON.stringify(this.activeStrategyConfig.options));
            }
            this.renderView();
        },
        strategyTypeChange(strategy) {
            this.activeStrategyConfig.strategy = strategy;
            let strategyDef = this.availableStrategies[this.activeStrategyConfig.strategy].options;
            let options = JSON.parse(JSON.stringify(strategyDef));
            for (let option of Object.values(options)) {
                option.value = option.value;
            }
            this.activeStrategyConfig.options = options;
            this.strategyParams = JSON.parse(JSON.stringify(this.activeStrategyConfig.options));
        },
        genericParamChange(data) {
            //update params, if strategy has changed update strategy param form
            for (let [key, value] of Object.entries(data)) {
                this.activeStrategyConfig[key] = value;
            }
            this.renderView();
        },
        strategyParamChange(data) {
            for (let [key, value] of Object.entries(data)) {
                this.activeStrategyConfig.options[key].value = value;
            }
        }
    },
    mounted () {
        this.$root.wait(this.update());
    },
};
export const AllocationPieView = {
    template: `
    `

};
export const EmptyView = {
    template: `
    `,
    data: function() {
        return {
        };
    },
};

app.component('allocatorview', AllocatorView);
app.component('allocationpieview', AllocationPieView);
app.component('emptyview', EmptyView);
