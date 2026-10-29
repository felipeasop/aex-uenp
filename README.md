# Lua e Flor

Para iniciar a aplicação localmente:

```bash
venv/bin/python manage.py migrate
venv/bin/python populate_db.py
venv/bin/python manage.py runserver
```

A loja fica disponível em `http://127.0.0.1:8000/` e o painel administrativo em
`http://127.0.0.1:8000/admin/`.
