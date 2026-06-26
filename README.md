# Provenance Guard

A backend system that provides transparency for creative content sharing platforms.
It classifies submitted content (text, image, video), scores confidence, surfaces
transparency labels, manages appeals, and provides production-grade safety (rate
limiting, audit logging).

## Architecture Overview
Provenance Guard is a backend detection system that processes multi-modal content to
verify provenance.
1. **Submission:** API receives text/media.
2. **Normalization:** Media is transcribed to text.
3. **Detection:** Ensemble signals output scores.
4. **Scoring:** Weighted voting produces the final confidence level.

## Quickstart
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (use: source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

# Configure your key
copy .env .env.local            # then edit GROQ_API_KEY in .env

python run.py                   # serves on http://localhost:5000
```

Then open **http://localhost:5000** in your browser for the built-in UI — submit
content, file appeals, issue certificates, and watch the live dashboard and audit log.

### Example request
```bash
curl -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{"text": "The cat sat on the mat.", "creator_id": "alice"}'
```

### Run tests
```bash
pytest -q
```

## API Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| POST | `/submit` | Classify text/media content |
| POST | `/appeal` | Open an appeal; sets status to `under_review` |
| GET | `/log` | Recent audit entries |
| GET | `/dashboard` | Analytics metrics (appeal rate, breakdowns) |
| POST | `/certify` | Issue a "Verified Human" certificate |
| GET | `/health` | Liveness probe |
| GET | `/` | Browser UI (single-page dashboard) |

All endpoints except `/health` require the `X-API-Key` header.

## Transparency Labels
| Category | Label Text |
| :--- | :--- |
| High-Confidence AI | "This content shows strong indicators of being AI-generated." |
| Uncertain | "Attribution inconclusive. Contextual verification recommended." |
| High-Confidence Human | "This content displays human-typical stylistic variation." |

## Confidence Scoring & Ensemble Signals
We use a weighted voting approach (0.5 LLM, 0.3 Stylometric, 0.2 Metadata) to calculate
confidence.
- **Example 1 (AI):** Formal, low-variance text -> Score 0.85 -> "Likely AI".
- **Example 2 (Human):** Casual, high-variance text -> Score 0.20 -> "Likely Human".

## Stretch Features
- **Ensemble Detection:** Integrated 3 independent signals.
- **Provenance Certificate:** Implemented "Verified Human" badge via database lookup.
- **Analytics Dashboard:** Available at `/dashboard` showing real-time appeal rates.
- **Multi-modal Support:** Uses internal parsing to convert media (like
  `image_e7af9e.png`) into analysable transcripts.

## Known Limitations
- The system may misclassify highly stylized creative fiction that mimics AI patterns.
- Media normalization uses placeholder transcripts unless a VLM/ASR backend is wired in.

## Spec Reflection
- *Helped:* The spec forced me to define "Uncertainty" before coding, which prevented
  logic drift.
- *Diverged:* I added a metadata signal late, which required updating the `scoring.py`
  weighted average.

## AI Usage
1. **Normalization Logic:** Asked AI to write an `image_parser.py` wrapper for VLM
   inference.
2. **Flask-Limiter:** Used AI to debug `storage_uri` initialization in the `Limiter`
   configuration.
