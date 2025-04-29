import { ApplicationWizardStep } from "@goauthentik/admin/applications/wizard/ApplicationWizardStep.js";
import "@goauthentik/admin/applications/wizard/ak-wizard-title.js";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-slug-input";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { type WizardButton } from "@goauthentik/components/ak-wizard/types";
import "@goauthentik/elements/ak-table/ak-select-table.js";
import { SelectTable } from "@goauthentik/elements/ak-table/ak-select-table.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { P, match } from "ts-pattern";

import { msg, str } from "@lit/localize";
import { css, html } from "lit";
import { customElement, query } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { makeEditButton } from "./bindings/ak-application-wizard-bindings-edit-button.js";
import "./bindings/ak-application-wizard-bindings-toolbar.js";

const COLUMNS = [
    [msg("Order"), "order"],
    [msg("Binding")],
    [msg("Enabled"), "enabled"],
    [msg("Timeout"), "timeout"],
    [msg("Actions")],
];

@customElement("ak-application-wizard-bindings-step")
export class ApplicationWizardBindingsStep extends ApplicationWizardStep {
    label = msg("Configure Bindings");

    get buttons(): WizardButton[] {
        return [
            { kind: "next", destination: "submit" },
            { kind: "back", destination: "provider" },
            { kind: "cancel" },
        ];
    }

    @query("ak-select-table")
    selectTable!: SelectTable;

    static get styles() {
        return super.styles.concat(
            PFCard,
            css`
                .pf-c-card {
                    margin-top: 1em;
                }
            `,
        );
    }

    get bindingsAsColumns() {
        return this.wizard.bindings.map((binding, index) => {
            const { order, enabled, timeout } = binding;
            const isSet = P.union(P.string.minLength(1), P.number);
            const policy = match(binding)
                .with({ policy: isSet }, (v) => msg(str`Policy ${v.policyObj?.name}`))
                .with({ group: isSet }, (v) => msg(str`Group ${v.groupObj?.name}`))
                .with({ user: isSet }, (v) => msg(str`User ${v.userObj?.name}`))
                .otherwise(() => msg("-"));

            return {
                key: index,
                content: [
                    order,
                    policy,
                    html`<ak-status-label type="warning" ?good=${enabled}></ak-status-label>`,
                    timeout,
                    makeEditButton(msg("Edit"), index, (ev: CustomEvent<number>) =>
                        this.onBindingEvent(ev.detail),
                    ),
                ],
            };
        });
    }

    // TODO Fix those dispatches so that we handle them here, in this component, and *choose* how to
    // forward them.
    onBindingEvent(binding?: number) {
        this.handleUpdate({ currentBinding: binding ?? -1 }, "edit-binding", {
            enable: "edit-binding",
        });
    }

    onDeleteBindings() {
        const toDelete = this.selectTable
            .json()
            .map((i) => (typeof i === "string" ? parseInt(i, 10) : i));
        const bindings = this.wizard.bindings.filter((binding, index) => !toDelete.includes(index));
        this.handleUpdate({ bindings }, "bindings");
    }

    renderEmptyCollection() {
        return html`<ak-wizard-title
                >${msg("Configure Policy/User/Group Bindings")}</ak-wizard-title
            >
            <h6 class="pf-c-title pf-m-md">
                ${msg("These policies control which users can access this application.")}
            </h6>
            <div class="pf-c-card">
                <ak-application-wizard-bindings-toolbar
                    @clickNew=${() => this.onBindingEvent()}
                    @clickDelete=${() => this.onDeleteBindings()}
                ></ak-application-wizard-bindings-toolbar>
                <ak-select-table
                    multiple
                    id="bindings"
                    order="order"
                    .columns=${COLUMNS}
                    .content=${[]}
                ></ak-select-table>
                <ak-empty-state icon="pf-icon-module"
                    ><span slot="header">${msg("No bound policies.")} </span>
                    <div slot="body">${msg("No policies are currently bound to this object.")}</div>
                    <div slot="primary">
                        <button
                            @click=${() => this.onBindingEvent()}
                            class="pf-c-button pf-m-primary"
                        >
                            ${msg("Bind policy/group/user")}
                        </button>
                    </div>
                </ak-empty-state>
            </div>`;
    }

    renderCollection() {
        return html` <ak-wizard-title>${msg("Configure Policy Bindings")}</ak-wizard-title>
            <h6 class="pf-c-title pf-m-md">
                ${msg("These policies control which users can access this application.")}
            </h6>
            <ak-application-wizard-bindings-toolbar
                @clickNew=${() => this.onBindingEvent()}
                @clickDelete=${() => this.onDeleteBindings()}
                ?can-delete=${this.wizard.bindings.length > 0}
            ></ak-application-wizard-bindings-toolbar>
            <ak-select-table
                multiple
                id="bindings"
                order="order"
                .columns=${COLUMNS}
                .content=${this.bindingsAsColumns}
            ></ak-select-table>`;
    }

    renderMain() {
        if ((this.wizard.bindings ?? []).length === 0) {
            return this.renderEmptyCollection();
        }
        return this.renderCollection();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-applications-step": ApplicationWizardBindingsStep;
    }
}
