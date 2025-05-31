import { AKElement } from "@goauthentik/elements/Base";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import DjangoQL from "@mrmarble/djangoql-completion";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import Completion from "@mrmarble/djangoql-completion/dist/index.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-search-ql")
export class QLSearch extends AKElement {
    @property()
    value?: string;

    @query("[name=search]")
    searchElement?: HTMLTextAreaElement;

    ql?: DjangoQL;

    set apiResponse(value: PaginatedResponse<unknown> | undefined) {
        if (!value || !value.autocomplete) {
            return;
        }
        if (this.ql) {
            this.ql.loadIntrospections(value.autocomplete);
            return;
        }
        if (!this.searchElement) {
            return;
        }
        this.ql = new DjangoQL({
            introspections: value.autocomplete,
            selector: this.searchElement,
            autoResize: false,
            onSubmit: (value: string) => {
                if (!this.onSearch) return;
                this.onSearch(value);
            },
        });
        // document.adoptedStyleSheets = [
        //     ...document.adoptedStyleSheets,
        //     Completion,
        // ];
    }

    @property()
    onSearch?: (value: string) => void;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFToolbar,
            PFInputGroup,
            PFFormControl,
            Completion,
            css`
                ::-webkit-search-cancel-button {
                    display: none;
                }
                .ql.pf-c-form-control {
                    font-family: monospace;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`<textarea
            class="pf-c-form-control ql"
            name="search"
            placeholder=${msg("Search...")}
            spellcheck="false"
        >
${ifDefined(this.value)}</textarea
        >`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-ql": QLSearch;
    }
}
