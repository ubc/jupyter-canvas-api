#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Provides an API for Instructors to interact with their Students Jupyter Hub Directories.
Instructors can use this API to snapshot student directories upon deadline, download
snapshotted directories as Zip files, download individual files from snapshots, list
snapshots of student’s directories, list files within a students’ snapshot, and put files
such as reports into the students’ home directory.
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
from waitress import serve
import unicodedata
import re
import datetime
import fcntl
import sysrsync

__author__ = "Rahim Khoja"
__credits__ = ["Rahim Khoja", "Balaji Srinivasarao", "Pan Luo"]
__license__ = "GPL"
__version__ = "0.5"
__maintainer__ = "Rahim Khoja"
__email__ = "rahim.khoja@ubc.ca"
__status__ = "Development"

# API Variables Defined by Enviroment Variable
DEBUG = os.getenv('DEBUG', 'False') == 'True'   # API Debug
PORT = int(os.getenv('JUPYTER_API_PORT', '5000'))  # API TCP Port Number
HOST = str(os.getenv('JUPYTER_API_HOST', '0.0.0.0'))  # API TCP Address
APIKEY = str(os.getenv('JUPYTER_API_KEY', '12345'))  # API Key Value
HOMEDIR = str(os.getenv('JNOTE_HOME', '/mnt/efs/stat-100a-home/'))  # Home Directory Root
SNAPDIR = str(os.getenv('JNOTE_SNAP', '/mnt/efs/stat-100a-snap/'))  # Instructor Snapshot Directory
INTSNAPDIR = str(os.getenv('JNOTE_INTSNAP', '/mnt/efs/stat-100a-internal/'))  # Intermediary Snapshot Directory
COURSECODE = str(os.getenv('JNOTE_COURSE_CODE', 'STAT100a'))  # The API Course Code

UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')   # Temporary Upload Folder
ALLOWED_EXTENSIONS = set(['txt', 'html', 'htm', 'ipynb'])   # Allowed Upload File Types

app = Flask(__name__)

# Provide API Key Value to Flask
app.config['API_KEY'] = APIKEY

# JSONIFY Does Not Work Correctly Without the Following Variable
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # Max Upload File Size (2MB)

