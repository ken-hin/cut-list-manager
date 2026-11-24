# Cut List Manager: app folder

Setup and run instructions, the six operations, and the database notes are in
the project README: [`../README.md`](../README.md).

Quick start, from this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app init-db
flask --app app run
```
