import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { AkFlowSearch } from "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { Meta } from "@storybook/web-components";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";

import { Flow, FlowsInstancesListDesignationEnum } from "@goauthentik/api";

const mockData = {
    pagination: {
        next: 0,
        previous: 0,
        count: 2,
        current: 1,
        total_pages: 1,
        start_index: 1,
        end_index: 2,
    },
    results: [
        {
            pk: "41468774-bef6-4ffb-b675-332d0d8c5d25",
            policybindingmodel_ptr_id: "0fb5b872-2734-44bd-ac7e-f23051481a83",
            name: "Authorize Application",
            slug: "default-provider-authorization-explicit-consent",
            title: "Redirecting to %(app)s",
            designation: "authorization",
            background: "/static/dist/assets/images/flow_background.jpg",
            stages: ["8adcdc74-0d3d-48a8-b628-38e3da4081e5"],
            policies: [],
            cache_count: 0,
            policy_engine_mode: "any",
            compatibility_mode: false,
            export_url:
                "/api/v3/flows/instances/default-provider-authorization-explicit-consent/export/",
            layout: "stacked",
            denied_action: "message_continue",
            authentication: "require_authenticated",
        },
        {
            pk: "89f57fd8-fd1e-42be-a5fd-abc13b19529b",
            policybindingmodel_ptr_id: "e8526408-c6ee-46e1-bbfe-a1d37c2c02c8",
            name: "Authorize Application",
            slug: "default-provider-authorization-implicit-consent",
            title: "Redirecting to %(app)s",
            designation: "authorization",
            background: "/static/dist/assets/images/flow_background.jpg",
            stages: [],
            policies: [],
            cache_count: 0,
            policy_engine_mode: "any",
            compatibility_mode: false,
            export_url:
                "/api/v3/flows/instances/default-provider-authorization-implicit-consent/export/",
            layout: "stacked",
            denied_action: "message_continue",
            authentication: "require_authenticated",
        },
    ],
};

const metadata: Meta<AkFlowSearch<Flow>> = {
    title: "Elements / Search Select / Flow",
    component: "ak-flow-search",
    parameters: {
        docs: {
            description: {
                component: "A Select Search for Authentication Flows",
            },
        },
        mockData: [
            {
                url: `${window.location.origin}/api/v3/flows/instances/?designation=authorization&ordering=slug`,
                method: "GET",
                status: 200,
                response: () => mockData,
            },
        ],
    },
};

export default metadata;

const container = (testItem: TemplateResult) => {
    return html` <div style="background: #fff; padding: 1.0rem;">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>
        ${testItem}
        <ul id="message-pad" style="margin-top: 1em; min-height: 5em;"></ul>
    </div>`;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const displayChange = (ev: any) => {
    document.getElementById("message-pad")!.innerText = `Value selected: ${JSON.stringify(
        ev.target.value,
        null,
        2,
    )}`;
};

export const Default = () =>
    container(
        html` <ak-form-element-horizontal
            label=${msg("Authorization flow")}
            ?required=${true}
            name="authorizationFlow"
        >
            <ak-flow-search
                flowType=${FlowsInstancesListDesignationEnum.Authorization}
                @input=${displayChange}
            ></ak-flow-search
        ></ak-form-element-horizontal>`,
    );

export const WithInitialValue = () =>
    container(
        html` <ak-form-element-horizontal
            label=${msg("Authorization flow")}
            ?required=${true}
            name="authorizationFlow"
        >
            <ak-flow-search
                flowType=${FlowsInstancesListDesignationEnum.Authorization}
                currentFlow="89f57fd8-fd1e-42be-a5fd-abc13b19529b"
                @input=${displayChange}
            ></ak-flow-search
        ></ak-form-element-horizontal>`,
    );
