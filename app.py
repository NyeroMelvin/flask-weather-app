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
    cur.execute("SELECT * FROM searches ORDER BY searched_at DESC LIMIT 10")
    history = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', weather=None, history=history, error=None, timedelta=timedelta)

@app.route('/weather', methods=['POST'])
def get_weather():
    city = request.form.get('city')
    api_key = os.getenv("WEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM searches ORDER BY searched_at DESC LIMIT 10")
    history = cur.fetchall()

    if response.status_code == 200:
        data = response.json()

        # Get city's timezone offset in seconds from API
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
            "INSERT INTO searches (city, temperature, description) VALUES (%s, %s, %s)",
            (weather['city'], weather['temperature'], weather['description'])
        )
        conn.commit()
        cur.execute("SELECT * FROM searches ORDER BY searched_at DESC LIMIT 10")
        history = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('index.html', weather=weather, history=history, error=None, timedelta=timedelta)
    else:
        cur.close()
        conn.close()
        return render_template('index.html', weather=None, history=history, error="City not found!", timedelta=timedelta)

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