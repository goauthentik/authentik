import { LitFC } from "#elements/types";

import { AKFlowField, FlowFieldProps } from "#admin/common/ak-flow-search/AKFlowSearch";

import { FlowDesignationEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";

/**
 * The props a provider flow field accepts. Its name, flow type, and wording have defaults.
 */
export type ProviderFlowFieldProps = Omit<FlowFieldProps, "name" | "flowType" | "label"> &
    Partial<Pick<FlowFieldProps, "flowType" | "label">>;

/**
 * The flow that authorizes access to a provider.
 */
export const AKAuthorizationFlowField: LitFC<ProviderFlowFieldProps> = ({
    label = msg("Authorization Flow"),
    placeholder = msg("Select an authorization flow..."),
    help = msg("Flow used when authorizing this provider."),
    required = true,
    flowType = FlowDesignationEnum.Authorization,
    ...props
}) =>
    AKFlowField({
        ...props,
        name: "authorizationFlow",
        flowType,
        label,
        placeholder,
        help,
        required,
    });

/**
 * The flow that authenticates a user reaching a provider without a session.
 */
export const AKAuthenticationFlowField: LitFC<ProviderFlowFieldProps> = ({
    label = msg("Authentication Flow"),
    placeholder = msg("Select an authentication flow..."),
    help = msg("Flow used when a user access this provider and is not authenticated."),
    flowType = FlowDesignationEnum.Authentication,
    ...props
}) =>
    AKFlowField({
        ...props,
        name: "authenticationFlow",
        flowType,
        label,
        placeholder,
        help,
    });

/**
 * The flow that runs when a user logs out of a provider.
 */
export const AKInvalidationFlowField: LitFC<ProviderFlowFieldProps> = ({
    label = msg("Invalidation Flow"),
    placeholder = msg("Select an invalidation flow..."),
    help = msg("Flow used when logging out of this provider."),
    defaultFlowSlug = "default-provider-invalidation-flow",
    required = true,
    flowType = FlowDesignationEnum.Invalidation,
    ...props
}) =>
    AKFlowField({
        ...props,
        name: "invalidationFlow",
        flowType,
        label,
        placeholder,
        help,
        defaultFlowSlug,
        required,
    });
