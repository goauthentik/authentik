from typing import Any

from authentik.providers.kerberos.lib.exceptions import KerberosError, KerberosPreauthRequiredError
from authentik.providers.kerberos.lib import protocol
from authentik.providers.kerberos.models import KerberosProvider
from authentik.core.models import User


class Check:
    error_code: int = KerberosError.Code.KRB_ERR_GENERIC
    error_message: str | None = None
    exception_class: Exception = KerberosError
    context_attrs: list[str] = []

    def __init__(self, parent: Any):
        self.parent = parent

    def raise_if_failed(self, **kwargs):
        if not self.check():
            raise self.get_exception(**kwargs)

    def get_context(self) -> dict[str, Any]:
        return dict({attr: getattr(self, attr) for attr in self.context_attrs})

    def check(self) -> bool:
        raise NotImplementedError

    def get_exception(self, **kwargs):
        kwargs.setdefault("code", self.error_code)
        kwargs.setdefault("message", self.error_message)
        return self.exception_class(**kwargs)


class Checks(Check):
    checks: list[Check] = []
    all_required = True
    pass_child_attributes = False

    def __init__(self, *args, **kwargs):
        self.checks = kwargs.pop("checks", self.checks)
        super().__init__(*args, **kwargs)

    def get_checks_kwargs(self) -> dict[str, Any]:
        return {"parent": self.parent}

    def check_all(self) -> bool:
        self.passed = []
        kwargs = self.get_checks_kwargs()
        for check in [cls(**kwargs) for cls in self.checks]:
            if self.all_required:
                check.raise_if_failed()
            elif not check.check():
                continue
            for attr, value in check.get_context().items():
                setattr(self, attr, value)
                if self.pass_child_attributes:
                    self.context_attrs.append(attr)
            self.passed.append(check)
        return bool(self.passed)

    def check(self) -> bool:
        return self.check_all()


class PvnoCheck(Check):
    error_code = KerberosError.Code.KDC_ERR_BAD_PVNO

    def check(self):
        return self.parent.request["pvno"] == protocol.KERBEROS_PVNO


class CnameFromKdcReqCheck(Check):
    error_code = KerberosError.Code.KDC_ERR_C_PRINCIPAL_UNKNOWN
    context_attrs = ["cname"]

    def check(self) -> bool:
        self.cname = self.parent.request["req-body"].get("cname")
        return self.cname is not None


class ClientExistsCheck(Check):
    error_code = KerberosError.Code.KDC_ERR_C_PRINCIPAL_UNKNOWN
    context_attrs = ["client"]

    def check(self) -> bool:
        self.client = (
            User.objects.filter(username=self.parent.cname).first()
            or KerberosProvider.objects.filter(
                spn=self.parent.cname,
                realms__pk=self.parent.realm.pk,
            ).first()
        )
        return self.client is not None


class ClientHasKeysCheck(Check):
    error_code = KerberosError.Code.KDC_ERR_NULL_KEY

    def check(self):
        return hasattr(self.parent.client, "kerberoskeys") and self.parent.client.kerberoskeys.keys


class ClientRequestsKnownEnctypesCheck(Check):
    error_code = KerberosError.Code.KDC_ERR_ETYPE_NOSUPP
    context_attrs = ["req_etypes"]

    def check(self):
        etypes = self.parent.request["req-body"]["etype"]
        self.req_etypes = list([e for _, e in etypes if e is not None])
        if etypes and not self.req_etypes:
            return False
        return True


class ServiceFromKdcReqCheck(Check):
    error_code = KerberosError.Code.KDC_ERR_S_PRINCIPAL_UNKNOWN
    context_attrs = ["service"]

    def check(self):
        self.service = KerberosProvider.objects.filter(
            spn=self.parent.request["req-body"]["sname"],
            realms__realm_name=self.parent.request["req-body"]["realm"],
        ).first()
        return self.service is not None


class ServiceHasKeysCheck(Check):
    error_code = KerberosError.Code.KDC_ERR_NULL_KEY

    def check(self):
        return (
            hasattr(self.parent.service, "kerberoskeys") and self.parent.service.kerberoskeys.keys
        )


class PreauthRequiredCheck(Checks):
    exception_class: Any = KerberosPreauthRequiredError
    error_code: int = KerberosError.Code.KDC_ERR_PREAUTH_REQUIRED
    all_required = False
    pass_child_attributes = True

    def __init__(self, *args, **kwargs):
        self.context_attrs = kwargs.pop("context_attrs", ["preauthenticated"])
        super().__init__(*args, **kwargs)

    def check(self):
        self.preauthenticated = super().check()
        return not self.parent.service.requires_preauth or self.preauthenticated

    def get_exception(self, **kwargs):
        padata = []
        for Pa in self.parent.PREAUTH_CHECKS:
            pa = Pa(self.parent).build_padata()
            if pa is not None:
                padata.append(pa)
        kwargs["padata"] = padata
        return super().get_exception(**kwargs)


class ForwardablePolicyCheck(Check):
    error_code: int = KerberosError.Code.KDC_ERR_POLICY

    def check(self):
        if not self.parent.request["req-body"]["kdc-options"]["forwardable"]:
            return True
        return self.parent.service.allow_forwardable


class ProxiablePolicyCheck(Check):
    def check(self):
        if not self.parent.request["req-body"]["kdc-options"]["proxiable"]:
            return True
        return self.parent.service.allow_proxiable


class ForwardableCheck(Check):
    error_code: int = KerberosError.Code.KDC_ERR_BADOPTION

    def check(self):
        if not self.parent.request["req-body"]["kdc-options"]["forwardable"]:
            return True
        if hasattr(self.parent, "pa_ap_req"):
            if not self.parent.pa_ap_req["ticket"]["enc-part"]["flags"]["forwardable"]:
                return False
        return self.parent.service.allow_forwardable


class ServiceMatchCheck(Check):
    error_code: int = KerberosError.Code.KDC_ERR_SERVER_NOMATCH

    def check(self):
        if self.parent.request["req-body"]["kdc-options"]["forwardable"]:
            return True
        if hasattr(self.parent, "pa_ap_req"):
            # TODO: if self.parent.pa_ap_req["ticket"]["enc-part"]["sname"] is TGS:
            #         return True
            if (
                self.parent.pa_ap_req["ticket"]["enc-part"]["sname"]
                != self.parent.request["req-body"]["sname"]
            ):
                return False
        return True


class TicketValidCheck(Check):
    error_code: int = KerberosError.Code.KRB_AP_ERR_TKT_NYV

    def check(self):
        if not hasattr(self.parent, "pa_ap_req"):
            return True
        if not self.parent.pa_ap_req["ticket"]["enc-part"]["flags"]["invalid"]:
            return True
        if self.parent.request["req-body"]["kdc-options"]["validate"]:
            return True
        return False
