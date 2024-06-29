from flask import Flask, render_template, jsonify, send_from_directory
import os
import json

app = Flask(__name__)

OUTPUT_FOLDER = 'output'

def parse_json_content(content):
    if isinstance(content, dict):
        return content
    return json.loads(content)

def get_student_ids():
    student_ids = []
    errors = []
    for folder in os.listdir(OUTPUT_FOLDER):
        folder_path = os.path.join(OUTPUT_FOLDER, folder)
        if os.path.isdir(folder_path):
            id_file = os.path.join(folder_path, 'id.json')
            if os.path.exists(id_file):
                try:
                    with open(id_file, 'r') as f:
                        file_content = f.read()
                        data = parse_json_content(file_content)
                        result = parse_json_content(data['result'])
                        student_id = result['student_id']
                        student_ids.append(student_id)
                except json.JSONDecodeError as e:
                    errors.append(f"Error parsing {id_file}: {str(e)}. File content: {file_content}")
                except KeyError as e:
                    errors.append(f"Key error in {id_file}: {str(e)}. Data: {data}")
                except Exception as e:
                    errors.append(f"Unexpected error processing {id_file}: {str(e)}")
    return student_ids, errors

@app.route('/')
def index():
    student_ids, errors = get_student_ids()
    return render_template('index.html', student_ids=student_ids, errors=errors)

@app.route('/student/<student_id>')
def student_detail(student_id):
    for folder in os.listdir(OUTPUT_FOLDER):
        folder_path = os.path.join(OUTPUT_FOLDER, folder)
        id_file = os.path.join(folder_path, 'id.json')
        if os.path.exists(id_file):
            try:
                with open(id_file, 'r') as f:
                    file_content = f.read()
                    data = parse_json_content(file_content)
                    if parse_json_content(data['result'])['student_id'] == student_id:
                        result_file = os.path.join(folder_path, 'result.json')
                        with open(result_file, 'r') as f:
                            result_content = f.read()
                            result_data = parse_json_content(result_content)
                        results = parse_json_content(result_data['result'])
                        image_files = [f for f in os.listdir(folder_path) if f.endswith('.jpg')]
                        return render_template('student_detail.html', student_id=student_id, results=results, image_files=image_files, folder=folder)
            except json.JSONDecodeError as e:
                return f"Error parsing {id_file}: {str(e)}", 500
            except KeyError as e:
                return f"Key error in {id_file}: {str(e)}", 500
            except Exception as e:
                return f"Unexpected error processing {id_file}: {str(e)}", 500
    return "Student not found", 404

@app.route('/output/<path:filename>')
def serve_image(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)