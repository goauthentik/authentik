import React from "react";

/**
 * Badge indicating the preview status of a feature or integration.
 */
export const PreviewBadge: React.FC = () => {
    return (
        <span
            title="This feature is in preview and may change in the future."
            aria-description="Preview badge"
            role="img"
            className="badge badge--preview"
        >
            Preview
        </span>
    );
};

export default PreviewBadge;
