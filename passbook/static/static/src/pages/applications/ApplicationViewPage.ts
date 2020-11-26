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
                        <img
                            class="pf-icon"
                            src="${this.application?.meta_icon || ""}"
                        />
                        ${this.application?.name}
                    </h1>
                    <p>${this.application?.meta_publisher}</p>
                </div>
            </section>
            <section class="pf-c-page__main-section pf-m-no-padding-mobile">
                <pb-tabs>
                    <div slot="page-1" tab-title="Users">users</div>
                    <div slot="page-2" tab-title="Containers">foo</div>
                </pb-tabs>
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
