/**
 * Labels for entities shown in tables.
 *
 * @category Table
 * @category i18n
 */
export interface EntityLabel {
    /**
     * Singular, typically a lowercased common-noun.
     *
     * e.g. "user", "application", "policy"
     */
    singular: string;
    /**
     * Plural, typically lowercased common-noun.
     *
     * e.g. "users", "applications", "policies"
     */
    plural: string;
}
