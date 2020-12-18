import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
import FlowChart from "flowchart.js";
import { Flow } from "../../api/Flows";

@customElement("ak-flow-diagram")
export class FlowDiagram extends LitElement {

    @property()
    flowSlug?: string;

    createRenderRoot(): Element | ShadowRoot {
        return this;
    }

    render(): TemplateResult {
        Flow.diagram(this.flowSlug!).then((data) => {
            var diagram = FlowChart.parse(data);
            diagram.drawSVG(this, {
                'font-color': 'white',
                'line-color': 'white',
                'element-color': 'white',
            });
        })
        return html``;
    }

}
