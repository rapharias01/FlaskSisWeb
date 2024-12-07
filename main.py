from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import base64
import requests
import io

app = Flask(__name__)

BASE_URL = 'https://parallelum.com.br/fipe/api/v1'

query_history = []

def get_vehicle_brands(vehicle_type):
    url = f'{BASE_URL}/{vehicle_type}/marcas'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def get_vehicle_models(vehicle_type, brand_id):
    url = f'{BASE_URL}/{vehicle_type}/marcas/{brand_id}/modelos'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('modelos', [])
    return []

def get_vehicle_years(vehicle_type, brand_id, model_id):
    url = f'{BASE_URL}/{vehicle_type}/marcas/{brand_id}/modelos/{model_id}/anos'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def get_vehicle_price(vehicle_type, brand_id, model_id, year_id):
    url = f'{BASE_URL}/{vehicle_type}/marcas/{brand_id}/modelos/{model_id}/anos/{year_id}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        price_info = {
            'price': data.get('Valor'),
            'brand': data.get('Marca'),
            'model': data.get('Modelo'),
            'year': data.get('AnoModelo'),
            'fuel': data.get('Combustivel'),
        }
        return price_info
    return None

def calculate_financing(vehicle_value, interest_rate, months):
    monthly_interest_rate = (interest_rate / 100) / 12
    monthly_payment = vehicle_value * (monthly_interest_rate / (1 - (1 + monthly_interest_rate) ** -months))
    return monthly_payment

def generate_price_graph(vehicle_type, brand_id, model_id):
    years = get_vehicle_years(vehicle_type, brand_id, model_id)
    prices = []

    for year in years:
        price_info = get_vehicle_price(vehicle_type, brand_id, model_id, year['codigo'])
        if price_info:
            prices.append((year['nome'], price_info['price']))

    prices.sort(key=lambda x: x[0])

    years = [x[0] for x in prices]
    prices = [float(x[1].replace('R$', '').replace('.', '').replace(',', '.')) for x in prices]

    plt.figure(figsize=(10, 6))
    plt.plot(years, prices, marker='o', linestyle='-', color='b')
    plt.title('Preço do Veiculo ao Longo dos Anos')
    plt.xlabel('Ano')
    plt.ylabel('Preço (R$)')
    plt.xticks(rotation=45)
    plt.grid(True)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    graph_url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()

    return graph_url


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/brands', methods=['POST'])
def brands():
    vehicle_type = request.form['vehicle_type']
    brands = get_vehicle_brands(vehicle_type)
    return render_template('brands.html', brands=brands, vehicle_type=vehicle_type)

@app.route('/models', methods=['POST'])
def models():
    vehicle_type = request.form['vehicle_type']
    brand_id = request.form['brand_id']
    models = get_vehicle_models(vehicle_type, brand_id)
    return render_template('models.html', models=models, vehicle_type=vehicle_type, brand_id=brand_id)

@app.route('/years', methods=['POST'])
def years():
    vehicle_type = request.form['vehicle_type']
    brand_id = request.form['brand_id']
    model_id = request.form['model_id']
    years = get_vehicle_years(vehicle_type, brand_id, model_id)
    return render_template('years.html', years=years, vehicle_type=vehicle_type, brand_id=brand_id, model_id=model_id)

@app.route('/price', methods=['POST'])
def price():
    vehicle_type = request.form['vehicle_type']
    brand_id = request.form['brand_id']
    model_id = request.form['model_id']
    year_id = request.form['year_id']
    
    vehicle_price = get_vehicle_price(vehicle_type, brand_id, model_id, year_id)

    if vehicle_price:
        query_history.append({
            'vehicle_type': vehicle_type,
            'brand': vehicle_price['brand'],
            'model': vehicle_price['model'],
            'year': vehicle_price['year'],
            'price': vehicle_price['price'],
            'fuel': vehicle_price['fuel']
        })

    price_graph = generate_price_graph(vehicle_type, brand_id, model_id)

    return render_template('price.html', vehicle_price=vehicle_price, price_graph=price_graph)

@app.route('/financing', methods=['GET', 'POST'])
def financing():
    if request.method == 'POST':
        vehicle_value = request.form['vehicle_value']
        interest_rate = float(request.form['interest_rate'])
        months = int(request.form['months'])

        vehicle_value = float(vehicle_value.replace('.', '').replace(',', '.'))

        monthly_payment = calculate_financing(vehicle_value, interest_rate, months)

        vehicle_value_formatted = f"R$ {vehicle_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        monthly_payment_formatted = f"R$ {monthly_payment:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        return render_template('financing_result.html', 
                               vehicle_value=vehicle_value_formatted, 
                               interest_rate=interest_rate,
                               months=months, 
                               monthly_payment=monthly_payment_formatted)
    
    return render_template('financing_form.html')

@app.route('/history')
def history():
    return render_template('history.html', history=query_history)

if __name__ == '__main__':
    app.run(debug=True)
