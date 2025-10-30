import { WizardReadyProviderSuffix } from "#admin/applications/wizard/steps/ProviderChoices";
import { OneOfProvider } from "#admin/applications/wizard/steps/providers/shared";

import {
    type ApplicationRequest,
    type PolicyBinding,
    type ProxyMode,
    type ValidationError,
} from "@goauthentik/api";

export type ValidationRecord = { [key: string]: string[] };

/**
 * An error that occurs during the creation or modification of an application.
 *
 * @todo (Elf) Extend this type to include all possible errors that can occur during the creation or modification of an application.
 */
export interface ApplicationTransactionValidationError extends ValidationError {
    app?: ValidationRecord;
    provider?: ValidationRecord;
    bindings?: ValidationRecord;
    detail?: unknown;
}

/**
 * Type-guard to determine if an API response is shaped like an {@linkcode ApplicationTransactionValidationError}.
 */
export function isApplicationTransactionValidationError(
    error: ValidationError,
): error is ApplicationTransactionValidationError {
    if ("app" in error) return true;
    if ("provider" in error) return true;
    if ("bindings" in error) return true;

    return false;
}

// We use the PolicyBinding instead of the PolicyBindingRequest here, because that gives us a slot
// in which to preserve the retrieved policy, group, or user object from the SearchSelect used to
// find it, which in turn allows us to create a user-friendly display of bindings on the "List of
// configured bindings" page in the wizard. The PolicyBinding is converted into a
// PolicyBindingRequest during the submission phase.

export interface ApplicationWizardState<
    T extends OneOfProvider | Partial<ApplicationRequest> = OneOfProvider,
> {
    app: Partial<ApplicationRequest>;
    providerModel?: WizardReadyProviderSuffix;
    provider?: T;
    proxyMode: ProxyMode;
    bindings: PolicyBinding[];
    currentBinding: number;
    errors: ValidationError | ApplicationTransactionValidationError;
}

export type ApplicationWizardStateUpdate<
    T extends OneOfProvider | Partial<ApplicationRequest> = OneOfProvider,
> = Partial<ApplicationWizardState<T>>;
