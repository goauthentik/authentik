import React from "react";
import {
    isSupportLevel,
    SupportLevelToLabel,
} from "@site/remark/support-directive";

export interface SupportBadgeProps {
    level: string;
}

/**
 * Badge indicating the support level of a feature or integration.
 */
export const SupportBadge: React.FC<SupportBadgeProps> = ({ level }) => {
    if (!isSupportLevel(level)) {
        throw new TypeError(`Invalid support level: ${level}`);
    }

    const label = SupportLevelToLabel[level];
    const className = `badge badge--support-${level}`;

    return (
        <span
            aria-description="Support level badge"
            title={`This feature is supported at the ${label} level.`}
            role="img"
            className={className}
        >
            Support level: {label}
        </span>
    );
};

export default SupportBadge;
