/**
 * @file Wizard utilities
 */

import { TypeCreate } from "@goauthentik/api";

/**
 * Formats a unique step ID for a given {@link TypeCreate} object,
 * using its `component` and `modelName` properties.
 */
export function formatTypeCreateStepID({ component, modelName }: TypeCreate): string {
    return ["type", component, modelName].filter(Boolean).join("-");
}
