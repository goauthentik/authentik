import "#elements/EmptyState";
import "#components/ak-radio-input";
import "#components/ak-slug-input";
import "#components/ak-status-label";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/ak-table/ak-select-table";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#admin/applications/wizard/steps/bindings/ak-application-wizard-bindings-toolbar";

import { SelectTable } from "#elements/ak-table/ak-select-table";

import { type WizardButton } from "#components/ak-wizard/shared";

import { ApplicationWizardStep } from "#admin/applications/wizard/ApplicationWizardStep";
import { makeEditButton } from "#admin/applications/wizard/steps/bindings/ak-application-wizard-bindings-edit-button";

import { match, P } from "ts-pattern";

import { msg, str } from "@lit/localize";
import { css, html } from "lit";
import { customElement, query } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

const COLUMNS = [
    [msg("Order"), "order"],
    [msg("Binding")],
    [msg("Enabled"), "enabled"],
    [msg("Timeout"), "timeout"],
    [msg("Actions"), null, msg("Row Actions")],
];

/**
 * @prop wizard - The current state of the application wizard, shared across all steps.
 */
@customElement("ak-application-wizard-bindings-step")
export class ApplicationWizardBindingsStep extends ApplicationWizardStep {
    label = msg("Configure Bindings");

    protected buttons: WizardButton[] = [
        { kind: "cancel" },
        { kind: "back", destination: "provider" },
        { kind: "next", destination: "submit" },
    ];

    @query("ak-select-table")
    selectTable!: SelectTable;

    static styles = [
        ...super.styles,
        PFCard,
        css`
            .pf-c-card {
                margin-top: 1em;
            }
        `,
    ];

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
        this.dispatchEvents({
            update: { currentBinding: binding ?? -1 },
            destination: "edit-binding",
            details: { enable: "edit-binding" },
        });
    }

    protected onDeleteBindings() {
        const toDelete = this.selectTable
            .toJSON()
            .map((i) => (typeof i === "string" ? parseInt(i, 10) : i));
        const bindings = this.wizard.bindings.filter((binding, index) => !toDelete.includes(index));

        return this.dispatchEvents({
            update: { bindings },
            destination: "bindings",
        });
    }

    protected renderEmptyCollection() {
        return html`<h3 class="pf-c-wizard__main-title">
                ${msg("Configure Policy/User/Group Bindings")}
            </h3>
            <h4 class="pf-c-title pf-m-md">
                ${msg("These policies control which users can access this application.")}
            </h4>
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
                    ><span>${msg("No bound policies.")}</span>
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

    protected renderCollection() {
        return html`<h3 class="pf-c-wizard__main-title">${msg("Configure Policy Bindings")}</h3>
            <h4 class="pf-c-title pf-m-md">
                ${msg("These policies control which users can access this application.")}
            </h4>
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

    protected renderMain() {
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-bindings-step": ApplicationWizardBindingsStep;
    }
}
