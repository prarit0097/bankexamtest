# Bank Exam Prep Platform

Python/Django web app for 2026 India banking-exam preparation. The app supports:

- Mock and topic-wise tests
- Automated scoring with right/wrong answer review
- Hybrid explanations: manual, RAG-grounded, or bootstrap AI fallback
- Likely-question practice sets based on historical pattern weighting
- Student profile dashboard with overall performance, recent tests, weak areas, opportunities, and goals
- Student name can be updated directly from the profile page
- In-app admin panel with platform overview, quick actions, recent activity, and deep control links
- Bootstrap AI mode that can serve tests before admin-uploaded corpus exists
- Admin content ingestion for papers, books, PDFs, and syllabus material
- Per-student Telegram daily summaries

## Stack

- Django 5.2
- PostgreSQL in production, SQLite fallback for local development
- Celery + Redis for ingestion, prediction, and Telegram jobs
- OpenAI API for question generation, explanations, and embeddings
- Backend-configured Telegram chat routing via `DEFAULT_TELEGRAM_CHAT_ID`

## Quick start

```bash
python -m pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_exam_taxonomy
python manage.py runserver
```

Default app login after migrations:
- Username: `chahat@gmail.com`
- Password: `Chahat@123`

If you want background ingestion to process queued uploads, run a Celery worker:

```bash
celery -A config worker -l info
```

## Key flows

1. Home page lets a student start a mock or topic-wise test.
2. If approved questions are insufficient, bootstrap AI generation fills the bank.
3. Submission calculates score, weak areas, and explanation payloads.
4. Admin can work from the in-app admin panel to inspect assets, questions, predictions, sessions, and logs.
5. Telegram reports are sent with `prep.tasks.send_daily_telegram_reports`.
6. Student form no longer asks for Telegram chat ID; backend default chat routing is controlled through `.env`.

## Notes

- Bootstrap AI tests are shown to students like regular tests, but stored with internal provenance.
- Prediction is exposed as probability-guided practice, not exact-exam guarantees.
- Payments and subscriptions are intentionally out of scope for V1.
