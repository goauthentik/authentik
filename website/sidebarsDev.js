const docsSidebar = require("./sidebars.js");
const generateVersionDropdown =
    require("./src/utils.js").generateVersionDropdown;

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
            link: {
                type: "generated-index",
                title: "Events",
                slug: "events",
            },
            items: ["hackathon/index"],
        },
    ],
};
