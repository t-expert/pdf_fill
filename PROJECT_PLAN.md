# Project Plan: AI-Powered PDF Form Filler

**Phase 1: Information Gathering & Clarification (Completed)**

**Phase 2: Planning**

**1. Project Goal:**
Create a system consisting of a Python-based MCP server and a Flask web interface. The system will allow users to upload PDF forms, provide data via natural language chat or CSV upload, use Google Gemini to extract relevant information, fill the PDF form fields using the extracted data, and download the filled PDF.

**2. Core Technologies:**
*   **Backend (MCP Server):** Python, `pypdf` (for PDF manipulation), Google Gemini API Client Library, `@modelcontextprotocol/sdk` (or equivalent Python MCP library if available, otherwise build according to spec).
*   **Frontend (Chat Interface):** Flask, HTML, CSS, JavaScript.
*   **AI Model:** Google Gemini (via API).
*   **Environment:** Python Virtual Environment.

**3. Project Structure:**

```
Gemini_PDF_fill/
├── pdf_filler_mcp_server/       # Directory for the MCP server code
│   ├── venv/                    # Python virtual environment
│   ├── src/
│   │   ├── __init__.py
│   │   ├── server.py            # Main MCP server logic (stdio communication)
│   │   ├── pdf_utils.py         # Functions for pypdf (get_fields, fill_form)
│   │   ├── gemini_utils.py      # Functions for Gemini interaction (extract_data)
│   │   └── requirements.txt     # Python dependencies for the server
│   └── run_server.bat           # Simple script to run the server (activates venv)
├── chat_interface/              # Directory for the Flask web application
│   ├── venv/                    # Python virtual environment
│   ├── app.py                   # Flask application logic
│   ├── requirements.txt         # Python dependencies for the web app
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # CSS styles
│   │   └── js/
│   │       └── script.js        # Frontend JavaScript
│   ├── templates/
│   │   └── index.html           # Main HTML page
│   ├── uploads/                 # Temporary storage for uploaded PDFs/CSVs
│   └── downloads/               # Temporary storage for filled PDFs
├── .gitignore                   # Git ignore file
└── README.md                    # Project documentation
```

**4. Key Components & Functionality:**

*   **PDF Filler MCP Server (`pdf_filler_mcp_server`):**
    *   Runs as a local stdio MCP server.
    *   Requires `GEMINI_API_KEY` environment variable.
    *   **Tools Exposed:**
        *   `get_pdf_fields`:
            *   Input: `{"pdf_path": "path/to/uploaded.pdf"}`
            *   Output: `{"fields": {"field_name1": "type", "field_name2": "type", ...}}` (JSON describing form fields)
            *   Uses `pypdf` to read the PDF and extract field names and types.
        *   `extract_data_for_pdf`:
            *   Input: `{"text": "User's natural language input", "fields": ["field_name1", "field_name2", ...]}`
            *   Output: `{"data": {"field_name1": "extracted_value1", ...}}` (JSON with data extracted by AI)
            *   Sends the text and target field names to Gemini with a prompt engineered to extract structured data suitable for the fields.
        *   `fill_pdf_form`:
            *   Input: `{"pdf_path": "path/to/original.pdf", "data": {"field_name1": "value1", ...}, "output_path": "path/to/filled.pdf"}`
            *   Output: `{"status": "success", "filled_pdf_path": "path/to/filled.pdf"}` or `{"status": "error", "message": "..."}`
            *   Uses `pypdf` to fill the specified fields in the PDF with the provided data and saves it to the output path.
*   **Chat Interface (`chat_interface`):**
    *   **UI:** Simple chat window, file upload button (accepts `.pdf`, `.csv`), area to display messages, list of filled fields, and download links.
    *   **Backend (Flask):**
        *   Serves `index.html`.
        *   Handles PDF uploads: Saves PDF to `uploads/`, calls MCP `get_pdf_fields`, stores fields in user session/context.
        *   Handles CSV uploads: Saves CSV to `uploads/`, parses it. For each row, determines if data needs Gemini extraction or can be used directly, calls MCP `extract_data_for_pdf` (if needed) and `fill_pdf_form`. Generates download links for each filled PDF (or potentially zips them).
        *   Handles text input: If a PDF's fields are known (from upload), calls MCP `extract_data_for_pdf` with user text and stored fields, then calls `fill_pdf_form`.
        *   Displays agent responses, lists of filled fields, and download links for generated PDFs (served from `downloads/`).
        *   Manages temporary files in `uploads/` and `downloads/`.

