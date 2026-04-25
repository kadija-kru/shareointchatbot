# IT Security Policy

**Contoso Corporation | Information Technology Department**  
**Version 2.1 | Last Revised: March 2024**

---

## 1. Purpose and Scope

This policy establishes the security requirements for all employees, contractors, and third parties who access Contoso Corporation's information systems. It applies to all devices, networks, applications, and data owned or managed by Contoso.

---

## 2. Password Management

### 2.1 Password Requirements
All passwords must meet the following minimum criteria:
- Minimum 12 characters
- Must include uppercase, lowercase, digits, and at least one special character
- Must not contain your name, username, or company name
- Must not reuse the last 12 passwords

### 2.2 Multi-Factor Authentication (MFA)
MFA is mandatory for:
- All Microsoft 365 applications (including SharePoint, Teams, Outlook)
- VPN access
- Administrative accounts
- Any system containing personally identifiable information (PII) or financial data

### 2.3 Password Storage
Employees must not store passwords in plain text (spreadsheets, notes apps, sticky notes). Approved password managers include: **Microsoft Authenticator**, **1Password** (company-issued licenses available from IT).

---

## 3. Device Security

### 3.1 Approved Devices
Only Contoso-issued or approved BYOD (Bring Your Own Device) devices may access company systems. BYOD devices must be enrolled in Microsoft Intune.

### 3.2 Screen Lock
All devices must lock automatically after 5 minutes of inactivity. Remote work devices must use full-disk encryption (BitLocker for Windows, FileVault for macOS).

### 3.3 Software Updates
Operating system and security updates must be applied within 7 days of release. IT deploys critical patches via Microsoft Endpoint Manager; manual override is not permitted.

---

## 4. Data Classification

| Classification | Description | Examples |
|---|---|---|
| **Public** | Safe for external sharing | Marketing materials, press releases |
| **Internal** | For employees only | Policies, process docs |
| **Confidential** | Restricted access | Financial reports, contracts |
| **Restricted** | Need-to-know, encrypted | PII, legal matters, trade secrets |

All files stored in SharePoint must be tagged with the appropriate classification label.

---

## 5. Email and Phishing

- Do not click links or open attachments from unexpected senders.
- Report suspicious emails using the **Phish Alert Button** in Outlook.
- IT will never ask for your password via email.
- External email is marked with a yellow "[EXTERNAL]" banner; verify sender identity before acting.

---

## 6. SharePoint and Data Sharing

### 6.1 External Sharing
External sharing in SharePoint must be approved by the data owner and a manager. Shared links should use expiry dates (maximum 30 days) and require authentication.

### 6.2 Sensitive Data in SharePoint
Do not upload Restricted-classified files to SharePoint without applying sensitivity labels and restricting access to named individuals only.

---

## 7. Incident Reporting

Security incidents must be reported within **1 hour** of discovery:
- Email: security@contoso.com
- Teams Channel: **#it-security-alerts**
- 24/7 hotline: +1-800-555-0199

Incidents include: lost devices, suspected account compromise, ransomware, unauthorized data access, or accidental data exposure.

---

## 8. Acceptable Use

Company IT resources are provided for business use. Incidental personal use is permitted provided it does not:
- Violate any law or regulation
- Consume excessive bandwidth
- Access inappropriate or illegal content
- Install unauthorized software

---

*Violations of this policy may result in disciplinary action up to and including termination.*  
*Contact IT Security at security@contoso.com for questions.*