# Create Upload Directory If Does Not Exist
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # Flask Upload Directory


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

    return (jsonify(status=401, error='Not Authorized',
            message='You are authorized to access the URL requested.'),
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
    """ Get List of Snapshot Files for the Specfied Student and Snapshot. """

    STUDENT_ID = request.form.get('STUDENT_ID')  # StudentID Post Variable
    SNAPSHOT_NAME = request.form.get('SNAPSHOT_NAME')  # Snapshot Name Variable

    # Error if StudentID Post Variable Missing
    if not STUDENT_ID:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing StudentID Post Value.'
                ), 406)

    # Error if Snapshot Name Post Variable Missing
    if not SNAPSHOT_NAME:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing SNAPSHOT_NAME Post Value.'
                ), 406)

    SNAP_STUDENT_PATH = SNAPDIR+STUDENT_ID  # Student Snapshot Directory Path
    SNAP_NAME_PATH = SNAP_STUDENT_PATH+'/'+SNAPSHOT_NAME  # Student Snapshot Path

    SNAP_STUDENT_PATH_OBJ = Path(SNAP_STUDENT_PATH)  # Student Snapshot Directory Path Object
    SNAP_NAME_PATH_OBJ = Path(SNAP_NAME_PATH)  # Student Snapshot Path Object

    # Error if Snapshot Directory Does Not Exist
    if not (SNAP_STUDENT_PATH_OBJ.exists() and SNAP_STUDENT_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot Directory was Not Found',
                message='Not Found - Student Snapshot Directory Not Found.'
                ), 404)

    # Error if Specific Snapshot Does Not Exist
    if not (SNAP_NAME_PATH_OBJ.exists()
            and SNAP_NAME_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot was Not Found',
                message='Not Found - Snapshot Not Found.'), 404)

    # Get List Of Files In Snapshot Directory
    SNAPSHOT_FILES = glob.glob(os.path.join(SNAP_NAME_PATH+'/', '**/*'),
                               recursive=True)
    SNAPSHOT_FILES = [f for f in SNAPSHOT_FILES if os.path.isfile(f)]
    SNAPSHOT_FILES = [s.replace(SNAP_NAME_PATH+'/', '') for s in
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

    STUDENT_ID = request.form.get('STUDENT_ID')  # StudentID Post Variable

    # Error if StudentID Post Variable Missing
    if not STUDENT_ID:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing StudentID Post Value.'
                ), 406)

    SNAP_STUDENT_PATH = SNAPDIR+STUDENT_ID  # Student Snapshot Directory Path

    SNAP_STUDENT_PATH_OBJ = Path(SNAP_STUDENT_PATH)  # Student Snapshot Directory Path Object

    # Error if Snapshot Directory Does Not Exist
    if not (SNAP_STUDENT_PATH_OBJ.exists() and SNAP_STUDENT_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot Directory was Not Found',
                message='Not Found - Student Snapshot Directory Not Found.'
                ), 404)

    # Get List of Directories in Student Snapshot Directory
    SNAPSHOTS = [f.path for f in os.scandir(SNAP_STUDENT_PATH) if f.is_dir()]
    SNAPSHOTS = [x for x in SNAPSHOTS if '.' not in x]
    SNAPSHOTS = [s.replace(SNAP_STUDENT_PATH + '/', '') for s in SNAPSHOTS]

    # Error No Snapshots Found
    if not SNAPSHOTS:
        return (jsonify(status=404,
                error='Not Found - No Snapshots Found',
                message='Not Found - No Snapshot Directories Found.'),
                404)

    # Return List of Student Snapshots
    return (jsonify(SNAPSHOTS), 200)


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

    STUDENT_ID = request.form.get('STUDENT_ID')  # StudentID Post Variable
    SNAPSHOT_NAME = request.form.get('SNAPSHOT_NAME')  # Snapshot Name Variable
    SNAPSHOT_FILENAME = request.form.get('SNAPSHOT_FILENAME')  # Snapshot File Name Variable

    # Error if StudentID Post Variable Missing
    if not STUDENT_ID:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing STUDENT_ID Post Value.'
                ), 406)

    # Error if Snapshot Name Post Variable Missing
    if not SNAPSHOT_NAME:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing SNAPSHOT_NAME Post Value.'
                ), 406)

    # Error if Snapshot File Name Post Variable Missing
    if not SNAPSHOT_FILENAME:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing SNAPSHOT_FILENAME Post Value.'
                ), 406)

    SNAP_STUDENT_PATH = SNAPDIR+STUDENT_ID  # Student Snapshot Directory Path
    SNAP_NAME_PATH = SNAP_STUDENT_PATH+'/'+SNAPSHOT_NAME  # Student Snapshot Path
    SNAP_FILE_PATH = SNAP_NAME_PATH+'/'+SNAPSHOT_FILENAME  # Student Snapshot File Path

    SNAP_STUDENT_PATH_OBJ = Path(SNAP_STUDENT_PATH)  # Student Snapshot Directory Path Object
    SNAP_NAME_PATH_OBJ = Path(SNAP_NAME_PATH)  # Student Snapshot Path Object
    SNAP_FILE_PATH_OBJ = Path(SNAP_FILE_PATH)  # Student Snapshot File Path Object

    # Error if Snapshot Directory Does Not Exist
    if not (SNAP_STUDENT_PATH_OBJ.exists() and SNAP_STUDENT_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot Directory was Not Found',
                message='Not Found - Student Snapshot Directory Not Found.'
                ), 404)

    # Error if Specific Snapshot Does Not Exist
    if not (SNAP_NAME_PATH_OBJ.exists()
            and SNAP_NAME_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot was Not Found',
                message='Not Found - Snapshot Not Found.'), 404)

    # Error if Requested Snapshot File Does Not Exist
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
    with open(SNAP_FILE_PATH, 'rb') as OPEN_FILE:  # Open Snapshot File and Read it into the File Variable
        SNAPSHOT_FILE_BYTES = OPEN_FILE.read()

    # Create Response With Requested File
    response = make_response(SNAPSHOT_FILE_BYTES)  # Includes the Snaphot File into the Response
    response.headers.set('Content-Type', SNAPSHOT_FILE_EXTENSION)  # Sets the Response Content-Type to File Extension of Snapshot File
    response.headers.set('Content-Disposition', 'attachment',
                         filename='%s' % SNAPSHOT_SHORT_FILENAME)  # Sets the Response Content-Disposition to Attachment and Includes the File Name

    # Return Response with Requested Snapshot File
    return response


