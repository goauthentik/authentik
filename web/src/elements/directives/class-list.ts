import { noChange } from "lit";
import {
    AttributePart,
    type AttributePartInfo,
    directive,
    Directive,
    DirectiveParameters,
    PartInfo,
    PartType,
} from "lit/directive.js";

type ClassUpdate = (string | null | false) | (string | null | false)[];

// Removed = Previous - Wanted (The set of all values in Previous that are not in Wanted)
// NewPrevious = Previous - Removed
// CleanClassList = ClassList - Removed
// MissingNew = Wanted - (NewPrevious + Static)
// FinalClassList = Classlist + MissingNew
// FinalPrevious = NewPrevious + MissingNew
//
//
const partIsAttribute = (v: unknown): v is AttributePartInfo =>
    typeof v === "object" && v !== null && "type" in v && v.type === PartType.ATTRIBUTE;

class ClassListDirective extends Directive {
    #currentClasses: Set<string> | null = null;
    #staticClasses: Set<string> | null = null;

    constructor(part: PartInfo) {
        super(part);
        if (!partIsAttribute(part) || part.name !== "class" || (part.strings ?? []).length > 2) {
            throw new Error(
                "'classSet()' can only be used in the 'class' attribute and must be the only " +
                    "directive in the attribute.",
            );
        }
    }

    render(rawClassUpdate: ClassUpdate) {
        const classUpdate = Array.isArray(rawClassUpdate) ? rawClassUpdate : [rawClassUpdate];
        return ` ${classUpdate.filter((s) => typeof s === "string").join(" ")} `;
    }

    firstUpdate(part: AttributePart, wanted: string[]) {
        // Store the static (i.e. not the directive's responsibility) classNames on the
        // element, and the classNames that came with the directive.
        this.#staticClasses = new Set(
            (part.strings ?? [])
                .join(" ")
                .split(/\s+/)
                .filter((s) => s !== ""),
        );

        // Ensure current and static are disjoint.
        const wantedAndNotStatic = wanted.filter((w) => !this.#staticClasses!.has(w));
        this.#currentClasses = new Set(wantedAndNotStatic);
        return this.render(wantedAndNotStatic);
    }

    // Time for some set theory.  We start with four sets:
    // update, current, static, and classes
    //
    // When we enter this function after the first time, classes is the union of current and static
    // `update` represents a desired new `current`, but the API for manipulating `classes` is
    // terrible, so:
    //
    override update(part: AttributePart, [rawClassUpdate]: DirectiveParameters<this>) {
        const classUpdate = Array.isArray(rawClassUpdate) ? rawClassUpdate : [rawClassUpdate];

        // Sets have the nice feature of automatically deduping.
        const wanted = new Set<string>(
            classUpdate.filter((s): s is string => !!s && typeof s === "string"),
        );

        if (this.#currentClasses === null || this.#staticClasses === null) {
            return this.firstUpdate(part, Array.from(wanted.values()));
        }

        const { classList } = part.element;

        // `removed` is the difference set from `current` with `wanted`
        const removed = this.#currentClasses.values().filter((v) => !wanted.has(v));

        // Since Static and Current are disjoint, `removed` cannot accidentally delete static
        // elements
        removed.forEach((r) => {
            classList.remove(r); // CleanClasslist
            this.#currentClasses!.delete(r); // NewCurrent
        });

        // `newAndNotStatic` is the difference of `wanted` with `static + current`
        const newAndNotStatic = wanted
            .values()
            .filter((s) => !this.#staticClasses!.has(s) && !this.#currentClasses!.has(s));

        for (const className of newAndNotStatic) {
            classList.add(className); // FinalClassList
            this.#currentClasses.add(className); // FinalCurrent
        }

        return noChange;
    }
}

/**
 * A directive that applies dynamic CSS classes from an array
 *
 * @remarks
 *
 * This must be used in the `class` attribute and must be the only directive used in the attribute.
 * It takes as an argument a list of strings, nulls, or `false` values (specifically), and updates
 * the element's `classList` property with a de-duplicated list of non-empty strings in the
 * argument, taking care to include any static classes provided. On subsequent renders, it analyzes
 * the argument and adds new classes to the element`s classList and removes any that no longer appear
 * in the argument.
 *
 * For example, ["foo", theme && "bar"] will always add `.foo`, and will only add `.bar` if theme is
 * Truthy. On the other hand, `[theme || "default"]` will return the content of theme if and only if
 * it is a string (and not an empty string).
 *
 * @param classUpdate
 */
export const classList = directive(ClassListDirective);

export type { ClassListDirective, ClassUpdate };