**5. High-Level Architecture Diagram:**

```mermaid
graph TD
    User[User] -- Interacts via Browser --> ChatUI[Chat Interface (Flask/HTML/JS/CSS)]
    ChatUI -- Uploads PDF/CSV --> FlaskBE[Flask Backend (app.py)]
    ChatUI -- Sends Text --> FlaskBE

    FlaskBE -- Manages Files --> TempStorage[uploads/ & downloads/ Dirs]
    FlaskBE -- Calls Tools --> RooCline[Roo/Cline Environment]

    RooCline -- Executes --> MCPServer[PDF Filler MCP Server (Python/pypdf)]
    MCPServer -- Reads/Writes --> PDFStore[PDF Files (e.g., in TempStorage)]
    MCPServer -- Calls --> GeminiAPI[Google Gemini API]

    FlaskBE -- Serves Filled PDF --> User
    FlaskBE -- Displays Status/Links --> ChatUI

    subgraph "User's Machine"
        subgraph "Web Application (chat_interface)"
            ChatUI
            FlaskBE
            TempStorage
        end
        subgraph "MCP Server Process (pdf_filler_mcp_server)"
            MCPServer
        end
        RooCline
        PDFStore
    end

    subgraph "Google Cloud"
        GeminiAPI
    end
```

**6. Implementation Steps:**

1.  **Setup:** Create base directories (`pdf_filler_mcp_server`, `chat_interface`), initialize Git (`.gitignore`).
2.  **MCP Server Dev:**
    *   Set up Python virtual environment (`pdf_filler_mcp_server/venv`).
    *   Install dependencies (`pypdf`, `google-generativeai`, potentially an MCP SDK helper or build stdio communication manually).
    *   Implement `pdf_utils.py` (`get_pdf_fields`, `fill_pdf_form`).
    *   Implement `gemini_utils.py` (`extract_data_for_pdf`).
    *   Implement `server.py` handling MCP requests over stdio, calling utility functions.
    *   Create `run_server.bat`.
3.  **Chat Interface Dev:**
    *   Set up Python virtual environment (`chat_interface/venv`).
    *   Install dependencies (`Flask`).
    *   Create basic HTML (`templates/index.html`), CSS (`static/css/style.css`), JS (`static/js/script.js`).
    *   Implement Flask routes in `app.py` for serving files, handling uploads, processing chat messages, and interacting with the (yet to be configured) MCP server via Roo/Cline.
    *   Implement JS for fetch requests to Flask backend, UI updates, file uploads.
4.  **MCP Configuration:**
    *   Guide user to get Gemini API Key.
    *   Use `ask_followup_question` to get the key.
    *   Construct the MCP JSON configuration pointing to the `server.py` script (or compiled executable if we go that route) and including the API key in `env`.
    *   Use `read_file` and `write_to_file` (or `apply_diff`) to add this configuration to `mcp_settings.json`.
5.  **Integration & Testing:**
    *   Start the Flask app.
    *   Ensure MCP server is started by Roo/Cline.
    *   Test PDF upload and field extraction.
    *   Test text input -> Gemini extraction -> PDF filling -> download.
    *   Test CSV upload -> batch filling -> downloads.
    *   Test with `ABC SA Form.pdf` and sample data.
6.  **Documentation:** Write `README.md`.

**7. Future Enhancements (Post-MVP):**
*   More sophisticated agent logic (error handling, clarification questions, self-correction).
*   Support for different PDF structures (non-form PDFs).
*   Improved UI/UX.
*   Zipping batch downloads.
*   More robust session management.

**Phase 3: Implementation (Switching to Code Mode)**