import type { ChallengeTypes } from "@goauthentik/api";

/**
 * Type utility to exclude the `component` property.
 */
export type ExcludeComponent<T> = T extends { component: string } ? Omit<T, "component"> : T;

/**
 * A {@link ChallengeTypes} without the `component` property.
 */
export type FlowChallengeLike = ExcludeComponent<ChallengeTypes>;
