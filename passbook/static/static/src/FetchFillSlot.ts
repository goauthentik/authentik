import { LitElement, html, customElement, property } from 'lit-element';

interface ComparisonHash {
    [key: string]: (a: any, b: any) => boolean
}

@customElement("fetch-fill-slot")
export class FetchFillSlot extends LitElement {

    @property()
    url: string = "";

    @property()
    key: string = "";

    @property()
    value: string = "";

    comparison(slotName: string) {
        let comparisonOperatorsHash = <ComparisonHash>{
            '<': function (a: any, b: any) { return a < b; },
            '>': function (a: any, b: any) { return a > b; },
            '>=': function (a: any, b: any) { return a >= b; },
            '<=': function (a: any, b: any) { return a <= b; },
            '==': function (a: any, b: any) { return a == b; },
            '!=': function (a: any, b: any) { return a != b; },
            '===': function (a: any, b: any) { return a === b; },
            '!==': function (a: any, b: any) { return a !== b; },
        };
        const tokens = slotName.split(" ");
        if (tokens.length < 3) {
            throw new Error("nah");
        }
        let a: any = tokens[0];
        if (a === "value") {
            a = this.value;
        } else {
            a = parseInt(a, 10);
        }
        let b: any = tokens[2];
        if (b === "value") {
            b = this.value;
        } else {
            b = parseInt(b, 10);
        }
        const comp = tokens[1];
        if (!(comp in comparisonOperatorsHash)) {
            throw new Error("Invalid comparison")
        }
        return comparisonOperatorsHash[comp](a, b);
    }

    firstUpdated() {
        fetch(this.url).then(r => r.json()).then(r => r[this.key]).then(r => this.value = r);
    }

    render() {
        if (this.value === undefined) {
            return html`<slot></slot>`;
        }
        let selectedSlot = "";
        this.querySelectorAll("[slot]").forEach(slot => {
            const comp = slot.getAttribute("slot")!;
            if (this.comparison(comp)) {
                selectedSlot = comp;
            }
        });
        this.querySelectorAll("[data-value]").forEach(dv => {
            dv.textContent = this.value;
        });
        return html`<slot name=${selectedSlot}></slot>`;
    }
}
