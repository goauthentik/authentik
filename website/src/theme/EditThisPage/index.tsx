import Link from "@docusaurus/Link";
import Translate from "@docusaurus/Translate";
import { ThemeClassNames } from "@docusaurus/theme-common";
import type { Props } from "@theme/EditThisPage";
import React, { type ReactNode } from "react";

export default function EditThisPage({ editUrl }: Props): ReactNode {
    return (
        <Link to={editUrl} className={ThemeClassNames.common.editThisPage}>
            <Translate
                id="theme.common.editThisPage"
                values={{
                    github: "GitHub",
                }}
                description="The link label to edit the current page"
            >
                {"Edit on {github}"}
            </Translate>
        </Link>
    );
}
