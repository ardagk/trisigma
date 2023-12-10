export function createLineChart(elemId, label, time, data){
    const rootStyles = getComputedStyle(document.documentElement);
    const bgColor = rootStyles.getPropertyValue('--line-chart-background-color');
    const borderColor = rootStyles.getPropertyValue('--line-chart-border-color');
    const fontColor = rootStyles.getPropertyValue('--line-chart-font-color');
    let ctx = document.getElementById(elemId).getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: time,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: bgColor,
                borderColor: borderColor,
                color: fontColor,
            }]
        },
        options: {responsive: true, maintainAspectRatio: false}
    });
}

export function createTable(elemId, config) {
    const o = {
        records: config.records,
        render: function () {
            //find the element by elemId and create a table inside it
            const main = document.getElementById(elemId);
            //clear the element
            while (main.firstChild) {
                main.removeChild(main.firstChild);
            }
            main.classList.add('generic-table-wrapper');
            const scrollable = main.appendChild(document.createElement('div'));
            scrollable.classList.add('generic-table-scrollable');
            
            const table = scrollable.appendChild(document.createElement('table'));
            table.classList.add('generic-table');
            //config.records is a list of objects with the same keys, create the header row
            const tr = table.appendChild(document.createElement('tr'));
            tr.classList.add('generic-table-header');
            const keys = Object.keys(this.records[0]);
            for (let i = 0; i < keys.length; i++) {
                const header = table.appendChild(document.createElement('th'));
                header.classList.add('generic-table-header-cell');
                header.innerText = keys[i];
            }
            for (let i = 0; i < this.records.length; i++) {
                const row = table.appendChild(document.createElement('tr'));
                row.classList.add('generic-table-row');
                for (let j = 0; j < keys.length; j++) {
                    let td = row.appendChild(document.createElement('td'));
                    td.classList.add('generic-table-row-cell');
                    td.innerText = this.records[i][keys[j]];
                }
            }
        },
        update: function () {
            o.render();
        }
    }
    o.render();
    return o;
}