#
# Curl Usage Command Examples For '/get_snapshot_zip' API Call
# Required Post Variables: STUDENT_ID, SNAPSHOT_NAME
# Required Header Variables: X-Api-Key
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

    STUDENT_ID = request.form.get('STUDENT_ID')   # StudentID Post Variable
    SNAPSHOT_NAME = request.form.get('SNAPSHOT_NAME')  # Snapshot Name Variable

    # Error if StudentID Post Variable Missing
    if not STUDENT_ID:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing STUDENT_ID Post Value.'
                ), 406)

    # Error if Snapshot Name Post Variable Missing
    if not SNAPSHOT_NAME:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing SNAPSHOT_NAME Post Value.'
                ), 406)

    SNAP_STUDENT_PATH = SNAPDIR+STUDENT_ID  # Student Snapshot Directory Path
    SNAP_NAME_PATH = SNAP_STUDENT_PATH+'/'+SNAPSHOT_NAME  # Student Snapshot Path
    ZIP_FILE_NAME = STUDENT_ID+'_'+SNAPSHOT_NAME+'.zip' # Snapshot Zip File Name

    SNAP_STUDENT_PATH_OBJ = Path(SNAP_STUDENT_PATH)  # Student Snapshot Directory Path Object
    SNAP_NAME_PATH_OBJ = Path(SNAP_NAME_PATH)  # Student Snapshot Path Object

    # Error if Student Snapshot Directory Does Not Exist
    if not (SNAP_STUDENT_PATH_OBJ.exists() and SNAP_STUDENT_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot Directory was Not Found',
                message='Not Found - Student Snapshot Directory Not Found.'
                ), 404)

    # Error if Specific Snapshot Does Not Exist
    if not (SNAP_NAME_PATH_OBJ.exists()
            and SNAP_NAME_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Snapshot was Not Found',
                message='Not Found - Snapshot Not Found.'), 404)

    # Create Zip File of Snapshot with Relative Path
    SNAP_FILE = io.BytesIO()  # Create Empty File In Memory
    with zf.ZipFile(SNAP_FILE, 'w') as SNAP_ZIP_FILE: # Open Empty File as Zip File Object for Writing
        for (dirname, subdirs, files) in os.walk(SNAP_NAME_PATH + '/'): # Loop Thru Snapshot Files and Directories
            if "/." not in dirname:
                SNAP_ZIP_FILE.write(dirname, dirname.replace(SNAPDIR, ''))  # Add Directory to Zip File Object
                for filename in files: # Loop Thru Each File in Snapshot Directory
                    if "/." not in filename:
                        SNAP_ZIP_FILE.write(os.path.join(dirname, filename),
                                            os.path.join(dirname,
                                            filename).replace(SNAPDIR, ''),
                                            zf.ZIP_DEFLATED) # Add Snapshot File To Zip File Object
        SNAP_ZIP_FILE.close() # Finish Writing to Zip File Object
    SNAP_FILE.seek(0) # Reset position of Snap Zip File to Beginning

    response = make_response(SNAP_FILE.read())  # Includes the Zip File into the Response
    response.headers.set('Content-Type', 'zip') # Sets the Response Content-Type to Zip File
    response.headers.set('Content-Disposition', 'attachment',
                         filename='%s' % ZIP_FILE_NAME)  # Sets the Response Content-Disposition to Attachment and Includes the File Name

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

    STUDENT_ID = request.form.get('STUDENT_ID') # StudentID Post Variable
    FILE_DATA = request.files['UPLOAD_FILE']  # File Uploaded Data Post Variable
    FILE_NAME = secure_filename(FILE_DATA.filename)  # Name of File Uploaded Data

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

    TEMP_FILE_NAME = uuid.uuid4().hex  # Unique Temp File Name
    STUDENT_PATH = HOMEDIR+STUDENT_ID  # Student Home Directory Path
    STUDENT_FILE_PATH = STUDENT_PATH+'/'+FILE_NAME  # Student Home File Path

    STUDENT_PATH_OBJ = Path(STUDENT_PATH) # Student Home Directory Path Object
    STUDENT_FILE_PATH_OBJ = Path(STUDENT_FILE_PATH) # Student Uploaded File Path Object

    # Error if Student Home Does Not Exist
    if not (STUDENT_PATH_OBJ.exists() and STUDENT_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Not Found - Student Directory Not Found',
                message='Not Found - STUDENT_ID Home Directory was Not Found.'
                ), 404)

    # Error if File Already Exists In Student Home Directory
    if STUDENT_FILE_PATH_OBJ.exists():
        return (jsonify(status=417,
                error='Expectation Failed - Uploaded File Already Exists'
                ,
                message='Expectation Failed - The File Uploaded Already Exists within the Student\'s Home Directory.'
                 + STUDENT_FILE_PATH), 417)

    # Error if Uploaded File Extension Not in Allowed Extensions List
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

    # Move & Rename File from Upload Directory with Temp Name to Student Home Directory with Actual Name
    shutil.move(os.path.join(app.config['UPLOAD_FOLDER'],
                TEMP_FILE_NAME), STUDENT_FILE_PATH)

    # Return Success Message
    return (jsonify('Success - File Uploaded - ' + FILE_NAME), 200)


