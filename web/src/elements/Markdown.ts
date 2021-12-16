import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import AKGlobal from "../authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";

@customElement("ak-markdown")
export class Markdown extends LitElement {
    @property()
    md?: string;

    static get styles(): CSSResult[] {
        return [PFList, PFContent, AKGlobal];
    }

    render(): TemplateResult {
        if (!this.md) {
            return html``;
        }
        const finalHTML = this.md.replace("<ul>", `<ul class="pf-c-list">`);
        return html`${unsafeHTML(finalHTML)}`;
    }
}
