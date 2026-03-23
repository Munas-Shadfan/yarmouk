# PDF Extraction & Knowledge Integration Guide

## Overview

The Yarmouk University AI Assistant now has **advanced PDF extraction capabilities** to automatically retrieve and process official university documents. This ensures accurate, up-to-date information directly from authoritative sources.

## Features

### ✨ Modern Best Practices

- **Lazy Loading**: PDFs are fetched and processed only when needed
- **Semantic Chunking**: Documents split into meaningful 1000-char chunks with 100-char overlap
- **In-Memory Caching**: Prevents re-processing of the same PDFs within a session
- **Security**: Restricted to `yu.edu.jo` domain only
- **Error Recovery**: Graceful handling of corrupted/inaccessible PDFs
- **Async/Await**: Non-blocking async operations for fast response times

### 🎯 What It Can Extract

✅ **Academic Calendars** — Registration deadlines, exam dates, semester schedules  
✅ **Admission Requirements** — Prerequisites, GPA thresholds, application procedures  
✅ **Financial Aid & Fees** — Scholarship details, payment schedules, fee structures  
✅ **Registration Procedures** — Course selection guidelines, add/drop deadlines  
✅ **Graduation Requirements** — Degree checklists, final procedures, thesis guidelines  
✅ **Policy Documents** — Academic conduct, disciplinary procedures, student handbook  
✅ **Course Syllabi** — Learning outcomes, assignments, grading criteria  

---

## How the Agent Uses PDFs

### 1. **Detection Phase**
When a user asks about procedural information, deadlines, or requirements, the agent recognizes PDF queries based on keywords:
- "registration", "deadline", "requirements", "policy", "admission", etc.

### 2. **Search Phase**
The agent uses `tavily_tool` to locate relevant PDFs on `yu.edu.jo`:
```
Query: "What are the registration deadlines?"
→ Tavily searches yu.edu.jo for academic calendar PDFs
→ Returns URLs pointing to official documents
```

### 3. **Extraction Phase**
The agent calls `pdf_extraction_tool` with the PDF URL:
```python
pdf_extraction_tool(
    pdf_url="https://yu.edu.jo/files/academic-calendar-2025.pdf",
    query="registration deadline"
)
```

### 4. **Response Phase**
The tool returns:
- Extracted text in semantic chunks
- Keyword-filtered relevant sections
- Original URL for user reference

---

## Tool: `pdf_extraction_tool`

### Signature
```python
@tool
async def pdf_extraction_tool(pdf_url: str, query: str = "") -> str:
    """Extract and search PDF documents on yu.edu.jo"""
```

### Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `pdf_url` | str | Full or relative URL to the PDF. Must be on `yu.edu.jo` |
| `query` | str | Optional filter query to search within extracted content |

### Returns
```
📄 **PDF**: https://yu.edu.jo/path/to/document.pdf
**Relevant content** (5 chunks matched):
[semantic chunks of text...]
```

### Error Handling
- **Domain validation**: Rejects non-`yu.edu.jo` URLs with clear message
- **HTTP errors**: Returns readable error messages for 404, timeout, etc.
- **Corrupt PDFs**: Attempts page-by-page extraction, marks unreadable pages
- **Empty PDFs**: Gracefully informs user if no extractable content found

---

## Architecture

```
User Query
    ↓
Agent (LLM + ReAct)
    ↓
├─→ tavily_tool (web search) → finds PDF URLs
│       ↓
│   (returns search results with links)
│
├─→ pdf_extraction_tool (PDF processing) → extracts content
│       ├─ fetch_pdf_async (aiohttp, timeout handling)
│       ├─ extract_text_from_pdf_bytes (PyPDF2, page-by-page)
│       ├─ semantic chunking (RecursiveCharacterTextSplitter)
│       ├─ in-memory cache (hashlib MD5 lookup)
│       └─ returns {chunks, summary, metadata}
│
└─→ Synthesized Answer to User
```

