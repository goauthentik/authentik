import React, { type ReactNode } from "react";
import Translate from "@docusaurus/Translate";
import { ThemeClassNames } from "@docusaurus/theme-common";
import Link from "@docusaurus/Link";
import type { Props } from "@theme/EditThisPage";

export default function EditThisPage({ editUrl }: Props): ReactNode {
    return (
        <Link to={editUrl} className={ThemeClassNames.common.editThisPage}>
            <Translate
                id="theme.common.editThisPage"
                values={{
                    github: <strong>GitHub</strong>,
                }}
                description="The link label to edit the current page"
            >
                {"Edit on {github}"}
            </Translate>
        </Link>
    );
}
