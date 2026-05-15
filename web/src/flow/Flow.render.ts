import "#elements/locale/ak-locale-select";
import "#flow/inspector/FlowInspectorButton";
import "#elements/LoadingOverlay";
import "#flow/FlowExecutor";

import { light } from "#elements/directives/light";
import { ThemedImage } from "#elements/utils/images";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { guard } from "lit/directives/guard.js";

/*
 * The render function for Flow.

 */

type IframeType = ReturnType<typeof guard>;
type HeaderType = ReturnType<typeof ThemedImage>;

interface FlowRenderProps {
    loading: boolean;
    layout: string;
    header: HeaderType;
    salesmark: TemplateResult;
    iframe: IframeType;
    slug: string;
}

export function render({ header, layout, loading, salesmark, slug, iframe }: FlowRenderProps) {
    return html` <div part="flow">
        ${iframe}
        <header part="header">
            <ak-locale-select
                part="locale-select"
                exportparts="label:locale-select-label,select:locale-select-select"
                class="pf-m-dark"
            ></ak-locale-select>
            <ak-flow-inspector-button></ak-flow-inspector-button>
        </header>
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
            <h4 class="ak-v2-c-salesmark">${salesmark}</h4>
        </footer>
    </div>`;
}

export default render;
