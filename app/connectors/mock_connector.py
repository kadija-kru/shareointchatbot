"""
Mock SharePoint data connector.

Returns realistic documents with SharePoint-like metadata fields:
  - title, library, owner, last_modified, source_url, file_type
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class SharePointDocument:
    """Represents a document with SharePoint-like metadata."""

    title: str
    content: str
    library: str
    owner: str
    last_modified: str
    source_url: str
    file_type: str = "md"
    doc_id: str = ""

    def metadata_dict(self) -> dict:
        return {
            "title": self.title,
            "library": self.library,
            "owner": self.owner,
            "last_modified": self.last_modified,
            "source_url": self.source_url,
            "file_type": self.file_type,
            "doc_id": self.doc_id,
        }


# Static metadata catalogue for mock documents.
# Each entry mirrors what a real Graph API response would include.
_MOCK_CATALOGUE = [
    {
        "filename": "hr_policy.md",
        "title": "HR Policy Handbook v3.2",
        "library": "HR Documents",
        "owner": "Sarah Mitchell",
        "last_modified": "2024-01-15",
        "source_url": "https://contoso.sharepoint.com/sites/hr/Shared%20Documents/HR%20Policy%20Handbook%20v3.2.md",
        "file_type": "md",
        "doc_id": "hr-policy-001",
    },
    {
        "filename": "it_security_policy.md",
        "title": "IT Security Policy v2.1",
        "library": "IT Documentation",
        "owner": "James Carter",
        "last_modified": "2024-03-10",
        "source_url": "https://contoso.sharepoint.com/sites/itsupport/Shared%20Documents/IT%20Security%20Policy%20v2.1.md",
        "file_type": "md",
        "doc_id": "it-sec-002",
    },
    {
        "filename": "onboarding_guide.md",
        "title": "New Employee Onboarding Guide",
        "library": "HR Documents",
        "owner": "Priya Sharma",
        "last_modified": "2024-02-01",
        "source_url": "https://contoso.sharepoint.com/sites/hr/Shared%20Documents/Onboarding%20Guide.md",
        "file_type": "md",
        "doc_id": "onboard-003",
    },
    {
        "filename": "project_management_templates.md",
        "title": "Project Management Templates & Guidelines v1.4",
        "library": "PMO Templates",
        "owner": "David Okonkwo",
        "last_modified": "2024-02-20",
        "source_url": "https://contoso.sharepoint.com/sites/pmo/Shared%20Documents/PM%20Templates%20v1.4.md",
        "file_type": "md",
        "doc_id": "pmo-004",
    },
    {
        "filename": "q1_2024_business_report.md",
        "title": "Q1 2024 Business Performance Report",
        "library": "Finance Reports",
        "owner": "Lisa Nguyen",
        "last_modified": "2024-04-05",
        "source_url": "https://contoso.sharepoint.com/sites/finance/Shared%20Documents/Q1%202024%20Business%20Report.md",
        "file_type": "md",
        "doc_id": "fin-005",
    },
    {
        "filename": "benefits_compensation_guide.md",
        "title": "Benefits & Compensation Guide 2024",
        "library": "HR Documents",
        "owner": "Sarah Mitchell",
        "last_modified": "2024-01-02",
        "source_url": "https://contoso.sharepoint.com/sites/hr/Shared%20Documents/Benefits%20Compensation%20Guide%202024.md",
        "file_type": "md",
        "doc_id": "hr-ben-006",
    },
]


def load_mock_documents(data_dir: str | None = None) -> List[SharePointDocument]:
    """Load all mock documents from *data_dir* (defaults to DATA_DIR env var or ../data/mock_docs)."""
    if data_dir is None:
        data_dir = os.environ.get(
            "DATA_DIR",
            str(Path(__file__).parent.parent.parent / "data" / "mock_docs"),
        )

    docs: List[SharePointDocument] = []
    docs_path = Path(data_dir)

    for meta in _MOCK_CATALOGUE:
        file_path = docs_path / meta["filename"]
        if not file_path.exists():
            continue
        content = file_path.read_text(encoding="utf-8")
        docs.append(
            SharePointDocument(
                title=meta["title"],
                content=content,
                library=meta["library"],
                owner=meta["owner"],
                last_modified=meta["last_modified"],
                source_url=meta["source_url"],
                file_type=meta["file_type"],
                doc_id=meta["doc_id"],
            )
        )

    return docs
