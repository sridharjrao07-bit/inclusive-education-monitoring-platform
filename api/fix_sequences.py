"""
Fix PostgreSQL sequence desync for all tables.
Run this once to reset all sequences to max(id) + 1.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from database import engine
from sqlalchemy import text

tables = ['schools', 'users', 'facilities', 'students', 'teachers', 'feedbacks']

with engine.connect() as conn:
    for table in tables:
        try:
            result = conn.execute(text(f'SELECT MAX(id) FROM {table}'))
            max_id = result.scalar() or 0
            print(f'{table}: max id = {max_id}')

            # Reset the sequence to max_id (next value will be max_id + 1)
            conn.execute(text(f"SELECT setval('{table}_id_seq', {max(max_id, 1)})"))
            print(f'  -> sequence reset to {max(max_id, 1)}')
        except Exception as e:
            print(f'  ERROR for {table}: {e}')
    conn.commit()

print('\nAll sequences fixed!')