### Caching Strategy
- **Cache Key**: MD5 hash of URL
- **Scope**: Per-session (in-memory dict)
- **Expires**: When session ends or `clear_pdf_cache()` called
- **Benefits**: Avoid re-parsing the same PDF twice in one conversation

---

## Example Conversations

### Example 1: Registration Deadlines
```
User: When is the registration deadline for next semester?

Agent Thought:
1. User asking about registration → need academic calendar PDF
2. Search for "Yarmouk registration deadline 2025"
3. Tavily returns: https://yu.edu.jo/calendar/academic-2024-2025.pdf
4. Extract PDF with query: "registration deadline"
5. PDF contains: "Spring 2025 Registration: Feb 1-14, 2025"

Agent Response:
"The spring 2025 registration period is **February 1-14, 2025**.
Make sure to register during this window, as late registration 
may incur additional fees."
```

### Example 2: Admission Requirements
```
User: What are the requirements to be admitted to the Computer Science program?

Agent Actions:
1. Search: "Yarmouk Computer Science admission requirements"
2. Tavily finds: https://yu.edu.jo/programs/cs/admission.pdf
3. Extract PDF with query: "CS admission requirements GPA"
4. PDF contains: "GPA: 85+ | Prerequisites: Mathematics, Physics"

Agent Response:
"To be admitted to Computer Science, you need:
• High school GPA of 85 or higher
• Minimum score of 70 in Mathematics
• Minimum score of 70 in Physics

[Full details from official admission PDF]"
```

---

## Dependencies

```
PyPDF2>=4.0.0           # PDF text extraction
langchain-text-splitters>=0.1.0  # Semantic chunking
aiohttp>=3.9.0          # Async HTTP requests
langchain-core>=0.1.0   # Tool definitions
```

**Installation:**
```bash
pip install PyPDF2 langchain-text-splitters aiohttp
```

---

## Best Practices for Agents/Developers

### ✅ When to Use PDF Extraction

- User asks about **specific dates, deadlines, or procedures**
- Search results contain **PDF links**
- User asks about **official requirements** (admission, graduation, etc.)
- Information likely exists in **downloadable documents** (syllabi, handbooks)

### ❌ When NOT to Use (Use Tavily Instead)

- General university news or announcements
- Faculty contact information (usually on web pages)
- Department descriptions or services
- Room numbers or building locations

### 🔍 Pro Tips

1. **Combine Tools**: First use `tavily_tool` to find PDFs, then use `pdf_extraction_tool` to extract content
2. **Be Specific**: When passing a query, use the exact keywords from the user's question
3. **Expect Failures Gracefully**: PDFs may be inaccessible, corrupted, or updated — always offer alternative help
4. **Preserve URLs**: Always include the source PDF URL in your response for transparency

---

## Future Enhancements

🚀 **Planned improvements:**
- Vector database (Pinecone/Weaviate) for semantic search across all PDFs
- Multi-language document support (Arabic/English)
- OCR fallback for scanned PDFs
- Automatic PDF discovery on university crawl
- PDF version tracking and update notifications

---

## Monitoring & Debugging

### Check Cache Status
```python
from agent.tools.pdf_extractor import _pdf_cache
print(f"Cached PDFs: {len(_pdf_cache)}")
```

### Clear Cache (if needed)
```python
from agent.tools.pdf_extractor import clear_pdf_cache
clear_pdf_cache()
```

### Enable Debug Logging
```python
import logging
logging.getLogger("agent.tools.pdf_extractor").setLevel(logging.DEBUG)
```

---

## Security & Compliance

✅ **Domain Restriction**: Only processes PDFs from `yu.edu.jo`  
✅ **No PII Storage**: Cache cleared after session  
✅ **Timeout Protection**: 10-second fetch timeout  
✅ **File Type Validation**: Only accepts `application/pdf` MIME type  
✅ **Error Transparency**: Users see exactly what failed and why  

---

Generated: March 2025 | Yarmouk University AI Assistant
