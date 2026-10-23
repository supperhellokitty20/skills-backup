---
name: email-security
description: "DMARC/SPF/DKIM check, email spoofing, SMTP test, and security header analysis"
version: 1.1.0
revision_date: 2026-07-25
license: MIT
category: recon
tags: [email, SPF, DKIM, DMARC, spoofing, SMTP, recon]
---


## MANDATORY ON INVOCATION

Some harnesses read only the first ~150 lines of this skill when it is triggered. The table below is the mandatory part of this skill — it applies the moment this skill is invoked, before any other tool call.

| # | Requirement | Action |
|---|---|---|
| 1 | Full read | Read the ENTIRE SKILL.md, including everything past this table, before starting any work |
| 2 | Bundled files | None shipped — this SKILL.md is self-contained |
| 3 | Stop condition | Do not run a single hunting/scanning/exploit command until items 1-2 are done |

Markdown checklist (duplicate this check in your working notes):

- [ ] Full SKILL.md read end to end before the first tool call
- [ ] Protocol confirmed before any work started

# Email Security -- DMARC, SPF, DKIM

## When to Use

- During passive reconnaissance (Phase 1)
- After initial DNS enumeration
- DMARC p=none means the domain can be totally spoofed
- Critical for identifying phishing/business email compromise risks

## DMARC/SPF/DKIM Check Commands

```bash
# SPF
dig +short TXT $target | grep "v=spf1"

# DMARC
dig +short TXT _dmarc.$target

# DKIM (common selector: google)
dig +short TXT google._domainkey.$target

# MX
dig +short MX $target
```

## Interpreting Results

| Config | Meaning | Risk |
|--------|---------|------|
| v=spf1 ~all (softfail) | SPF suggests blocking but doesnt enforce | Spoofed emails may pass |
| v=spf1 ?all (neutral) | SPF does nothing | Totally permissive |
| v=spf1 include:amazonses.com ~all | SES can send as domain | Any AWS SES account can spoof |
| v=DMARC1; p=none | DMARC disabled | Zero spoofing protection |
| v=DMARC1; p=quarantine | Failed emails go to spam | Partial protection |
| v=DMARC1; p=reject | Failed emails rejected | Full protection |
| DKIM missing | No cryptographic signature | Email can be forged |

## Email Spoofing via SMTP

```bash
# Test SMTP relay
timeout 3 bash -c 'exec 3<>/dev/tcp/TARGET/25; head -1 <&3'

# Send spoofed email via open relay (swaks)
swaks --to victim@target.com --from admin@target.com   --server TARGET --body "Spoofed email"
```

## Headers That Indicate Security Level

| Header | Value | Meaning |
|--------|-------|---------|
| Authentication-Results | spf=pass | SPF passed |
| Authentication-Results | spf=fail | SPF failed |
| Authentication-Results | dmarc=pass | DMARC passed |
| Authentication-Results | dmarc=fail | DMARC failed |
| Authentication-Results | dkim=pass | DKIM passed |
| Received-SPF | Pass | Sender authorized |
| Received-SPF | Softfail | Sender not fully authorized |
| Received-SPF | Fail | Sender not authorized |
| ARC-Authentication-Results | | Authentication chain |

## AWS SES Spoofing (When SPF includes amazonses.com)

With `v=spf1 include:amazonses.com ~all`:
1. Create AWS account
2. Configure SES with your own domain (verified)
3. Send email with From: admin@target.com
4. SPF PASSES (because of include:amazonses.com)
5. DMARC p=none -- provider delivers normally

## Real-World Cases

**Real-world case (CRITICAL)**: Political party -- DMARC p=none on both domains (DOMAIN_PLACEHOLDER_A, DOMAIN_PLACEHOLDER_B). SPF with include:amazonses.com (any SES account can send as the domain). Total email spoofing.

## Pitfalls

| Issue | Solution |
|-------|----------|
| SPF lookup limit | DNS has 10 lookup limit for SPF includes |
| DKIM selector unknown | Try common selectors: google, selector1, selector2, 2022, 2023 |
| DMARC reporting | rua=mailto: may leak authentication results to third party |

## Verification

```bash
# Verify email spoofing is possible
# Send test email and check headers:
dig +short TXT _dmarc.target.com
# If p=none -> confirmed spoofable
```