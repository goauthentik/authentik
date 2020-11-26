import { customElement, html, LitElement, property } from "lit-element";
import { Application } from "../../api/application";
import { COMMON_STYLES } from "../../common/styles";

@customElement("pb-application-view")
export class ApplicationViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: string; }) {
        this.applicationSlug = value.slug;
    }

    @property()
    set applicationSlug(value: string) {
        Application.get(value).then(app => this.application = app);
    }

    @property()
    application?: Application;

    static get styles() {
        return COMMON_STYLES;
    }

    render() {
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        <i class="pf-icon pf-icon-applications"></i>
                        ${this.application?.name}
                    </h1>
                    <p>External Applications which use passbook as Identity-Provider, utilizing protocols like OAuth2 and SAML.</p>
                </div>
            </section>
            <section class="pf-c-page__main-section pf-m-no-padding-mobile">
                <div class="pf-c-card">
                    <div class="pf-c-toolbar">
                        <div class="pf-c-toolbar__content">
                            <h1>test</h1>

                            <span>${this.applicationSlug}</span>
                        </div>
                    </div>
                </div>
            </section>`;
    }

}
