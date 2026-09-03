/**
 * @file Types related to flow stages.
 */

import { DefaultImportCallback } from "#common/modules/types";

import type {
    AccessDeniedChallenge,
    AuthenticatorDuoChallenge,
    AuthenticatorEmailChallenge,
    AuthenticatorStaticChallenge,
    AuthenticatorTOTPChallenge,
    AuthenticatorWebAuthnChallenge,
    CaptchaChallenge,
    ChallengeTypes,
    ConsentChallenge,
    CurrentBrand,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    PasswordChallenge,
    SessionEndChallenge,
    UserLoginChallenge,
} from "@goauthentik/api";

import { ReactiveControllerHost } from "lit";

/**
 * Type utility to exclude the `component` property.
 */
export type ExcludeComponent<T> = T extends { component: string } ? Omit<T, "component"> : T;

/**
 * A {@link ChallengeTypes} without the `component` property.
 */
export type FlowChallengeLike = ExcludeComponent<ChallengeTypes>;

export type FlowChallengeComponentName = ChallengeTypes["component"];

/**
 * @internal
 */
export type FormStaticChallenge =
    | SessionEndChallenge
    | AccessDeniedChallenge
    | AuthenticatorDuoChallenge
    | AuthenticatorEmailChallenge
    | AuthenticatorStaticChallenge
    | AuthenticatorTOTPChallenge
    | AuthenticatorWebAuthnChallenge
    | CaptchaChallenge
    | ConsentChallenge
    | PasswordChallenge
    | UserLoginChallenge;

export type StageChallengeLike = Partial<
    Pick<FormStaticChallenge, "pendingUserAvatar" | "pendingUser" | "flowInfo" | "responseErrors">
>;

/**
 * Type-predicate to determine if a given challenge is a {@linkcode FormStaticChallenge}.
 */
export function isFormStaticChallengeLike(
    challenge: StageChallengeLike | FlowErrorChallenge | null | undefined,
): challenge is FormStaticChallenge {
    if (!challenge) return false;

    return (
        "pendingUser" in challenge ||
        "pendingUserAvatar" in challenge ||
        "flowInfo" in challenge ||
        "responseErrors" in challenge
    );
}

export interface SubmitOptions {
    invisible: boolean;
}

// Make the "component" field optional, since the Executor controls what component type is being
// manipulated.
type PartialComponent<T> = T extends { component: infer C } & infer Rest
    ? { component?: C } & Omit<Rest, "component">
    : never;

export type FlowChallengeResponseRequestBody = PartialComponent<FlowChallengeResponseRequest>;

export interface SubmitRequest {
    payload: FlowChallengeResponseRequestBody;
    options: SubmitOptions;
}

export interface StageHost {
    challenge?: unknown;
    flowSlug?: string;
    loading: boolean;
    reset?: () => void;
    submit(payload: unknown, options?: SubmitOptions): Promise<boolean>;

    readonly brand?: CurrentBrand;
}

export interface IBaseStage<Tin extends StageChallengeLike, Tout = never>
    extends HTMLElement, ReactiveControllerHost {
    host?: StageHost;
    challenge: Tin | null;
    submitForm: (event?: SubmitEvent, defaults?: Tout) => Promise<boolean>;
    reset?(): void;
}

export interface ExecutorMessage {
    source?: string;
    context?: string;
    message: string;
}

export type BaseStageConstructor<
    Tin extends StageChallengeLike = StageChallengeLike,
    Tout = never,
> = new () => IBaseStage<Tin, Tout>;

export type StageModuleConstructor<
    Tin extends StageChallengeLike = StageChallengeLike,
    Tout = never,
> = DefaultImportCallback<BaseStageConstructor<Tin, Tout>>;

/**
 * A type representing an ES module that exports a stage constructor as its default export.
 * This is used for dynamic imports of stages.
 */
export type StageModuleCallback = DefaultImportCallback<BaseStageConstructor>;
