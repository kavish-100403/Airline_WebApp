from flask import Flask, render_template, request
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT"),
    )


@app.route("/", methods=["GET", "POST"])
def index():
    error = None

    if request.method == "POST":
        origin_code = request.form["origin_code"].strip().upper()
        dest_code = request.form["dest_code"].strip().upper()
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        if start_date > end_date:
            error = "Start date cannot be later than end date."
            return render_template(
                "index.html",
                error=error,
                origin_code=origin_code,
                dest_code=dest_code,
                start_date=start_date,
                end_date=end_date,
            )

        conn = get_connection()
        cur = conn.cursor()

        query = """
            SELECT
                f.flight_number,
                f.departure_date,
                fs.origin_code,
                fs.dest_code,
                fs.departure_time
            FROM Flight f
            JOIN FlightService fs
                ON f.flight_number = fs.flight_number
            WHERE fs.origin_code = %s
              AND fs.dest_code = %s
              AND f.departure_date BETWEEN %s AND %s
            ORDER BY f.departure_date, fs.departure_time;
        """

        cur.execute(query, (origin_code, dest_code, start_date, end_date))
        flights = cur.fetchall()

        cur.close()
        conn.close()

        return render_template("results.html", flights=flights)

    return render_template(
        "index.html",
        error=error,
        origin_code="",
        dest_code="",
        start_date="",
        end_date="",
    )


@app.route("/flight/<flight_number>/<departure_date>")
def flight_details(flight_number, departure_date):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            f.flight_number,
            f.departure_date,
            f.plane_type,
            a.capacity,
            COUNT(b.pid) AS booked_seats,
            a.capacity - COUNT(b.pid) AS available_seats
        FROM Flight f
        JOIN Aircraft a
            ON f.plane_type = a.plane_type
        LEFT JOIN Booking b
            ON f.flight_number = b.flight_number
           AND f.departure_date = b.departure_date
        WHERE f.flight_number = %s
          AND f.departure_date = %s
        GROUP BY f.flight_number, f.departure_date, f.plane_type, a.capacity;
    """

    cur.execute(query, (flight_number, departure_date))
    details = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("details.html", details=details)


if __name__ == "__main__":
    app.run(debug=True)
