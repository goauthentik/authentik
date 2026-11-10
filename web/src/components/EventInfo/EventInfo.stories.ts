import "#components/ak-event-info";
import { EventInfoFixture, fixtures } from "./EventInfo.fixtures";

import { createPaginatedResponse } from "#common/api/responses";

import { FlowFromJSON, FlowsApi } from "@goauthentik/api";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

type Args = { fixture: EventInfoFixture };

const metadata: Meta<Args> = {
    title: "Components/<ak-event-info>",
    component: "ak-event-info",
    argTypes: {
        fixture: { control: "select", options: Object.keys(fixtures) },
    },
    render: ({ fixture }) =>
        html`<div style="padding: 1rem">
            <ak-event-info .event=${fixtures[fixture]}></ak-event-info>
        </div>`,
};

export default metadata;

const story = (fixture: EventInfoFixture): StoryObj<Args> => ({ args: { fixture } });

export const ModelCreated = story("modelCreated");
export const ModelUpdated = story("modelUpdated");
export const ModelUpdatedM2M = story("modelUpdatedM2M");
export const ModelDeleted = story("modelDeleted");
export const EmailSent = story("emailSent");
export const SecretView = story("secretView");
export const SystemException = story("systemException");
export const SystemTaskException = story("systemTaskException");
export const ConfigurationWarning = story("configurationWarning");
export const ConfigurationError = story("configurationError");
export const UpdateAvailable = story("updateAvailable");
export const Login = story("login");
export const LoginWithSource = story("loginWithSource");
export const LoginFailed = story("loginFailed");
export const Logout = story("logout");
export const PropertyMappingException = story("propertyMappingException");
export const PolicyException = story("policyException");
export const PolicyExecution = story("policyExecution");
export const PolicyExecutionDryRun = story("policyExecutionDryRun");
export const Unhandled = story("unhandled");

export const AuthorizeApplication: StoryObj<Args> = {
    ...story("authorizeApplication"),
    // The renderer looks up the flow by UUID; stub so the story has no server dependency.
    beforeEach: () => {
        const original = FlowsApi.prototype.flowsInstancesList;

        FlowsApi.prototype.flowsInstancesList = async () => ({
            ...createPaginatedResponse([
                FlowFromJSON({ slug: "default-provider-authorization", name: "Authorize" }),
            ]),
            autocomplete: {},
        });

        return () => {
            FlowsApi.prototype.flowsInstancesList = original;
        };
    },
};

export const Loading: StoryObj<Args> = {
    render: () => html`<ak-event-info></ak-event-info>`,
};