#
# Curl Usage Command Examples For '/snapshot' API Call
# Required Post Variables: STUDENT_ID, SNAPSHOT_NAME
# Required Header Variables: X-Api-Key
# Example Response:
#
# curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=Assignment-1-snap" http://localhost:5000/snapshot
#
@app.route('/snapshot', methods=['POST'])
@requires_apikey
def snapshot():
    """ Create a Snapshot of the Specified Student's Home Directory with the Specfied Snapshot Name. """

    STUDENT_ID = request.form.get('STUDENT_ID') # StudentID Post Variable
    SNAPSHOT_NAME = request.form.get('SNAPSHOT_NAME') # SNAPSHOT_NAME Post Variable

    DATE=datetime.datetime.now()  # Get Current Date
    DATE=DATE.isoformat()  # Convert to ISO Format Date
    DATE=DATE[0:10] # Trim Time from ISO Date

    # Error if StudentID Post Variable Missing
    if not STUDENT_ID:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing STUDENT_ID Post Value.'
                ), 406)

    # Error if SNAPSHOT_NAME Post Variable Missing
    if not SNAPSHOT_NAME:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing SNAPSHOT_NAME Post Value.'
                ), 406)


    SNAPSHOT_NAME_CLEAN = slugify(SNAPSHOT_NAME) # Ensure The SNAPSHOT_NAME is a Safe Filename
    SNAPSHOT_NAME_CLEAN = SNAPSHOT_NAME_CLEAN+'_'+DATE  # Add Date to SNAPSHOT_NAME_CLEAN

    STUDENT_PATH = HOMEDIR+STUDENT_ID  # Student Home Directory Path
    SNAP_STUDENT_PATH = SNAPDIR+STUDENT_ID  # Student Snapshot Directory Path
    SNAP_NAME_PATH = SNAP_STUDENT_PATH+'/'+SNAPSHOT_NAME_CLEAN  # Student Snapshot Path
    LOCKFILE = '/var/lock/'+COURSECODE+'_'+STUDENT_ID+'.lock'  # Lock File For Student
    INTSNAP_STUDENT_PATH = INTSNAPDIR+STUDENT_ID


    STUDENT_PATH_OBJ = Path(STUDENT_PATH) # Student Home Directory Path Object
    SNAP_STUDENT_PATH_OBJ = Path(SNAP_STUDENT_PATH)  # Student Snapshot Directory Path Object
    SNAP_NAME_PATH_OBJ = Path(SNAP_NAME_PATH)  # Student Snapshot Path Object

    # Error if Student Home Does Not Exist
    if not (STUDENT_PATH_OBJ.exists() and STUDENT_PATH_OBJ.is_dir()):
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
    if (SNAP_NAME_PATH_OBJ.exists()
            and SNAP_NAME_PATH_OBJ.is_dir()):
        return (jsonify(status=404,
                error='Already Exists - Snapshot Name Already Exists',
                message='Already Exists - Student Snapshot Already Exists.'), 404)

    # Create FLOCK or Wait 2 Seconds
    while True:
        try:
            LOCKFILE_OBJ = open(LOCKFILE, 'w+')  # Open Lock File, Create if Does Not Exist
            fcntl.flock(LOCKFILE_OBJ, fcntl.LOCK_EX | fcntl.LOCK_NB)  # Create Non Blocking Exclusive Flock
            break   #  Break Out of While Loop if no Errors
        except:
            time.sleep(2)

    # RSYNC Student Home Directory Structure to Final Snapshot Directory
    sysrsync.run(source=STUDENT_PATH,
             destination=SNAP_STUDENT_PATH,
             options=['-a' ,'-v' ,'-f"+ */"' ,'-f"- *"', '--exclude="*/*"'])       
            
    # RSYNC Student Home to Intermediate Snapshot Directory
    sysrsync.run(source=STUDENT_PATH,
             destination=INTSNAP_STUDENT_PATH,
             sync_source_contents=True,
             options=['-a' ,'-v' ,'-h' ,'-W', '--no-compress'])

    # Move Int Snap to Final Snap Location with New Name
    shutil.move(INTSNAP_STUDENT_PATH, SNAP_NAME_PATH)

    # Unlock Flock
    fcntl.flock(LOCKFILE_OBJ, fcntl.LOCK_UN)
    LOCKFILE_OBJ.close()
    os.remove(LOCKFILE)

    # Return Success Message
    return (jsonify('Success - Snapshot Created - '+SNAPSHOT_NAME_CLEAN+' for Student: '+STUDENT_ID), 200)


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
    """ Create a Snapshot of tll the Student's Home Directories with the Specfied Snapshot Name. """

    SNAPSHOT_NAME = request.form.get('SNAPSHOT_NAME') # SNAPSHOT_NAME Post Variable

    DATE=datetime.datetime.now()  # Get Current Date
    DATE=DATE.isoformat()  # Convert to ISO Format Date
    DATE=DATE[0:10] # Trim Time from ISO Date

    # Error if SNAPSHOT_NAME Post Variable Missing
    if not SNAPSHOT_NAME:
        return (jsonify(status=406,
                error='Not Acceptable - Missing Data',
                message='Not Acceptable - Missing SNAPSHOT_NAME Post Value.'
                ), 406)

    # Get List of Directories in Student Snapshot Directory
    STUDENTS = [f.path for f in os.scandir(HOMEDIR) if f.is_dir()]
    STUDENTS = [x for x in STUDENTS if '.' not in x]
    STUDENTS = [s.replace(HOMEDIR, '') for s in STUDENTS]

    SNAPSHOT_NAME_CLEAN = slugify(SNAPSHOT_NAME) # Ensure The SNAPSHOT_NAME is a Safe Filename
    SNAPSHOT_NAME_CLEAN = SNAPSHOT_NAME_CLEAN+'_'+DATE  # Add Date to SNAPSHOT_NAME_CLEAN

    # Check All Students Snapshot Directories that the Snapshot Does Not Existse
    for STUDENT in STUDENTS:
        SNAP_STUDENT_PATH = SNAPDIR+STUDENT  # Student Snapshot Directory Path
        SNAP_NAME_PATH = SNAP_STUDENT_PATH+'/'+SNAPSHOT_NAME_CLEAN  # Student Snapshot Path

        SNAP_STUDENT_PATH_OBJ = Path(SNAP_STUDENT_PATH)  # Student Snapshot Directory Path Object
        SNAP_NAME_PATH_OBJ = Path(SNAP_NAME_PATH)  # Student Snapshot Path Object

        # Error if Student Snapshot Directory Does Not Exist
