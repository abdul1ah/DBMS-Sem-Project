import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from configparser import ConfigParser
from firebase_admin import credentials, firestore
import firebase_admin


def config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in {filename}')
    return db


def get_db_connection():
    try:
        params = config()
        connection = psycopg2.connect(**params)
        return connection
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None


def backup_database():
    
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate("C:/Users/idekb/OneDrive/Desktop/Project/player-portal-backup-firebase-adminsdk-fbsvc-ff02727fc1.json")
            firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        messagebox.showerror("Firebase Error", f"Error initializing Firebase:\n{e}")
        return

   
    conn = get_db_connection()
    if conn is None:
        messagebox.showerror("Database Error", "Could not connect to PostgreSQL database.")
        return

    cursor = conn.cursor()


    tables = {
        "users": "users",
        "games": "games",
        "player_games": "player_games",
        "teams": "teams",
        "team_members": "team_members",
        "tournaments": "tournaments",
        "tournament_participants": "tournament_participants",
        "matches": "matches",
        "player_stats": "player_stats"
    }


    try:
        for table, collection in tables.items():

            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            for row in rows:
                data = dict(zip(columns, row))
                db.collection(collection).add(data)
        messagebox.showinfo("Success", "Database backed up to Firebase successfully.")

    except Exception as e:
        messagebox.showerror("Backup Error", f"Error during backup:\n{e}")
    finally:
        cursor.close()
        conn.close()



def setup_styles():
    style = ttk.Style()
    style.configure('TFrame', background='#f0f0f0')
    style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
    style.configure('TButton', font=('Arial', 10))
    style.configure('Header.TLabel', font=('Arial', 16, 'bold'))
    style.configure('TEntry', font=('Arial', 10))

def clear_window(root):
    for widget in root.winfo_children():
        widget.destroy()

def get_games():
    conn = get_db_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM games")
    games = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return games

def get_players():
    conn = get_db_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE role = 'player'")
    players = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return players

def get_teams():
    conn = get_db_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM teams")
    teams = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return teams

def login(root, username_var, password_var):
    username = username_var.get()
    password = password_var.get()
    
    if not username or not password:
        messagebox.showerror("Error", "Please fill in all fields")
        return
    
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, role FROM users WHERE username = %s AND password = %s",
                  (username, password))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user:
        current_user = {'id': user[0], 'username': username, 'role': user[1]}
        if user[1] == 'admin':
            show_admin_dashboard(root, current_user)
        else:
            show_player_dashboard(root, current_user)
    else:
        messagebox.showerror("Error", "Invalid username or password")

def register_user(root, username_var, password_var):
    username = username_var.get()
    password = password_var.get()
    
    if not username or not password:
        messagebox.showerror("Error", "Please fill in all fields")
        return
    
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
   
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        messagebox.showerror("Error", "Username already exists")
        cursor.close()
        conn.close()
        return
    
    
    cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (%s, %s, 'player')
        RETURNING id
    """, (username, password))
    
    user_id = cursor.fetchone()[0]
    
    
    cursor.execute("""
        INSERT INTO player_stats (player_id)
        VALUES (%s)
    """, (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    messagebox.showinfo("Success", "Registration successful! Please login.")
    show_login_window(root)

def show_register_window(root):
    clear_window(root)
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(expand=True, fill='both')
    
    ttk.Label(main_frame, text="Register New Player", style='Header.TLabel').pack(pady=20)
    
    register_frame = ttk.Frame(main_frame)
    register_frame.pack(pady=10)
    
    ttk.Label(register_frame, text="Username:").grid(row=0, column=0, pady=5, padx=5)
    username_var = tk.StringVar()
    ttk.Entry(register_frame, textvariable=username_var, width=30).grid(row=0, column=1, pady=5)
    
    ttk.Label(register_frame, text="Password:").grid(row=1, column=0, pady=5, padx=5)
    password_var = tk.StringVar()
    ttk.Entry(register_frame, textvariable=password_var, width=30, show="*").grid(row=1, column=1, pady=5)
    
    ttk.Button(register_frame, text="Register", 
               command=lambda: register_user(root, username_var, password_var), 
               width=20).grid(row=2, column=0, columnspan=2, pady=10)
    
    ttk.Button(register_frame, text="Back to Login", 
               command=lambda: show_login_window(root), 
               width=20).grid(row=3, column=0, columnspan=2, pady=5)

def show_login_window(root):
    clear_window(root)
    setup_styles()
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(expand=True, fill='both')
    
    ttk.Label(main_frame, text="Gaming Portal Project", style='Header.TLabel').pack(pady=20)
    
    login_frame = ttk.Frame(main_frame)
    login_frame.pack(pady=10)
    
    ttk.Label(login_frame, text="Username:").grid(row=0, column=0, pady=5, padx=5)
    username_var = tk.StringVar()
    ttk.Entry(login_frame, textvariable=username_var, width=30).grid(row=0, column=1, pady=5)
    
    ttk.Label(login_frame, text="Password:").grid(row=1, column=0, pady=5, padx=5)
    password_var = tk.StringVar()
    ttk.Entry(login_frame, textvariable=password_var, width=30, show="*").grid(row=1, column=1, pady=5)
    
    ttk.Button(login_frame, text="Login", 
               command=lambda: login(root, username_var, password_var), 
               width=20).grid(row=2, column=0, columnspan=2, pady=10)
    
    ttk.Button(login_frame, text="Register as Player", 
               command=lambda: show_register_window(root), 
               width=20).grid(row=3, column=0, columnspan=2, pady=5)
    
    ttk.Button(login_frame, text="View as Spectator", 
               command=lambda: show_spectator_view(root), 
               width=20).grid(row=4, column=0, columnspan=2, pady=5)

def show_spectator_view(root):
    clear_window(root)
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(expand=True, fill='both')
    
    ttk.Label(main_frame, text="Player Statistics", style='Header.TLabel').pack(pady=10)
    
    columns = ('Username', 'Tournaments Won', 'Matches Won', 'Total Matches')
    tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=10)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    
    tree.pack(pady=10, padx=10, fill='both', expand=True)
    
    scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscrollcommand=scrollbar.set)
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.username, ps.tournaments_won, ps.matches_won, ps.total_matches
            FROM users u
            JOIN player_stats ps ON u.id = ps.player_id
            WHERE u.role = 'player'
        """)
        
        for row in cursor.fetchall():
            tree.insert('', tk.END, values=row)
        
        cursor.close()
        conn.close()
    
    ttk.Button(main_frame, text="Back to Login", 
               command=lambda: show_login_window(root)).pack(pady=10)

