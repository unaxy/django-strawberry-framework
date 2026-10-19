# Review: `django_strawberry_framework/auth/sessions.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: hot - once per login/logout mutation per request (twice on async bodies); per-mutation, never per-row
