#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Provides am API for Instructors to interact with Student Jupyter Hub Directories.

Instructors can use this API to snapshot student directories upon deadline, download 
snapshotted directories as Zip files, download individual files from snapshots, list 
snapshots of students directories, list files within a students snapshot, and put files
such as reports into the students home directroy. 

"""

import os
import uuid
import io
import zipfile as zf
import time
from functools import wraps
from flask import Flask, request, jsonify, abort, url_for, send_file, \
    make_response
from pathlib import Path
import shutil
from werkzeug.utils import secure_filename
import glob

__author__ = "Rahim Khoja"
__copyright__ = "Copyright 2007, The Cogent Project"
__credits__ = ["Rahim Khoja", "Bala", ""]
__license__ = "MIT"
__version__ = "0.5"
__maintainer__ = "Rahim Khoja"
__email__ = "rahim.khoja@ubc.ca"
__status__ = "Development"

# Get global variables from the environment
DEBUG = os.getenv('DEBUG', 'False') == 'True'
PORT = int(os.getenv('JUPYTER_API_PORT', '5000'))
HOST = str(os.getenv('JUPYTER_API_HOST', '0.0.0.0'))
SNAPDIR = '/mnt/efs/snap/'
HOMEDIR = '/mnt/efs/home/'
FINALSNAPDIR
UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')  # Temporary Upload Folder
ALLOWED_EXTENSIONS = set(['txt', 'html', 'htm', 'ipynb', 'json']) # Allowed Upload File Types

app = Flask(__name__)
app.config['API_KEY'] = str(os.getenv('JUPYTER_API_KEY', '12345'))  # Get API_KEY from Env Variable

# jsonify does not work without this option in current versions
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # Max Upload File Size (2MB)

# Create Temporary Directory If Does Not Exist
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # Define Flask Upload Directory 

@app.errorhandler(401)
def not_authorized(e):
    """ Respose sent back when not autorized """

    return (jsonify(status=401, error='Not Authorized',
            message='You are authorized to access the URL requested.'),
            401)


def check_auth():
    """ Checks the environment that the API_KEY has been set """

    if app.config['API_KEY']:
        return app.config['API_KEY'] == request.headers.get('X-Api-Key')
    return False


def requires_apikey(f):
    """ Decorator function to require API Key """

    @wraps(f)
    def decorated(*args, **kwargs):
        """ Decorator function that does the checking """

        if check_auth():
            return f(*args, **kwargs)
        else:
            abort(401)
    return decorated


@app.route('/')
def index():
    return (jsonify(message='UBC Canvas / JupyterHub Instructor API',
            url=url_for('get_snapshot_list', _external=True),
            version='1.0'), 200)


#
# Curl Usage Command Examples For '/get_snapshot_file_list' API Call
# Required Post Variables: STUDENT_ID, SNAPSHOT_DATE
# Required Header Variables: X-Api-Key
# Example Respose: ["file2.txt","jupyterhubtest.txt","file1.txt","subdir_test/subdir_file1.txt"]
#
# curl -i -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_DATE=12-08-2021" http://localhost:5000/get_snapshot_file_list
# curl -i -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_DATE=12-08-2021" http://localhost:5000/get_snapshot_file_list
# curl -i -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_DATE=12-08-2021" http://localhost:5000/get_snapshot_file_list
#
@app.route('/get_snapshot_file_list', methods=['POST'])
@requires_apikey
def get_snapshot_file_list():
    """ Get List of Snapshot Files for the Specfied Student and Snapshot. """
    
    STUDENT_ID = request.form.get('STUDENT_ID')   # StudentID Post Variable
    SNAPSHOT_DATE = request.form.get('SNAPSHOT_DATE')  # Snapshot Name Variable
    
    SNAP_PATH = SNAPDIR+STUDENT_ID+'/'+SNAPSHOT_DATE # Snapshot Directory
    SNAP_PATH_OBJ = Path(SNAP_PATH)
    
    # Error if StudentID Post Variable Missing
    if not STUDENT_ID:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing StudentID Post Value.'
                ), 406)
                
    # Error if Snapshot Name Post Variable Missing
    if not SNAPSHOT_DATE:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing SNAPSHOT_DATE Post Value.'
                ), 406)

    # Error if Snapshot Directory Does Not Exist
    if not (SNAP_PATH_OBJ.exists() and SNAP_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot Directory was Not Found',
                message='Not Found - Student Snapshot Directory Not Found.'
                 + SNAP_PATH), 404)

    # Get List Of Files In Snapshot Directory
    SNAPSHOT_FILES = glob.glob(os.path.join(SNAP_PATH+'/', '**/*'),
                               recursive=True)
    SNAPSHOT_FILES = [f for f in SNAPSHOT_FILES if os.path.isfile(f)]
    SNAPSHOT_FILES = [s.replace(SNAP_PATH+'/', '') for s in
                      SNAPSHOT_FILES]
    
    # Error if No Snapshot Files Found
    if not SNAPSHOT_FILES:
        return (jsonify(status=404,
                error='Not Found - No Snapshots Found',
                message='Not Found - No Snapshot Directories Found.'),
                404)

	# Return List of Snapshot Files
    return (jsonify(SNAPSHOT_FILES), 200)


#
# Curl Usage Command Examples For '/get_snapshot_list' API Call
# Required Post Variables: STUDENT_ID
# Required Header Variables: X-Api-Key
# Example Respose: 
#
# curl -i -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714" http://localhost:5000/get_snapshot_list
# curl -i -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" http://localhost:5000/get_snapshot_list
# curl -i -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" http://localhost:5000/get_snapshot_list
#
@app.route('/get_snapshot_list', methods=['POST'])
@requires_apikey
def get_snapshot_list():
    """ Get List of Snapshot Directories for the Specfied Student. """
	
    STUDENT_ID = request.form.get('STUDENT_ID')   # StudentID Post Variable
	
    SNAP_PATH = SNAPDIR + STUDENT_ID
    PATH_OBJ = Path(SNAP_PATH)
	
	# Error if StudentID Post Variable Missing
    if not STUDENT_ID:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing StudentID Post Value.'
                ), 406)
				
	# Error if Snapshot Directory Does Not Exist
    if not (PATH_OBJ.exists() and PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot Directory was Not Found',
                message='Not Found - Student Snapshot Directory Not Found.'
                ), 404)

    # Get List of Directories in Student Snapshot Directory
    SNAPSHOTS = [f.path for f in os.scandir(SNAP_PATH) if f.is_dir()]
    SNAPSHOTS = [x for x in SNAPSHOTS if '.' not in x]
    SNAPSHOTS = [s.replace(SNAP_PATH + '/', '') for s in SNAPSHOTS]

    if not SNAPSHOTS:
        return (jsonify(status=404,
                error='Not Found - No Snapshots Found',
                message='Not Found - No Snapshot Directories Found.'),
                404)
				
	
    return (jsonify(SNAPSHOTS), 200)


#
# Curl Usage Command Examples For '/get_snapshot_file' API Call
# Required Post Variables: STUDENT_ID, SNAPSHOT_DATE, SNAPSHOT_FILENAME
# Required Header Variables: X-Api-Key
# Example Respose: 
#
# curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_DATE=12-08-2021" -d "SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
# curl -OJ -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_DATE=12-08-2021" -F "SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
# curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714&SNAPSHOT_DATE=12-08-2021&SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
# curl -OJ -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_DATE=12-08-2021&SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
#
@app.route('/get_snapshot_file', methods=['POST'])
@requires_apikey
def get_snapshot_file():
    """ Get the Specified File from Specified Student Snapshot. """

    STUDENT_ID = request.form.get('STUDENT_ID')   # StudentID Post Variable
    SNAPSHOT_DATE = request.form.get('SNAPSHOT_DATE')  # Snapshot Name Variable
    SNAPSHOT_FILENAME = request.form.get('SNAPSHOT_FILENAME')  # Snapshot File Name Variable
	
    SNAP_PATH = SNAPDIR + STUDENT_ID
    SNAP_DATE_PATH = SNAP_PATH + '/' + SNAPSHOT_DATE
    SNAP_PATH_OBJ = Path(SNAP_PATH)
    SNAP_DATE_PATH_OBJ = Path(SNAP_DATE_PATH)
    SNAP_FILE_PATH = SNAP_DATE_PATH + '/' + SNAPSHOT_FILENAME
    SNAP_FILE_PATH_OBJ = Path(SNAP_FILE_PATH)
	
	# Error if StudentID Post Variable Missing
    if not STUDENT_ID:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing STUDENT_ID Post Value.'
                ), 406)
    
	# Error if Snapshot Name Post Variable Missing
	if not SNAPSHOT_DATE:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing SNAPSHOT_DATE Post Value.'
                ), 406)
    
	# Error if Snapshot Directory Does Not Exist
	if not (SNAP_PATH_OBJ.exists() and SNAP_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot Directory was Not Found',
                message='Not Found - Student Snapshot Directory Not Found.'
                ), 404)
    
	# Error if Specfic Snapshot Does Not Exist
	if not (SNAP_DATE_PATH_OBJ.exists()
            and SNAP_DATE_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot was Not Found',
                message='Not Found - Snapshot Not Found.'), 404)
    
	# Error if Snapshot File Does Not Exist
	if not (SNAP_FILE_PATH_OBJ.exists()
            and SNAP_FILE_PATH_OBJ.is_file()):
        return (jsonify(status=404,
                error='Not Found - Snapshot File was Not Found',
                message='Not Found - Snapshot File Not Found.'), 404)

    SNAPSHOT_FILE_EXTENSION = SNAPSHOT_FILENAME.rsplit('.', 1)[-1]  # File Extension
    if '/' in SNAPSHOT_FILENAME:  # Get File Name Without Directory
        SNAPSHOT_SHORT_FILENAME = SNAPSHOT_FILENAME.rsplit('/', 1)[-1]
    else:
        SNAPSHOT_SHORT_FILENAME = SNAPSHOT_FILENAME

    SNAPSHOT_FILE_BYTES = ''  # Empty File Variable
    with open(SNAP_FILE_PATH, 'rb') as OPEN_FILE:
        SNAPSHOT_FILE_BYTES = OPEN_FILE.read()

    # Create Response With File
    response = make_response(SNAPSHOT_FILE_BYTES)
    response.headers.set('Content-Type', SNAPSHOT_FILE_EXTENSION)
    response.headers.set('Content-Disposition', 'attachment',
                         filename='%s' % SNAPSHOT_SHORT_FILENAME)
    return response


#
# Curl Usage Command Examples For '/get_snapshot_zip' API Call
# Required Post Variables: STUDENT_ID, SNAPSHOT_DATE
# Required Header Variables: X-Api-Key
# Example Respose: 
#
# curl -OJ -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_DATE=12-08-2021" http://localhost:5000/get_snapshot_zip
# curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_DATE=12-08-2021" http://localhost:5000/get_snapshot_zip
# curl -OJ -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_DATE=12-08-2021" http://localhost:5000/get_snapshot_zip
#
@app.route('/get_snapshot_zip', methods=['POST'])
@requires_apikey
def get_snapshot_zip():
    """ Get Zip File of Specified Student Snapshot. """

    STUDENT_ID = request.form.get('STUDENT_ID')   # StudentID Post Variable
    SNAPSHOT_DATE = request.form.get('SNAPSHOT_DATE')  # Snapshot Name Variable
	
    SNAP_PATH = SNAPDIR + STUDENT_ID
    SNAP_DATE_PATH = SNAP_PATH + '/' + SNAPSHOT_DATE
    SNAP_PATH_OBJ = Path(SNAP_PATH)
    SNAP_DATE_PATH_OBJ = Path(SNAP_DATE_PATH)
    ZIP_FILE_NAME = STUDENT_ID + '_' + SNAPSHOT_DATE + '.zip'
    
	# Error if StudentID Post Variable Missing
	if not STUDENT_ID:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing STUDENT_ID Post Value.'
                ), 406)
				
	# Error if Snapshot Name Post Variable Missing
    if not SNAPSHOT_DATE:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing SNAPSHOT_DATE Post Value.'
                ), 406)
				
	# Error if Snapshot Directory Does Not Exist
    if not (SNAP_PATH_OBJ.exists() and SNAP_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot Directory was Not Found',
                message='Not Found - Student Snapshot Directory Not Found.'
                ), 404)
    if not (SNAP_DATE_PATH_OBJ.exists()
            and SNAP_DATE_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot was Not Found',
                message='Not Found - Snapshot Not Found.'), 404)

    SNAP_FILE = io.BytesIO()  # Create Empty File In Memory
    with zf.ZipFile(SNAP_FILE, 'w') as SNAP_ZIP_FILE:
        for (dirname, subdirs, files) in os.walk(SNAP_DATE_PATH + '/'):
            SNAP_ZIP_FILE.write(dirname, dirname.replace(SNAPDIR, ''))
            for filename in files:
                SNAP_ZIP_FILE.write(os.path.join(dirname, filename),
                                    os.path.join(dirname,
                                    filename).replace(SNAPDIR, ''),
                                    zf.ZIP_DEFLATED)
        SNAP_ZIP_FILE.close()
    SNAP_FILE.seek(0)

    response = make_response(SNAP_FILE.read())
    response.headers.set('Content-Type', 'zip')
    response.headers.set('Content-Disposition', 'attachment',
                         filename='%s' % ZIP_FILE_NAME)
    return response


#
# Curl Usage Command Examples For '/put_student_report' API Call
# Required Post Variables: STUDENT_ID, file (Pointer to Actual File)
# Required Header Variables: X-Api-Key
# Example Respose: 
#
# curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F UPLOAD_FILE=@upload_test.txt http://localhost:5000/put_student_report
#
@app.route('/put_student_report', methods=['POST'])
@requires_apikey
def put_student_report():
    """ Put Specified File into Specified Student Home Directory. """

    STUDENT_ID = request.form.get('STUDENT_ID') # StudentID Post Variable
    FILE_DATA = request.files['UPLOAD_FILE']  # File Uploaded Data Post Variable
    FILE_NAME = secure_filename(FILE_DATA.filename)  # Name of File Uploaded Data
	
    TEMP_FILE_NAME = uuid.uuid4().hex  # Unique Temp File Name
    STUDENT_PATH = HOMEDIR+STUDENT_ID  # Student Home Directory Path
    STUDENT_FILE_PATH = STUDENT_PATH+'/'+FILE_NAME  # Student Home File Path
	
    STUDENT_PATH_OBJ = Path(STUDENT_PATH) 
    STUDENT_FILE_PATH_OBJ = Path(STUDENT_FILE_PATH)
	
    # Error if StudentID Post Variable Missing
    if not STUDENT_ID:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing STUDENT_ID Post Value.'
                ), 406)
    
    # Error if No Data in UPLOAD_FILE Post Variable
    if not FILE_DATA:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing File Upload Post Data.'
                ), 406)
    
    # Error if No Filename for UPLOAD_FILE Post Variable
    if not FILE_NAME:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing File Name Value.'),
                406)
    
    # Error if Student Home Does Not Exist
    if not (STUDENT_PATH_OBJ.exists() and STUDENT_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Student Directory Not Found',
                message='Not Found - STUDENT_ID Home  Directory was Not Found.'
                ), 404)
    
    # Error if File Already Exists In Student Home Directory 
    if STUDENT_FILE_PATH_OBJ.exists():
        return (jsonify(status=417,
                error='Expectation Failed - Uploaded File Already Exists'
                ,
                message='Expectation Failed - The File Uploaded Already Exists within the Student\'s Home Directory.'
                 + STUDENT_FILE_PATH), 417)

    # Error if Uploaded File Extention Not in Allowed Extentions List
    if not ('.' in FILE_NAME and FILE_NAME.rsplit('.', 1)[1].lower()
            in ALLOWED_EXTENSIONS):
        return (jsonify(status=417,
                error='Expectation Failed - Invalid Uploaded File Type'
                ,
                message='Expectation Failed - The File Uploaded is Not Allowed. Please upload only '
                 + str(ALLOWED_EXTENSIONS) + ' file types.'), 417)

    # Save File with Temp Name to Upload Directory
    FILE_DATA.save(os.path.join(app.config['UPLOAD_FOLDER'],
                   TEMP_FILE_NAME))

    # Move File to Student Directory from Upload Directory
    shutil.move(os.path.join(app.config['UPLOAD_FOLDER'],
                TEMP_FILE_NAME), STUDENT_FILE_PATH)
				
	
    return (jsonify('Success - File Uploaded - ' + FILE_NAME), 200)


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