def fetch_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.username, 
                   STRING_AGG(g.name, ', ') as games,
                   t.name as team,
                   ps.tournaments_won,
                   ps.matches_won
            FROM users u
            LEFT JOIN player_games pg ON u.id = pg.player_id
            LEFT JOIN games g ON pg.game_id = g.id
            LEFT JOIN team_members tm ON u.id = tm.player_id
            LEFT JOIN teams t ON tm.team_id = t.id
            LEFT JOIN player_stats ps ON u.id = ps.player_id
            WHERE u.role = 'player'
            GROUP BY u.id, u.username, t.name, ps.tournaments_won, ps.matches_won
        """)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return columns, rows
    except Exception as e:
        print("Database error:", e)
        return [], []

def refresh_tree(tree):
    try:
        for item in tree.get_children():
            tree.delete(item)
        
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, 
                   STRING_AGG(g.name, ', ') as games,
                   t.name as team,
                   ps.tournaments_won,
                   ps.matches_won
            FROM users u
            LEFT JOIN player_games pg ON u.id = pg.player_id
            LEFT JOIN games g ON pg.game_id = g.id
            LEFT JOIN team_members tm ON u.id = tm.player_id
            LEFT JOIN teams t ON tm.team_id = t.id
            LEFT JOIN player_stats ps ON u.id = ps.player_id
            WHERE u.role = 'player'
            GROUP BY u.id, u.username, t.name, ps.tournaments_won, ps.matches_won
        """)
        
        for row in cursor.fetchall():
            tree.insert('', tk.END, values=row)
        
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")

