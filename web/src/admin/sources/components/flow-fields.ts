import { LitFC } from "#elements/types";

import { AKFlowField, FlowFieldProps } from "#admin/common/ak-flow-search/AKFlowSearch";

import { FlowDesignationEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";

/**
 * The props a source flow field accepts. Its name, flow type, and wording have defaults.
 */
export type SourceFlowFieldProps = Omit<
    FlowFieldProps,
    "name" | "flowType" | "label" | "defaultFlowSlug"
> &
    Partial<Pick<FlowFieldProps, "label">> & {
        /**
         * The primary key of the source being edited. A new source preselects the default flow.
         */
        sourcePk?: string | null;
    };

/**
 * The flow that runs before a source authenticates the user.
 */
export const AKSourcePreAuthenticationFlowField: LitFC<SourceFlowFieldProps> = ({
    label = msg("Pre-authentication flow"),
    help = msg("Flow used before authentication."),
    required = true,
    sourcePk,
    ...props
}) =>
    AKFlowField({
        ...props,
        name: "preAuthenticationFlow",
        flowType: FlowDesignationEnum.StageConfiguration,
        defaultFlowSlug: sourcePk ? null : "default-source-pre-authentication",
        label,
        help,
        required,
    });

/**
 * The flow that authenticates a user who already exists.
 */
export const AKSourceAuthenticationFlowField: LitFC<SourceFlowFieldProps> = ({
    label = msg("Authentication Flow"),
    help = msg("Flow to use when authenticating existing users."),
    sourcePk,
    ...props
}) =>
    AKFlowField({
        ...props,
        name: "authenticationFlow",
        flowType: FlowDesignationEnum.Authentication,
        defaultFlowSlug: sourcePk ? null : "default-source-authentication",
        label,
        help,
    });

/**
 * The flow that enrolls a user who doesn't exist yet.
 */
export const AKSourceEnrollmentFlowField: LitFC<SourceFlowFieldProps> = ({
    label = msg("Enrollment flow"),
    help = msg("Flow to use when enrolling new users."),
    sourcePk,
    ...props
}) =>
    AKFlowField({
        ...props,
        name: "enrollmentFlow",
        flowType: FlowDesignationEnum.Enrollment,
        defaultFlowSlug: sourcePk ? null : "default-source-enrollment",
        label,
        help,
    });
