from flask import Flask, request, redirect, url_for, render_template, jsonify, make_response
import os
from flask import send_from_directory
from werkzeug.middleware.shared_data import SharedDataMiddleware
from urllib.parse import quote, unquote
from model import work_path, util
from datetime import datetime, timezone, timedelta
import api
import logging
from tasks import iss_query, job_ready_byid, job_get_byid

ALLOWED_EXTENSIONS = set(['zip'])
local_tz = timezone(timedelta(hours=8))

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = work_path.get_upload()
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['DOWNLOAD_FOLDER'] = work_path.in_project('./downloads')
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

app.logger.setLevel(logging.INFO)
logger = app.logger


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def secure_filename(filename):
    filename, file_extension = os.path.splitext(filename)
    return quote(filename) + file_extension


@app.route('/')
def home():
    return render_template("index.html", title='Bugine')


@app.route('/descript', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        logger.info(file.filename)
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_path = util.uuid_file_name(file_path)
            file.save(file_path)
            dep_path = api.zip2descript(file_path, app.config['DOWNLOAD_FOLDER'])
            logger.info(dep_path)
            return jsonify({
                'code': 200,
                'path': url_for('downloaded_file',
                                filename=work_path.rela_path(dep_path, app.config['DOWNLOAD_FOLDER'])),
                'name': util.restore_uuid_file_name(os.path.basename(dep_path)),
                'token': util.just_uuid(os.path.basename(dep_path))
            })
        else:
            return jsonify({
                'code': 400,
                'message': 'bad upload file.'
            })
    return render_template('descript.html', title='Bugine | Description')


@app.route('/query', methods=['GET', 'POST'])
def query_issue_view():
    if request.method == 'POST':
        user_uuid = request.form.get('csv_token')
        if not api.uuid_valid(user_uuid):
            return jsonify({
                'code': 400,
                'message': 'Bad token.'
            })
        else:
            csv_path = api.csv_uuid_exist(user_uuid, app.config['DOWNLOAD_FOLDER'])
            if csv_path is not None:
                ban_files = api.format_ban_files(request.form)
                job_token = iss_query.delay(csv_path, ban_files).id
                job_receive_time = datetime.now(tz=local_tz).isoformat()
                api.save_job_meta(job_token, {
                    "csv_path": csv_path,
                    "ban_files": ban_files,
                    'timestamp': job_receive_time,
                })
                return jsonify({
                    'code': 200,
                    'message': 'query created',
                    'timestamp': job_receive_time,
                    'job-token': job_token,
                })
            else:
                return jsonify({
                    'code': 400,
                    'message': 'Bad token.'
                })
    return render_template('query.html', title='Bugine | Query', ext_files=api.except_list_build_helper())


@app.route('/result', methods=['GET', 'POST'])
def result_view():
    if request.method == 'POST':
        # import time
        # time.sleep(2)
        job_uuid = request.form.get('job_token')
        return verify_job(job_uuid)
    elif request.method == 'GET':
        job_uuid = request.args.get('token')
        if job_uuid is not None:
            return verify_job(job_uuid)
        else:
            return render_template('result.html', title='Bugine | Result')


def verify_job(job_uuid):
    if api.valid_key(job_uuid):
        meta = api.get_job_meta(job_uuid)
        if not job_ready_byid(job_uuid):
            return jsonify({
                'code': 201,
                'job-token': job_uuid,
                "create-time": meta["timestamp"],
                'name': util.bare_name(meta['csv_path']),
            })
        else:
            res = job_get_byid(job_uuid)
            return jsonify({
                'code': 202,
                'job-token': job_uuid,
                "create-time": meta["timestamp"],
                "done-time": res['date_done'],
                "data": res['data'],
                'name': util.bare_name(meta['csv_path']),
            })
    else:
        return jsonify({
            'code': 400,
            'message': 'Bad token.'
        })

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'],
#                                filename)


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename,
                               attachment_filename=util.restore_uuid_file_name(filename), as_attachment=True,
                               mimetype='text/csv')


app.add_url_rule('/downloads/<filename>', 'downloaded_file', build_only=True)
# app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
#     '/downloads': app.config['DOWNLOAD_FOLDER']
# })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
