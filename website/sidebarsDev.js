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
            items: ["blueprints/v1/structure", "blueprints/v1/tags"],
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
            ],
        },
        {
            type: "category",
            label: "Setup",
            items: [
                "setup/full-dev-environment",
                "setup/frontend-only-dev-environment",
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
    ],
};
