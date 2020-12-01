declare module "django" {
    export = django;
}
declare namespace django {
    function gettext(name: string): string;
    function ngettext(singular: string, plural: string, count: number): string;
    function gettext_noop(msgid: string): string;
    function pgettext(context: string, msgid: string): string;
    function interpolate(fmt: string, obj: unknown, named: boolean): string;
}
