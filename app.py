from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import pyodbc
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

class NotesWebApp:
    def __init__(self):
        # Azure SQL Database connection strings (Cloud-first approach)
        self.connection_strings = [
            # Azure SQL with SQL Authentication (Primary for cloud)
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=laserlink.database.windows.net;DATABASE=LaserLink;UID={os.getenv('AZURE_SQL_USER', 'sqladmin')};PWD={os.getenv('AZURE_SQL_PASSWORD', '')};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;",
            
            # Azure SQL with Entra Authentication (for local development)
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=laserlink.database.windows.net;DATABASE=LaserLink;Authentication=ActiveDirectoryInteractive;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;",
            
            # Local connections (for testing)
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=LaserCloudDB;Trusted_Connection=yes;",
        ]
    
    def connect_to_db(self):
        """Establish database connection"""
        for i, conn_str in enumerate(self.connection_strings):
            try:
                print(f"Trying connection {i+1}")
                return pyodbc.connect(conn_str)
            except pyodbc.Error as e:
                print(f"Connection {i+1} failed: {e}")
                continue
        return None
    
    def get_all_notes(self):
        """Get all notes from database"""
        conn = self.connect_to_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, content, created_date 
                    FROM notes 
                    WHERE is_archived = 0 
                    ORDER BY created_date DESC
                """)
                notes = cursor.fetchall()
                conn.close()
                return notes
            except pyodbc.Error as e:
                print(f"Error fetching notes: {e}")
                conn.close()
        return []
    
    def add_note(self, content):
        """Add a new note"""
        conn = self.connect_to_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO notes (title, content, created_date, modified_date)
                    VALUES (?, ?, GETDATE(), GETDATE())
                """, (content[:50], content))
                conn.commit()
                conn.close()
                return True
            except pyodbc.Error as e:
                print(f"Error adding note: {e}")
                conn.close()
        return False
    
    def delete_note(self, note_id):
        """Delete a note"""
        conn = self.connect_to_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                conn.commit()
                conn.close()
                return True
            except pyodbc.Error as e:
                print(f"Error deleting note: {e}")
                conn.close()
        return False

# Initialize the notes app
notes_app = NotesWebApp()

@app.route('/')
def index():
    """Main page - display all notes"""
    notes = notes_app.get_all_notes()
    return render_template('index.html', notes=notes)

@app.route('/add_note', methods=['POST'])
def add_note():
    """Add a new note"""
    note_content = request.form.get('note_content', '').strip()
    
    if not note_content:
        flash('Please enter a note!', 'warning')
        return redirect(url_for('index'))
    
    if notes_app.add_note(note_content):
        flash('Note added successfully!', 'success')
    else:
        flash('Failed to add note. Please check database connection.', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_note/<int:note_id>')
def delete_note(note_id):
    """Delete a note"""
    if notes_app.delete_note(note_id):
        flash('Note deleted successfully!', 'success')
    else:
        flash('Failed to delete note.', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/notes')
def api_notes():
    """API endpoint to get notes as JSON"""
    notes = notes_app.get_all_notes()
    notes_data = []
    for note in notes:
        notes_data.append({
            'id': note[0],
            'title': note[1],
            'content': note[2],
            'created_date': note[3].strftime('%m/%d/%Y, %I:%M:%S %p')
        })
    return jsonify(notes_data)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)