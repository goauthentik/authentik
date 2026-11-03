/**
 * Common types and interfaces for entities in the authentik client API.
 *
 * @remarks
 *   An "entity" is any Object (in the authentik sense) that we get from the server that has a
 *   primary key and a REST Endpoint: an Application, a Group, a Policy Binding, a Certificate-Key
 *   Pair. We use "Entity" because "Object" is a reserved word and a specific concept in
 *   Javascript/TypeScript, so using it would imply the wrong thing to casual reviewers.
 */

/**
 * An Object (in the authentik sense) in the client API that has these traits: they have names that
 * we intend to display to the customer.
 */
export interface NamedEntity {
    /**
     * Singular label for the type of object this form creates/edits.
     */
    verboseName?: string | null;
    /**
     * Plural label for the type of object this form creates/edits.
     */
    verboseNamePlural?: string | null;
}

/**
 * Predicate to determine if a given instance has verbose name properties.
 *
 * This is useful for plucking out the labels for dynamic forms.
 */
export function isNamedEntity(instance: unknown): instance is NamedEntity {
    if (!instance || typeof instance !== "object") {
        return false;
    }

    return "verboseName" in instance || "verboseNamePlural" in instance;
}

/**
 * In several cases, we have constructors that carry information about the verboseName with them to
 * enhance the displays of generic classes like Form and Table. This interface can be declared on
 * these generic classes so that TypeScript accept that the object's constructor carries these
 * fields.
 */
// oxlint-disable-next-line @typescript-eslint/no-unsafe-function-type
export interface NamedEntityElement extends Function, NamedEntity {}

/**
 * Constructor interface for elements that implement {@link NamedEntityElement}
 */
export interface NamedEntityElementConstructor extends NamedEntity, CustomElementConstructor {
    createLabel?: string | null;
}
