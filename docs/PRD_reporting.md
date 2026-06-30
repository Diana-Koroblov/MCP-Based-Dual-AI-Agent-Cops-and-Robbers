# PRD: Automated Reporting Mechanism
**Version:** 1.00 | Part of: Cops & Robbers MCP Assignment

---

## 1. Description

After all 6 sub-games complete, the system automatically generates a structured JSON report and sends it as an email via the Gmail API (OAuth2). No SMTP, no user intervention, no attachment — the JSON is the email body. The report is triggered by `GameSDK.send_report()`, which delegates to the API Gatekeeper.

---

## 2. Theoretical Background

The Gmail API requires OAuth2 authorization, not username/password authentication. On the first run, a browser-based OAuth flow presents a consent screen and writes a `token.json` file. Subsequent runs use the saved token silently, refreshing it automatically when it expires. Credentials are stored in `my_google.json` (downloaded from Google Cloud Console) and must never be committed to the repository.

---

## 3. Gmail API Setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → Create project → Enable Gmail API
2. OAuth consent screen: External; add your Gmail as a test user
3. Create credentials: OAuth 2.0 Client ID → Desktop App → Download → save as `my_google.json` **outside** the project directory (e.g., `~/private_google/my_google.json`)
4. Set environment variable: `GMAIL_CREDENTIALS_PATH=~/private_google/my_google.json`
5. Run the app once: a browser window opens → grant access → `token.json` is written next to `my_google.json`
6. Every subsequent run: `token.json` is used silently; browser not required

---

## 4. JSON Report Schema

The email body must be **valid JSON only** — no prose, no greeting, no subject explanation.

```json
{
  "student_id": "<YOUR_STUDENT_ID>",
  "timestamp": "2024-12-01T14:30:00Z",
  "game_config": {
    "grid_size": [5, 5],
    "max_moves": 25,
    "num_games": 6,
    "max_barriers": 5,
    "visibility_radius": 2,
    "llm_provider": "gemini"
  },
  "sub_games": [
    {
      "game_id": 1,
      "winner": "cop",
      "moves": 18,
      "cop_score": 10,
      "thief_score": 0,
      "barriers_placed": 3,
      "messages_exchanged": 36,
      "technical_failures": 0
    }
  ],
  "totals": {
    "cop_total_score": 35,
    "thief_total_score": 25,
    "cop_wins": 3,
    "thief_wins": 3,
    "technical_failures_total": 0
  },
  "llm_usage": {
    "total_input_tokens": 14200,
    "total_output_tokens": 3800,
    "estimated_cost_usd": 0.0042
  }
}
```

---

## 5. Email Trigger Logic

- Report is sent exactly once: after the 6th valid sub-game completes
- Sending is triggered by `full_game.py` → `GameSDK.send_report()` → `gatekeeper.py` → `gmail_sender.py`
- If sending fails, the error is logged and raised (does NOT trigger a sub-game rerun)
- Recipient address: `rmisegal+uoh26b@gmail.com`
- Subject line: `Cops and Robbers — Student ID: <YOUR_STUDENT_ID>`
- Body: JSON string only (no markdown, no explanation)

---

## 6. Inputs

| Input | Source |
|-------|--------|
| `SubGameResult` × 6 | `full_game.py` via `GameSDK` |
| `game_config` dict | `config.json` |
| `llm_usage` totals | `gatekeeper.py` token log |
| `GMAIL_CREDENTIALS_PATH` | `.env` |
| Student ID | `config.json` |

---

## 7. Outputs

| Output | Consumer |
|--------|----------|
| Sent email with JSON body | Instructor (rmisegal+uoh26b@gmail.com) |
| Local log entry: "Email sent; subject; timestamp" | `logging` module |
| Error log if sending fails | `logging` module; exception re-raised |

---

## 8. Security Requirements

- `my_google.json` and `token.json` must be stored **outside** the project directory
- Both must be listed in `.gitignore` (by path pattern) even if stored outside
- `GMAIL_CREDENTIALS_PATH` must be set via environment variable, not hardcoded
- Minimal OAuth scope: `https://www.googleapis.com/auth/gmail.send` only — no read, modify, or delete scope

---

## 9. Performance Expectations

- JSON generation (6 sub-games): < 10 ms
- Gmail send (via API): < 5 seconds under normal network conditions
- On failure: 3 retries with 2-second delay (handled by Gatekeeper)

---

## 10. Alternatives Considered

| Alternative | Reason rejected |
|-------------|----------------|
| SMTP email | Requires Gmail "less secure app access" which Google has deprecated; OAuth2 is the only supported path |
| Attachment (JSON file attached to email) | Assignment requires JSON as the email body, not an attachment |
| Send after each sub-game | Assignment requires one report at the end of the full 6-game series |
| Store credentials inside project directory | Security risk; credentials committed to Git are considered compromised |

---

## 11. Success Criteria and Test Scenarios

| Scenario | Expected result |
|----------|----------------|
| 6 sub-games complete successfully | `gmail_sender.py` called exactly once |
| `json_builder.py` given valid sub-game results | Returns valid JSON matching schema; `json.loads()` succeeds |
| `json_builder.py` given missing field | Raises `ValueError` with a clear message identifying the missing field |
| `gmail_sender.py` called in test (mocked) | Mock receives expected recipient, subject, and JSON body |
| Credentials file not found at startup | Raises `FileNotFoundError` with path shown in error message |
| OAuth token expired | Library auto-refreshes token; email sends successfully without user action |
| Network error during send | Gatekeeper retries 3 times; on 3rd failure, exception logged and re-raised |
