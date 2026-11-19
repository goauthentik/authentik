import "@patternfly/patternfly/components/Login/login.css";
import "./ConsentStage.js";
import { flowFactory } from "#stories/flow-interface";

export default {
    title: "Flow / Stages / <ak-stage-consent>",
};

export const NewConsent = flowFactory("ak-stage-consent", {
    headerText: "lorem ipsum",
    token: "",
    permissions: [
        { name: "Perm 1", id: "perm_1" },
        { name: "Perm 2", id: "perm_2" },
        { name: "Perm 3", id: "perm_3" },
    ],
    additionalPermissions: [],
});

export const ExistingConsentNewPermissions = flowFactory("ak-stage-consent", {
    headerText: "lorem ipsum",
    token: "",
    permissions: [
        { name: "Perm 1", id: "perm_1" },
        { name: "Perm 2", id: "perm_2" },
        { name: "Perm 3", id: "perm_3" },
    ],
    additionalPermissions: [{ name: "Perm 4", id: "perm_4" }],
});

export const NonRegisteredClient = flowFactory("ak-stage-consent", {
    headerText: "lorem ipsum",
    token: "",
    clientId: "https://client.example.com/oauth/metadata.json",
    clientName: "Example Client",
    permissions: [{ name: "Perm 1", id: "perm_1" }],
    additionalPermissions: [],
});

export const NonRegisteredClientWithRedirectHost = flowFactory("ak-stage-consent", {
    headerText: "lorem ipsum",
    token: "",
    clientId: "https://client.example.com/oauth/metadata.json",
    clientName: "Example Client",
    redirectHost: "app.example.net",
    permissions: [{ name: "Perm 1", id: "perm_1" }],
    additionalPermissions: [],
});
