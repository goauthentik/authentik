import { Body } from "@theme/ApiExplorer/Body/slice";
import sdk from "postman-collection";
declare function makeRequest(request: sdk.Request, proxy: string | undefined, _body: Body): Promise<any>;
export default makeRequest;
