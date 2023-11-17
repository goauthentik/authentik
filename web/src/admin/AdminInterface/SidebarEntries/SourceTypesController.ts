import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { SourcesApi } from "@goauthentik/api";

import { createTypesController } from "./GenericTypesController";

export const SourceTypesController = createTypesController(
    () => new SourcesApi(DEFAULT_CONFIG).sourcesAllTypesList(),
    "/core/sources",
);

export default SourceTypesController;
