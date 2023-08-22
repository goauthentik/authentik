import React from "react";
import { Check, X, AlertTriangle } from "react-feather";
import "./style.css";
import "react-tooltip/dist/react-tooltip.css";
import { Tooltip } from "react-tooltip";

export default function Comparison() {
    const tooltipAvailableThirdParty = "Available as a third-party extension";
    const tooltipPlanned = "Planned as a future feature";
    const tooltipRequiresLicense =
        "Requires additional licenses/not included in base tier";
    const toolRequiresProductAADS =
        "Requires additional product: Azure AD Domain Services";
    const toolRequiresProductWAP =
        "Requires additional product: Web Application Proxy";
    return (
        <>
            <div id="comparison"></div>
            <h1 className="header">Why authentik?</h1>
            <div className="table-responsive">
                <div className="table">
                    <table className="comparison">
                        <thead>
                            <tr>
                                <th></th>
                                <th className="authentik">authentik</th>
                                <th>Keycloak</th>
                                <th>Microsoft ADFS</th>
                                <th>Microsoft Azure AD</th>
                                <th>Okta</th>
                                <th>Duo</th>
                                <th>Authelia</th>
                            </tr>
                        </thead>
                        <thead className="group">
                            <tr>
                                <th>Protocol Support (as a provider)</th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td className="row-label">SAML2</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">OAuth2 and OIDC</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">SCIM</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle
                                        className="tooltip"
                                        data-tooltip-content={
                                            tooltipAvailableThirdParty
                                        }
                                    ></AlertTriangle>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">LDAP</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle
                                        className="tooltip"
                                        data-tooltip-content={
                                            toolRequiresProductAADS
                                        }
                                    ></AlertTriangle>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">RADIUS</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle
                                        className="tooltip"
                                        data-tooltip-content={
                                            tooltipAvailableThirdParty
                                        }
                                    ></AlertTriangle>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                            </tr>
                        </tbody>
                        <thead className="group">
                            <tr>
                                <th>Federation support</th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td className="row-label">SAML2</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">OAuth2 and OIDC</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">OAuth1</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">LDAP</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">SCIM</td>
                                <td className="result warning authentik">
                                    <AlertTriangle
                                        className="tooltip"
                                        data-tooltip-content={tooltipPlanned}
                                    ></AlertTriangle>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle
                                        className="tooltip"
                                        data-tooltip-content={
                                            tooltipAvailableThirdParty
                                        }
                                    ></AlertTriangle>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                            </tr>
                        </tbody>
                        <thead className="group">
                            <tr>
                                <th>Use-cases</th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td className="row-label">Authentication</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">Enrollment</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">Self-service</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                            </tr>
                        </tbody>
                        <thead className="group">
                            <tr>
                                <th>Features</th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td className="row-label">MFA</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">
                                    Conditional Access
                                </td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle
                                        className="tooltip"
                                        data-tooltip-content={
                                            tooltipRequiresLicense
                                        }
                                    ></AlertTriangle>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle
                                        className="tooltip"
                                        data-tooltip-content={
                                            tooltipRequiresLicense
                                        }
                                    ></AlertTriangle>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">Open-source</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                            </tr>
                            <tr>
                                <td className="row-label">Application Proxy</td>
                                <td className="result passed authentik">
                                    <Check></Check>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle
                                        className="tooltip"
                                        data-tooltip-content={
                                            tooltipAvailableThirdParty
                                        }
                                    ></AlertTriangle>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle
                                        className="tooltip"
                                        data-tooltip-content={
                                            toolRequiresProductWAP
                                        }
                                    ></AlertTriangle>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result failed">
                                    <X></X>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <Tooltip anchorSelect=".tooltip" place="top" />
                </div>
            </div>
        </>
    );
}
