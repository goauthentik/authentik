import { aki } from "#common/api/client";

import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";
import { LitFC } from "#elements/types";

import { AKSearchSelectField, SearchSelectFieldProps } from "#components/ak-search-select-field";

import { PropertymappingsApi, SAMLPropertyMapping } from "@goauthentik/api";

import { msg } from "@lit/localize";

/**
 * A search select source for SAML provider property mappings.
 */
export const samlPropertyMappingSource: SearchSelectSource<SAMLPropertyMapping> = {
    fetchObjects: (query) =>
        aki(PropertymappingsApi)
            .propertymappingsProviderSamlList(withQuery(query, { ordering: "saml_name" }))
            .then(({ results }) => results),
    keyOf: (mapping) => mapping.pk,
    labelOf: (mapping) => mapping.name,
};

/**
 * The props a SAML property mapping field accepts. Its name, source, and wording have defaults.
 */
export type SAMLPropertyMappingFieldProps = Omit<
    SearchSelectFieldProps<SAMLPropertyMapping>,
    "name" | "source" | "label"
> &
    Partial<Pick<SearchSelectFieldProps<SAMLPropertyMapping>, "label">>;

/**
 * The property mapping that creates a SAML NameID.
 */
export const AKNameIDMappingField: LitFC<SAMLPropertyMappingFieldProps> = ({
    label = msg("NameID Property Mapping"),
    help = msg(
        "Configure how the NameID value will be created. When left empty, the NameIDPolicy of the incoming request will be respected.",
    ),
    ...props
}) =>
    AKSearchSelectField({
        ...props,
        name: "nameIdMapping",
        source: samlPropertyMappingSource,
        label,
        help,
    });

/**
 * The property mapping that creates a SAML AuthnContextClassRef.
 */
export const AKAuthnContextClassRefMappingField: LitFC<SAMLPropertyMappingFieldProps> = ({
    label = msg("AuthnContextClassRef Property Mapping"),
    help = msg(
        "Configure how the AuthnContextClassRef value will be created. When left empty, the AuthnContextClassRef will be set based on which authentication methods the user used to authenticate.",
    ),
    ...props
}) =>
    AKSearchSelectField({
        ...props,
        name: "authnContextClassRefMapping",
        source: samlPropertyMappingSource,
        label,
        help,
    });
