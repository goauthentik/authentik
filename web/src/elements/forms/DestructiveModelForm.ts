import "#elements/buttons/SpinnerButton/index";
import "#elements/entities/UsedByTable";
import "#elements/forms/FormGroup";
import "#elements/ak-table/ak-simple-table";
import PFList from "@patternfly/patternfly/components/List/list.css";

import { plural } from "#common/ui/locale/plurals";

import { RawContent } from "#elements/ak-table/ak-simple-table";
import { pluckEntityName } from "#elements/entities/names";
import { formatUsedByConsequence } from "#elements/entities/used-by";
import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { UsedBy } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

/**
 * A generic form for confirming the deletion of an object, with an optional list of objects that
 * use the object being deleted.
 */
@customElement("ak-destructive-model-form")
export class DestructiveModelForm<T extends object = object> extends ModelForm<T> {
    public static override verboseName = msg("Object");
    public static override verboseNamePlural = msg("Objects");
    public static override submitVerb = msg("Modify");
    public static override createLabel = msg("Review");
    public static override submittingVerb = msg("Modifying");

    public static styles: CSSResult[] = [...super.styles, PFList];

    protected override loadInstance(): Promise<T | null> {
        return Promise.resolve(this.instance);
    }

    @property({ attribute: false })
    public usedBy?: () => Promise<UsedBy[]>;

    @state()
    protected usedByList: UsedBy[] = [];

    /**
     * Get the display name for the object being deleted/updated.
     */
    protected formatDisplayName(): string {
        return pluckEntityName(this.instance) ?? msg("Unnamed object");
    }

    public override formatSubmitLabel(submitVerb?: string): string {
        const noun = this.verboseName;
        const verb = submitVerb ?? (this.constructor as typeof DestructiveModelForm).submitVerb;

        return noun
            ? msg(str`${verb} ${noun}`, {
                  id: "form.submit.verb-entity",
              })
            : verb;
    }

    protected override load(): Promise<void> {
        if (!this.usedBy) {
            this.usedByList = [];

            return Promise.resolve();
        }

        return this.usedBy().then((usedBy) => {
            this.usedByList = usedBy;
        });
    }

    protected renderUsedBySection(): SlottedTemplateResult {
        const { usedByList, verboseName } = this;

        return guard([usedByList, verboseName], () => {
            const displayName = this.formatDisplayName();

            // English never selects the CLDR "zero" category, so an empty list is checked first.
            const objectUsageMessage =
                usedByList.length === 0
                    ? msg(str`${verboseName} is not associated with any objects.`, {
                          id: "used-by.count.none",
                          desc: "No objects use this entity.",
                      })
                    : plural(usedByList.length, {
                          one: () =>
                              msg(
                                  str`${verboseName} is associated with ${usedByList.length} object.`,
                                  {
                                      id: "used-by.count.one",
                                      desc: "The first placeholder is the entity type, the second the number of objects using it.",
                                  },
                              ),
                          other: () =>
                              msg(
                                  str`${verboseName} is associated with ${usedByList.length} objects.`,
                                  {
                                      id: "used-by.count.other",
                                      desc: "The first placeholder is the entity type, the second the number of objects using it.",
                                  },
                              ),
                      });

            return html`<ak-form-group ?open=${usedByList.length} label=${objectUsageMessage}>
                <div
                    class="pf-m-monospace"
                    aria-description=${msg(
                        str`List of objects that are associated with this ${verboseName}.`,
                        {
                            id: "usedBy.description",
                        },
                    )}
                    slot="description"
                >
                    ${displayName}
                </div>
                <ak-simple-table
                    .columns=${[msg("Object Name"), msg("Consequence"), msg("ID")]}
                    .content=${usedByList.map((ub): RawContent[] => {
                        return [
                            pluckEntityName(ub) || msg("Unnamed"),
                            formatUsedByConsequence(ub),
                            html`<code>${ub.pk}</code>`,
                        ];
                    })}
                ></ak-simple-table>
            </ak-form-group>`;
        });
    }

    protected override renderForm(): SlottedTemplateResult {
        return this.renderUsedBySection();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-forms-delete": DestructiveModelForm;
    }
}
