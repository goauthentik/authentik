import { light } from "#elements/directives/light";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";

/*
 * The render function for Flow.

 */

interface FlowRenderProps {
    loading: boolean;
    layout: string;
    header: TemplateResult;
    slug: string;
}

export function render({ loading, layout, header, slug }: FlowRenderProps) {
    return html`<div class="ak-c-v2-flow" part="panel">
        <div class="ak-c-v2-flow__headroom" part="headroom"></div>
        <main
            data-layout=${layout}
            class="ak-c-v2-flow__card"
            aria-label=${msg("Authentication form")}
            part="main"
        >
            <div class="ak-c-v2-flow__header" part="branding">${header}</div>
            ${loading
                ? html`<ak-loading-overlay part="loading-overlay"></ak-loading-overlay>`
                : nothing}
            <div class="ak-c-v2-flow__executor" part="executor">
                ${light(html`<ak-flow-executor slug=${slug}></ak-flow-executor>`)}
            </div>
        </main>
        <footer
            aria-label=${msg("Site footer")}
            name="site-footer"
            part="footer"
            class="ak-v2-c-flow__footer"
        >
            <slot name="footer"></slot>
        </footer>
    </div>`;
}

export default render;
