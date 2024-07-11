from flask import Flask, request, redirect, url_for, render_template, send_file, send_from_directory, after_this_request
import os
from io import BytesIO
from datetime import datetime
from werkzeug.utils import secure_filename
import zipfile
import tempfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'captured_images/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_PATH'] = 500000  # 500KB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if request.method == 'POST':
        image_data = request.get_data()
        with open('captured_images/image.jpg', 'wb') as f:
            f.write(image_data)
        return 'Image uploaded successfully!'
    return 'Invalid request'

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'imageFile' not in request.files:
        return "No file part"
    file = request.files['imageFile']
    if file.filename == '':
        return "No selected file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        date_string = datetime.now().strftime('%Y-%m-%d_%H%M%S ')
        filename = date_string + filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return f"Photos successfully uploaded to the server with the name: {filename}"
    return "Sorry, only JPG, JPEG, PNG & GIF files are allowed."

@app.route('/count', methods=['POST'])
def count_files():
    if request.form.get('cmd') == 'GTP':
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
        return str(len(files))
    return "Invalid command"

@app.route('/gallery')
def load_photos():
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
    files.sort(reverse=True)
    return render_template('gallery.html', files=files)

@app.route('/delete/<filename>', methods=['GET'])
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path) and allowed_file(filename):
        os.remove(file_path)
        return redirect(url_for('load_photos'))
    return "File not found or unsupported file type."

@app.route('/captured_images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download')
def download_files():
    folder = 'captured_images/'
    zip_filename = "ESP32CAM_1.zip"
    
    # Create a temporary zip file
    with tempfile.TemporaryDirectory() as tmpdirname:
        zip_path = os.path.join(tmpdirname, zip_filename)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if allowed_file(file):
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, folder))
        
        # Read the zip file content to memory before sending it
        with open(zip_path, 'rb') as f:
            zip_content = f.read()

        # Remove the zip file
        os.remove(zip_path)

        # Send the zip file content as a response
        return send_file(
            BytesIO(zip_content),
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
