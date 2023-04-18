import React from "react";
import { Check, X, AlertTriangle } from "react-feather";

function Comparison() {
    return (
        <section className="">
            <div className="container">
                <h2 id="correctness">Why authentik?</h2>
                <div className="table-responsive">
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
                                    <AlertTriangle></AlertTriangle>
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
                                    <AlertTriangle></AlertTriangle>
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
                                    <AlertTriangle></AlertTriangle>
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
                                    <AlertTriangle></AlertTriangle>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle></AlertTriangle>
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
                                    <AlertTriangle></AlertTriangle>
                                </td>
                                <td className="result passed">
                                    <Check></Check>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle></AlertTriangle>
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
                                    <AlertTriangle></AlertTriangle>
                                </td>
                                <td className="result warning">
                                    <AlertTriangle></AlertTriangle>
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
                                <td className="result warning">
                                    <AlertTriangle></AlertTriangle>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    );
}

export default Comparison;
