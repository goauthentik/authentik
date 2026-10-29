import type { Props } from "@theme/EditMetaRow";
import LastUpdated from "@theme/LastUpdated";
import clsx from "clsx";
import React, { type ReactNode } from "react";

export default function EditMetaRow({
    className,
    lastUpdatedAt,
    lastUpdatedBy,
}: Props): ReactNode {
    if (!lastUpdatedAt && !lastUpdatedBy) {
        return null;
    }

    return (
        <div className={clsx("row", className)}>
            <div className="col text--right">
                <LastUpdated
                    lastUpdatedAt={lastUpdatedAt}
                    lastUpdatedBy={lastUpdatedBy}
                />
            </div>
        </div>
    );
}
