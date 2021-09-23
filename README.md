# Instructor API for the JupyterHub and Canvas Cluster POC

## Description

An API to interact with the file system hosting the JupyterHub home directories. It allows Instructors to Snapshot their Students Home Drives for deadlines via an API call. These Snapshots can be triggered via an API call initiaated from a Canvas Assignment deadline. Instructors can create multiple Snapshots with custom names for each student or sets of students. Instructors can retrieve the Snapshots via a ZIP file of the whole Snapshot or by specifing specfic files within the Snapshot. Instryctors can also Put grading reports into the Students Home Directory by an API call.

## Jupyter Hub Integration

## Canvas LTI Integration

### Headers & Post Variables

Header: *X-Api-Key*

This is a security header that allows users to interact with the API. Generally speaking this should be 16 to 32 characters long.

Post Variable: *STUDENT_ID* 

This POST variable is used to target a specfic student via many of the API Routes. This refers to the Canvas Student ID.

Post Variable: *SNAPSHOT_NAME*

This POST variable is represents a name of a student's home directories file system snapshot, it is used by many API routes when creating or accessing snapshots. 

Post Varible: *SNAPSHOT_FILENAME*

Post Variable: *UPLOAD_FILE*

This Post Variable holds a file being uploaded to the API. To pass files in

### API Curl Usage Examples
You must update the URI for the API call to the one provided by the Team responsible for managing the application.

Each API call also requires the API Key (), which will also be provided on an as needed bases by the Team responsible for managing the application.

#### Get Snapshot List

Required Headers:  
 - **X-Api-Key** [The API Key is Provided by UBC IT]  <BR>
Required Post Variables:  <BR>
 - **STUDENT_ID** [The Student's Canvas ID]   <BR>
 
*In the following example(s) we will use an X-Api-Key of '12345', a Canvas Student ID of '31387714', and a URL of https://localhost:5000*  

1. curl -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714" https://localhost:5000/get_snapshot_list  
2. curl -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" https://localhost:5000/get_snapshot_list  
3. curl -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" https://localhost:5000/get_snapshot_list  

##### Example Response
```
user@host:~$  curl -H "X-Api-Key: 1234567" -d "STUDENT_ID=31387714" https://api.example.com:5000/get_snapshot_list
["assignment-3_2021-09-09","assignment-2-snap_2021-09-09","assignment-1-snap_2021-09-09","flocking-test-snapshot-call_2021-09-09","assignment-6_2021-09-09","assignment-60_2021-09-09","exam_work_2021-09-10"]
user@host:~$
``` 

#### Get Snapshot File List

Required Headers:        
 - **X-Api-Key** [The API Key is Provided by UBC IT]  
Required Post Variables:   
 - **STUDENT_ID** [The Student's Canvas ID]                           
 - **SNAPSHOT_NAME** [The Name of the Snapshot]  

*In the following example(s) we will use an X-Api-Key of '12345', a Canvas Student ID of '31387714', a Snapshot Name of 'Assignment-1-Snap_12-08-2021', and a URL of https://localhost:5000*

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

This deployment has been tested on Ubuntu 20.04, however it should work with previos versions of Ubuntu and Debain.

```
# Prep System
sudo apt update 
sudp apy upgrade
sudo apt install python3 python3-pip curl rsync git

# Get This Repo
cd /tmp
git clone https://github.com/ubc/jupyter-canvas-api.git
cd jupyter-canvas-api
sudo mkdir /usr/share/jupyter-canvas-api/

# Copy Files
sudo cp usr/share/jupyter-canvas-api/api-server.py /usr/share/jupyter-canvas-api/api-server.py
sudo cp usr/share/jupyter-canvas-api/requirements.txt /usr/share/jupyter-canvas-api/requirements.txt
sudo cp usr/local/bin/hourly-rsync.sh /usr/local/bin/hourly-rsync.sh
sudo cp etc/systemd/system/jupyter-canvas-api.service /etc/systemd/system/jupyter-canvas-api.service
sudo cp etc/systemd/system/jupyter-rsync.service /etc/systemd/system/jupyter-rsync.service
sudo cp etc/systemd/system/jupyter-rsync.timer /etc/systemd/system/jupyter-rsync.timer
sudo cp etc/systemd/system/mnt-efs.mount /etc/systemd/system/mnt-efs.mount
sudo chmod +x /usr/local/bin/hourly-rsync.sh

# SystemD
systemctl daemon-reload
systemctl enable jupyter-rsync.timer
systemctl enable jupyter-canvas-api.service
# Update the following mount to fit your needs, or add the Jupyter Lab home directory mount point to /etc/fstab
#systemctl enable mnt-efs.mount

# Setup Python
sudo pip3 install -r /usr/share/jupyter-canvas-api/requirements.txt

# Add Enviroment Variables (Update These To Fit Your Needs)
sudo echo 'JUPYTER_API_PORT="5000"' >> /etc/environment
sudo echo 'JUPYTER_API_HOST="0.0.0.0"' >> /etc/environment
sudo echo 'JUPYTER_API_KEY="12345"' >> /etc/environment      
sudo echo 'JNOTE_HOME="/mnt/efs/stat-100a-home/"' >> /etc/environment
sudo echo 'JNOTE_SNAP="/mnt/efs/stat-100a-snap/"' >> /etc/environment
sudo echo 'JNOTE_INTSNAP="/mnt/efs/stat-100a-internal/"' >> /etc/environment
sudo echo 'JNOTE_COURSE_CODE="STAT100a"' >> /etc/environment

# Reboot
sudo reboot now
```

## Kubernetes Pod Deployments

## Notes

- The API needs to be run as Root, as such the Enviroment Variables need to be accessable by Root.
- On the Virtual Machine Deployment, the hourly rsync script is controlled by a SystemD Timer, rather than a cronjob.
- On the docker/kubernetes deployment the hourly rsync script is controlled via cron. A script is placed into /etc/cron.hourly, and the /etc/crontab for that directory is triggered on the 17th minute. 
- When running the API call /snapshot_all there is a 1 hour cool down. If run sooner, it can take along time to complete.

## Support

As this is a Proof of Concept project no support is going to be provided unless you are an Instructor or UBC Staff member participating in the trial.

That being said, feel free to contact Rahim Khoja <rahim.khoja@ubc.ca> in the offchance he feels like providing additional support.  
