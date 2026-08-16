# Contributing

GoreeCloud Monitor is developed repository-first. Keep changes focused, documented, tested, and consistent with the GoreeCloud project specification and Glaze UI.

Before opening a pull request:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Never commit secrets, production `.env` files, private keys, database exports, or user data.
