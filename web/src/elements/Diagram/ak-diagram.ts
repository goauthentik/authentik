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
import { guard } from "lit-html/directives/guard.js";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";

@customElement("ak-diagram")
export class Diagram extends AKElement {
    static styles: CSSResult[] = [MermaidStyles, Styles];

    #diagram = "";
    @property({ attribute: false, useDefault: true })
    public get diagram(): string {
        return this.#diagram || this.textContent.trim() || "";
    }

    public set diagram(value: string) {
        const previous = this.#diagram;
        this.#diagram = value.trim();

        this.requestUpdate("diagram", previous);
    }

    @listen(AKRefreshEvent, {
        target: window,
    })
    protected syncDiagramContent = (): void => {
        if (!this.textContent) return;
        this.diagram = this.textContent;
    };

    loadingPlaceholder: EmptyState;

    constructor() {
        super();
        this.loadingPlaceholder = new EmptyState();
        this.loadingPlaceholder.loading = true;
    }

    protected firstUpdated(changedProperties: PropertyValues<this>): void {
        super.firstUpdated(changedProperties);
        this.syncDiagramContent();
    }

    protected renderMermaid(): Promise<SlottedTemplateResult> {
        return loadMermaid(this.activeTheme).then((mermaid) => {
            if (!this.diagram) {
                return null;
            }

            return mermaid.render(`mermaid-svg-${this.localName}`, this.diagram).then((result) => {
                result.bindFunctions?.(this.renderRoot as HTMLElement);

                return unsafeHTML(result.svg);
            });
        });
    }

    protected override render(): SlottedTemplateResult {
        const { diagram, loadingPlaceholder, activeTheme } = this;

        return guard([diagram, activeTheme], () => {
            if (!diagram) {
                return loadingPlaceholder;
            }

            return until(this.renderMermaid(), loadingPlaceholder);
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-diagram": Diagram;
    }
}
