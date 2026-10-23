# Mobile-app-driven API recon

When the target has a consumer-facing mobile app (Android/iOS), the app's API is a first-class recon surface that often exposes endpoints the web app does not.

## Community API documentation

Search GitHub for community-maintained API specs before reverse-engineering the app binary:

```
GitHub search: <target> openapi OR swagger OR api-docs
GitHub org search: lib<target>-wg, <target>-api, <target>-client
```

Community projects (Home Assistant integrations, Homebridge plugins, Python/Go client libraries) frequently document the mobile app's API in OpenAPI specs, YAML files, or library source code. These are often more complete than the official documentation because the community maintains them by reverse-engineering the app.

Check these sources in order:
1. OpenAPI specs in community repos (`openapi.yaml`, `openapi.json`)
2. Python/Go/JS library source files for hardcoded API paths and auth flows
3. Home Assistant custom integrations (`custom_components/<brand>/`)
4. README/docs in the same repos for authentication flow descriptions

## OIDC provider enumeration

When a mobile app uses an OIDC identity provider, the OIDC discovery endpoint reveals the full auth surface:

```
GET /.well-known/openid-configuration
```

Probe every endpoint from the response:
- `jwks_uri` — public signing keys (always accessible)
- `authorization_endpoint` — redirect behavior reveals auth requirements
- `token_endpoint` — grant_type fuzzing (client_credentials, device_code, refresh_token)
- `userinfo_endpoint` — returns 401/200 (auth required)
- `introspection_endpoint` / `revocation_endpoint` — may accept requests without auth
- `device_authorization_endpoint` — device_code flow often has different auth requirements

Check which grant_types_supported are listed; each may have different auth enforcement.

## Cognito user pool testing

When the app's JS bundle or config reveals Cognito configuration (UserPoolId, ClientId):

1. Try SignUp: POST to `cognito-idp.<region>.amazonaws.com/` with `X-Amz-Target: AWSCognitoIdentityProviderService.SignUp`
   - Error `SignUp is not permitted` means self-registration is disabled
   - Success means you can create an account programmatically
2. Try InitiateAuth: POST with `X-Amz-Target: AWSCognitoIdentityProviderService.InitiateAuth` and `AuthFlow: USER_PASSWORD_AUTH`
   - Error `USER_PASSWORD_AUTH flow not enabled` means direct auth is blocked
   - Success means you can authenticate with username/password directly
3. Try DescribeUserPool / DescribeUserPoolClient — these require AWS credentials and will fail with `MissingAuthenticationToken`

## User enumeration via mobile API

Mobile app APIs often expose user status endpoints without authentication:

```
POST /v3/userregistration/email/userstatus
{"email": "<target>"}
```

Response differentiates registered (`ACTIVE`) from unregistered (`UNREGISTERED`) accounts. Check for:
- Rate limiting (429 after N requests)
- A second endpoint that confirms the difference (e.g., login initiation returns 200 for registered, 400 for unregistered)
- The policy scope — user/email enumeration is frequently OOS on bug bounty programs

## Provisioning endpoints

Mobile apps often require a provisioning call before other API calls work:

```
GET /v1/provisioningservice/application/Android/version
```

This returns a version string and tells the server the client is active. Without it, subsequent API calls may be ignored or return errors. Always call the provisioning endpoint first when testing mobile app APIs.

## Auth flow from client libraries

Third-party client libraries often document the full auth flow:

1. Provision the client
2. Check user status
3. Begin login (triggers OTP email/SMS)
4. Complete login with OTP code
5. Use returned Bearer token for authenticated requests

The OpenAPI spec or library README usually describes the flow — read it instead of reverse-engineering from scratch.
