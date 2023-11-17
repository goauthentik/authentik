import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { PropertymappingsApi } from "@goauthentik/api";

import { createTypesController } from "./GenericTypesController";

export const PropertyMappingsController = createTypesController(
    () => new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllTypesList(),
    "/core/property-mappings",
);

export default PropertyMappingsController;
