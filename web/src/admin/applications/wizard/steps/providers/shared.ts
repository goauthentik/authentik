import {
    type ApplicationRequest,
    type LDAPProviderRequest,
    type OAuth2ProviderRequest,
    type PolicyBinding,
    type ProvidersSamlImportMetadataCreateRequest,
    type ProxyMode,
    type ProxyProviderRequest,
    type RACProviderRequest,
    type RadiusProviderRequest,
    type SAMLProviderRequest,
    type SCIMProviderRequest,
    type ValidationError,
} from "@goauthentik/api";

export type OneOfProvider = Partial<
    | SCIMProviderRequest
    | SAMLProviderRequest
    | ProvidersSamlImportMetadataCreateRequest
    | RACProviderRequest
    | RadiusProviderRequest
    | ProxyProviderRequest
    | OAuth2ProviderRequest
    | LDAPProviderRequest
>;

export type WizardValidationRecord<K extends PropertyKey = string> = {
    [key in K]: string[] | undefined;
};

/**
 * An error that occurs during the creation or modification of an application.
 *
 * @todo (Elf) Extend this type to include all possible errors that can occur during the creation or modification of an application.
 */
export interface ApplicationTransactionValidationError extends Pick<
    ValidationError,
    "code" | "nonFieldErrors"
> {
    app?: WizardValidationRecord;
    name?: WizardValidationRecord;
    provider?: WizardValidationRecord;
    bindings?: WizardValidationRecord;
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

export type ApplicationWizardStateError = ValidationError | ApplicationTransactionValidationError;

// We use the PolicyBinding instead of the PolicyBindingRequest here, because that gives us a slot
// in which to preserve the retrieved policy, group, or user object from the SearchSelect used to
// find it, which in turn allows us to create a user-friendly display of bindings on the "List of
// configured bindings" page in the wizard. The PolicyBinding is converted into a
// PolicyBindingRequest during the submission phase.

export interface ApplicationWizardState<
    P extends OneOfProvider = OneOfProvider,
    E = ApplicationTransactionValidationError,
> {
    app: Partial<ApplicationRequest>;
    providerModel: string;
    provider: P;
    proxyMode: ProxyMode;
    bindings: PolicyBinding[];
    currentBinding: number;
    errors: E;
}

export interface ApplicationWizardStateUpdate {
    app?: Partial<ApplicationRequest>;
    providerModel?: string;
    provider?: OneOfProvider;
    proxyMode?: ProxyMode;
    bindings?: PolicyBinding[];
    currentBinding?: number;
    errors?: ValidationError;
}
