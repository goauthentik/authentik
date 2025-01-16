import type { Oas3Rule } from '../../visitors';
import type { UserContext } from '../../walk';
import { validateMimeTypeOAS3 } from '../../utils';

export const RequestMimeType: Oas3Rule = ({ allowedValues }) => {
  return {
    Paths: {
      RequestBody: {
        leave(requestBody, ctx: UserContext) {
          validateMimeTypeOAS3({ type: 'consumes', value: requestBody }, ctx, allowedValues);
        },
      },
      Callback: {
        RequestBody() {},
        Response: {
          leave(response, ctx: UserContext) {
            validateMimeTypeOAS3({ type: 'consumes', value: response }, ctx, allowedValues);
          },
        },
      },
    },
    WebhooksMap: {
      Response: {
        leave(response, ctx: UserContext) {
          validateMimeTypeOAS3({ type: 'consumes', value: response }, ctx, allowedValues);
        },
      },
    },
  };
};
