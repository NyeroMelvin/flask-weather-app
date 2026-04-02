from flask import Flask, render_template, request, redirect, url_for
import requests
import os
from dotenv import load_dotenv
import psycopg2
from db import get_connection, init_db

load_dotenv()

app = Flask(__name__)

# Test DB connection on startup
try:
    init_db()
    print("✅ Database connected successfully")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

@app.route('/')
def index():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM searches ORDER BY searched_at DESC LIMIT 10")
        history = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('index.html', weather=None, history=history, error=None)
    except Exception as e:
        return f"Database error: {str(e)}", 500