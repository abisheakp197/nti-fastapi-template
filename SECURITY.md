# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## NTI Post-Quantum Security

This project relies on **NTI (Neutral Trust Infrastructure)** to enforce zero-trust post-quantum security:
- **Capability Enforcement**: Explicit grant required for all tool invocations.
- **Post-Quantum Cryptography**: NIST-standardized Dilithium5 signatures and Kyber1024 encryption provided via `ube-foundation`.
- **Response Signing**: Every API response is signed with a PQC keypair.
- **Request Verification**: API endpoints require cryptographic signatures (`X-NTI-Signature`).

## Reporting a Vulnerability

If you discover a security vulnerability within this project or NTI dependencies:

1. **Do not** report security vulnerabilities through public GitHub issues.
2. Email security reports to `security@nti-trust.org` or contact repository maintainers directly.
3. Include detailed steps to reproduce the issue and any cryptographic details.
4. Reports will be acknowledged within 48 hours and patches released promptly.
