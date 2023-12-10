import { app } from './app.js';
import { pm_id } from './app.js';
import { toRaw } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js'
//import random int

// Allocator Views
export const AllocatorView = {
    template: `
    <div class="allocation-allocator-wrapper">
        <div class="allocation-allocator-pie-wrapper">
            <canvas class="line-chart-canvas" id="allocation-allocator-pie"></canvas>
        </div>
        <form class="allocation-allocator-config-form-wrapper">
            <div class="allocation-allocator-config-wrapper">
                <div v-if="focus()" id="allocation-allocator-dropdown-wrapper">
                    <select id="allocation-allocator-dropdown" v-model="activeStrategyConfig.strategy" @change="onStrategySelection">
                        <option v-for="strategy in availableStrategies" :key="strategy.name" :value="strategy.name">
                            {{ strategy.name }}
                        </option>
                    </select>
                </div>
                <div v-if="focus()" class="allocation-allocator-config-params-wrapper">
                    <div class="allocation-allocator-input-wrapper">
                        <label class="allocation-allocator-input-label">name</label>
                        <input class="allocation-allocator-text-input" id="allocation-allocator-name" type="text" v-model="nameValue">
                    </div>
                    <div class="allocation-allocator-input-wrapper">
                        <label class="allocation-allocator-input-label">allocation {{ allocSliderValue }}%</label>
                        <input class="allocation-allocator-slider-input" id="allocation-allocator-alloc-slider" type="range" min="0" :max="100" step="1" v-model="allocSliderValue">
                    </div>
                    <div v-for="(param, label, index) in activeStrategyConfig.options" :key="index">
                        <div class="allocation-allocator-input-wrapper">
                            <template v-if="param.type === 'range'">
                                <label class="allocation-allocator-input-label">{{ label }}: {{ param.value }}</label>
                                <input class="allocation-allocator-slider-input" type=range :min=param.min :max=param.max :step=param.step v-model="param.value">
                            </template>
                
                            <template v-else-if="param.type === 'dropdown'">
                                <label class="allocation-allocator-input-label">{{ label }}</label>
                                <select class="allocation-allocator-dropdown-input" v-model="param.value">
                                    <option v-for="option in param.options" :key="option" :value="option">
                                    {{ option }}
                                    </option>
                                </select>
                            </template>
                        </div>
                    </div>
                    <div id="allocation-allocator-reset-wrapper">
                        <button id="allocation-allocator-remove" type="button" @click="onRemoveStrategy">Remove</button>
                        <button :disabled="activeStrategyConfig.new" id="allocation-allocator-reset" type="button" @click="onRevertStrategy">Revert</button>
                    </div>
                </div>
                <div v-else id="allocation-allocator-empty-wrapper">
                    <div id="allocation-allocator-create-wrapper">
                        <button id="allocation-allocator-create" type="button" @click="onNewStrategy">Define new strategy</button>
                    </div>
                </div>
            </div>
            <div id="allocation-allocator-submit-wrapper">
                <button type="button" id="allocation-allocator-submit" @click="saveStrategyAllocation">Save</button>
            </div>
        </form>
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
        };
    },
    methods: {
        focus() {
            //false if activeStrategyConfig is empty
            return Object.keys(this.activeStrategyConfig).length !== 0;
        },
        update () {
            const req1 = axios.get('/strategy/definition')
            const req2 = axios.get('/portfolio/allocation', {
                params: { portfolio_manager_id: pm_id }
            })
            axios.all([req1, req2]).then(axios.spread((definitionResp, allocationResp) => {
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
        },
        _processStrategyAllocation(resp) {
            const strategyConfigs = [];
            for (let [strategyUri, allocation] of Object.entries(resp)) {
                const strategyName = strategyUri.split('?')[0];
                const name = strategyName; //XXX
                const params = {};
                for (let param of strategyUri.split('?')[1].split('&')) {
                    let key = param.split('=')[0];
                    let val = param.split('=')[1];
                    params[key] = val;
                }
                const options = JSON.parse(
                    JSON.stringify(
                        this.availableStrategies[strategyName].options
                    )
                );
                for (let option of Object.values(options)) {
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
        onStrategySelection() {
            let strategyDef = this.availableStrategies[this.activeStrategyConfig.strategy].options;
            let options = JSON.parse(JSON.stringify(strategyDef));
            for (let option of Object.values(options)) {
                option.default = option.value;
            }
            this.activeStrategyConfig.options = options;
        },
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
            //this.existingStrategies.push(newStrategyConfig);
            this.activeStrategyConfig = newStrategyConfig;
            this.renderView();
        },
        onRevertStrategy () {
            //find the strategy name in originalStrategies, if exists set it to original
            let name = this.activeStrategyConfig.qualifiedName;
            for (let value of Object.values(this.originalStrategies)) {
                if (value.qualifiedName === name) {
                    this.activeStrategyConfig.options = JSON.parse(JSON.stringify(value.options));
                    this.activeStrategyConfig.strategy = value.strategy;
                    this.renderView();
                }
            }
        },
        onRemoveStrategy () {
            let name = this.activeStrategyConfig.qualifiedName;
            // remove from existing strategies
            this.existingStrategies = this.existingStrategies.filter(
                strategy => strategy.qualifiedName != name).map(
                strategy => toRaw(strategy));
            //destroy chart
            //this.chart.destroy();
            //this.chart = null;
            this.activeStrategyConfig = {};
            this.renderView();
        },
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
            if (this.chart == null) {
                let elemId = 'allocation-allocator-pie';
                let ctx = document.getElementById(elemId).getContext('2d');
                let chart = new Chart(ctx, {
                    type: 'pie',
                    data: { labels: labelDisp, datasets: [{label: label, data: data}]},
                    options: {animations: false, responsive: true, maintainAspectRatio: false,
                        layout: {padding: {top: 10, bottom: 10, left: 10, right: 10}}},
                });
                chart.legend.options.position = 'right';
                chart.legend.options.align = 'start';
                chart.legend.options.labels.fontSize = 10;
                chart.update();
                this.chart = chart;
                chart.options.onClick = (evt, item) => {
                    if (!this.paramsVerified) return;
                    if (item.length === 0) return;
                    const label = item[0]._model.label;
                    if (label == 'free') { this.activeStrategyConfig = {};
                    } else { this.activeStrategyConfig = this.existingStrategies.filter(strategy => strategy.name === label)[0]; }
                    this.renderView();
                }
            }
            this.chart.data.datasets[0].data = data;
            this.chart.data.datasets[0].label = label;
            this.chart.data.labels = labelDisp;
            //this.chart.data.datasets[0].data = this.existingStrategies.map(strategy => strategy.allocation);
            //this.chart.data.datasets[0].label = this.existingStrategies.map(strategy => strategy.name);
            //this.chart.data.labels = this.existingStrategies.map(strategy => strategy.name);
            if (this.focus()){
                const labelIndex = this.chart.data.datasets[0].label.indexOf(this.activeStrategyConfig.qualifiedName);
                var name = this.activeStrategyConfig.name;
                if (name.length > 10)
                    name =  name.slice(0, 10) + '...';
                this.chart.data.labels[labelIndex] = name;
                const freeIndex = this.chart.data.labels.indexOf('free');
                this.chart.data.datasets[0].data[labelIndex] = this.activeStrategyConfig.allocation;
                this.chart.data.datasets[0].data[freeIndex] = this.freeAllocation;
                this.chart.update();
                this.chart.getDatasetMeta(0).data[freeIndex]._model.outerRadius -= 10;
                this.chart.getDatasetMeta(0).data[labelIndex]._model.outerRadius += 10;
            } else {
                const freeIndex = this.chart.data.labels.indexOf('free');
                this.chart.update();
                this.chart.getDatasetMeta(0).data[freeIndex]._model.outerRadius -= 10;
            }
        },
        updateFreeAllocation() {
            let totAlloc = this.existingStrategies.reduce((a, b) => a + b.allocation, 0);
            this.freeAllocation = 100 - totAlloc;
        },
        saveStrategyAllocation() {
            const allocCopy = JSON.parse(JSON.stringify(this.existingStrategies));
            this.originalStrategies = allocCopy;
        }
    },
    computed: {
        allocSliderValue: {
            get: function () {
                this.updateFreeAllocation();
                var free = document.querySelector(':root');
                free.style.setProperty('--slider-blocked-portion', (this.freeAllocation + this.activeStrategyConfig.allocation) + '%');
                return this.activeStrategyConfig.allocation;
            },
            set: function(value) {
                //free allocation is 100 - sum of all other allocations
                if (!this.focus()) return;
                this.activeStrategyConfig.allocation = parseInt(value);
                let totAlloc = Object.values(this.existingStrategies
                    ).reduce((a, b) => a + b.allocation, 0);
                if (totAlloc > 100) { this.activeStrategyConfig.allocation = 100 - totAlloc + this.activeStrategyConfig.allocation; }
                this.renderView();
                return this.activeStrategyConfig.allocation;
            }
        },
        nameValue: {
            get: function () {
                if (!this.focus()) return '';
                if (this.paramsVerified) return this.activeStrategyConfig.name;
                else return this.activeStrategyConfig.name;
            },
            set: function (value) {
                if (!this.focus()) return;
                this.activeStrategyConfig.name = value;
                let sMatch = this.existingStrategies.filter(strategy => strategy.name === value);
                if ((sMatch.length > 0 && sMatch[0] != this.activeStrategyConfig) || sMatch.length > 1) {
                    this.paramsVerified = false;
                    //find the name input element and set background color to red
                    document.getElementById('allocation-allocator-name').style.backgroundColor = 'hsl(0, 80%, 70%)';
                } else {
                    this.paramsVerified = true;
                    this.renderView();
                    //find the name input element and set background color to whatever it was before
                    document.getElementById('allocation-allocator-name').style.backgroundColor = '';
                }
            }
        },
    },
    mounted () {
        this.update();
    },
};

export const AllocationPieView = {
    template: `
    `
};

export const EmptyView = {
    template: `
    `
};

app.component('allocatorview', AllocatorView);
app.component('allocationpieview', AllocationPieView);
app.component('emptyview', EmptyView);
