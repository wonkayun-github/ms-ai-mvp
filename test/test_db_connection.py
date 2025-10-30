import os
from dotenv import load_dotenv
import psycopg2

# 1. 환경 변수 로드
load_dotenv()

# 2. DB 연결 정보
DB_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "database": os.getenv("PG_DATABASE"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "port": os.getenv("PG_PORT")
}

# 3. DB 연결 테스트
try:
    print("🔄 Connecting to PostgreSQL server...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 간단한 쿼리 실행
    cur.execute("SELECT version();")
    version = cur.fetchone()

    print("✅ Connection successful!")
    print("PostgreSQL version:", version[0])

except Exception as e:
    print("❌ Connection failed!")
    print("Error:", e)

finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
