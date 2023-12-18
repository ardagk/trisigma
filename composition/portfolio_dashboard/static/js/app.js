import { createApp, ref } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js'
import  'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.js'


export const pm_id = 200000001;


let activeFacet = ref('allocation');

const switchFacet = function (target) {
    activeFacet.value = target;
};

export const navitem = {
    props: ['title', 'target'],
    template: '<button class="navitem" @click="switchFacet">{{ title }}</button>',
    methods: {
        switchFacet() {
            switchFacet(this.target);
        },
    },
};

export const navbar = {
    template: `<div class="navbar"><slot></slot></div>`,
};

export const facetframe = {
    template: '<div class="facetframe"><slot></slot></div>',
};

export const facet = {
    props: ['name'],
    template: '<div class="facet" v-if="isActive"><slot></slot></div>',
    computed: {
        isActive() {
            return this.name === activeFacet.value;
        },
    },
};

export const optbar = {
    template: '<div class="optbar"><slot></slot></div>',
};

export const contentgrid = {
    props: ['grid'],
    template: `
    <div class="contentgrid-wrapper">
        <div :class="grid"><slot></slot></div>
    </div>
    `,
};

export const tab = {
    props: ['region'],
    template: `
    <div class="tab" :style="cssGrid">
        <div class="tab-bar"></div>
        <div class="tab-content">
            <slot></slot>
        </div>
    </div>`,
    computed: {
        cssGrid() {
            return { 'grid-area': this.region };
        },
    },
};



export const DropdownField = {
    template: `
        <select class="dropdown-field" @change="this.$emit('update', $event.target.value)" :value="val">
            <option v-for="option in options">
            {{ option }}
            </option>
        </select>
    `,
    props: ['options', 'value'],
    data() { return { val: '' }; },
    mounted() {
        if (this.value !== undefined) this.val = this.value;
        else this.val = this.options[0];
    } 
};
export const TextField = {
    template: `
        <input ref="input" class="text-field" type="text" v-model="text" />
    `,
    props: ['placeholder', 'banned', 'value'],
    data() {return {textValue: ''};},
    computed: {
        text: {
            get() {
                return this.textValue;
            },
            set(value) {
                if (this.banned !== undefined && this.banned.includes(value)){
                    this.$refs.input.setCustomValidity('invalid');
                } else {
                    this.$refs.input.setCustomValidity('');
                }
                this.$emit('update', value);
                this.textValue = value;
            },
        },
    },
    mounted() {
        if (this.value !== undefined) this.textValue = this.value;
        else this.textValue = '';
    }
};
export const CheckboxField = {
    template: `
        <input class="checkbox-field" type="checkbox" @change="this.$emit('update', $event.target.checked)" />
    `,
    props: ['checked'],
};
export const SliderField = {
    template: `
        <input ref="theSlider" class="slider-field" type="range" :min="min" :max="max" :step="step" v-model="cValue" :style="style"/>
    `,
    data() { return { val: 0, upperLimit: 0}; },
    props: ['min', 'max', 'step', 'value', 'available', 'style'],
    methods: {
        updateRestriction() {
            const slider = this.$refs.theSlider;
            slider.style.background = `linear-gradient(to right, white ${this.upperLimit}%, gray ${this.upperLimit}%)`;
            this.val = Math.min(this.upperLimit, this.val);
            slider.value = this.val;
        }
    },
    computed: {
        cValue: {
            get() { return this.val; },
            set(value) {
                this.val = Math.min(this.upperLimit, value);
                this.$refs.theSlider.value = this.val;
                this.$emit('update', this.val);
            }
        }
    },
    updated() {
        this.updateRestriction(); 
    },
    mounted() {
        if (this.available === undefined) this.upperLimit = 100;
        else this.upperLimit = this.available / this.max * 100;
        if (this.value !== undefined) this.val = this.value;
        else this.val = this.min;
        this.updateRestriction();
    },
}
export const ModelForm = {
    template: `
        <div class="form-option-wrapper" v-for="(option, label, index) in options" :key="index">
                <label :style="labelStyle">{{ label }}</label>
                <template v-if="option.type === 'range'">
                    <slider-field :style="fieldStyle" :min="option.min" :max="option.max" :step="option.step"\
                        :value="option.value" :available="option.available" @update="onChange(label, $event)"/>
                </template>
                <template v-else-if="option.type === 'dropdown'">
                    <dropdown-field :style="fieldStyle" :value="option.value" :options="option.options" @update="onChange(label, $event)"/>
                </template>
                <template v-else-if="option.type === 'checkbox'">
                    <checkbox-field :style="fieldStyle" :checked="option.value" @update="onChange(label, $event)"/>
                </template>
                <template v-else-if="option.type === 'text'">
                    <text-field :style="fieldStyle" :value="option.value" :placeholder="option.placeholder"\
                     :banned="option.banned" @update="onChange(label, $event)"/>
                </template>
        </div>
        `,
    data() {
         return {
            labelStyle: "justify-content: flex-start; flex-basis: 50%",
            fieldStyle: "justify-content: flex-end; flex-basis: 50%",
            data: {},
          }; 
        },
    props: ['options'],
    emits: ['update'],
    methods: {
        onChange(key, value) {
            this.data[key] = value;
            this.$emit('update', this.data);
        },
    },
    updated() {
        for (const [key, value] of Object.entries(this.options))
            this.data[key] = value.value;
    },
    mounted() {
        for (const [key, value] of Object.entries(this.options))
            this.data[key] = value.value;
    }
}

export const app = createApp({});
app.component('dropdown-field', DropdownField);
app.component('text-field', TextField);
app.component('checkbox-field', CheckboxField);
app.component('slider-field', SliderField);
app.component('model-form', ModelForm);
app.component('navitem', navitem);
app.component('navbar', navbar);
app.component('facet', facet);
app.component('facetframe', facetframe);
app.component('optbar', optbar);
app.component('contentgrid', contentgrid);
app.component('tab', tab);


