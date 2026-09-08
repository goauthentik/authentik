import "#elements/EmptyState";

import { AKRefreshEvent } from "#common/events";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";
import Styles from "#elements/Diagram/ak-diagram.css";
import { EmptyState } from "#elements/EmptyState";
import MermaidStyles from "#elements/mermaid/mermaid.css";
import { loadMermaid } from "#elements/mermaid/utils";
import { SlottedTemplateResult } from "#elements/types";

import { CSSResult, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

@customElement("ak-diagram")
export class Diagram extends AKElement {
    static styles: CSSResult[] = [MermaidStyles, Styles];

    #diagram = "";

    public get diagram(): string {
        return this.#diagram || this.textContent.trim() || "";
    }

    @property({ attribute: false, useDefault: true })
    public set diagram(value: string) {
        this.#diagram = value.trim();
    }

    @property({ attribute: false })
    public diagramUpdatedCallback?: (diagram: Diagram) => void;

    @listen(AKRefreshEvent, {
        target: window,
    })
    protected syncDiagramContent = (): void => {
        if (!this.textContent) return;
        this.diagram = this.textContent;
    };

    loadingPlaceholder: EmptyState;

    // Mermaid has its own internal renderer with its own task queue. We need to keep the most
    // recent version Mermaid produces as a state, so when mermaid completes it triggers a re-render
    // of the whole diagram.
    @state()
    protected renderedSVG: SlottedTemplateResult = null;

    protected generation = 0;

    protected mermaidRenderFrameId = -1;

    constructor() {
        super();
        this.loadingPlaceholder = new EmptyState();
        this.loadingPlaceholder.loading = true;
    }

    protected firstUpdated(changedProperties: PropertyValues<this>): void {
        super.firstUpdated(changedProperties);
        this.syncDiagramContent();
    }

    protected override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);
        if (changedProperties.has("diagram") || changedProperties.has("activeTheme")) {
            cancelAnimationFrame(this.mermaidRenderFrameId);
            this.mermaidRenderFrameId = requestAnimationFrame(() =>
                this.#renderMermaid().catch((error: unknown) => {
                    console.warn("Could not render diagram:", error);
                }),
            );
        }
    }

    async #renderMermaid(): Promise<void> {
        this.generation = this.generation + 1;

        if (!this.diagram) {
            this.renderedSVG = null;
            return;
        }

        const generation = this.generation;
        const overridden = () => generation !== this.generation;

        const mermaid = await loadMermaid(this.activeTheme);
        // Something else updated the render while we were waiting
        if (overridden()) return;

        const { svg, bindFunctions } = await mermaid.render(
            `mermaid-svg-${this.localName}`,
            this.diagram,
        );
        if (overridden()) return;

        this.renderedSVG = unsafeHTML(svg);

        // Hand control back to Lit's scheduling thread. We do this here so that when
        // `bindFunctions()` and `diagramUpdated()` are called, the diagram is already present.
        await this.updateComplete;
        if (overridden()) return;

        bindFunctions?.(this.renderRoot as HTMLElement);
        this.diagramUpdated();
    }

    /**
     * Callback to be called when the *diagram* (not the component) has been updated. This is called
     * after the diagram has been rendered, and can be used to fill in details using the SVG
     * ForeignObject protocol.
     *
     * Meant to let clients fill in details using the SVG ForeignObject protocol. The diagram is
     * completely torn down and replaced every time. Whatever you put here must fully render and
     * never assume anything from a previous pass is still present.
     */
    protected diagramUpdated(): void {
        this.diagramUpdatedCallback?.call(this.diagramUpdatedCallback, this);
    }

    protected override render(): SlottedTemplateResult {
        return this.renderedSVG ?? this.loadingPlaceholder;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-diagram": Diagram;
    }
}
