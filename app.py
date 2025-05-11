from flask import Flask, request, send_from_directory, jsonify
import subprocess, os
from builder import extract_zip, run_user_code, build_ipa

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/extract', methods=['POST'])
def extract():
    file = request.files['zip_file']
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    extract_zip(path, 'extracted')
    return jsonify({'message': 'ZIP extracted successfully.'})

@app.route('/run', methods=['POST'])
def run():
    code = request.json.get('code', '')
    output = run_user_code(code, 'extracted')
    return jsonify({'output': output})

@app.route('/build', methods=['POST'])
def build():
    try:
        ipa_path, manifest_url = build_ipa()
        return jsonify({'success': True, 'manifest_url': manifest_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)