import * as React from 'react';
import type { SchemaOptions } from '../Schema/Schema';
import type { FieldModel } from '../../services/models';
export interface FieldProps extends SchemaOptions {
    className?: string;
    isLast?: boolean;
    showExamples?: boolean;
    field: FieldModel;
    expandByDefault?: boolean;
    renderDiscriminatorSwitch?: (opts: FieldProps) => JSX.Element;
}
export declare class Field extends React.Component<FieldProps> {
    toggle: () => void;
    handleKeyPress: (e: any) => void;
    render(): React.JSX.Element;
}
