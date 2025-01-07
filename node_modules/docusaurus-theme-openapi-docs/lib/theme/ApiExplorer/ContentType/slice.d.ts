import { PayloadAction } from "@reduxjs/toolkit";
export interface State {
    value: string;
    options: string[];
}
export declare const slice: import("@reduxjs/toolkit").Slice<State, {
    setContentType: (state: import("immer/dist/internal").WritableDraft<State>, action: PayloadAction<string>) => void;
}, "contentType">;
export declare const setContentType: import("@reduxjs/toolkit").ActionCreatorWithPayload<string, "contentType/setContentType">;
declare const _default: import("redux").Reducer<State, import("redux").AnyAction>;
export default _default;
