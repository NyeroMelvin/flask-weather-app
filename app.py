from flask import Flask, render_template, request, redirect, url_for
import requests
import os
from dotenv import load_dotenv
from datetime import timedelta
from db import get_connection, init_db

load_dotenv()

app = Flask(__name__)

try:
    init_db()
    print("✅ Database initialized")
except Exception as e:
    print(f"❌ DB Error: {e}")

@app.route('/')
def index():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM searches ORDER BY searched_at DESC LIMIT 10")
        history = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ DB fetch error: {e}")
        history = []
    return render_template('index.html', weather=None, history=history, error=None, timedelta=timedelta)

@app.route('/weather', methods=['POST'])
def get_weather():
    city = request.form.get('city')
    api_key = os.getenv("WEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM searches ORDER BY searched_at DESC LIMIT 10")
        history = cur.fetchall()
    except Exception:
        history = []

    if response.status_code == 200:
        data = response.json()
        weather = {
            'city': data['name'],
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description']
        }
        try:
            cur.execute(
                "INSERT INTO searches (city, temperature, description) VALUES (%s, %s, %s)",
                (weather['city'], weather['temperature'], weather['description'])
            )
            conn.commit()
            cur.execute("SELECT * FROM searches ORDER BY searched_at DESC LIMIT 10")
            history = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"❌ Insert error: {e}")
        return render_template('index.html', weather=weather, history=history, error=None, timedelta=timedelta)
    else:
        return render_template('index.html', weather=None, history=history, error="City not found!", timedelta=timedelta)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_search(id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM searches WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Delete error: {e}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)