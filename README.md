# CSV SQL Graph

![CSV SQL Graph Demo](video.gif)

CSV SQL Graph is a web application that allows users to upload CSV files, convert them into SQLite tables, visualize table relationships, and perform SQL queries. It provides an intuitive interface for data analysis and exploration.

## Features

- CSV file upload and conversion to SQLite tables
- Automatic schema analysis and view suggestions
- Interactive graph visualization of table relationships
- SQL query execution with result display
- Combined view creation based on graph selection
- Table and view management (preview and delete)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/csv_sql_graph.git
   cd csv_sql_graph
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install flask sqlite3
   ```

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open a web browser and go to `http://localhost:8100`

3. Upload CSV files:
   - Click on "Choose File" under the "Upload CSV" section
   - Select a CSV file from your computer
   - Click "Upload"

4. Analyze schema and suggest views:
   - Click on "Analyze Schema and Suggest Views"
   - The application will generate suggested views based on the uploaded data

5. Explore suggested views:
   - Each suggested view shows the SQL query and a graph visualization
   - Click "Execute View" to see the results of the view

6. Combine views:
   - Check the boxes next to the views you want to combine
   - A combined graph will appear at the bottom
   - Click on a node in the combined graph to select it as the end node
   - Click "Combine Views" to generate a combined view based on the selected node

7. Run custom queries:
   - Enter your SQL query in the "Run Query" text area
   - Click "Run Query" to execute and see the results

8. Manage tables and views:
   - The "Available Tables" section shows all tables and views
   - Use the "Preview" button to see the contents of a table or view
   - Use the "Delete" button to remove a table or view (with confirmation)

## Example Data

The application comes with example CSV files that you can use to test its functionality:
- customers.csv
- products.csv
- orders.csv
- order_details.csv

You can download these files from the main page and upload them to explore the features.

## Notes

- The application uses an SQLite database named `database.db` in the root directory
- Uploaded CSV files are converted to SQLite tables with the same name as the file (without the .csv extension)
- The application runs in debug mode by default. For production use, set `debug=False` in `app.py`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
