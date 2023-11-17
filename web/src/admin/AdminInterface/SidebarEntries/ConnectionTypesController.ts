import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { OutpostsApi } from "@goauthentik/api";

import { createTypesController } from "./GenericTypesController";

export const ConnectionTypesController = createTypesController(
    () => new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsAllTypesList(),
    "/outpost/integrations",
);

export default ConnectionTypesController;
