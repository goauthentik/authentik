/** @type { import("stylelint").Config } */
export default {
    extends: "stylelint-config-standard",
    rules: {
        "custom-property-pattern": [
            "^([A-Za-z][A-Za-z0-9]*)((__|--?)[A-Za-z0-9]+)*$",
            {
                message: "Expected custom property name to be kebab-case",
            },
        ],
        "selector-class-pattern": [
            "^([a-z][a-z0-9]*)((__?|-)[A-Za-z0-9]+)*$",
            {
                message: (/** @type {string} */ selector) =>
                    `Expected class selector "${selector}" to be kebab-case`,
            },
        ],
        "declaration-empty-line-before": null,
        "media-feature-range-notation": null,
    },
};
