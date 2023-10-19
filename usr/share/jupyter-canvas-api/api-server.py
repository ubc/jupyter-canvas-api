#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Provides an API for Instructors to interact with their Students Jupyter Hub Directories.
Instructors can use this API to snapshot student directories upon deadline, download
snapshot directories as Zip files, download individual files from snapshots, list
snapshots of student’s directories, list files within a students’ snapshot, and put files
such as reports into the students’ home directory.
"""

import datetime
import fcntl
import glob
import io
import logging
import os
import re
import shutil
import time
import unicodedata
import uuid
import zipfile as zf
from functools import wraps
from pathlib import Path
from sys import stdout
from paste.translogger import TransLogger

import sysrsync
from flask import Flask, request, jsonify, abort, make_response
from waitress import serve
from werkzeug.utils import secure_filename

__author__ = "Rahim Khoja"
__credits__ = ["Rahim Khoja", "Balaji Srinivasarao", "Pan Luo"]
__license__ = "GPL"
__version__ = "0.5"
__maintainer__ = "Rahim Khoja"
__email__ = "rahim.khoja@ubc.ca"
__status__ = "Development"

# API Variables Defined by Environment Variable
DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'  # API Debug
PORT = int(os.getenv('JUPYTER_API_PORT', '5000'))  # API TCP Port Number
HOST = str(os.getenv('JUPYTER_API_HOST', '0.0.0.0'))  # API TCP Address
APIKEY = str(os.getenv('JUPYTER_API_KEY', '12345'))  # API Key Value
HOMEDIR = str(os.getenv('JNOTE_HOME', '/mnt/efs/stat-100a-home/'))  # Home Directory Root
SNAPSHOT_DIR = str(os.getenv('JNOTE_SNAP', '/mnt/efs/stat-100a-snap/'))  # Instructor Snapshot Directory
INTERMEDIARY_DIR = str(os.getenv('JNOTE_INTSNAP', '/mnt/efs/stat-100a-internal/'))  # Intermediary Snapshot Directory
COURSE_CODE = str(os.getenv('JNOTE_COURSE_CODE', 'STAT100a'))  # The API Course Code

UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')  # Temporary Upload Folder
ALLOWED_EXTENSIONS = {'txt', 'html', 'htm', 'ipynb'}  # Allowed Upload File Types

app = Flask(__name__)

# Provide API Key Value to Flask
app.config['API_KEY'] = APIKEY

# JSONIFY Does Not Work Correctly Without the Following Variable
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Max Upload File Size (2MB)

# Create Upload Directory If it Does Not Exist
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Flask Upload Directory

# Define Logger
logger = logging.getLogger('Jupyter-Canvas-API')
logger.setLevel(logging.DEBUG)  # set logger level
logFormatter = logging.Formatter("%(name)-12s %(asctime)s %(levelname)-8s %(filename)s:%(funcName)s %(message)s")
consoleHandler = logging.StreamHandler(stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

loggerWaitress = logging.getLogger('waitress')
if DEBUG:
    loggerWaitress.setLevel(logging.DEBUG)


# Converts Strings into FileName Safe Values
def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


# Default Flask HTTP 401 Error
@app.errorhandler(401)
def not_authorized(e):
    """ Response sent back when not authorized. """
    if request.headers.getlist("X-Forwarded-For"):
        client_ip_address = str(request.headers.getlist("X-Forwarded-For"))
    else:
        client_ip_address = request.remote_addr
    logger.error("Invalid Authentication from IP: " + str(client_ip_address))

    return (jsonify(status=401, error='Not Authorized',
                    message='You are Not authorized to access the URL requested.'),
            401)


def check_auth():
    """ Checks the environment that the API_KEY has been set. """

    if app.config['API_KEY']:
        return app.config['API_KEY'] == request.headers.get('X-Api-Key')
    return False


# Function Required For Flask Routes Secured by API Key
def requires_apikey(f):
    """ Decorator function to require API Key. """

    @wraps(f)
    def decorated(*args, **kwargs):
        """ Decorator function that does the checking """

        if check_auth():
            return f(*args, **kwargs)
        else:
            abort(401)

    return decorated


#
# Curl Usage Command Examples For '/get_snapshot_file_list' API Call
# Required Post Variables: STUDENT_ID, SNAPSHOT_NAME
# Required Header Variables: X-Api-Key
# Example Response: ["file2.txt","jupyterhubtest.txt","file1.txt","subdir_test/subdir_file1.txt"]
#
# curl -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_NAME=12-08-2021" http://localhost:5000/get_snapshot_file_list
# curl -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=12-08-2021" http://localhost:5000/get_snapshot_file_list
# curl -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=12-08-2021" http://localhost:5000/get_snapshot_file_list
#
@app.route('/get_snapshot_file_list', methods=['POST'])
@requires_apikey
def get_snapshot_file_list():
    """ Get List of Snapshot Files for the Specified Student and Snapshot. """

    student_id = request.form.get('STUDENT_ID')  # StudentID Post Variable
    snapshot_name = request.form.get('SNAPSHOT_NAME')  # Snapshot Name Variable

    # Error if StudentID Post Variable Missing
    if not student_id:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing StudentID Post Value.'
                        ), 406)

    # Error if Snapshot Name Post Variable Missing
    if not snapshot_name:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing SNAPSHOT_NAME Post Value.'
                        ), 406)

    snap_student_path = SNAPSHOT_DIR + student_id  # Student Snapshot Directory Path
    snap_name_path = snap_student_path + '/' + snapshot_name  # Student Snapshot Path

    snap_student_path_obj = Path(snap_student_path)  # Student Snapshot Directory Path Object
    snap_name_path_obj = Path(snap_name_path)  # Student Snapshot Path Object

    # Error if Snapshot Directory Does Not Exist
    if not (snap_student_path_obj.exists() and snap_student_path_obj.is_dir()):
        logger.info("Snapshots Directory Does NOT Exist for: " + str(student_id))
        return (jsonify(status=404,
                        error='Not Found - Snapshot Directory was Not Found',
                        message='Not Found - Student Snapshot Directory Not Found.'
                        ), 404)

    # Error if Specific Snapshot Does Not Exist
    if not (snap_name_path_obj.exists()
            and snap_name_path_obj.is_dir()):
        logger.info("No Snapshot Found For Student: " + str(student_id) + " and Snapshot: " + str(snapshot_name))
        return (jsonify(status=404,
                        error='Not Found - Snapshot was Not Found',
                        message='Not Found - Snapshot Not Found.'), 404)

    # Get List Of Files In Snapshot Directory
    snapshot_files = glob.glob(os.path.join(snap_name_path + '/', '**/*'),
                               recursive=True)
    snapshot_files = [f for f in snapshot_files if os.path.isfile(f)]
    snapshot_files = [s.replace(snap_name_path + '/', '') for s in
                      snapshot_files]

    # Error if No Snapshot Files Found
    if not snapshot_files:
        logger.info("No Snapshots Files Found For Student: " + str(student_id) + " and Snapshot: " + str(snapshot_name))
        return (jsonify(status=404,
                        error='Not Found - No Snapshots Found',
                        message='Not Found - No Snapshot Directories Found.'),
                404)

    # Return List of Snapshot Files
    return jsonify(snapshot_files), 200


#
# Curl Usage Command Examples For '/get_snapshot_list' API Call
# Required Post Variables: STUDENT_ID
# Required Header Variables: X-Api-Key
# Example Response: ["12-08-2021","11-07-2020"]
#
# curl -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714" http://localhost:5000/get_snapshot_list
# curl -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" http://localhost:5000/get_snapshot_list
# curl -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" http://localhost:5000/get_snapshot_list
#
@app.route('/get_snapshot_list', methods=['POST'])
@requires_apikey
def get_snapshot_list():
    """ Get List of Snapshot Directories for the Specified Student. """

    student_id = request.form.get('STUDENT_ID')  # StudentID Post Variable

    # Error if StudentID Post Variable Missing
    if not student_id:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing StudentID Post Value.'
                        ), 406)

    snap_student_path = SNAPSHOT_DIR + student_id  # Student Snapshot Directory Path

    snap_student_path_obj = Path(snap_student_path)  # Student Snapshot Directory Path Object

    # Error if Snapshot Directory Does Not Exist
    if not (snap_student_path_obj.exists() and snap_student_path_obj.is_dir()):
        return (jsonify(status=404,
                        error='Not Found - Snapshot Directory was Not Found',
                        message='Not Found - Student Snapshot Directory Not Found.'
                        ), 404)

    # Get List of Directories in Student Snapshot Directory
    snapshots = [f.path for f in os.scandir(snap_student_path) if f.is_dir()]
    snapshots = [x for x in snapshots if '.' not in x]
    snapshots = [s.replace(snap_student_path + '/', '') for s in snapshots]

    # Error No Snapshots Found
    if not snapshots:
        return (jsonify(status=404,
                        error='Not Found - No Snapshots Found',
                        message='Not Found - No Snapshot Directories Found.'),
                404)

    # Return List of Student Snapshots
    return jsonify(snapshots), 200


#
# Curl Usage Command Examples For '/get_snapshot_file' API Call
# Required Post Variables: STUDENT_ID, SNAPSHOT_NAME, SNAPSHOT_FILENAME
# Required Header Variables: X-Api-Key
# Example Response: curl: Saved to filename 'subdir_file1.txt'
#
# curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=12-08-2021" -d "SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
# curl -OJ -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=12-08-2021" -F "SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
# curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714&SNAPSHOT_NAME=12-08-2021&SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
# curl -OJ -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_NAME=12-08-2021&SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
#
@app.route('/get_snapshot_file', methods=['POST'])
@requires_apikey
def get_snapshot_file():
    """ Get the Specified File from Specified Student Snapshot. """

    student_id = request.form.get('STUDENT_ID')  # StudentID Post Variable
    snapshot_name = request.form.get('SNAPSHOT_NAME')  # Snapshot Name Variable
    snapshot_filename = request.form.get('SNAPSHOT_FILENAME')  # Snapshot File Name Variable

    # Error if StudentID Post Variable Missing
    if not student_id:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing STUDENT_ID Post Value.'
                        ), 406)

    # Error if Snapshot Name Post Variable Missing
    if not snapshot_name:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing SNAPSHOT_NAME Post Value.'
                        ), 406)

    # Error if Snapshot File Name Post Variable Missing
    if not snapshot_filename:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing SNAPSHOT_FILENAME Post Value.'
                        ), 406)

    snap_student_path = SNAPSHOT_DIR + student_id  # Student Snapshot Directory Path
    snap_name_path = snap_student_path + '/' + snapshot_name  # Student Snapshot Path
    snap_file_path = snap_name_path + '/' + snapshot_filename  # Student Snapshot File Path

    snap_student_path_obj = Path(snap_student_path)  # Student Snapshot Directory Path Object
    snap_name_path_obj = Path(snap_name_path)  # Student Snapshot Path Object
    snap_file_path_obj = Path(snap_file_path)  # Student Snapshot File Path Object

    # Error if Snapshot Directory Does Not Exist
    if not (snap_student_path_obj.exists() and snap_student_path_obj.is_dir()):
        return (jsonify(status=404,
                        error='Not Found - Snapshot Directory was Not Found',
                        message='Not Found - Student Snapshot Directory Not Found.'
                        ), 404)

    # Error if Specific Snapshot Does Not Exist
    if not (snap_name_path_obj.exists()
            and snap_name_path_obj.is_dir()):
        return (jsonify(status=404,
                        error='Not Found - Snapshot was Not Found',
                        message='Not Found - Snapshot Not Found.'), 404)

    # Error if Requested Snapshot File Does Not Exist
    if not (snap_file_path_obj.exists()
            and snap_file_path_obj.is_file()):
        return (jsonify(status=404,
                        error='Not Found - Snapshot File was Not Found',
                        message='Not Found - Snapshot File Not Found.'), 404)

    snapshot_file_extension = snapshot_filename.rsplit('.', 1)[-1]  # File Extension
    if '/' in snapshot_filename:  # Get File Name Without Directory
        snapshot_short_filename = snapshot_filename.rsplit('/', 1)[-1]
    else:
        snapshot_short_filename = snapshot_filename

    with open(snap_file_path, 'rb') as OPEN_FILE:  # Open Snapshot File and Read it into the File Variable
        snapshot_file_bytes = OPEN_FILE.read()

    # Create Response With Requested File
    response = make_response(snapshot_file_bytes)  # Includes the Snapshot File into the Response
    response.headers.set('Content-Type',
                         snapshot_file_extension)  # Sets the Response Content-Type to File Extension of Snapshot File
    # Sets the Response Content-Disposition to Attachment and Includes the File Name
    response.headers.set('Content-Disposition', 'attachment',
                         filename='%s' % snapshot_short_filename)

    # Return Response with Requested Snapshot File
    return response


#
# Curl Usage Command Examples For '/get_snapshot_zip' API Call
# Required Post Variables: SNAPSHOT_NAME
# Required Header Variables: X-Api-Key
# Optional Post Variables: STUDENT_ID
# If STUDENT_ID does not exist in the request, the whole snapshot will be archived and downloaded.
# Example Response: curl: Saved to filename '31387714_12-08-2021.zip'
#
# curl -OJ -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_NAME=12-08-2021" http://localhost:5000/get_snapshot_zip
# curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=12-08-2021" http://localhost:5000/get_snapshot_zip
# curl -OJ -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=12-08-2021" http://localhost:5000/get_snapshot_zip
#
@app.route('/get_snapshot_zip', methods=['POST'])
@requires_apikey
def get_snapshot_zip():
    """ Get Zip File of Specified Student Snapshot. """

    student_id = request.form.get('STUDENT_ID')  # StudentID Post Variable
    snapshot_name = request.form.get('SNAPSHOT_NAME')  # Snapshot Name Variable

    # Error if StudentID Post Variable Missing
    # if not student_id:
    #     return (jsonify(status=406,
    #                     error='Not Acceptable - Missing Data',
    #                     message='Not Acceptable - Missing STUDENT_ID Post Value.'
    #                     ), 406)

    # Error if Snapshot Name Post Variable Missing
    if not snapshot_name:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing SNAPSHOT_NAME Post Value.'
                        ), 406)
    if student_id:
        snap_path = SNAPSHOT_DIR + student_id  # Student Snapshot Directory Path
        snap_name_path = snap_path + '/' + snapshot_name  # Student Snapshot Path
        zip_file_name = student_id + '_' + snapshot_name + '.zip'  # Snapshot Zip File Name
    else:
        snap_path = SNAPSHOT_DIR  # Student Snapshot Directory Path
        snap_name_path = snap_path + '/' + snapshot_name  # Student Snapshot Path
        zip_file_name = snapshot_name + '.zip'  # Snapshot Zip File Name

    snap_student_path_obj = Path(snap_path)  # Student Snapshot Directory Path Object
    snap_name_path_obj = Path(snap_name_path)  # Student Snapshot Path Object

    # Error if Student Snapshot Directory Does Not Exist
    if not (snap_student_path_obj.exists() and snap_student_path_obj.is_dir()):
        return (jsonify(status=404,
                        error='Not Found - Snapshot Directory was Not Found',
                        message='Not Found - Student Snapshot Directory Not Found.'
                        ), 404)

    # Error if Specific Snapshot Does Not Exist
    if not (snap_name_path_obj.exists()
            and snap_name_path_obj.is_dir()):
        return (jsonify(status=404,
                        error='Not Found - Snapshot was Not Found',
                        message='Not Found - Snapshot Not Found.'), 404)

    # Create Zip File of Snapshot with Relative Path
    snap_file = io.BytesIO()  # Create Empty File In Memory
    with zf.ZipFile(snap_file, 'w') as SNAP_ZIP_FILE:  # Open Empty File as Zip File Object for Writing
        for (dirname, subdirs, files) in os.walk(snap_name_path + '/'):  # Loop Through Snapshot Files and Directories
            if "/." not in dirname:
                SNAP_ZIP_FILE.write(dirname, dirname.replace(SNAPSHOT_DIR, ''))  # Add Directory to Zip File Object
                for filename in files:  # Loop Through Each File in Snapshot Directory
                    if "/." not in filename:
                        SNAP_ZIP_FILE.write(os.path.join(dirname, filename),
                                            os.path.join(dirname,
                                                         filename).replace(SNAPSHOT_DIR, ''),
                                            zf.ZIP_DEFLATED)  # Add Snapshot File To Zip File Object
        SNAP_ZIP_FILE.close()  # Finish Writing to Zip File Object
    snap_file.seek(0)  # Reset position of Snap Zip File to Beginning

    response = make_response(snap_file.read())  # Includes the Zip File into the Response
    response.headers.set('Content-Type', 'zip')  # Sets the Response Content-Type to Zip File
    # Sets the Response Content-Disposition to Attachment and Includes the File Name
    response.headers.set('Content-Disposition', 'attachment',
                         filename='%s' % zip_file_name)

    # Return Response with Zip File
    return response


#
# Curl Usage Command Examples For '/put_student_report' API Call
# Required Post Variables: STUDENT_ID, file (Pointer to Actual File)
# Required Header Variables: X-Api-Key
# Example Response: "Success - File Uploaded - upload_test.txt"
#
# curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F UPLOAD_FILE=@upload_test.txt http://localhost:5000/put_student_report
#
@app.route('/put_student_report', methods=['POST'])
@requires_apikey
def put_student_report():
    """ Put Specified File into Specified Student Home Directory. """

    student_id = request.form.get('STUDENT_ID')  # StudentID Post Variable
    file_data = request.files['UPLOAD_FILE']  # File Uploaded Data Post Variable
    file_name = secure_filename(file_data.filename)  # Name of File Uploaded Data

    # Error if StudentID Post Variable Missing
    if not student_id:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing STUDENT_ID Post Value.'
                        ), 406)

    # Error if No Data in UPLOAD_FILE Post Variable
    if not file_data:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing File Upload Post Data.'
                        ), 406)

    # Error if No Filename for UPLOAD_FILE Post Variable
    if not file_name:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing File Name Value.'),
                406)

    temp_file_name = uuid.uuid4().hex  # Unique Temp File Name
    student_path = HOMEDIR + student_id  # Student Home Directory Path
    student_file_path = student_path + '/' + file_name  # Student Home File Path

    student_path_obj = Path(student_path)  # Student Home Directory Path Object
    student_file_path_obj = Path(student_file_path)  # Student Uploaded File Path Object

    # Error if Student Home Does Not Exist
    if not (student_path_obj.exists() and student_path_obj.is_dir()):
        return (jsonify(status=404,
                        error='Not Found - Student Directory Not Found',
                        message='Not Found - STUDENT_ID Home Directory was Not Found.'
                        ), 404)

    # Error if File Already Exists In Student Home Directory
    if student_file_path_obj.exists():
        return (jsonify(status=417,
                        error='Expectation Failed - Uploaded File Already Exists'
                        ,
                        message='Expectation Failed - The File Uploaded Already Exists within the Student\'s Home Directory.'
                                + student_file_path), 417)

    # Error if Uploaded File Extension Not in Allowed Extensions List
    if not ('.' in file_name and file_name.rsplit('.', 1)[1].lower()
            in ALLOWED_EXTENSIONS):
        return (jsonify(status=417,
                        error='Expectation Failed - Invalid Uploaded File Type'
                        ,
                        message='Expectation Failed - The File Uploaded is Not Allowed. Please upload only '
                                + str(ALLOWED_EXTENSIONS) + ' file types.'), 417)

    # Save File with Temp Name to Upload Directory
    file_data.save(os.path.join(app.config['UPLOAD_FOLDER'],
                                temp_file_name))

    # Move & Rename File from Upload Directory with Temp Name to Student Home Directory with Actual Name
    shutil.move(os.path.join(app.config['UPLOAD_FOLDER'],
                             temp_file_name), student_file_path)

    # Return Success Message
    return jsonify('Success - File Uploaded - ' + file_name), 200


#
# Curl Usage Command Examples For '/snapshot' API Call
# Required Post Variables: STUDENT_ID, SNAPSHOT_NAME
# Required Header Variables: X-Api-Key
# Example Response:
#
# curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=Assignment-1-snap"
# http://localhost:5000/snapshot
#
@app.route('/snapshot', methods=['POST'])
@requires_apikey
def snapshot():
    """ Create a Snapshot of the Specified Student's Home Directory with the Specified Snapshot Name. """

    student_id = request.form.get('STUDENT_ID')  # StudentID Post Variable
    snapshot_name = request.form.get('SNAPSHOT_NAME')  # SNAPSHOT_NAME Post Variable

    date = datetime.datetime.now()  # Get Current Date
    date = date.isoformat()  # Convert to ISO Format Date
    date = date[0:10]  # Trim Time from ISO Date

    # Error if StudentID Post Variable Missing
    if not student_id:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing STUDENT_ID Post Value.'
                        ), 406)

    # Error if SNAPSHOT_NAME Post Variable Missing
    if not snapshot_name:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing SNAPSHOT_NAME Post Value.'
                        ), 406)

    snapshot_name_clean = slugify(snapshot_name)  # Ensure The SNAPSHOT_NAME is a Safe Filename
    snapshot_name_clean = snapshot_name_clean + '_' + date  # Add Date to SNAPSHOT_NAME_CLEAN

    student_path = HOMEDIR + student_id  # Student Home Directory Path
    snap_student_path = SNAPSHOT_DIR + student_id  # Student Snapshot Directory Path
    snap_name_path = snap_student_path + '/' + snapshot_name_clean  # Student Snapshot Path
    lockfile = '/var/lock/' + COURSE_CODE + '_' + student_id + '.lock'  # Lock File For Student
    intsnap_student_path = INTERMEDIARY_DIR + student_id

    student_path_obj = Path(student_path)  # Student Home Directory Path Object
    snap_student_path_obj = Path(snap_student_path)  # Student Snapshot Directory Path Object
    snap_name_path_obj = Path(snap_name_path)  # Student Snapshot Path Object

    # Error if Student Home Does Not Exist
    if not (student_path_obj.exists() and student_path_obj.is_dir()):
        return (jsonify(status=404,
                        error='Not Found - Student Directory Not Found',
                        message='Not Found - STUDENT_ID Home Directory was Not Found.'
                        ), 404)

    #    # Error if Student Snapshot Directory Does Not Exist
    #    if not (SNAP_STUDENT_PATH_OBJ.exists() and SNAP_STUDENT_PATH_OBJ.is_dir()):
    #        return (jsonify(status=404,
    #                error='Not Found - Snapshot Directory was Not Found',
    #                message='Not Found - Student Snapshot Directory Not Found.'
    #                ), 404)

    # Error if Specific Snapshot Already Exists
    if (snap_name_path_obj.exists()
            and snap_name_path_obj.is_dir()):
        return (jsonify(status=404,
                        error='Already Exists - Snapshot Name Already Exists',
                        message='Already Exists - Student Snapshot Already Exists.'), 404)

    # Create FLOCK or Wait 2 Seconds
    while True:
        try:
            lockfile_obj = open(lockfile, 'w+')  # Open Lock File, Create if Does Not Exist
            fcntl.flock(lockfile_obj, fcntl.LOCK_EX | fcntl.LOCK_NB)  # Create Non Blocking Exclusive Flock
            break  # Break Out of While Loop if no Errors
        except:
            time.sleep(2)

    # Create Student Home Directory Structure to Final Snapshot Directory If Missing
    Path(snap_student_path).mkdir(parents=True, exist_ok=True)

    # RSYNC Student Home to Intermediate Snapshot Directory
    sysrsync.run(source=student_path,
                 destination=intsnap_student_path,
                 sync_source_contents=True,
                 options=['-a', '-v', '-h', '-W', '--no-compress'])

    # Move Int Snap to Final Snap Location with New Name
    shutil.move(intsnap_student_path, snap_name_path)

    # Unlock Flock
    fcntl.flock(lockfile_obj, fcntl.LOCK_UN)
    lockfile_obj.close()
    os.remove(lockfile)

    # Return Success Message
    return jsonify('Success - Snapshot Created - ' + snapshot_name_clean + ' for Student: ' + student_id), 200


