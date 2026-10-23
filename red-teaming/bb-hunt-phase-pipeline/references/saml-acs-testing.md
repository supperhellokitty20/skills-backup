# SAML ACS Testing

Test whether a SAML Service Provider validates assertion signatures and how it handles malformed or forged assertions.

## When to use

- The target uses SAML SSO (often visible as a `/saml` endpoint, a `saml/metadata` path, or an IdP redirect to AzureAD/Okta/OneLogin).
- The SP metadata is publicly accessible at `/saml/metadata` or a known metadata URL.

## Procedure

### 1. Fetch and parse the SP metadata

```
GET /saml/metadata
```

Key fields to check:
- `WantAssertionsSigned` — if `false`, the SP does not require SAML assertions to be signed
- `AuthnRequestsSigned` — if `false`, the SP does not sign its own AuthnRequests
- `AssertionConsumerService` — the ACS URL where SAML responses are POSTed
- `NameIDFormat` — what identity format the SP expects (emailAddress, persistent, unspecified, etc.)

### 2. Verify the ACS endpoint is live

Send a well-formed but unsigned SAML Response as a `SAMLResponse` form parameter:

```
POST /saml/consume HTTP/1.1
Content-Type: application/x-www-form-urlencoded

SAMLResponse=<base64-urlencoded-unsigned-SAML-assertion>
```

A **302** redirect (not a 4xx error) means the ACS processed the assertion through the auth pipeline. A **422** with a parsing error means it tried to decode the XML but found it malformed — the endpoint is active. A **400** "Unpermitted Parameters" means the endpoint exists but expects a different parameter name or format.

### 3. Craft an unsigned SAML assertion

Minimal structure for testing:

```xml
<?xml version="1.0"?>
<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                ID="_test-001" Version="2.0"
                IssueInstant="2026-10-12T10:00:00Z"
                Destination="https://target.com/saml/consume">
  <saml:Issuer>https://idp.example.com/</saml:Issuer>
  <samlp:Status>
    <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
  </samlp:Status>
  <saml:Assertion ID="_assert-001" Version="2.0" IssueInstant="2026-10-12T10:00:00Z">
    <saml:Issuer>https://idp.example.com/</saml:Issuer>
    <saml:Subject>
      <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">target-user@example.com</saml:NameID>
      <saml:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">
        <saml:SubjectConfirmationData NotOnOrAfter="2026-10-12T11:00:00Z"
                                      Recipient="https://target.com/saml/consume"/>
      </saml:SubjectConfirmation>
    </saml:Subject>
    <saml:Conditions NotBefore="2026-10-12T09:00:00Z" NotOnOrAfter="2026-10-12T11:00:00Z">
      <saml:AudienceRestriction>
        <saml:Audience>https://target.com/</saml:Audience>
      </saml:AudienceRestriction>
    </saml:Conditions>
    <saml:AuthnStatement AuthnInstant="2026-10-12T10:00:00Z"/>
  </saml:Assertion>
</samlp:Response>
```

Key requirements for a valid-looking assertion:
- `Destination` must match the ACS URL
- `Recipient` must match the ACS URL
- `Audience` must match the SP entity ID
- `NameID Format` should match what the metadata advertises
- `IssueInstant` and time windows must be current (use a broad window to avoid clock-skew rejection)

Base64-encode the XML and URL-encode the base64 before submitting.

### 4. Test with a real AuthnRequest ID

If step 2 succeeds but the user is not found (lands on `not_logged_in` home page), the assertion may need to match a pending AuthnRequest. Initiate the SAML flow first:

```
GET /saml
Redirects to IdP with SAMLRequest parameter
```

Extract the `ID` from the decoded SAMLRequest, then include `InResponseTo="<id>"` in both the Response and the SubjectConfirmationData of your forged assertion. This can bypass request-response correlation checks.

### 5. Test with different NameID formats

Some SPs accept multiple NameID formats. Try:
- `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`
- `urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified`
- `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent`
- `urn:oasis:names:tc:SAML:1.1:nameid-format:WindowsDomainQualifiedName`

### 6. Check the RelayState parameter

Some ACS endpoints process a `RelayState` parameter alongside `SAMLResponse`. Include `RelayState=test123` to see if it affects the redirect target or session behavior.

## What a positive result looks like

- **ACS returns 302** with a `_filetransfer_session` or similar cookie — the assertion was processed through the auth pipeline, not rejected at the signature gate
- **ACS returns 302 to `/saml/consume/error` then redirects to home** — the user was not found but the assertion format was accepted
- **ACS returns 200 with a login page** — the assertion was parsed but authentication failed (user not found or session rejected)

## What a negative result looks like

- **ACS returns 400/422** — malformed XML, wrong parameter name, or missing required fields
- **ACS returns 401** — authentication required or assertion rejected
- **ACS returns 403** — access denied (WAF or IP block)

## Triage gate

A SAML ACS that accepts unsigned assertions is a **CANDIDATE** finding. To upgrade to DIG you need:
1. A valid user email that exists in the target system
2. The assertion to successfully authenticate as that user (observed via a session cookie + authenticated page content)

Without step 2, the finding is a security misconfiguration (informational) — the SP should require signed assertions but no concrete authentication bypass was demonstrated.

## Pitfalls

- The NameID must match an existing user in the target system. Without a user enumeration vector, the assertion will be accepted but authentication will fail silently.
- AzureAD/Entra ID always signs its SAML assertions regardless of the SP's `WantAssertionsSigned` setting — the metadata flag controls only what the SP requires, not what the IdP sends.
- A signed assertion where the signature is stripped is functionally an unsigned assertion — test this by taking a real SAML response from the IdP, removing the `<ds:Signature>` element, and submitting it.
- The ACS may require the `InResponseTo` attribute to match an active AuthnRequest session. A freshly initiated SAML flow gives you a valid request ID to use.
- Session cookies from a failed SAML authentication (user not found) are NOT a valid authenticated session — the cookie is created but the user is not logged in. Check the HTML body for `not_logged_in` class or similar markers before claiming authentication.