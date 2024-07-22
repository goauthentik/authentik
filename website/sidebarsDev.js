const docsSidebar = require("./sidebars.js");
const generateVersionDropdown =
    require("./src/utils.js").generateVersionDropdown;
const apiReference = require("./developer-docs/api/reference/sidebar");

module.exports = {
    docs: [
        {
            type: "html",
            value: generateVersionDropdown(docsSidebar),
        },
        {
            type: "doc",
            id: "index",
        },
        {
            type: "category",
            label: "Blueprints",
            link: {
                type: "doc",
                id: "blueprints/index",
            },
            items: [
                "blueprints/export",
                "blueprints/v1/structure",
                "blueprints/v1/tags",
                "blueprints/v1/example",
                {
                    type: "category",
                    label: "Models",
                    link: {
                        type: "doc",
                        id: "blueprints/v1/models",
                    },
                    items: ["blueprints/v1/meta"],
                },
            ],
        },
        {
            type: "category",
            label: "API",
            link: {
                type: "doc",
                id: "api/api",
            },
            items: [
                "api/flow-executor",
                "api/making-schema-changes",
                "api/websocket",
                {
                    type: "category",
                    label: "Reference",
                    items: apiReference,
                },
                "api/clients",
            ],
        },
        {
            type: "category",
            label: "Setup",
            items: [
                "setup/full-dev-environment",
                "setup/frontend-dev-environment",
                "setup/website-dev-environment",
            ],
        },
        {
            type: "doc",
            id: "translation",
        },
        {
            type: "category",
            label: "Writing documentation",
            link: {
                type: "doc",
                id: "docs/writing-documentation",
            },
            items: [
                "docs/style-guide",
                {
                    type: "category",
                    label: "Templates",
                    link: {
                        type: "doc",
                        id: "docs/templates/index",
                    },
                    items: [
                        "docs/templates/procedural",
                        "docs/templates/conceptual",
                        "docs/templates/reference",
                        "docs/templates/combo",
                    ],
                },
            ],
        },
        {
            type: "doc",
            id: "releases/index",
        },
        {
            type: "category",
            label: "Community Events",
            items: ["hackathon/index"],
        },
    ],
};
