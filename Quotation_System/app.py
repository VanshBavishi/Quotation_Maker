from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for
import sqlite3
from fpdf import FPDF

app = Flask(__name__)


def create_database():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        brand TEXT NOT NULL,
        price REAL NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quotation_counter (
        id INTEGER PRIMARY KEY,
        counter INTEGER
    )
    ''')

    cursor.execute(
        'INSERT OR IGNORE INTO quotation_counter (id, counter) VALUES (1, 0)')

    conn.commit()
    conn.close()

# Get products from database


def get_products():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, brand, price FROM products')
    products = cursor.fetchall()
    conn.close()
    return products


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/products', methods=['GET'])
def products():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, brand, price FROM products')
    products = [{'id': row[0], 'name': row[1], 'brand': row[2],
                 'price': row[3]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(products)


@app.route('/add-products', methods=['POST'])
def add_products():
    data = request.json
    products = data['products']

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    for product in products:
        cursor.execute('INSERT INTO products (name, brand, price) VALUES (?, ?, ?)',
                       (product['name'], product['brand'], product['price']))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


def generate_quotation_number():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    cursor.execute('SELECT counter FROM quotation_counter WHERE id=1')
    result = cursor.fetchone()
    if result:
        counter = result[0] + 1
    else:
        counter = 1

    cursor.execute(
        'REPLACE INTO quotation_counter (id, counter) VALUES (1, ?)', (counter,))
    conn.commit()
    conn.close()

    return f"GW/QTN/23-24/{counter}"


@app.route('/generate-quotation', methods=['POST'])
def generate_quotation():
    data = request.json
    client_name = data.get('client_name')
    client_add = data.get('client_add')
    products = data['products']

    total = 0
    for product in products:
        try:
            price = float(product['price'])
            quantity = int(product['quantity'])
            total += price * quantity
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid data: {e}'}), 400

    tax_amount = total * 0.18
    total_with_tax = total + tax_amount

    # Generate unique quotation number
    quotation_number = generate_quotation_number()

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Business Details
    pdf.set_font("Arial", size=28, style='B')
    pdf.set_text_color(255, 0, 0)  # Red color
    pdf.cell(0, 10, txt="GENERAL ELECTRICALS", ln=True, align='C')
    pdf.ln(1)
    pdf.set_text_color(0, 0, 0)  # Reset color to black
    pdf.set_font("Arial", size=12, style='B')
    pdf.cell(0, 6.5, txt="5-2-160, R.P ROAD, SECUNDRABAD-500003",
             ln=True, align='C')
    pdf.set_text_color(255, 0, 0)
    pdf.cell(0, 6.5, txt="TELE  7673919497", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=11, style='B')
    pdf.cell(0, 6.5, txt="Email: generalelectricals82@gmail.com",
             ln=True, align='C')
    pdf.ln()
    pdf.set_font("Arial", size=14, style='B')
    pdf.cell(0, 6.5, txt="PROFORMA INVIOCE",
             ln=True, align='C')

    pdf.ln(1)  # Reduce space between business details and the table

    # Client Name

    # Quotation Number
    pdf.set_font("Arial", size=10)
    pdf.cell(
        0, 3, txt=f"Quotation No: {quotation_number}", ln=True, align='R')
    pdf.ln(1)  # Reduce space between quotation number and the table

    # Date
    pdf.set_font("Arial", size=10)
    pdf.cell(
        0, 4, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
    pdf.ln(5)  # Reduce space between date and the table

    pdf.set_font("Times", size=16)
    pdf.cell(
        0, 5, txt=f"To, {client_name}", ln=True, align='L')
    pdf.set_font("Times", size=12)
    pdf.cell(
        0, 10, txt=f" {client_add}", ln=True, align='L')
    pdf.ln(1)  # Reduce space between client name and the table

    # Table Header
    pdf.set_font("Arial", size=10)
    pdf.cell(10, 10, 'S.No', 1)
    pdf.cell(60, 10, 'Name', 1)
    pdf.cell(40, 10, 'Brand', 1)
    pdf.cell(20, 10, 'Price', 1)    # Price per item
    pdf.cell(30, 10, 'Quantity', 1)
    pdf.cell(30, 10, 'Total', 1)    # Total price
    pdf.ln()

    # Table Content
    pdf.set_font("Arial", size=10)
    for index, product in enumerate(products, start=1):
        try:
            price = float(product['price'])
            quantity = int(product['quantity'])
            total_price = price * quantity
            pdf.cell(10, 10, str(index), 1)
            pdf.cell(60, 10, product['name'], 1)
            pdf.cell(40, 10, product['brand'], 1)
            pdf.cell(20, 10, f"{price:.2f}", 1)   # Price per item
            pdf.cell(30, 10, str(quantity), 1)
            pdf.cell(30, 10, f"{total_price:.2f}", 1)   # Total price
            pdf.ln()
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Error in product data: {e}'}), 400

    pdf.ln()
    pdf.cell(
        0, 10, txt=f"Sub Total: {total:.2f}", border=1, ln=True, align='R')
    pdf.cell(
        0, 10, txt=f"GST 18%: {tax_amount:.2f}", border=1, ln=True, align='R')
    pdf.set_font("Arial", size=11, style='B')
    pdf.cell(
        0, 10, txt=f"Grand Total : {total_with_tax:.2f}", border=1, ln=True, align='R')

    pdf.image('signature.png', x=170, y=pdf.get_y() + 3, w=15)

    pdf.set_font("Arial", size=9, style='B')
    pdf.cell(0, 30, txt="GENERAL ELECTRICALS",
             ln=True, align='R')
    pdf.cell(0, -10, txt="PARTNER",
             ln=True, align='R')

    pdf.ln()
    pdf.set_text_color(0, 0, 0)  # Reset color to black
    pdf.set_font("Arial", size=9, style='B')
    pdf.cell(0, 5, txt="BANK DETAILS",
             ln=True, align='L')
    pdf.cell(0, 5, txt="HDFC BANK", ln=True, align='L')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=9, style='B')
    pdf.cell(0, 5, txt="A/C NO 00422020000179",
             ln=True, align='L')
    pdf.cell(0, 5, txt="IFSC : HDFC0000042 , BRANCH : S D ROAD",
             ln=True, align='L')

    pdf.cell(0, 10, txt="STOCKLIST FOR",
             ln=True, align='C')
    pdf.cell(0, 5, txt="POLYCAB WIRES AND CABLE / FINOLEX WIRES AND CABLE / L&T SWITCH GEAR / SCHNEIDER ELECTRIC ", ln=True, align='C')
    pdf.cell(0, 5, txt="PHILIPS LIGHTING/GROMPTON LIGHTING BAJAJ LIGHTING OREVA LED QUTAK SIREN GM MODULAR", ln=True, align='C')
    pdf_file = 'quotation.pdf'
    pdf.output(pdf_file)

    return send_file(pdf_file, as_attachment=True, download_name='quotation.pdf')


if __name__ == '__main__':
    create_database()
    app.run(debug=True)
