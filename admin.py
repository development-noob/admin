from flask import send_from_directory
from flask import Flask, request, jsonify, render_template
import requests
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ip_storage.db' 
db = SQLAlchemy(app)

class IpAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15), unique=True, nullable=False)

def get_client_ip(environ):
    client_ip = environ.get('HTTP_X_FORWARDED_FOR', environ.get('REMOTE_ADDR'))
    return client_ip
def get_facebook_info(user_id):
    fields = 'id,is_verified,cover,created_time,work,hometown,username,link,name,locale,location,about,website,birthday,gender,relationship_status,significant_other,quotes,first_name,subscribers.limit(0)'
    access_token = 'EAAD6V7os0gcBO3AjmZCI4ZAHEhrdNEgJEWT1f6TNa46215Fwk3vJQkyzDFUwNWrClDZB2r6nF4Pa1HzXRQSlmECuA6BQsf7uZBocKwvDMZASoY0PmXAhYPuoIWeZBrdVJHv2FOSr6WEnZC2VxizDSHuCDtPgxHUZAf9fki67ZABbxid4S6XfN0vjK1v6bmAZDZD'
    try:
        response = requests.get(f"https://graph.facebook.com/{user_id}?fields={fields}&access_token={access_token}")
        response.raise_for_status()
        data = response.json()
        created_time = data.get('created_time', '')

        if created_time:
            created_datetime = datetime.strptime(created_time, '%Y-%m-%dT%H:%M:%S%z')
            created_date = created_datetime.strftime('%d/%m/%Y')
            user_info = {
                'created_date': created_date,
                'name': data.get('name', ''),
            }
            return user_info
        else:
            return {'created_date': "There is no information with this Facebook UID", 'name': ''}
    except requests.exceptions.HTTPError as err:
        return {'created_date': f"Error fetching Facebook data: {err}", 'name': ''}

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        client_ip = get_client_ip(request.environ)
        print(f"Client IP: {client_ip}")
        ip_object = IpAddress.query.filter_by(ip=client_ip).first()
        if ip_object:
            if request.method == 'POST':
                user_id = request.form['uid']
                user_info = get_facebook_info(user_id)
                return render_template('result.html', user_id=user_id, user_info=user_info)

            return render_template('index.html')
        else:
            return jsonify({"message": f"Block ip {client_ip}"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/home', methods=['GET'])
def home():
    return render_template('admin.html')

@app.route('/themip', methods=['GET'])
def themip():
    try:
        ip = request.args.get('ip')

        if not IpAddress.query.filter_by(ip=ip).first():
            new_ip = IpAddress(ip=ip)
            db.session.add(new_ip)
            db.session.commit()
            return jsonify({"message": f"IP {ip} added successfully"})
        else:
            return jsonify({"message": f"IP {ip} already exists"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/xoaip', methods=['GET'])
def xoaip():
    try:
        ip_to_delete = request.args.get('ip')
        ip_object = IpAddress.query.filter_by(ip=ip_to_delete).first()

        if ip_object:
            db.session.delete(ip_object)
            db.session.commit()
            return jsonify({"message": f"IP {ip_to_delete} deleted successfully"})
        else:
            return jsonify({"message": f"IP {ip_to_delete} does not exist"})
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/kiemtraip', methods=['GET'])
def checkinfoip():
    try:
        ip_to_check = request.args.get('ip')

        # Kiểm tra xem IP có tồn tại trong cơ sở dữ liệu không
        ip_object = IpAddress.query.filter_by(ip=ip_to_check).first()

        if ip_object:
            return jsonify(message=f"Ip {ip_to_check} has access to the URL")
        else:
            return jsonify(message=f"Ip {ip_to_check} is blocked from accessing the URL")
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/check', methods=['GET'])
def check():
    try:
        # Lấy danh sách tất cả các địa chỉ IP từ cơ sở dữ liệu
        ip_addresses = [ip.ip for ip in IpAddress.query.all()]
        return jsonify(ip_addresses)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)
