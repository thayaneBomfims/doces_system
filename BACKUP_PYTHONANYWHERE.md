# Backup de banco (PythonAnywhere)

Este projeto usa SQLite. O script abaixo cria backup com timestamp e remove os antigos automaticamente.

## 1) Executar manualmente

No Bash Console do PythonAnywhere, dentro da pasta do projeto:

```bash
cd ~/doces_system
python scripts/backup_sqlite.py --db db.sqlite3 --out /home/<seu_usuario>/backups/doces_system --keep 30
```

- `--keep 30`: mantem os 30 backups mais recentes.
- Por padrao o backup eh comprimido (`.sqlite3.gz`).

## 2) Agendar no PythonAnywhere (Scheduled tasks)

No painel do PythonAnywhere:

1. Abra **Tasks**
2. Clique em **Add a new scheduled task**
3. Use um comando como:

```bash
cd /home/<seu_usuario>/doces_system ; /home/<seu_usuario>/.virtualenvs/<seu_venv>/bin/python scripts/backup_sqlite.py --db db.sqlite3 --out /home/<seu_usuario>/backups/doces_system --keep 30
```

Sugestao: agendar 1 vez por dia (ex.: 02:30).

## 3) Restaurar backup

1. Pare o web app no PythonAnywhere.
2. Faça backup do arquivo atual, por seguranca.
3. Restaure o arquivo:

```bash
cp /home/<seu_usuario>/backups/doces_system/db_YYYYMMDD_HHMMSS.sqlite3.gz /tmp/db_restore.sqlite3.gz
gunzip -f /tmp/db_restore.sqlite3.gz
cp /tmp/db_restore.sqlite3 /home/<seu_usuario>/doces_system/db.sqlite3
```

4. Inicie novamente o web app.

## 4) Opcional: enviar para armazenamento externo

Como boa pratica, mantenha uma copia fora do servidor (Drive, S3, etc.).

