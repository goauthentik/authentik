FROM quay.io/oauth2-proxy/oauth2-proxy

ENV OAUTH2_PROXY_EMAIL_DOMAINS=*
ENV OAUTH2_PROXY_PROVIDER=oidc
ENV OAUTH2_PROXY_HTTP_ADDRESS=:4180
# TODO: If service is access over HTTPS, this needs to be set to true (default), otherwise needs to be false
# ENV OAUTH2_PROXY_COOKIE_SECURE=true
ENV OAUTH2_PROXY_SKIP_PROVIDER_BUTTON=true
