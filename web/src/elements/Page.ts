import { gettext } from "django";
import { LitElement } from "lit-element";
import { html, TemplateResult } from "lit-html";

export abstract class Page extends LitElement {
    abstract pageTitle(): string;
    abstract pageDescription(): string | undefined;
    abstract pageIcon(): string;

    abstract renderContent(): TemplateResult;

    render(): TemplateResult {
        const description = this.pageDescription();
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        <i class="${this.pageIcon()}"></i>
                        ${gettext(this.pageTitle())}
                    </h1>
                    ${description ? html`<p>${gettext(description)}</p>` : html``}
                </div>
            </section>
            ${this.renderContent()}`;
    }
}
