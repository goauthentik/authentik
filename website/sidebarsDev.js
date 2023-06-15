module.exports = {
    docs: [
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
                "api/browser",
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
            type: "doc",
            id: "docs/writing-documentation",
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
