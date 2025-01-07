import React from "react";
import { Language } from "prism-react-renderer";
export interface Props {
    readonly responseExample: string;
    readonly language: Language;
}
declare function ResponseSamples({ responseExample, language, }: Props): React.JSX.Element;
export default ResponseSamples;
