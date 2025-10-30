import os
from dotenv import load_dotenv
import psycopg2

# 1. 환경 변수 로드
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "database": os.getenv("PG_DATABASE"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "port": os.getenv("PG_PORT"),
    "sslmode": "require"
}

# 2. schema.sql 파일 읽기
with open("schema.sql", "r", encoding="utf-8") as f:
    schema_sql = f.read()

# 3. PostgreSQL 연결 및 실행
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute(schema_sql)
    conn.commit()

    print("✅ Tables created successfully!")

except Exception as e:
    print("❌ Error:", e)

finally:
    if conn:
        cur.close()
        conn.close()