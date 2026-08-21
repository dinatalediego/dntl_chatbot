import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("MEDALLIO_DATABASE_URL", "sqlite:///:memory:")
