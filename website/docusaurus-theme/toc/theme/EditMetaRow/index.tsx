import { DocTOCEnabledContext } from "#components/DocTOCContext.ts";

import InitialEditMetaRow from "@theme-init/EditMetaRow";
import type { Props } from "@theme/EditMetaRow";
import LastUpdated from "@theme/LastUpdated";
import clsx from "clsx";
import React, { type ReactNode, useContext } from "react";

export default function EditMetaRow(props: Props): ReactNode {
    const enabled = useContext(DocTOCEnabledContext);

    if (!enabled) {
        return <InitialEditMetaRow {...props} />;
    }

    const { className, lastUpdatedAt, lastUpdatedBy } = props;

    if (!lastUpdatedAt && !lastUpdatedBy) {
        return null;
    }

    return (
        <div className={clsx("row", className)}>
            <div className="col text--right">
                <LastUpdated lastUpdatedAt={lastUpdatedAt} lastUpdatedBy={lastUpdatedBy} />
            </div>
        </div>
    );
}
