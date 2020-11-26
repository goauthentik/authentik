import { css, customElement, html, LitElement, property } from "lit-element";
import { Application } from "../../api/application";
import { COMMON_STYLES } from "../../common/styles";

@customElement("pb-application-view")
export class ApplicationViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: string }) {
        this.applicationSlug = value.slug;
    }

    @property()
    set applicationSlug(value: string) {
        Application.get(value).then((app) => (this.application = app));
    }

    @property()
    application?: Application;

    static get styles() {
        return COMMON_STYLES.concat(
            css`
                img.pf-icon {
                    max-height: 24px;
                }
            `
        );
    }

    render() {
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        <img class="pf-icon" src="${this.application?.meta_icon || ""}" />
                        ${this.application?.name}
                    </h1>
                    <p>${this.application?.meta_publisher}</p>
                </div>
            </section>
            <pb-tabs>
                <section slot="page-1" tab-title="Users" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        users
                        <h1>test</h1>

                        <span>${this.application?.slug}</span>
                    </div>
                </section>
                <div slot="page-2" tab-title="Containers">
                    foo
                </div>
            </pb-tabs>`;
    }
}
