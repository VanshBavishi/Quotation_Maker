from flask import Flask, request, jsonify, render_template, send_file
import sqlite3
from fpdf import FPDF

app = Flask(__name__)


def get_products():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
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
    products = cursor.fetchall()
    conn.close()
    return jsonify(products)


@app.route('/generate-quotation', methods=['POST'])
def generate_quotation():
    data = request.json
    products = data['products']

    total = 0
    for product in products:
        try:
            # Ensure correct data types
            price = float(product['price'])
            quantity = int(product['quantity'])
            total += price * quantity
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid data: {e}'}), 400

    total_with_tax = total * 1.18

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Quotation", ln=True, align='C')

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
    pdf.cell(150, 10, txt=f"Total: {total:.2f}", border=1, ln=True, align='R')
    pdf.cell(
        150, 10, txt=f"Total with 18% tax: {total_with_tax:.2f}", border=1, ln=True, align='R')

    pdf_file = 'quotation.pdf'
    pdf.output(pdf_file)

    return send_file(pdf_file, as_attachment=True, download_name='quotation.pdf')


if __name__ == '__main__':
    app.run(debug=True)
