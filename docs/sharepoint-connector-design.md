# SharePoint Connector Design

**Status:** Design / Future Implementation  
**Authors:** Contoso Architecture Team  
**Last Updated:** April 2024

---

## Overview

This document describes the design for a **production SharePoint connector** that will replace the `mock` connector used in the demo. The connector retrieves documents from one or more SharePoint Online sites using the **Microsoft Graph API** with **Entra ID delegated (on-behalf-of-user) authentication**.

The guiding principles are:

1. **Permission-safe**: the chatbot can only surface documents the signed-in user is allowed to read. No app-only tokens for content retrieval.
2. **Zero additional cost**: reuses the Microsoft 365 licence the organisation already has.
3. **Incremental**: re-index only changed documents to keep latency low.
4. **No content leakage**: metadata and full-text content are never stored outside the organisation's infrastructure.

---

## 1. Authentication — Entra ID Delegated (On-Behalf-Of)

### 1.1 App Registration

Create an Entra ID (Azure AD) App Registration in the tenant:

| Setting | Value |
|---|---|
| **Name** | `contoso-sharepoint-chatbot` |
| **Supported account types** | Accounts in this directory only (single-tenant) |
| **Platform** | Web (or SPA for client-side flows) |
| **Redirect URIs** | `https://<your-app-host>/auth/callback` |

Generate a **client secret** (or use a certificate — recommended for production) and store it in Azure Key Vault or as a Docker secret. **Never commit secrets to source control.**

### 1.2 Required Graph API Permissions (Delegated)

| Permission | Type | Reason |
|---|---|---|
| `Sites.Read.All` | Delegated | Enumerate and read SharePoint sites |
| `Files.Read.All` | Delegated | Download file content from document libraries |
| `User.Read` | Delegated | Read the signed-in user's profile |

> **Important:** Use **Delegated** permissions, not Application permissions. This ensures the token only grants access to documents the user can already see in SharePoint, preserving row-level security.

### 1.3 Token Acquisition (On-Behalf-Of Flow)

The recommended flow for a server-side application:

```
1. User signs in to the chatbot (MSAL.js or MSAL Python — interactive or SSO).
2. App receives an access token for Microsoft Graph.
3. For each RAG query, the app uses that token to call Graph.
   (Optionally: exchange via OBO flow if the token was acquired by a different service.)
4. Never cache tokens server-side beyond their expiry; refresh silently using MSAL's token cache.
```