def delete_player(tree):
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Warning", "No player selected for deletion.")
        return

    confirm = messagebox.askyesno("Confirm Delete", f"Delete {len(selected_items)} player(s)?")
    if not confirm:
        return

    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        for item in selected_items:
            player_id = tree.item(item)['values'][0]
            

            cursor.execute("DELETE FROM player_stats WHERE player_id = %s", (player_id,))
            cursor.execute("DELETE FROM player_games WHERE player_id = %s", (player_id,))
            cursor.execute("DELETE FROM team_members WHERE player_id = %s", (player_id,))
            cursor.execute("DELETE FROM tournament_participants WHERE player_id = %s", (player_id,))
           
            cursor.execute("DELETE FROM users WHERE id = %s", (player_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        messagebox.showinfo("Success", "Player(s) deleted successfully!")
        refresh_tree(tree)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete player(s): {str(e)}")

def create_tournament(name_var, game_var, tree, admin_id, tournament_tree):
    name = name_var.get()
    game = game_var.get()
    
    if not name or not game:
        messagebox.showerror("Error", "Please fill in all fields")
        return
    
    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        
        cursor.execute("SELECT id FROM games WHERE name = %s", (game,))
        game_result = cursor.fetchone()
        
        if not game_result:
            messagebox.showerror("Error", "Selected game not found")
            cursor.close()
            conn.close()
            return
        
        game_id = game_result[0]
        
        
        cursor.execute("""
            INSERT INTO tournaments (name, game_id, created_by)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (name, game_id, admin_id))
        
        tournament_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        messagebox.showinfo("Success", f"Tournament '{name}' created successfully!")
        name_var.set("")
        game_var.set("")
        
    
        refresh_tree(tree)
        refresh_tournaments(tournament_tree)
        
    except psycopg2.IntegrityError as e:
        if "unique constraint" in str(e).lower():
            messagebox.showerror("Error", "A tournament with this name already exists")
        else:
            messagebox.showerror("Error", f"Database error: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create tournament: {str(e)}")

def create_match(player1_var, player2_var, game_var, winner_var, match_type_var, tree, match_tree):
    player1 = player1_var.get()
    player2 = player2_var.get()
    game = game_var.get()
    winner = winner_var.get()
    match_type = match_type_var.get().lower()  # Convert to lowercase
    
    if not all([player1, player2, game, winner, match_type]):
        messagebox.showerror("Error", "Please fill in all fields")
        return
    
    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        
        cursor.execute("SELECT id FROM users WHERE username = %s", (player1,))
        player1_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM users WHERE username = %s", (player2,))
        player2_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM users WHERE username = %s", (winner,))
        winner_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM games WHERE name = %s", (game,))
        game_id = cursor.fetchone()[0]
        
        
        cursor.execute("""
            INSERT INTO matches (game_id, player1_id, player2_id, winner_id, match_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (game_id, player1_id, player2_id, winner_id, match_type))
        
        
        cursor.execute("""
            UPDATE player_stats
            SET matches_won = matches_won + 1,
                total_matches = total_matches + 1
            WHERE player_id = %s
        """, (winner_id,))
        
        
        cursor.execute("""
            UPDATE player_stats
            SET total_matches = total_matches + 1
            WHERE player_id IN (%s, %s)
            AND player_id != %s
        """, (player1_id, player2_id, winner_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        messagebox.showinfo("Success", "Match recorded successfully!")
        
        player1_var.set("")
        player2_var.set("")
        game_var.set("")
        winner_var.set("")
        match_type_var.set("")
        
        
        refresh_tree(tree)
        refresh_matches(match_tree)
        
    except Exception as e:
        messagebox.showerror("Error", str(e))


def refresh_tournaments(tree):
    for item in tree.get_children():
        tree.delete(item)
    
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.name, g.name, u.username
                FROM tournaments t
                JOIN games g ON t.game_id = g.id
                JOIN users u ON t.created_by = u.id
                ORDER BY t.id DESC
            """)
            
            for row in cursor.fetchall():
                tree.insert('', tk.END, values=row)
            
            cursor.close()
            conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to refresh tournaments: {str(e)}")

def refresh_matches(tree):
    for item in tree.get_children():
        tree.delete(item)
    
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, g.name, 
                       u1.username as player1, 
                       u2.username as player2,
                       w.username as winner,
                       m.match_type
                FROM matches m
                JOIN games g ON m.game_id = g.id
                JOIN users u1 ON m.player1_id = u1.id
                JOIN users u2 ON m.player2_id = u2.id
                JOIN users w ON m.winner_id = w.id
                ORDER BY m.id DESC
            """)
            
            for row in cursor.fetchall():
                tree.insert('', tk.END, values=row)
            
            cursor.close()
            conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to refresh matches: {str(e)}")

def show_admin_dashboard(root, current_user):
    clear_window(root)
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(expand=True, fill='both')
    
    ttk.Label(main_frame, text=f"Admin Dashboard - {current_user['username']}", 
              style='Header.TLabel').pack(pady=10)
    
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill='both', expand=True, padx=10, pady=5)
    
    
    players_frame = ttk.Frame(notebook)
    notebook.add(players_frame, text='Players')
    
    columns = ('ID', 'Username', 'Games', 'Team', 'Tournaments Won', 'Matches Won')
    tree = ttk.Treeview(players_frame, columns=columns, show='headings', height=10)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=80)
    
    tree.pack(pady=10, padx=10, fill='both', expand=True)
    
    scrollbar = ttk.Scrollbar(players_frame, orient=tk.VERTICAL, command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscrollcommand=scrollbar.set)
    
    btn_frame = ttk.Frame(players_frame)
    btn_frame.pack(pady=5)
    
    ttk.Button(btn_frame, text="Delete Player", 
               command=lambda: delete_player(tree)).pack(side=tk.LEFT, padx=5)
    
    
    tournaments_frame = ttk.Frame(notebook)
    notebook.add(tournaments_frame, text='Tournaments')
    
    tournament_form = ttk.Frame(tournaments_frame)
    tournament_form.pack(pady=20)
    
    ttk.Label(tournament_form, text="Tournament Name:").grid(row=0, column=0, padx=5, pady=5)
    tournament_name = tk.StringVar()
    ttk.Entry(tournament_form, textvariable=tournament_name).grid(row=0, column=1, padx=5, pady=5)
    
    ttk.Label(tournament_form, text="Game:").grid(row=1, column=0, padx=5, pady=5)
    tournament_game = tk.StringVar()
    game_combo = ttk.Combobox(tournament_form, textvariable=tournament_game)
    game_combo['values'] = get_games()
    game_combo.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(tournaments_frame, text="Existing Tournaments").pack(pady=10)
    tournament_tree = ttk.Treeview(tournaments_frame, columns=('ID', 'Name', 'Game', 'Created By'), show='headings', height=5)
    
    for col in ('ID', 'Name', 'Game', 'Created By'):
        tournament_tree.heading(col, text=col)
        tournament_tree.column(col, width=100)
    
    tournament_tree.pack(pady=10, padx=10, fill='both', expand=True)
    
    tournament_buttons = ttk.Frame(tournaments_frame)
    tournament_buttons.pack(pady=5)
    
    ttk.Button(tournament_form, text="Create Tournament", 
               command=lambda: create_tournament(tournament_name, tournament_game, tree, current_user['id'], tournament_tree)).grid(row=2, column=0, columnspan=2, pady=10)
    
    ttk.Button(tournament_buttons, text="Edit Tournament", 
               command=lambda: edit_tournament(tournament_tree, tournament_name, tournament_game)).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(tournament_buttons, text="Delete Tournament", 
               command=lambda: delete_tournament(tournament_tree)).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(tournament_buttons, text="Undo Delete Tournament", 
               command=lambda: restore_tournament(tournament_tree)).pack(side=tk.LEFT, padx=5)
    
   
    matches_frame = ttk.Frame(notebook)
    notebook.add(matches_frame, text='Matches')
    
    match_form = ttk.Frame(matches_frame)
    match_form.pack(pady=20)
    
    players = get_players()
    
    ttk.Label(match_form, text="Player 1:").grid(row=0, column=0, padx=5, pady=5)
    player1_var = tk.StringVar()
    player1_combo = ttk.Combobox(match_form, textvariable=player1_var)
    player1_combo['values'] = players
    player1_combo.grid(row=0, column=1, padx=5, pady=5)
    
    ttk.Label(match_form, text="Player 2:").grid(row=1, column=0, padx=5, pady=5)
    player2_var = tk.StringVar()
    player2_combo = ttk.Combobox(match_form, textvariable=player2_var)
    player2_combo['values'] = players
    player2_combo.grid(row=1, column=1, padx=5, pady=5)
    
    ttk.Label(match_form, text="Game:").grid(row=2, column=0, padx=5, pady=5)
    match_game_var = tk.StringVar()
    match_game_combo = ttk.Combobox(match_form, textvariable=match_game_var)
    match_game_combo['values'] = get_games()
    match_game_combo.grid(row=2, column=1, padx=5, pady=5)
    
    ttk.Label(match_form, text="Winner:").grid(row=3, column=0, padx=5, pady=5)
    winner_var = tk.StringVar()
    winner_combo = ttk.Combobox(match_form, textvariable=winner_var)
    winner_combo['values'] = players
    winner_combo.grid(row=3, column=1, padx=5, pady=5)
    
    
    ttk.Label(match_form, text="Match Type:").grid(row=4, column=0, padx=5, pady=5)
    match_type_var = tk.StringVar()
    match_type_combo = ttk.Combobox(match_form, textvariable=match_type_var)
    match_type_combo['values'] = ['Friendly', 'Tournament']
    match_type_combo.grid(row=4, column=1, padx=5, pady=5)
    
    ttk.Button(match_form, text="Record Match", 
               command=lambda: create_match(player1_var, player2_var, match_game_var, winner_var, match_type_var, tree, match_tree)).grid(row=5, column=0, columnspan=2, pady=10)
    
    ttk.Label(matches_frame, text="Match History").pack(pady=10)
    match_tree = ttk.Treeview(matches_frame, 
                             columns=('ID', 'Game', 'Player 1', 'Player 2', 'Winner', 'Type'), 
                             show='headings', 
                             height=5)
    
    for col in ('ID', 'Game', 'Player 1', 'Player 2', 'Winner', 'Type'):
        match_tree.heading(col, text=col)
        match_tree.column(col, width=80)
    
    match_tree.pack(pady=10, padx=10, fill='both', expand=True)
    
    match_buttons = ttk.Frame(matches_frame)
    match_buttons.pack(pady=5)
    
    ttk.Button(match_buttons, text="Edit Match", 
               command=lambda: edit_match(match_tree, player1_var, player2_var, match_game_var, winner_var, match_type_var)).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(match_buttons, text="Delete Match", 
               command=lambda: delete_match(match_tree)).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(match_buttons, text="Undo Delete Match", 
               command=lambda: restore_match(match_tree, tree)).pack(side=tk.LEFT, padx=5)
    
    backup_button_frame = ttk.Frame(main_frame)
    backup_button_frame.pack(pady=10)
    
    ttk.Button(backup_button_frame, text="Backup Database", 
               command=backup_database).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(main_frame, text="Logout", 
               command=lambda: show_login_window(root)).pack(pady=10)
    
    
    refresh_tree(tree)
    refresh_tournaments(tournament_tree)
    refresh_matches(match_tree)


def show_player_dashboard(root, current_user):
    clear_window(root)
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(expand=True, fill='both')
    
    ttk.Label(main_frame, text=f"Player Dashboard - {current_user['username']}", 
              style='Header.TLabel').pack(pady=10)
    
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill='both', expand=True, padx=10, pady=5)
    
    
    profile_frame = ttk.Frame(notebook)
    notebook.add(profile_frame, text='Profile')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.username, ps.tournaments_won, ps.matches_won, ps.total_matches
            FROM users u
            JOIN player_stats ps ON u.id = ps.player_id
            WHERE u.id = %s
        """, (current_user['id'],))
        
        player_info = cursor.fetchone()
        
        info_frame = ttk.Frame(profile_frame)
        info_frame.pack(pady=20)
        
        ttk.Label(info_frame, text=f"Username: {player_info[0]}").grid(row=0, column=0, pady=5, sticky='w')
        ttk.Label(info_frame, text=f"Tournaments Won: {player_info[1]}").grid(row=1, column=0, pady=5, sticky='w')
        ttk.Label(info_frame, text=f"Matches Won: {player_info[2]}").grid(row=2, column=0, pady=5, sticky='w')
        ttk.Label(info_frame, text=f"Total Matches: {player_info[3]}").grid(row=3, column=0, pady=5, sticky='w')
        
        cursor.close()
        conn.close()
    
    
    games_frame = ttk.Frame(notebook)
    notebook.add(games_frame, text='Games')
    
    ttk.Label(games_frame, text="Select Games:").pack(pady=10)
    
    games_list = ttk.Frame(games_frame)
    games_list.pack(pady=10)
    
    selected_games = []
    games = get_games()
    
    
    tournaments_frame = ttk.Frame(notebook)
    notebook.add(tournaments_frame, text='Tournaments')
    
    ttk.Label(tournaments_frame, text="Available Tournaments").pack(pady=10)
    
    columns = ('Name', 'Game', 'Status')
    tournaments_tree = ttk.Treeview(tournaments_frame, columns=columns, show='headings', height=10)
    
    for col in columns:
        tournaments_tree.heading(col, text=col)
        tournaments_tree.column(col, width=150)
    
    tournaments_tree.pack(pady=10, padx=10, fill='both', expand=True)
    

    for i, game in enumerate(games):
        var = tk.BooleanVar()
        ttk.Checkbutton(games_list, text=game, variable=var).grid(row=i, column=0, sticky='w', pady=2)
        selected_games.append((game, var))
    
    ttk.Button(games_list, text="Update Games", 
               command=lambda: update_player_games(current_user['id'], selected_games, tournaments_tree)).grid(row=len(games), column=0, pady=10)
    
  
    teams_frame = ttk.Frame(notebook)
    notebook.add(teams_frame, text='Teams')
    
    ttk.Label(teams_frame, text="Team Management").pack(pady=10)
    
    team_form = ttk.Frame(teams_frame)
    team_form.pack(pady=10)
    
    ttk.Label(team_form, text="Join Team:").grid(row=0, column=0, pady=5, padx=5)
    team_choice = tk.StringVar()
    team_combo = ttk.Combobox(team_form, textvariable=team_choice, width=28)
    team_combo['values'] = get_teams()
    team_combo.grid(row=0, column=1, pady=5)
    
    ttk.Button(team_form, text="Join Team", 
               command=lambda: join_team(current_user['id'], team_choice)).grid(row=1, column=0, columnspan=2, pady=5)
    
    ttk.Label(team_form, text="Create Team:").grid(row=2, column=0, pady=5, padx=5)
    new_team_name = tk.StringVar()
    ttk.Entry(team_form, textvariable=new_team_name, width=30).grid(row=2, column=1, pady=5)
    
    ttk.Button(team_form, text="Create Team", 
               command=lambda: create_team(current_user['id'], new_team_name)).grid(row=3, column=0, columnspan=2, pady=5)
    
    ttk.Button(tournaments_frame, text="Register for Tournament", 
               command=lambda: register_for_tournament(tournaments_tree, current_user['id'])).pack(pady=10)
    
    ttk.Button(main_frame, text="Logout", 
               command=lambda: show_login_window(root)).pack(pady=10)
    
  
    refresh_player_tournaments(tournaments_tree, current_user['id'])

def refresh_player_tournaments(tree, player_id):
    """Refresh the tournaments view for a player based on their selected games"""
    for item in tree.get_children():
        tree.delete(item)
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT DISTINCT 
                    t.name as tournament_name, 
                    g.name as game_name,
                    CASE 
                        WHEN tp.player_id IS NOT NULL THEN 'Registered'
                        ELSE 'Available'
                    END as status
                FROM tournaments t
                INNER JOIN games g ON t.game_id = g.id
                INNER JOIN player_games pg ON g.id = pg.game_id AND pg.player_id = %s
                LEFT JOIN tournament_participants tp ON t.id = tp.tournament_id AND tp.player_id = %s
                ORDER BY t.name ASC
            """, (player_id, player_id))
            
            for row in cursor.fetchall():
                tree.insert('', tk.END, values=row)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh tournaments: {str(e)}")
        finally:
            cursor.close()
            conn.close()

