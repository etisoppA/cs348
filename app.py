from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

@app.route('/')
def index():
    # Read optional filter parameters from query string
    show_name        = request.args.get('show_name') or None
    city             = request.args.get('city') or None
    state            = request.args.get('state') or None
    start_date       = request.args.get('start_date') or None
    end_date         = request.args.get('end_date') or None
    car_manufacturer = request.args.get('car_manufacturer') or None
    org_name         = request.args.get('org_name') or None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get list of organizers for the drop-down
    cursor.callproc('sp_get_organizers')
    organizers = []
    for result in cursor.stored_results():
        organizers = result.fetchall()
    
    # Call the filtering stored procedure to retrieve auto shows
    cursor.callproc('sp_filter_autoshows', (
        show_name,
        city,
        state,
        start_date,
        end_date,
        car_manufacturer,
        org_name
    ))
    autoshows = []
    for result in cursor.stored_results():
        autoshows = result.fetchall()
    
    # Call the total cars procedure
    cursor2 = conn.cursor(dictionary=True)
    cursor2.callproc('sp_total_cars', (
        show_name,
        city,
        state,
        start_date,
        end_date,
        car_manufacturer,
        org_name
    ))
    total_cars = 0
    for result in cursor2.stored_results():
        row = result.fetchone()
        if row:
            total_cars = row.get('total_cars', 0)
    cursor2.close()
    
    # Call the average price procedure
    cursor3 = conn.cursor(dictionary=True)
    cursor3.callproc('sp_avg_price', (
        show_name,
        city,
        state,
        start_date,
        end_date,
        car_manufacturer,
        org_name
    ))
    avg_price = None
    for result in cursor3.stored_results():
        row = result.fetchone()
        if row:
            avg_price = row.get('avg_price')
    cursor3.close()

    cursor.close()
    conn.close()
    
    return render_template('index.html', autoshows=autoshows, organizers=organizers, total_cars=total_cars, avg_price=avg_price)

@app.route('/view_cars/<int:auto_show_id>')
def view_cars(auto_show_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Retrieve the auto show's name
    query = "SELECT name FROM auto_shows WHERE id = %s"
    cursor.execute(query, (auto_show_id,))
    autoshow_info = cursor.fetchone()
    auto_show_name = autoshow_info['name']
    
    # Call stored procedure to retrieve the cars for this auto show
    cursor.callproc('sp_get_autoshow_cars', (auto_show_id,))
    cars = []
    for result in cursor.stored_results():
        cars = result.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('view_cars.html', cars=cars, auto_show_name=auto_show_name)

@app.route('/add', methods=['GET', 'POST'])
def add_autoshow():
    if request.method == 'POST':
        show_name  = request.form['show_name']
        city       = request.form['city']
        state      = request.form['state']
        start_date = request.form['start_date']
        end_date   = request.form['end_date']
        
        org_name    = request.form['org_name']
        org_contact = request.form['org_contact']
        
        # Use getlist() to obtain all submitted car details
        manufacturers = request.form.getlist("manufacturer[]")
        models        = request.form.getlist("model[]")
        years         = request.form.getlist("year[]")
        prices        = request.form.getlist("price[]")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert auto show
        query = "INSERT INTO auto_shows (name, city, state, start_date, end_date) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (show_name, city, state, start_date, end_date))
        auto_show_id = cursor.lastrowid

        # Insert organization
        query = "INSERT INTO organizations (name, contact_info) VALUES (%s, %s)"
        cursor.execute(query, (org_name, org_contact))
        org_id = cursor.lastrowid

        # Link auto show with organization
        query = "INSERT INTO auto_show_organizations (auto_show_id, organization_id) VALUES (%s, %s)"
        cursor.execute(query, (auto_show_id, org_id))

        # Insert each car for this auto show
        query = "INSERT INTO auto_show_cars (auto_show_id, manufacturer, model, year, price) VALUES (%s, %s, %s, %s, %s)"
        for manu, mod, yr, pr in zip(manufacturers, models, years, prices):
            cursor.execute(query, (auto_show_id, manu, mod, int(yr), float(pr)))
            
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
        
    return render_template('add_autoshow.html')

@app.route('/edit_autoshow/<int:id>', methods=['GET', 'POST'])
def edit_autoshow(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, prepared=True)
    
    if request.method == 'POST':
        show_name  = request.form['show_name']
        city       = request.form['city']
        state      = request.form['state']
        start_date = request.form['start_date']
        end_date   = request.form['end_date']
        
        org_name    = request.form['org_name']
        org_contact = request.form['org_contact']
        
        manufacturers = request.form.getlist("manufacturer[]")
        models        = request.form.getlist("model[]")
        years         = request.form.getlist("year[]")
        prices        = request.form.getlist("price[]")
        
        # Update auto show record
        query = "UPDATE auto_shows SET name=%s, city=%s, state=%s, start_date=%s, end_date=%s WHERE id=%s"
        cursor.execute(query, (show_name, city, state, start_date, end_date, id))
        
        # Get organization id from the linking table
        query = "SELECT organization_id FROM auto_show_organizations WHERE auto_show_id = %s"
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        if result:
            org_id = result['organization_id']
            query = "UPDATE organizations SET name=%s, contact_info=%s WHERE id=%s"
            cursor.execute(query, (org_name, org_contact, org_id))
        
        # For simplicity, delete all existing car records for the auto show,
        # then reinsert the submitted ones
        query = "DELETE FROM auto_show_cars WHERE auto_show_id = %s"
        cursor.execute(query, (id,))
        
        query = "INSERT INTO auto_show_cars (auto_show_id, manufacturer, model, year, price) VALUES (%s, %s, %s, %s, %s)"
        for manu, mod, yr, pr in zip(manufacturers, models, years, prices):
            cursor.execute(query, (id, manu, mod, int(yr), float(pr)))
        
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    else:
        # Fetch current auto show and organizer data
        query = "SELECT * FROM auto_shows WHERE id = %s"
        cursor.execute(query, (id,))
        autoshow = cursor.fetchone()
        
        query = "SELECT organization_id FROM auto_show_organizations WHERE auto_show_id = %s"
        cursor.execute(query, (id,))
        org_link = cursor.fetchone()
        organization = {}
        if org_link:
            org_id = org_link['organization_id']
            query = "SELECT * FROM organizations WHERE id = %s"
            cursor.execute(query, (org_id,))
            organization = cursor.fetchone()
        
        # Fetch all car records for this auto show
        query = "SELECT * FROM auto_show_cars WHERE auto_show_id = %s"
        cursor.execute(query, (id,))
        cars = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('edit_autoshow.html', autoshow=autoshow, organization=organization, cars=cars)

@app.route('/delete_autoshow/<int:id>', methods=['POST'])
def delete_autoshow(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Retrieve the organization_id
    query = "SELECT organization_id FROM auto_show_organizations WHERE auto_show_id = %s"
    cursor.execute(query, (id,))
    org_result = cursor.fetchone()
    org_id = org_result[0]

    # Delete related car records
    query = "DELETE FROM auto_show_cars WHERE auto_show_id = %s"
    cursor.execute(query, (id,))
    
    # Delete the linking record
    query = "DELETE FROM auto_show_organizations WHERE auto_show_id = %s"
    cursor.execute(query, (id,))
    
    # Delete the auto show record
    query = "DELETE FROM auto_shows WHERE id = %s"
    cursor.execute(query, (id,))

    # Delete the organization record
    query = "DELETE FROM organizations WHERE id = %s"
    cursor.execute(query, (org_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()