**Libraries:**
- Python: [`msal`](https://pypi.org/project/msal/) (Microsoft Authentication Library)
- Node.js: [`@azure/msal-node`](https://www.npmjs.com/package/@azure/msal-node)

---

## 2. Core Graph API Endpoints

### 2.1 Site and Drive Discovery

```http
# List all SharePoint sites the user can access
GET https://graph.microsoft.com/v1.0/sites?search=*

# Get a specific site by hostname and path
GET https://graph.microsoft.com/v1.0/sites/{hostname}:/{server-relative-path}

# List document libraries (drives) in a site
GET https://graph.microsoft.com/v1.0/sites/{siteId}/drives
```

### 2.2 Listing and Downloading Files

```http
# List items in the root of a drive
GET https://graph.microsoft.com/v1.0/drives/{driveId}/root/children

# Recursively list all items (use $expand or delta for large libraries)
GET https://graph.microsoft.com/v1.0/drives/{driveId}/root/delta

# Download file content
GET https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/content
```

Supported file types for text extraction: `.docx`, `.pdf`, `.txt`, `.md`, `.pptx`.  
For `.docx` and `.pptx`, use `python-docx` and `python-pptx`.  
For `.pdf`, use `pypdf` or `pdfminer.six`.

### 2.3 Search

```http
# Full-text search across SharePoint content (respects user permissions)
POST https://graph.microsoft.com/v1.0/search/query
Content-Type: application/json

{
  "requests": [{
    "entityTypes": ["driveItem"],
    "query": { "queryString": "annual leave policy" },
    "from": 0,
    "size": 25,
    "fields": ["name", "lastModifiedDateTime", "webUrl", "parentReference"]
  }]
}
```

> **Note:** The Search API automatically filters results to what the signed-in user can access. Use it for keyword pre-filtering before vector retrieval.

---

## 3. Connector Implementation Plan

### 3.1 Class Interface

The production connector will implement the same interface as `mock_connector.py`:

```python
class SharePointConnector:
    def __init__(self, token: str, site_allowlist: list[str] | None = None):
        ...

    def load_documents(self) -> list[SharePointDocument]:
        """Retrieve all indexable documents for the current user."""
        ...

    def get_delta(self, delta_token: str) -> tuple[list[SharePointDocument], str]:
        """Return only changed documents since the last delta token."""
        ...
```

### 3.2 Site Allowlist

An optional `SHAREPOINT_SITE_ALLOWLIST` environment variable accepts a comma-separated list of site relative paths (e.g., `/sites/hr,/sites/pmo`). When set, the connector will only index documents from those sites, reducing surface area and index size.

```python
# Example
SHAREPOINT_SITE_ALLOWLIST=/sites/hr,/sites/itsupport,/sites/pmo
```

If not set, all sites the user can access will be crawled (subject to Graph pagination).

---

## 4. Incremental Indexing Strategy

### 4.1 Graph Delta Queries

The Graph `/delta` endpoint returns only items that have changed since a given `deltaToken`. The connector stores the token after each full crawl and uses it for subsequent runs.

```
Initial crawl: GET /drives/{driveId}/root/delta  → full item list + deltaToken
Next run:      GET /drives/{driveId}/root/delta?$deltatoken={token} → changes only
```

Changed items are re-embedded and upserted into FAISS. Deleted items are removed from the index.

### 4.2 Scheduled Re-Indexing

Run the indexer on a schedule (e.g., every 15 minutes via a cron job or Azure Function timer) to pick up changes. For immediate freshness, a webhook (Graph change notification) can trigger a targeted re-index of a specific item.

### 4.3 Metadata Cache

Cache document metadata (title, owner, last_modified) in a lightweight SQLite database alongside the FAISS index. This avoids re-downloading unchanged files just to update metadata display.

---

## 5. Security and Permission-Safe Design

### 5.1 Delegated Tokens Only for Retrieval

The chatbot **must never** use application (app-only) tokens to retrieve document content. This ensures:

- Users cannot query documents they do not have access to.
- Sensitive documents in restricted libraries are naturally excluded.
- Audit logs in Microsoft 365 correctly attribute access to the user, not the service principal.

### 5.2 Token Handling

- Tokens are stored **only in memory** for the duration of the user's session.
- The MSAL token cache (in-memory by default) is scoped to the user session.
- For multi-user deployments, use a session-isolated cache (e.g., Redis with per-user keys, encrypted at rest).
- Tokens are **never** written to the FAISS index, logs, or any persistent store.

### 5.3 Content Isolation

- The FAISS index stores embeddings, not raw document text. However, source nodes in LlamaIndex cache text chunks. This cache should be:
  - Encrypted at rest if stored on disk.
  - Scoped to the user session when used in a multi-user deployment.
- For strict data residency requirements, run the entire stack inside the organisation's Azure tenant.

### 5.4 Audit Logging

Every retrieval request should log:
- User identity (from token claims)
- Query text (with PII scrubbing applied)
- Document IDs and site paths returned
- Timestamp

This log enables compliance reviews and detection of unusual access patterns.

---

## 6. Environment Variables (Production)

In addition to the demo variables in `.env.example`, the SharePoint connector requires:

```bash
DATA_CONNECTOR=sharepoint

# Entra ID
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<app-registration-client-id>
AZURE_CLIENT_SECRET=<client-secret>          # or use managed identity

# SharePoint
SHAREPOINT_HOST=contoso.sharepoint.com
SHAREPOINT_SITE_ALLOWLIST=/sites/hr,/sites/pmo   # optional

# Delta indexing
DELTA_TOKEN_FILE=/app/.index/delta_tokens.json   # persisted between runs
INDEX_SCHEDULE_MINUTES=15
```

---

## 7. Migration Path from Mock to Production

1. Set `DATA_CONNECTOR=sharepoint` in `.env`.
2. Configure Entra ID variables.
3. Implement `SharePointConnector` in `app/connectors/sharepoint_connector.py`.
4. Update `app/rag/indexer.py` to select the connector based on `DATA_CONNECTOR`.
5. Add MSAL authentication to the Streamlit app (or use a reverse proxy with AAD auth).
6. Run `Rebuild Index` in the UI to trigger the first full SharePoint crawl.
7. Validate that only documents the test user can access appear in answers.

---

## 8. Future Enhancements

| Feature | Notes |
|---|---|
| **Teams bot surface** | Integrate with Azure Bot Service for Teams channel |
| **SPFx web part** | Embed the chat UI natively in a SharePoint page |
| **Fine-grained access control** | Pass user claims to FAISS filter to pre-filter by site/library |
| **Answer caching** | Cache identical queries per-user for speed and cost reduction |
| **Feedback loop** | Thumbs up/down → fine-tune retrieval ranking |
| **Multi-language** | Use `paraphrase-multilingual-MiniLM-L12-v2` for non-English sites |

---

*Questions or contributions: open an issue or PR in this repository.*
