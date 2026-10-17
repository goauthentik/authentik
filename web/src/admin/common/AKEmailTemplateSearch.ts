import { aki } from "#common/api/client";
import { groupBy } from "#common/utils";

import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";
import { LitFC } from "#elements/types";

import { AKSearchSelectField, SearchSelectFieldProps } from "#components/ak-search-select-field";

import { EmailTemplate, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";

export interface EmailTemplateSourceInit {
    /** Choose the built-in template with this managed ID when the field has no value */
    defaultTemplate?: string | null;
}

const emailTemplateSources = new Map<string, SearchSelectSource<EmailTemplate>>();

/**
 * A search select source for email templates, grouped into built-in and custom templates.
 *
 * @remarks
 *   Sources are cached by their options, so rendering a field again passes the same source and
 *   doesn't refetch.
 */
export function emailTemplateSource({
    defaultTemplate,
}: EmailTemplateSourceInit = {}): SearchSelectSource<EmailTemplate> {
    const cacheKey = defaultTemplate ?? "";
    const cached = emailTemplateSources.get(cacheKey);

    if (cached) {
        return cached;
    }

    const source: SearchSelectSource<EmailTemplate> = {
        fetchObjects: async (query) => {
            const api = aki(StagesApi);

            const { results } = await api.stagesEmailTemplatesList(
                withQuery(query, { ordering: "path" }),
            );

            if (
                query ||
                !defaultTemplate ||
                results.some((template) => template.managed === defaultTemplate)
            ) {
                return results;
            }

            // if the default is not on the first page, fetch it so `preselect` can find it
            const { results: defaults } = await api.stagesEmailTemplatesList({
                managed: defaultTemplate,
            });

            return [...results, ...defaults];
        },
        keyOf: (template) => template.uuid,
        labelOf: (template) => template.path,
        describe: (template) =>
            template.managed ? template.displayName : template.description || "",
        groupBy: (templates) =>
            groupBy(templates, (template) => (template.managed ? msg("Built-in") : msg("Custom"))),
        preselect: defaultTemplate
            ? (templates) => templates.find((template) => template.managed === defaultTemplate)
            : undefined,
    };

    emailTemplateSources.set(cacheKey, source);

    return source;
}

export type EmailTemplateFieldProps = Omit<
    SearchSelectFieldProps<EmailTemplate>,
    "source" | "label"
> &
    EmailTemplateSourceInit & { label?: string };

/**
 * A search select for choosing an email template
 */
export const AKEmailTemplateField: LitFC<EmailTemplateFieldProps> = ({
    defaultTemplate,
    ...props
}) =>
    AKSearchSelectField({
        label: msg("Template"),
        placeholder: msg("Select an email template..."),
        ...props,
        source: emailTemplateSource({ defaultTemplate }),
    });
