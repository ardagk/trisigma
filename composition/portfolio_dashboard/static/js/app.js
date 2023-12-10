import { createApp, ref } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js'
import  'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.js'


export const pm_id = 200000001;


let activeFacet = ref('activity');

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

export const app = createApp({});
app.component('navitem', navitem);
app.component('navbar', navbar);
app.component('facet', facet);
app.component('facetframe', facetframe);
app.component('optbar', optbar);
app.component('contentgrid', contentgrid);
app.component('tab', tab);


