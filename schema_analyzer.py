import sqlite3
import itertools
from collections import defaultdict

DATABASE = 'database.db'

def get_table_schemas():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    schemas = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        schemas[table] = columns
    
    conn.close()
    return schemas

def find_similar_columns(schemas):
    similar_columns = defaultdict(list)
    for table, columns in schemas.items():
        for column in columns:
            similar_columns[column.lower()].append((table, column))
    return {k: v for k, v in similar_columns.items() if len(v) > 1}

def suggest_views(schemas, similar_columns):
    views = []
    
    # Suggest views for tables with similar columns
    for column, tables in similar_columns.items():
        if len(tables) == 2:
            table1, col1 = tables[0]
            table2, col2 = tables[1]
            view_name = f"view_{table1}_{table2}"
            view_sql = f"""CREATE VIEW {view_name} AS
SELECT *
FROM {table1}
JOIN {table2} ON {table1}.{col1} = {table2}.{col2};"""
            views.append((view_name, view_sql))
    
    # Suggest views for tables with '_id' columns
    for table, columns in schemas.items():
        foreign_keys = [col for col in columns if col.endswith('_id') and col != f"{table[:-1]}_id"]
        for fk in foreign_keys:
            related_table = fk[:-3] + 's'
            if related_table in schemas:
                view_name = f"view_{table}_with_{related_table}"
                view_sql = f"""CREATE VIEW {view_name} AS
SELECT *
FROM {table}
JOIN {related_table} ON {table}.{fk} = {related_table}.{fk};"""
                views.append((view_name, view_sql))
    
    return views

def main():
    schemas = get_table_schemas()
    similar_columns = find_similar_columns(schemas)
    suggested_views = suggest_views(schemas, similar_columns)
    
    print("Suggested views:")
    for view_name, view_sql in suggested_views:
        print(f"\n-- {view_name}")
        print(view_sql)

if __name__ == "__main__":
    main()
