from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import csv
import os
from schema_analyzer import get_table_schemas, find_similar_columns, suggest_views
from itertools import combinations
from collections import defaultdict

app = Flask(__name__)

DATABASE = 'database.db'
EXAMPLE_FILES = ['customers.csv', 'products.csv', 'orders.csv', 'order_details.csv']

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and file.filename.endswith('.csv'):
        filename = file.filename
        table_name = os.path.splitext(filename)[0]
        
        # Save CSV data to SQLite
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Read CSV and create table
        csv_data = csv.reader(file.stream.read().decode('utf-8').splitlines())
        headers = next(csv_data)
        
        # Create table
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join([f'{header} TEXT' for header in headers])})"
        cursor.execute(create_table_query)
        
        # Insert data
        insert_query = f"INSERT INTO {table_name} VALUES ({', '.join(['?' for _ in headers])})"
        cursor.executemany(insert_query, csv_data)
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'CSV file "{filename}" uploaded and saved to table "{table_name}"'})
    
    return jsonify({'error': 'Invalid file format'})

@app.route('/tables')
def get_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get views
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
    views = [row[0] for row in cursor.fetchall()]
    
    table_info = []
    for item in tables + views:
        cursor.execute(f"PRAGMA table_info({item})")
        columns = [col[1] for col in cursor.fetchall()]
        table_info.append({"name": item, "columns": columns, "type": "table" if item in tables else "view"})
    
    conn.close()
    return jsonify(table_info)

@app.route('/query', methods=['POST'])
def run_query():
    query = request.json['query']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        if cursor.description:
            columns = [description[0] for description in cursor.description]
        else:
            columns = []
        conn.close()
        return jsonify({'columns': columns, 'data': results})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'error': str(e)})

@app.route('/example/<filename>')
def download_example(filename):
    if filename in EXAMPLE_FILES:
        return send_file(filename, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/analyze_schema')
def analyze_schema():
    schemas = get_table_schemas()
    similar_columns = find_similar_columns(schemas)
    suggested_views = suggest_views(schemas, similar_columns)
    database_graph = build_database_graph()
    return jsonify({
        'suggested_views': list(suggested_views),  # Ensure it's a list
        'database_graph': database_graph
    })

@app.route('/combine_views', methods=['POST'])
def combine_views():
    view_names = request.json['view_names']
    schemas = get_table_schemas()
    database_graph = build_database_graph()
    
    # Get the tables involved in the selected views
    tables_involved = set()
    for view_name in view_names:
        tables = view_name.replace('view_', '').split('_with_')
        tables_involved.update(tables)
    
    # Find an optimal join sequence
    join_sequence = find_optimal_join_sequence(database_graph, list(tables_involved))
    
    if not join_sequence:
        return jsonify({'error': 'Unable to find a valid join sequence for the selected views'})
    
    return jsonify({'join_sequence': join_sequence, 'schemas': schemas, 'database_graph': database_graph})

def find_optimal_join_sequence(graph, tables):
    if len(tables) <= 1:
        return tables

    all_tables = set(tables)
    start_table = max(tables, key=lambda t: sum(len(connections) for connections in graph[t].values()))
    sequence = [start_table]
    visited = set([start_table])
    
    while len(visited) < len(all_tables):
        best_table = None
        best_score = -1
        
        for table in sequence:
            for next_table in graph[table]:
                if next_table in all_tables and next_table not in visited:
                    score = len(graph[table][next_table])
                    if score > best_score:
                        best_score = score
                        best_table = next_table
        
        if best_table is None:
            # If no direct connection is found, find any unvisited table
            for table in all_tables - visited:
                best_table = table
                break
        
        if best_table is None:
            return None
        
        sequence.append(best_table)
        visited.add(best_table)
    
    return sequence

@app.route('/execute_view', methods=['POST'])
def execute_view():
    query = request.json['query']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        # Extract the SELECT part of the query
        select_part = query[query.upper().index('SELECT'):]
        
        # Remove any trailing semicolon
        select_part = select_part.rstrip(';')
        
        # Add LIMIT if not present
        if 'LIMIT' not in select_part.upper():
            select_part += " LIMIT 100"
        
        # Execute the SELECT statement
        cursor.execute(select_part)
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        conn.close()
        return jsonify({'columns': columns, 'data': results})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'error': str(e)})
    except ValueError as e:
        conn.close()
        return jsonify({'error': 'Invalid query format. SELECT statement not found.'})

def build_database_graph():
    schemas = get_table_schemas()
    graph = defaultdict(dict)
    for table1, columns1 in schemas.items():
        for table2, columns2 in schemas.items():
            if table1 != table2:
                common_columns = set(columns1) & set(columns2)
                if common_columns:
                    graph[table1][table2] = list(common_columns)
    return graph

@app.route('/delete_table_or_view', methods=['POST'])
def delete_table_or_view():
    data = request.json
    name = data['name']
    item_type = data['type']
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        if item_type.lower() == 'view':
            cursor.execute(f"DROP VIEW IF EXISTS {name}")
        else:
            cursor.execute(f"DROP TABLE IF EXISTS {name}")
        
        conn.commit()
        conn.close()
        return jsonify({'message': f'{item_type.capitalize()} "{name}" has been deleted successfully.'})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8100)
