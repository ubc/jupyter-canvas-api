# Instructor API for the JupyterHub and Canvas Cluster POC

## Description

An API to interact with the file system hosting the JupyterHub home directories. It allows Instructors to Snapshot their Students Home Drives for deadlines via an API call. These Snapshots can be triggered via an API call initiaated from a Canvas Assignment deadline. Instructors can create multiple Snapshots with custom names for each student or sets of students. Instructors can retrieve the Snapshots via a ZIP file of the whole Snapshot or by specifing specfic files within the Snapshot. Instryctors can also Put grading reports into the Students Home Directory by an API call.

## Jupyter Hub Integration

## Canvas LTI Integration

## API Useage

### Headers & Post Variables

Header: X-Api-Key

This is a security header that allows users to interact with the API. Generally speaking this should be 16 to 32 characters long.

Post Variable: STUDENT_ID 

This POST variable is used to target a specfic student via many of the API Routes. This refers to the Canvas Student ID.

Post Variable: SNAPSHOT_NAME

This POST variable is represents a name of a student's home directories file system snapshot, it is used by many API routes when creating or accessing snapshots. 

Post Varible: SNAPSHOT_FILENAME

Post Variable: UPLOAD_FILE

This Post Variable holds a file being uploaded to the API. To pass files in


### API Routes


### API Curl Examples
You must update the URI for the API call to the one provided by the Team responsible for managing the application.

Each API call also requires the API Key (), which will also be provided on an as needed bases by the Team responsible for managing the application.

#### Get Snapshot List

Required Headers: **X-Api-Key** [The API Key is Provided by UBC IT]

Required Post Variables: **STUDENT_ID** [The Student's Canvas ID]

*In the following example(s) we will use an X-Api-Key of '12345', a Canvas Student ID of '31387714', and a URL of https://localhost:5000*

1. curl -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714" https://localhost:5000/get_snapshot_list
2. curl -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" https://localhost:5000/get_snapshot_list
3. curl -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" https://localhost:5000/get_snapshot_list

#### Get Snapshot File List

Required Headers: **X-Api-Key** [The API Key is Provided by UBC IT]

Required Post Variables: **STUDENT_ID** [The Student's Canvas ID]
                         **SNAPSHOT_NAME** [The Name of the Snapshot]

*In the following example(s) we will use an X-Api-Key of '12345', a Canvas Student ID of '31387714', a Snapshot Name of 'Assignment-1-Snap_12-08-2021' and a URL of https://localhost:5000*

1. curl -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_NAME=Assignment-1-Snap_12-08-2021" http://localhost:5000/get_snapshot_file_list
2. curl -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=Assignment-1-Snap_12-08-2021" http://localhost:5000/get_snapshot_file_list
3. curl -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=Assignment-1-Snap_12-08-2021" http://localhost:5000/get_snapshot_file_list

#### Get Snapshot Zip File

curl -OJ -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_NAME=12-08-2021" http://localhost:5000/get_snapshot_zip
curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=12-08-2021" http://localhost:5000/get_snapshot_zip
curl -OJ -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=12-08-2021" http://localhost:5000/get_snapshot_zip

#### Get Snapshot File

curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=12-08-2021" -d "SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
curl -OJ -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=12-08-2021" -F "SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714&SNAPSHOT_NAME=12-08-2021&SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file
curl -OJ -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_NAME=12-08-2021&SNAPSHOT_FILENAME=subdir_test/subdir_file1.txt" http://localhost:5000/get_snapshot_file

#### Upload File To Student Home Directory

curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F UPLOAD_FILE=@upload_test.txt http://localhost:5000/put_student_report

#### Create Snapshot for Student

curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=Assignment-1-snap" http://localhost:5000/snapshot

#### Create Snapshot for All Students

curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_NAME=assignment-1-snap-all" http://localhost:5000/snapshot_all
curl -X POST -H "X-Api-Key: 12345" -d "STUDENT_NAME=assignment-1-snap-all" http://localhost:5000/snapshot_all
curl -X POST -H "X-Api-Key: 12345" -data "STUDENT_NAME=assignment-1-snap-all" http://localhost:5000/snapshot_all

## Repo Files

## Enviroment Variables

DEBUG (TRUE:BOOL)
JUPYTER_API_PORT (5000:INT)
JUPYTER_API_HOST (0.0.0.0:STRING)
JUPYTER_API_KEY (12345:STRING)
JNOTE_HOME (/mnt/efs/stat-100a-home/:STRING)
JNOTE_SNAP (/mnt/efs/stat-100a-snap/:STRING)
JNOTE_INTSNAP (/mnt/efs/stat-100a-internal/:STRING)
JNOTE_COURSE_CODE (STAT100a:STRING)

## Docker Deployments

## Virtual Machine Deployments

## Kubernetes Pod Deployments

## Support

As this is a Proof of Concept project no support is going to be provided unless you are an Instructor or UBC Staff member participating in the trial.

That being said, feel free to contact Rahim Khoja <rahim.khoja@ubc.ca> in the offchance he feels like providing additional support.  
