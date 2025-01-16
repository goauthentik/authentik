import callBind from 'call-bind-apply-helpers';

declare function callBoundIntrinsic(
    name: string,
    allowMissing?: false
): ReturnType<typeof callBind>;

declare function callBoundIntrinsic(
    name: string,
    allowMissing: true
): undefined | ReturnType<typeof callBind>;

export = callBoundIntrinsic;