#        if not (SNAP_STUDENT_PATH_OBJ.exists() and SNAP_STUDENT_PATH_OBJ.is_dir()):
#            return (jsonify(status=404,
#                error='Not Found - Snapshot Directory was Not Found',
#                message='Not Found - Student ('+STUDENT+') Snapshot Directory Not Found.'
#                ), 404)

        # Error if Specific Snapshot Already Exists
        if (SNAP_NAME_PATH_OBJ.exists() and SNAP_NAME_PATH_OBJ.is_dir()):
            return (jsonify(status=404,
                error='Already Exists - Snapshot Name Already Exists',
                message='Already Exists - Student ('+STUDENT+') Snapshot Already Exists.'), 404)

    # Create Snapshots for All Students
    for STUDENT in STUDENTS:
        STUDENT_PATH = HOMEDIR+STUDENT  # Student Home Directory Path
        SNAP_STUDENT_PATH = SNAPDIR+STUDENT  # Student Snapshot Directory Path
        SNAP_NAME_PATH = SNAP_STUDENT_PATH+'/'+SNAPSHOT_NAME_CLEAN  # Student Snapshot Path
        LOCKFILE = '/var/lock/'+COURSECODE+'_'+STUDENT+'.lock'  # Lock File For Student
        INTSNAP_STUDENT_PATH = INTSNAPDIR+STUDENT

        # Create FLOCK or Wait 2 Seconds
        while True:
            try:
                LOCKFILE_OBJ = open(LOCKFILE, 'w+')  # Open Lock File, Create if Does Not Exist
                fcntl.flock(LOCKFILE_OBJ, fcntl.LOCK_EX | fcntl.LOCK_NB)  # Create Non Blocking Exclusive Flock
                break   #  Break Out of While Loop if no Errors
            except:
                time.sleep(2)

        # RSYNC Student Home Directory Structure to Final Snapshot Directory
        sysrsync.run(source=STUDENT_PATH,
             destination=SNAP_STUDENT_PATH,
             options=['-a' ,'-v' ,'-f"+ */"' ,'-f"- *"', '--exclude="*/*"'])    
                
        # RSYNC Student Home to Intermediate Snapshot Directory
        sysrsync.run(source=STUDENT_PATH,
                     destination=INTSNAP_STUDENT_PATH,
                     sync_source_contents=True,
                     options=['-a' ,'-v' ,'-h' ,'-W', '--no-compress'])

        # Move Int Snap to Final Snap Location with New Name
        shutil.move(INTSNAP_STUDENT_PATH, SNAP_NAME_PATH)

        # Unlock Flock
        fcntl.flock(LOCKFILE_OBJ, fcntl.LOCK_UN)
        LOCKFILE_OBJ.close()
        os.remove(LOCKFILE)

    # Return Success Message
    return (jsonify('Success - Snapshot Created - '+SNAPSHOT_NAME_CLEAN+' for All Students'), 200)

if __name__ == '__main__':
    #app.run(host=HOST, port=PORT, debug=DEBUG)
    serve(app, host=HOST, port=PORT)
