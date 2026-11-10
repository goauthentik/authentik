import "#elements/Expand";
import "#elements/Label";
import "#elements/Spinner";
import "#elements/ak-attribute-view";
import { renderDefault } from "./EventInfo.shared";
import Styles from "./EventInfo.styles";
import * as R from "./renderers/index";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFTable from "@patternfly/patternfly/components/Table/table.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFSplit from "@patternfly/patternfly/layouts/Split/split.css";

import { PFSize } from "#common/enums";
import { EventWithContext } from "#common/events";

import { AKElement } from "#elements/Base";

import { EventActions } from "@goauthentik/api";

import { match, P } from "ts-pattern";

import { CSSResult, html, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

export class EventInfo extends AKElement {
    @property({ attribute: false })
    event!: EventWithContext;

    static styles: CSSResult[] = [
        PFButton,
        PFFlex,
        PFCard,
        PFTable,
        PFList,
        PFSplit,
        PFDescriptionList,
        Styles,
    ];

    // It's commonplace not to put the return type on most functions in Typescript. In this case,
    // however, putting this return type creates a virtuous check of *all* the subrenderers to
    // ensure that all of them return what we're expecting.

    render(): TemplateResult {
        const { event } = this;

        if (!event) {
            return html`<ak-spinner size=${PFSize.Medium}></ak-spinner>`;
        }

        const EventActionsModelChanged = P.union(
            EventActions.ModelCreated,
            EventActions.ModelUpdated,
            EventActions.ModelDeleted,
        );

        const EventActionsConfigurationWarning = P.union(
            EventActions.ConfigurationWarning,
            EventActions.ConfigurationError,
        );

        // prettier-ignore
        return match(event?.action)
            .with(EventActionsModelChanged, () => R.renderModelChanged(event))
            .with(EventActions.AuthorizeApplication, () => R.renderAuthorizeApplication(event))
            .with(EventActions.EmailSent, () => R.renderEmailSent(event))
            .with(EventActions.SecretView, () => R.renderSecretView(event))
            .with(EventActions.SystemException, () => R.renderSystemException(event))
            .with(EventActions.PropertyMappingException, () => R.renderPropertyMappingException(event))
            .with(EventActions.PolicyException, () => R.renderPolicyException(event))
            .with(EventActions.PolicyExecution, () => R.renderPolicyExecution(event))
            .with(EventActionsConfigurationWarning, () => R.renderConfigurationEvent(event))
            .with(EventActions.UpdateAvailable, () => R.renderUpdateAvailable(event))
            // Action types which typically don't record any extra context.
            // If context is not empty, we fall to the default response.
            .with(EventActions.Login, () => R.renderLogin(event))
            .with(EventActions.LoginFailed, () => R.renderLoginFailed(event))
            .with(EventActions.Logout, () => R.renderLogout(event))
            .with(EventActions.SystemTaskException, () => R.renderSystemTaskException(event))
            .otherwise(() => renderDefault(event));
    }
}
