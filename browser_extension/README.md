# Smart Apply Agent — Chrome Extension

Browser-assisted Internship Copilot. Never auto-sends messages.

## Install

1. Open Chrome → `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked" → select this `browser_extension/` directory

## Usage

1. Start the local API: `uvicorn career_agent.api.app:app --host 127.0.0.1 --port 8765`
2. Open a BOSS/job listing page
3. Click the Smart Apply icon → side panel opens
4. Click "Analyze Current Page"
5. Review results, copy message, generate resume

## Safety

- Reads page text only
- Never auto-sends messages
- Never auto-applies
- Never saves passwords
