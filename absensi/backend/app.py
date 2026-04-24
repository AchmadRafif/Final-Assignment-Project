from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import base64
import os
from datetime import datetime, date
import uuid

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',          # ← kosongkan saja untuk Laragon default
    'database': 'attendance_db',
    'charset': 'utf8mb4'
}

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static', 'img', 'snapshots')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/employees', methods=['GET'])
def get_employees():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM employees ORDER BY name")
    rows = cur.fetchall()
    db.close()
    return jsonify(rows)

@app.route('/api/employees/<int:eid>', methods=['GET'])
def get_employee(eid):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM employees WHERE id=%s", (eid,))
    row = cur.fetchone(); db.close()
    if not row: return jsonify({'error': 'Not found'}), 404
    return jsonify(row)

@app.route('/api/employees', methods=['POST'])
def create_employee():
    data = request.json
    db = get_db(); cur = db.cursor()
    cur.execute(
        "INSERT INTO employees (name, rfid_uid, department, position, photo) VALUES (%s,%s,%s,%s,%s)",
        (data['name'], data['rfid_uid'], data.get('department',''), data.get('position',''), data.get('photo',''))
    )
    db.commit(); new_id = cur.lastrowid; db.close()
    return jsonify({'id': new_id, 'message': 'Employee created'}), 201

@app.route('/api/employees/<int:eid>', methods=['PUT'])
def update_employee(eid):
    data = request.json
    db = get_db(); cur = db.cursor()
    cur.execute(
        "UPDATE employees SET name=%s, rfid_uid=%s, department=%s, position=%s WHERE id=%s",
        (data['name'], data['rfid_uid'], data.get('department',''), data.get('position',''), eid)
    )
    db.commit(); db.close()
    return jsonify({'message': 'Updated'})

@app.route('/api/employees/<int:eid>', methods=['DELETE'])
def delete_employee(eid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM employees WHERE id=%s", (eid,))
    db.commit(); db.close()
    return jsonify({'message': 'Deleted'})

@app.route('/api/scan', methods=['POST'])
def scan():
    data = request.json
    rfid_uid  = data.get('rfid_uid', '').strip()
    image_b64 = data.get('image_b64', '')

    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM employees WHERE rfid_uid=%s", (rfid_uid,))
    emp = cur.fetchone()
    if not emp:
        db.close()
        return jsonify({'success': False, 'message': f'RFID {rfid_uid} tidak terdaftar'}), 404

    snapshot_filename = ''
    if image_b64:
        try:
            img_data = base64.b64decode(image_b64)
            snapshot_filename = f"{uuid.uuid4().hex}.jpg"
            with open(os.path.join(UPLOAD_FOLDER, snapshot_filename), 'wb') as f:
                f.write(img_data)
        except Exception as e:
            print(f"Image save error: {e}")

    today = date.today()
    cur.execute(
        "SELECT * FROM attendance WHERE employee_id=%s AND DATE(check_in)=%s ORDER BY check_in DESC LIMIT 1",
        (emp['id'], today)
    )
    existing = cur.fetchone()
    now = datetime.now()

    if existing and existing['check_out'] is None:
        cur.execute(
            "UPDATE attendance SET check_out=%s, snapshot_out=%s WHERE id=%s",
            (now, snapshot_filename, existing['id'])
        )
        action = 'check_out'
        record_id = existing['id']
    else:
        cur.execute(
            "INSERT INTO attendance (employee_id, check_in, snapshot_in) VALUES (%s,%s,%s)",
            (emp['id'], now, snapshot_filename)
        )
        action = 'check_in'
        record_id = cur.lastrowid

    db.commit(); db.close()
    return jsonify({
        'success': True,
        'action': action,
        'employee': emp,
        'time': now.strftime('%H:%M:%S'),
        'record_id': record_id
    })

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    date_filter = request.args.get('date', '')
    emp_filter  = request.args.get('employee_id', '')
    db = get_db(); cur = db.cursor(dictionary=True)
    q = """
        SELECT a.*, e.name AS employee_name, e.department, e.position
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE 1=1
    """
    params = []
    if date_filter:
        q += " AND DATE(a.check_in) = %s"; params.append(date_filter)
    if emp_filter:
        q += " AND a.employee_id = %s"; params.append(emp_filter)
    q += " ORDER BY a.check_in DESC"
    cur.execute(q, params)
    rows = cur.fetchall()
    for r in rows:
        for k in ('check_in','check_out'):
            if r[k]: r[k] = r[k].strftime('%Y-%m-%d %H:%M:%S')
    db.close()
    return jsonify(rows)

@app.route('/api/attendance/<int:aid>', methods=['DELETE'])
def delete_attendance(aid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM attendance WHERE id=%s", (aid,))
    db.commit(); db.close()
    return jsonify({'message': 'Deleted'})

@app.route('/api/attendance/<int:aid>', methods=['PUT'])
def update_attendance(aid):
    data = request.json
    db = get_db(); cur = db.cursor()
    cur.execute(
        "UPDATE attendance SET check_in=%s, check_out=%s WHERE id=%s",
        (data.get('check_in'), data.get('check_out'), aid)
    )
    db.commit(); db.close()
    return jsonify({'message': 'Updated'})

@app.route('/api/stats', methods=['GET'])
def stats():
    today = date.today().isoformat()
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS total FROM employees")
    total_emp = cur.fetchone()['total']
    cur.execute("SELECT COUNT(DISTINCT employee_id) AS present FROM attendance WHERE DATE(check_in)=%s", (today,))
    present = cur.fetchone()['present']
    cur.execute("SELECT COUNT(*) AS total FROM attendance WHERE DATE(check_in)=%s AND check_out IS NOT NULL", (today,))
    checked_out = cur.fetchone()['total']
    db.close()
    return jsonify({
        'total_employees': total_emp,
        'present_today':   present,
        'checked_out':     checked_out,
        'absent':          total_emp - present
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)