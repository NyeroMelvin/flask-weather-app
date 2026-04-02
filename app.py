from flask import Flask, render_template, request, redirect, url_for
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from db import get_connection, init_db

load_dotenv()

app = Flask(__name__)

init_db()

@app.route('/')
def index():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, city, temperature, description, searched_at, tz_offset FROM searches ORDER BY searched_at DESC LIMIT 10")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    history = []
    for row in rows:
        tz_offset = int(row[5]) if row[5] is not None else 0
        local_time = (row[4] + timedelta(seconds=tz_offset)).strftime('%Y-%m-%d %H:%M')
        history.append({
            'id': row[0],
            'city': row[1],
            'temperature': row[2],
            'description': row[3],
            'local_time': local_time
        })

    return render_template('index.html', weather=None, history=history, error=None)

@app.route('/weather', methods=['POST'])
def get_weather():
    city = request.form.get('city')
    api_key = os.getenv("WEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)

    conn = get_connection()
    cur = conn.cursor()

    if response.status_code == 200:
        data = response.json()
        tz_offset_seconds = data['timezone']
        city_tz = timezone(timedelta(seconds=tz_offset_seconds))
        local_time = datetime.now(city_tz).strftime('%Y-%m-%d %H:%M')

        weather = {
            'city': data['name'],
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description'],
            'local_time': local_time
        }

        cur.execute(
            "INSERT INTO searches (city, temperature, description, tz_offset) VALUES (%s, %s, %s, %s)",
            (weather['city'], weather['temperature'], weather['description'], tz_offset_seconds)
        )
        conn.commit()

        cur.execute("SELECT id, city, temperature, description, searched_at, tz_offset FROM searches ORDER BY searched_at DESC LIMIT 10")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        history = []
        for row in rows:
            tz_offset = int(row[5]) if row[5] is not None else 0
            row_local_time = (row[4] + timedelta(seconds=tz_offset)).strftime('%Y-%m-%d %H:%M')
            history.append({
                'id': row[0],
                'city': row[1],
                'temperature': row[2],
                'description': row[3],
                'local_time': row_local_time
            })

        return render_template('index.html', weather=weather, history=history, error=None)
    else:
        cur.execute("SELECT id, city, temperature, description, searched_at, tz_offset FROM searches ORDER BY searched_at DESC LIMIT 10")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        history = []
        for row in rows:
            tz_offset = int(row[5]) if row[5] is not None else 0
            row_local_time = (row[4] + timedelta(seconds=tz_offset)).strftime('%Y-%m-%d %H:%M')
            history.append({
                'id': row[0],
                'city': row[1],
                'temperature': row[2],
                'description': row[3],
                'local_time': row_local_time
            })

        return render_template('index.html', weather=None, history=history, error="City not found!")

@app.route('/delete/<int:id>', methods=['POST'])
def delete_search(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM searches WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)