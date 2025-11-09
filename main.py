import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pyodbc
from datetime import datetime

class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notes - Updated!")
        self.root.geometry("500x600")
        self.root.configure(bg="#FF69B4")  # Pink background
        
        # Database connection string - try multiple options
        self.connection_strings = [
            # Option 1: ODBC Driver 17 for SQL Server
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=LaserCloudDB;Trusted_Connection=yes;",
            # Option 2: ODBC Driver 18 for SQL Server  
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=LaserCloudDB;Trusted_Connection=yes;TrustServerCertificate=yes;",
            # Option 3: SQL Server Native Client
            "DRIVER={SQL Server Native Client 11.0};SERVER=localhost;DATABASE=LaserCloudDB;Trusted_Connection=yes;",
            # Option 4: Basic SQL Server driver
            "DRIVER={SQL Server};SERVER=localhost;DATABASE=LaserCloudDB;Trusted_Connection=yes;",
            # Option 5: Using server instance name
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=LaserCloudDB;Trusted_Connection=yes;",
        ]
        
        self.setup_ui()
        self.test_connection()
        self.load_notes()
    
    def setup_ui(self):
        # Title
        title_label = tk.Label(
            self.root, 
            text="Notes - Updated!", 
            font=("Arial", 20, "bold"),
            bg="#FF69B4", 
            fg="white"
        )
        title_label.pack(pady=20)
        
        # Input frame
        input_frame = tk.Frame(self.root, bg="#FF69B4")
        input_frame.pack(pady=10, padx=20, fill="x")
        
        # Text entry
        self.note_entry = tk.Text(
            input_frame,
            height=4,
            font=("Arial", 12),
            wrap=tk.WORD,
            relief="flat",
            bd=0
        )
        self.note_entry.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Add button
        add_button = tk.Button(
            input_frame,
            text="Add Note",
            font=("Arial", 11, "bold"),
            bg="#FFB6C1",
            fg="black",
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
            command=self.add_note,
            cursor="hand2"
        )
        add_button.pack(side="right", fill="y")
        
        # Notes frame with scrollbar
        notes_frame = tk.Frame(self.root, bg="#FF69B4")
        notes_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Canvas and scrollbar for scrollable notes
        canvas = tk.Canvas(notes_frame, bg="#FF69B4", highlightthickness=0)
        scrollbar = ttk.Scrollbar(notes_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#FF69B4")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas = canvas
    
    def test_connection(self):
        """Test database connection and show available drivers"""
        print("Available ODBC drivers:")
        try:
            drivers = pyodbc.drivers()
            for driver in drivers:
                print(f"  - {driver}")
        except Exception as e:
            print(f"Error getting drivers: {e}")
    
    def connect_to_db(self):
        """Establish database connection"""
        for i, conn_str in enumerate(self.connection_strings):
            try:
                print(f"Trying connection {i+1}: {conn_str}")
                return pyodbc.connect(conn_str)
            except pyodbc.Error as e:
                print(f"Connection {i+1} failed: {e}")
                continue
        
        # If all connections failed, show available drivers
        try:
            drivers = pyodbc.drivers()
            driver_list = '\n'.join(drivers)
            messagebox.showerror("Database Error", 
                f"Failed to connect with all connection strings.\n\n"
                f"Available ODBC drivers:\n{driver_list}\n\n"
                f"Please check:\n"
                f"1. SQL Server is running\n"
                f"2. LaserCloudDB database exists\n"
                f"3. You have the right SQL Server drivers installed")
        except:
            messagebox.showerror("Database Error", 
                f"Failed to connect to database.\n\n"
                f"Please check:\n"
                f"1. SQL Server is running\n"
                f"2. LaserCloudDB database exists\n"
                f"3. Install SQL Server ODBC drivers")
        return None
    
    def add_note(self):
        """Add a new note to the database"""
        note_text = self.note_entry.get("1.0", tk.END).strip()
        
        if not note_text:
            messagebox.showwarning("Warning", "Please enter a note!")
            return
        
        # Connect to database and insert note
        conn = self.connect_to_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO notes (title, content, created_date, modified_date)
                    VALUES (?, ?, GETDATE(), GETDATE())
                """, (note_text[:50], note_text))  # Use first 50 chars as title
                conn.commit()
                conn.close()
                
                # Clear the entry
                self.note_entry.delete("1.0", tk.END)
                
                # Reload notes
                self.load_notes()
                
                messagebox.showinfo("Success", "Note added successfully!")
                
            except pyodbc.Error as e:
                messagebox.showerror("Database Error", f"Failed to add note:\n{e}")
                conn.close()
    
    def load_notes(self):
        """Load all notes from the database"""
        # Clear existing notes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Connect to database and fetch notes
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
                
                # Display notes
                for note in notes:
                    self.create_note_widget(note)
                
                # Update scroll region
                self.canvas.update_idletasks()
                
            except pyodbc.Error as e:
                messagebox.showerror("Database Error", f"Failed to load notes:\n{e}")
                conn.close()
    
    def create_note_widget(self, note):
        """Create a widget for displaying a note"""
        note_id, title, content, created_date = note
        
        # Note container
        note_frame = tk.Frame(
            self.scrollable_frame,
            bg="white",
            relief="flat",
            bd=0
        )
        note_frame.pack(fill="x", pady=5, padx=10)
        
        # Content frame
        content_frame = tk.Frame(note_frame, bg="white")
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Note text
        note_label = tk.Label(
            content_frame,
            text=content,
            font=("Arial", 11),
            bg="white",
            fg="black",
            justify="left",
            wraplength=350,
            anchor="w"
        )
        note_label.pack(anchor="w")
        
        # Created date
        date_str = created_date.strftime("%m/%d/%Y, %I:%M:%S %p")
        date_label = tk.Label(
            content_frame,
            text=f"Created: {date_str}",
            font=("Arial", 9),
            bg="white",
            fg="gray",
            anchor="w"
        )
        date_label.pack(anchor="w", pady=(5, 0))
        
        # Delete button
        delete_button = tk.Button(
            note_frame,
            text="✖",
            font=("Arial", 12, "bold"),
            bg="#FF69B4",
            fg="white",
            relief="flat",
            bd=0,
            width=3,
            height=1,
            command=lambda: self.delete_note(note_id),
            cursor="hand2"
        )
        delete_button.pack(side="right", padx=10, pady=10)
    
    def delete_note(self, note_id):
        """Delete a note from the database"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this note?"):
            conn = self.connect_to_db()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                    conn.commit()
                    conn.close()
                    
                    # Reload notes
                    self.load_notes()
                    
                    messagebox.showinfo("Success", "Note deleted successfully!")
                    
                except pyodbc.Error as e:
                    messagebox.showerror("Database Error", f"Failed to delete note:\n{e}")
                    conn.close()

def main():
    root = tk.Tk()
    app = NotesApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()