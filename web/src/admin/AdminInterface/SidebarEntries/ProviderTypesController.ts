import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { ProvidersApi } from "@goauthentik/api";

import { createTypesController } from "./GenericTypesController";

export const ProviderTypesController = createTypesController(
    () => new ProvidersApi(DEFAULT_CONFIG).providersAllTypesList(),
    "/core/providers",
);

export default ProviderTypesController;
