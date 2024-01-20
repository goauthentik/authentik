import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { StagesApi } from "@goauthentik/api";

import { createTypesController } from "./GenericTypesController";

export const StageTypesController = createTypesController(
    () => new StagesApi(DEFAULT_CONFIG).stagesAllTypesList(),
    "/flow/stages",
);

export default StageTypesController;
