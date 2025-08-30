import React from "react";

const LongDescription: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div className="glossary__long">{children}</div>
);

export default LongDescription;
