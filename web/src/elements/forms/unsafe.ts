import type { ModelForm } from "#elements/forms/ModelForm";
import type { ElementTagNamesOf } from "#elements/types";

/**
 * Element tags that extend {@linkcode ModelForm}.
 *
 * @deprecated Dependence on this type indicates a lack of strong typing in API driven forms.
 * Consider revising the endpoint to return a more specific component type.
 */
export type CustomFormElementTagName = ElementTagNamesOf<ModelForm>;
