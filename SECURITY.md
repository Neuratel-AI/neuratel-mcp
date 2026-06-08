# Security Policy

## Reporting a Vulnerability

We take the security of Neuratel SDKs seriously. If you believe you have found a security vulnerability, please report it responsibly.

**Do not file a public GitHub issue.** Instead, report it via email to:

**security@neuratel.ai**

## Response Timeline

| Severity | Acknowledgment | Initial Assessment | Resolution |
|---|---|---|---|
| Critical (RCE, data leak) | 2 business days | 5 business days | 7 business days |
| High (auth bypass, injection) | 3 business days | 7 business days | 14 business days |
| Medium/ Low (info disclosure, DoS) | 5 business days | 14 business days | 30 business days |

## Scope

### In Scope
- Source code in this repository (SDK client, types, utilities)
- Authentication and API key handling
- Dependency vulnerabilities introduced by this package

### Out of Scope
- The Neuratel Platform API itself — report via [api.neuratel.ai](https://api.neuratel.ai) support
- The Neuratel MCP server — report to security@neuratel.ai but note it is a separate package
- Third-party services accessed through the SDK
- Vulnerabilities requiring physical access or social engineering

## Coordinated Disclosure

We follow a **90-day coordinated disclosure** timeline. After a vulnerability is confirmed:

1. We will work with you to develop and test a fix
2. We will release the fix and publish an advisory
3. We request that you do not publicly disclose the vulnerability until the fix is released, or until 90 days have passed since your initial report — whichever comes first

We credit researchers who report vulnerabilities responsibly (unless you prefer to remain anonymous).

## Supported Versions

Only the latest released version of this package receives security updates. We encourage all users to upgrade promptly.