def update_player_games(player_id, selected_games, tournaments_tree=None):
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
    try:
        
        cursor.execute("BEGIN")
        
    
        cursor.execute("ALTER TABLE player_games DISABLE TRIGGER player_games_backup_trigger")
        
       
        cursor.execute("DELETE FROM player_games WHERE player_id = %s", (player_id,))
        
      
        for game, var in selected_games:
            if var.get():
                cursor.execute("""
                    INSERT INTO player_games (player_id, game_id)
                    SELECT %s, id FROM games WHERE name = %s
                """, (player_id, game))
        
      
        cursor.execute("ALTER TABLE player_games ENABLE TRIGGER player_games_backup_trigger")
        
     
        cursor.execute("COMMIT")
        messagebox.showinfo("Success", "Games updated successfully!")
        
      
        if tournaments_tree:
            refresh_player_tournaments(tournaments_tree, player_id)
            
    except Exception as e:
        cursor.execute("ROLLBACK")
        messagebox.showerror("Error", str(e))
    finally:
        cursor.close()
        conn.close()

def join_team(player_id, team_choice):
    team_name = team_choice.get()
    if not team_name:
        messagebox.showerror("Error", "Please select a team")
        return
    
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM teams WHERE name = %s", (team_name,))
        team_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO team_members (team_id, player_id)
            VALUES (%s, %s)
        """, (team_id, player_id))
        
        conn.commit()
        messagebox.showinfo("Success", f"Joined team {team_name} successfully!")
    except psycopg2.IntegrityError:
        messagebox.showerror("Error", "Already a member of this team")
    finally:
        cursor.close()
        conn.close()

def create_team(player_id, team_name_var):
    team_name = team_name_var.get()
    if not team_name:
        messagebox.showerror("Error", "Please enter a team name")
        return
    
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO teams (name)
            VALUES (%s)
            RETURNING id
        """, (team_name,))
        
        team_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO team_members (team_id, player_id)
            VALUES (%s, %s)
        """, (team_id, player_id))
        
        conn.commit()
        messagebox.showinfo("Success", f"Team {team_name} created successfully!")
        team_name_var.set("")
    except psycopg2.IntegrityError:
        messagebox.showerror("Error", "Team name already exists")
    finally:
        cursor.close()
        conn.close()

def register_for_tournament(tree, player_id):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a tournament")
        return
    
    tournament_name = tree.item(selected_item[0])['values'][0]
    
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO tournament_participants (tournament_id, player_id)
            SELECT t.id, %s
            FROM tournaments t
            WHERE t.name = %s
        """, (player_id, tournament_name))
        
        conn.commit()
        messagebox.showinfo("Success", f"Registered for tournament {tournament_name} successfully!")
    except psycopg2.IntegrityError:
        messagebox.showerror("Error", "Already registered for this tournament")
    finally:
        cursor.close()
        conn.close()

