from flask import Flask, render_template, request, url_for, flash
from werkzeug.utils import redirect
from flask_mysqldb import MySQL
import pandas as pd


app = Flask(__name__)
app.secret_key = 'many random bytes'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'our_users'

mysql = MySQL(app)

def insert_csv_data_to_mysql(filename):
    # Select only the columns you need from the CSV file
    columns = ['Id', 'Timestamp', 'Src_IP', 'Dst_IP', 'output_Label', 'output_Cat']
    df = pd.read_csv(filename, usecols=columns)

    # Connect to MySQL and insert only the remaining data
    conn = mysql.connection
    cursor = conn.cursor()

    cursor.execute("SELECT Id FROM ids")
    existing_ids = [id[0] for id in cursor.fetchall()]

    new_data = df[~df['Id'].isin(existing_ids)]

    if not new_data.empty:
        cursor.executemany("INSERT INTO ids (Id, Timestamp, Src_IP, Dst_IP, output_Label, output_Cat) VALUES (%s,%s, %s, %s, %s, %s)", new_data.values.tolist())
        conn.commit()
        flash(f"{len(new_data)} new records have been added to the ids table.")
    else:
        flash("No new records were added to the ids table.")

first_run_flag = True

@app.route('/')
def Index():
    global first_run_flag

    if first_run_flag:
        # Perform data insertion on first run
        filename = 'ML/results.csv'
        insert_csv_data_to_mysql(filename)
        first_run_flag = False
        # Redirect to the /insert route to prevent the insertion process from running again
        return redirect(url_for('insert'))

    # Fetch data from MySQL and render the index page
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ids")
    data = cur.fetchall()
    cur.close()

    return render_template('index.html',ids=data)

@app.route('/blacklist')
def blacklist():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blacklist")
    data2 = cur.fetchall()
    cur.close()
    return render_template('blacklist.html', blacklist=data2)


@app.route('/ignore/<string:id_data>', methods = ['GET'])
def ignore(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM blacklist WHERE Id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('blacklist'))

@app.route('/ignoredata/<string:id_data2>', methods = ['GET'])
def ignoredata(id_data2):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM ids WHERE Id=%s", (id_data2,))
    mysql.connection.commit()
    return redirect(url_for('Index'))

@app.route('/alldelete', methods=['GET'])
def alldelete():
    cur = mysql.connection.cursor()

    # Check if all records already exist in the blacklist table
    cur.execute("SELECT * FROM ids")
    all_deleted_data = cur.fetchall()
    existing_data = []

    for data in all_deleted_data:
        cur.execute("SELECT * FROM blacklist WHERE Id=%s", (data[0],))
        existing_record = cur.fetchone()
        if existing_record:
            existing_data.append(existing_record)

    if len(existing_data) == len(all_deleted_data):
        flash("All records already exist in the blacklist")
    elif len(existing_data) > 0:
        # Insert only the remaining data into the blacklist table
        remaining_data = list(set(all_deleted_data) - set(existing_data))
        cur.executemany("INSERT INTO blacklist (Id, Timestamp, Src_IP, Dst_IP, output_Label, output_Cat) VALUES (%s,%s, %s, %s, %s, %s)", remaining_data)
        flash(f"{len(remaining_data)} records have been added to the blacklist")
    else:
        cur.execute("INSERT INTO blacklist (Id, Timestamp, Src_IP, Dst_IP, output_Label, output_Cat) SELECT Id, Timestamp, Src_IP, Dst_IP, output_Label, output_Cat FROM ids")
        flash("All records have been added to the blacklist")

    cur.execute("DELETE FROM ids")
    mysql.connection.commit()
    flash("All records have been deleted successfully")
    return redirect(url_for('Index'))


def insert_csv_data_to_mysql(filename):
    # Select only the columns you need from the CSV file
    columns = ['Id', 'Timestamp', 'Src_IP', 'Dst_IP', 'output_Label', 'output_Cat']
    df = pd.read_csv(filename, usecols=columns)

    # Connect to MySQL and insert only the remaining data
    conn = mysql.connection
    cursor = conn.cursor()

    cursor.execute("SELECT Id FROM ids")
    existing_ids = [id[0] for id in cursor.fetchall()]

    new_data = df[~df['Id'].isin(existing_ids)]

    if not new_data.empty:
        cursor.executemany("INSERT INTO ids (Id, Timestamp, Src_IP, Dst_IP, output_Label, output_Cat) VALUES (%s,%s, %s, %s, %s, %s)", new_data.values.tolist())
        conn.commit()
        flash(f"{len(new_data)} new records have been added to the ids table.")
    else:
        flash("No new records were added to the ids table.")

    cursor.close()

@app.route('/insert')
def insert():
    filename = 'ML/results.csv'
    insert_csv_data_to_mysql(filename)

    # Connect to MySQL and fetch data to display on web UI
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ids")
    data = cur.fetchall()
    cur.close()

    return redirect(url_for('Index'))


@app.route('/delete/<string:id_data>', methods=['GET'])
def delete(id_data):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ids WHERE Id=%s", (id_data,))
    deleted_data = cur.fetchone()

    # Check if the entry already exists in the blacklist table
    cur.execute("SELECT * FROM blacklist WHERE Id=%s", (id_data,))
    existing_data = cur.fetchone()

    if existing_data:
        flash("Record already exists in the blacklist")
    else:
        cur.execute("INSERT INTO blacklist (Id, Timestamp, Src_IP, Dst_IP, output_Label, output_Cat) VALUES (%s,%s, %s, %s, %s, %s)", deleted_data)
        flash("Record has been added to the blacklist")

    cur.execute("DELETE FROM ids WHERE Id=%s", (id_data,))
    mysql.connection.commit()
    flash("Record has been deleted successfully")
    return redirect(url_for('Index'))


if __name__ == "__main__":
    app.run(host='0.0.0.0')















