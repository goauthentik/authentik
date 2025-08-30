import React from "react";

const ShortDescription: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div className="glossary__short">{children}</div>
);

export default ShortDescription;
