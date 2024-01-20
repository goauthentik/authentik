import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { PoliciesApi } from "@goauthentik/api";

import { createTypesController } from "./GenericTypesController";

export const PolicyTypesController = createTypesController(
    () => new PoliciesApi(DEFAULT_CONFIG).policiesAllTypesList(),
    "/policy/policies",
);

export default PolicyTypesController;