def delete_tournament(tree):
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Warning", "No tournament selected for deletion.")
        return

    confirm = messagebox.askyesno("Confirm Delete", f"Delete {len(selected_items)} tournament(s)?")
    if not confirm:
        return

    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        for item in selected_items:
            tournament_id = tree.item(item)['values'][0]
          
            cursor.execute("DELETE FROM tournament_participants WHERE tournament_id = %s", (tournament_id,))
            cursor.execute("DELETE FROM tournaments WHERE id = %s", (tournament_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        messagebox.showinfo("Success", "Tournament(s) deleted successfully!")
        refresh_tournaments(tree)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete tournament(s): {str(e)}")

def edit_tournament(tree, name_var, game_var):
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Warning", "No tournament selected for editing.")
        return
    
    if len(selected_items) > 1:
        messagebox.showwarning("Warning", "Please select only one tournament to edit.")
        return

    tournament_id = tree.item(selected_items[0])['values'][0]
    new_name = name_var.get()
    new_game = game_var.get()

    if not new_name or not new_game:
        messagebox.showerror("Error", "Please fill in all fields")
        return

    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        
        cursor.execute("SELECT id FROM games WHERE name = %s", (new_game,))
        game_result = cursor.fetchone()
        
        if not game_result:
            messagebox.showerror("Error", "Selected game not found")
            cursor.close()
            conn.close()
            return
        
        game_id = game_result[0]
        

        cursor.execute("""
            UPDATE tournaments 
            SET name = %s, game_id = %s
            WHERE id = %s
        """, (new_name, game_id, tournament_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        messagebox.showinfo("Success", f"Tournament updated successfully!")
        name_var.set("")
        game_var.set("")
        refresh_tournaments(tree)
        
    except psycopg2.IntegrityError as e:
        if "unique constraint" in str(e).lower():
            messagebox.showerror("Error", "A tournament with this name already exists")
        else:
            messagebox.showerror("Error", f"Database error: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update tournament: {str(e)}")

def delete_match(tree):
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Warning", "No match selected for deletion.")
        return

    confirm = messagebox.askyesno("Confirm Delete", f"Delete {len(selected_items)} match(es)?")
    if not confirm:
        return

    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        for item in selected_items:
            match_id = tree.item(item)['values'][0]
            
            cursor.execute("""
                SELECT player1_id, player2_id, winner_id
                FROM matches
                WHERE id = %s
            """, (match_id,))
            match_info = cursor.fetchone()
            
            if match_info:
                player1_id, player2_id, winner_id = match_info
                
                
                cursor.execute("""
                    UPDATE player_stats
                    SET total_matches = total_matches - 1
                    WHERE player_id IN (%s, %s)
                """, (player1_id, player2_id))
                
                cursor.execute("""
                    UPDATE player_stats
                    SET matches_won = matches_won - 1
                    WHERE player_id = %s
                """, (winner_id,))
            
            
            cursor.execute("DELETE FROM matches WHERE id = %s", (match_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        messagebox.showinfo("Success", "Match(es) deleted successfully!")
        refresh_matches(tree)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete match(es): {str(e)}")

def edit_match(tree, player1_var, player2_var, game_var, winner_var, match_type_var):
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Warning", "No match selected for editing.")
        return
    
    if len(selected_items) > 1:
        messagebox.showwarning("Warning", "Please select only one match to edit.")
        return

    match_id = tree.item(selected_items[0])['values'][0]
    player1 = player1_var.get()
    player2 = player2_var.get()
    game = game_var.get()
    winner = winner_var.get()
    match_type = match_type_var.get().lower()

    if not all([player1, player2, game, winner, match_type]):
        messagebox.showerror("Error", "Please fill in all fields")
        return

    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        
        cursor.execute("SELECT id FROM users WHERE username = %s", (player1,))
        player1_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM users WHERE username = %s", (player2,))
        player2_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM users WHERE username = %s", (winner,))
        winner_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM games WHERE name = %s", (game,))
        game_id = cursor.fetchone()[0]
        
        
        cursor.execute("""
            SELECT winner_id, player1_id, player2_id
            FROM matches
            WHERE id = %s
        """, (match_id,))
        old_match_info = cursor.fetchone()
        old_winner_id = old_match_info[0]
        

        cursor.execute("""
            UPDATE matches 
            SET game_id = %s, 
                player1_id = %s, 
                player2_id = %s, 
                winner_id = %s, 
                match_type = %s
            WHERE id = %s
        """, (game_id, player1_id, player2_id, winner_id, match_type, match_id))
        
        
        if old_winner_id != winner_id:
            
            cursor.execute("""
                UPDATE player_stats
                SET matches_won = matches_won - 1
                WHERE player_id = %s
            """, (old_winner_id,))
            
            
            cursor.execute("""
                UPDATE player_stats
                SET matches_won = matches_won + 1
                WHERE player_id = %s
            """, (winner_id,))
            
            
            cursor.execute("""
                UPDATE player_stats
                SET total_matches = total_matches - 1
                WHERE player_id IN (%s, %s)
            """, (old_match_info[1], old_match_info[2]))
            
            cursor.execute("""
                UPDATE player_stats
                SET total_matches = total_matches + 1
                WHERE player_id IN (%s, %s)
            """, (player1_id, player2_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        messagebox.showinfo("Success", "Match updated successfully!")
        
        player1_var.set("")
        player2_var.set("")
        game_var.set("")
        winner_var.set("")
        match_type_var.set("")
        
        
        refresh_matches(tree)
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update match: {str(e)}")

def restore_tournament(tree):
    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        
        cursor.execute("""
            WITH deleted_tournament AS (
                DELETE FROM tournaments_backup
                WHERE id = (
                    SELECT id 
                    FROM tournaments_backup 
                    ORDER BY created_at DESC 
                    LIMIT 1
                )
                RETURNING *
            )
            INSERT INTO tournaments (id, name, game_id, created_by, created_at, winner_id)
            SELECT id, name, game_id, created_by, created_at, winner_id
            FROM deleted_tournament
            RETURNING id;
        """)
        
        restored_id = cursor.fetchone()
        if restored_id:
            
            cursor.execute("""
                WITH deleted_participants AS (
                    DELETE FROM tournament_participants_backup
                    WHERE tournament_id = %s
                    RETURNING *
                )
                INSERT INTO tournament_participants (tournament_id, player_id, registered_at)
                SELECT tournament_id, player_id, registered_at
                FROM deleted_participants;
            """, (restored_id[0],))
            
            conn.commit()
            messagebox.showinfo("Success", "Tournament restored successfully!")
            refresh_tournaments(tree)
        else:
            messagebox.showinfo("Info", "No deleted tournaments to restore.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to restore tournament: {str(e)}")

def restore_match(tree, player_tree):
    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        
        cursor.execute("""
            WITH deleted_match AS (
                DELETE FROM matches_backup
                WHERE id = (
                    SELECT id 
                    FROM matches_backup 
                    ORDER BY created_at DESC 
                    LIMIT 1
                )
                RETURNING *
            )
            INSERT INTO matches (id, game_id, player1_id, player2_id, winner_id, match_type, created_at)
            SELECT id, game_id, player1_id, player2_id, winner_id, match_type, created_at
            FROM deleted_match
            RETURNING winner_id, player1_id, player2_id;
        """)
        
        restored = cursor.fetchone()
        if restored:
            winner_id, player1_id, player2_id = restored
            
            
            cursor.execute("""
                UPDATE player_stats
                SET matches_won = matches_won + 1,
                    total_matches = total_matches + 1
                WHERE player_id = %s
            """, (winner_id,))
            
            cursor.execute("""
                UPDATE player_stats
                SET total_matches = total_matches + 1
                WHERE player_id IN (%s, %s)
                  AND player_id != %s
            """, (player1_id, player2_id, winner_id))
            
            conn.commit()
            messagebox.showinfo("Success", "Match restored successfully!")
            refresh_matches(tree)
            refresh_tree(player_tree)
        else:
            messagebox.showinfo("Info", "No deleted matches to restore.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to restore match: {str(e)}")

def restore_player(tree):
    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        
        cursor.execute("""
            WITH deleted_user AS (
                DELETE FROM users_backup
                WHERE id = (
                    SELECT id 
                    FROM users_backup 
                    ORDER BY created_at DESC 
                    LIMIT 1
                )
                RETURNING *
            )
            INSERT INTO users (id, username, password, role, created_at)
            SELECT id, username, password, role, created_at
            FROM deleted_user
            RETURNING id;
        """)
        
        restored_id = cursor.fetchone()
        if restored_id:
            
            cursor.execute("""
                WITH deleted_stats AS (
                    DELETE FROM player_stats_backup
                    WHERE player_id = %s
                    RETURNING *
                )
                INSERT INTO player_stats (player_id, tournaments_won, matches_won, total_matches)
                SELECT player_id, tournaments_won, matches_won, total_matches
                FROM deleted_stats;
            """, (restored_id[0],))
            
            
            cursor.execute("""
                WITH deleted_games AS (
                    DELETE FROM player_games_backup
                    WHERE player_id = %s
                    RETURNING *
                )
                INSERT INTO player_games (player_id, game_id)
                SELECT player_id, game_id
                FROM deleted_games;
            """, (restored_id[0],))
            
            
            cursor.execute("""
                WITH deleted_memberships AS (
                    DELETE FROM team_members_backup
                    WHERE player_id = %s
                    RETURNING *
                )
                INSERT INTO team_members (team_id, player_id, joined_at)
                SELECT team_id, player_id, joined_at
                FROM deleted_memberships;
            """, (restored_id[0],))
            
            conn.commit()
            messagebox.showinfo("Success", "Player restored successfully!")
            refresh_tree(tree)
        else:
            messagebox.showinfo("Info", "No deleted players to restore.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to restore player: {str(e)}")

def main():
    root = tk.Tk()
    root.title("Tournament Manager")
    root.geometry("800x600")
    show_login_window(root)
    root.mainloop()

if __name__ == "__main__":
    main() 