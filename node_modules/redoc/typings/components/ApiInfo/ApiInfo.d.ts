import * as React from 'react';
import { AppStore } from '../../services/AppStore';
export interface ApiInfoProps {
    store: AppStore;
}
export declare class ApiInfo extends React.Component<ApiInfoProps> {
    handleDownloadClick: (e: any) => void;
    render(): React.JSX.Element;
}