#
# Curl Usage Command Examples For '/snapshot_all' API Call
# Required Post Variables: SNAPSHOT_NAME
# Required Header Variables: X-Api-Key
# Example Response:
#
# curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_NAME=assignment-1-snap-all" http://localhost:5000/snapshot_all
# curl -X POST -H "X-Api-Key: 12345" -d "STUDENT_NAME=assignment-1-snap-all" http://localhost:5000/snapshot_all
# curl -X POST -H "X-Api-Key: 12345" -data "STUDENT_NAME=assignment-1-snap-all" http://localhost:5000/snapshot_all
#
@app.route('/snapshot_all', methods=['POST'])
@requires_apikey
def snapshot_all():
    """ Create a Snapshot of tll the Student's Home Directories with the Specified Snapshot Name. """

    snapshot_name = request.form.get('SNAPSHOT_NAME')  # SNAPSHOT_NAME Post Variable

    date = datetime.datetime.now()  # Get Current Date
    date = date.isoformat()  # Convert to ISO Format Date
    date = date[0:10]  # Trim Time from ISO Date

    # Error if SNAPSHOT_NAME Post Variable Missing
    if not snapshot_name:
        return (jsonify(status=406,
                        error='Not Acceptable - Missing Data',
                        message='Not Acceptable - Missing SNAPSHOT_NAME Post Value.'
                        ), 406)

    # Get List of Directories in Student Snapshot Directory
    students = [f.path for f in os.scandir(HOMEDIR) if f.is_dir()]
    students = [x for x in students if '.' not in x]
    students = [s.replace(HOMEDIR, '') for s in students]

    snapshot_name_clean = slugify(snapshot_name)  # Ensure The SNAPSHOT_NAME is a Safe Filename
    snapshot_name_clean = snapshot_name_clean + '_' + date  # Add Date to SNAPSHOT_NAME_CLEAN

    # Check All Students Snapshot Directories that the Snapshot Does Not Exist
    for student in students:
        snap_student_path = SNAPSHOT_DIR + student  # Student Snapshot Directory Path
        snap_name_path = snap_student_path + '/' + snapshot_name_clean  # Student Snapshot Path

        snap_student_path_obj = Path(snap_student_path)  # Student Snapshot Directory Path Object
        snap_name_path_obj = Path(snap_name_path)  # Student Snapshot Path Object

        # Error if Student Snapshot Directory Does Not Exist
        #        if not (SNAP_STUDENT_PATH_OBJ.exists() and SNAP_STUDENT_PATH_OBJ.is_dir()):
        #            return (jsonify(status=404,
        #                error='Not Found - Snapshot Directory was Not Found',
        #                message='Not Found - Student ('+STUDENT+') Snapshot Directory Not Found.'
        #                ), 404)

        # Error if Specific Snapshot Already Exists
        if snap_name_path_obj.exists() and snap_name_path_obj.is_dir():
            return (jsonify(status=404,
                            error='Already Exists - Snapshot Name Already Exists',
                            message='Already Exists - Student (' + student + ') Snapshot Already Exists.'), 404)

    # Create Snapshots for All Students
    for student in students:
        student_path = HOMEDIR + student  # Student Home Directory Path
        snap_student_path = SNAPSHOT_DIR + student  # Student Snapshot Directory Path
        snap_name_path = snap_student_path + '/' + snapshot_name_clean  # Student Snapshot Path
        lockfile = '/var/lock/' + COURSE_CODE + '_' + student + '.lock'  # Lock File For Student
        intsnap_student_path = INTERMEDIARY_DIR + student

        # Create FLOCK or Wait 2 Seconds
        while True:
            try:
                lockfile_obj = open(lockfile, 'w+')  # Open Lock File, Create if Does Not Exist
                fcntl.flock(lockfile_obj, fcntl.LOCK_EX | fcntl.LOCK_NB)  # Create Non Blocking Exclusive Flock
                break  # Break Out of While Loop if no Errors
            except:
                time.sleep(2)

        # Create Student Home Directory Structure to Final Snapshot Directory If Missing
        Path(snap_student_path).mkdir(parents=True, exist_ok=True)

        # RSYNC Student Home to Intermediate Snapshot Directory
        sysrsync.run(source=student_path,
                     destination=intsnap_student_path,
                     sync_source_contents=True,
                     options=['-a', '-v', '-h', '-W', '--no-compress'])

        # Move Int Snap to Final Snap Location with New Name
        shutil.move(intsnap_student_path, snap_name_path)

        # Unlock Flock
        fcntl.flock(lockfile_obj, fcntl.LOCK_UN)
        lockfile_obj.close()
        os.remove(lockfile)

    # Return Success Message
    return jsonify('Success - Snapshot Created - ' + snapshot_name_clean + ' for All Students'), 200


if __name__ == '__main__':
    # app.run(host=HOST, port=PORT, debug=DEBUG)
    serve(TransLogger(app, setup_console_handler=False), host=HOST, port=PORT)
