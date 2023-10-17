# Instructor API for the JupyterHub and Canvas Cluster POC

## Description

An API to interact with the file system hosting the JupyterHub home directories. It allows Instructors to Snapshot their Students Home Drives for deadlines via an API call. These Snapshots can be triggered via an API call initiated from a Canvas Assignment deadline. Instructors can create multiple Snapshots with custom names for each student or sets of students. Instructors can retrieve the Snapshots via a ZIP file of the whole Snapshot or by specifying specific files within the Snapshot. Instructors can also Put grading reports into the Students Home Directory by an API call.


### Headers & Post Variables

<div>
  <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Type</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
    <tr>
        <td><strong>X-Api-Key</strong></td>
        <td>Request Header</td>
        <td>This is a security header that allows users to interact with the API. Generally speaking this should be 16 to 32 characters long.</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>STUDENT_ID</strong></td>
        <td>Post Request Variable</td>
        <td>This POST variable value represents a Student Canvas ID.</td>
    </tr>
    <tr>
        <td><strong>SNAPSHOT_NAME</strong></td>
        <td>Post Request Variable</td>
        <td>This POST variable value represents a name of a Snapshot</td>
    </tr>
    <tr>
        <td><strong>SNAPSHOT_FILENAME</strong></td>
        <td>Post Request Variable</td>
        <td>This POST variable value represents the name of a file within a Snapshot.</td>
    </tr>
    <tr>
        <td><strong>UPLOAD_FILE</strong></td>
        <td>Binary Post Request Variable</td>
        <td>This Binary POST variable value contains the file being uploaded to the API.</td>
    </tr>
    <tr>
        <td><strong>Content-Disposition</strong></td>
        <td>Response Header Variable & Data</td>
        <td>This Header response variable value contains the filename of file binary data being sent by the API. The request data contains the associated file binary data as an attachment.</td>
    </tr>
</table>

## API Examples

### Get Snapshot List

Retrieve a list of Snapshots for a specified Canvas student.

##### API URI: https://{HOST}:{PORT}/get_snapshot_list

##### API Return HTTP Codes:
- *200* for Success with a POST Response,
- *404* Failure Not Found with a POST Response.


#### Required Headers & Post Variables:

<table>
    <tr>
        <td><strong>X-Api-Key</strong></td>
        <td>Header Variable</td>
        <td>The API Key is Provided by UBC IT</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>STUDENT_ID</strong></td>
        <td>Post Variable</td>
        <td>The Student's Canvas ID</td>
    </tr>
</table>

#### Curl Command Call Examples:

*In the following example(s) we will use HEADER variable __X-Api-Key__ with a value of '12345', and a __Student_ID__ POST variable with a value of '31387714', and a URL of __https://api.example.com:5000/get_snapshot_list__*

1. curl -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714" https://api.example.com:5000/get_snapshot_list
2. curl -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" https://api.example.com:5000/get_snapshot_list
3. curl -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" https://api.example.com:5000/get_snapshot_list


```
user@host:~$  curl -H "X-Api-Key: 1234567" -d "STUDENT_ID=31387714" https://api.example.com:5000/get_snapshot_list
["assignment-3_2021-09-09","assignment-2_2021-09-09","assignment-1_2021-09-09","flocking-test-call_2021-09-09","exam_work_2021-09-10"]
user@host:~$
```

#

### Get Snapshot File List


Retrieve a list of files within the specified Canvas students' Snapshot.

##### API URI: https://{HOST}:{PORT}/get_snapshot_file_list

##### API Return HTTP Codes:
- *200* Success with a POST Response
- *406* Failure Missing Data, with a POST Response.
- *404* Failure Not Found with a POST Response.

#### Required Headers & Post Variables:

<table>
    <tr>
        <td><strong>X-Api-Key</strong></td>
        <td>Header Variable</td>
        <td>The API Key is Provided by UBC IT</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>STUDENT_ID</strong></td>
        <td>Post Variable</td>
        <td>The Student's Canvas ID</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>SNAPSHOT_NAME</strong></td>
        <td>Post Variable</td>
        <td>The Name of the Snapshot</td>
    </tr>
</table>

#### Curl Command Call Examples:

*In the following example(s) we will use HEADER variable __X-Api-Key__ with a value of '12345', and a __Student_ID__ POST variable with a value of '31387714', a __SNAPSHOT_NAME__ POST variable with a value of 'assignment-1_2021-09-09', and a URL of __https://api.example.com:5000/get_snapshot_file_list__*


1. curl -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_NAME=assignment-1_2021-09-09" https://api.example.com:5000/get_snapshot_file_list
2. curl -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=assignment-1_2021-09-09" https://api.example.com:5000/get_snapshot_file_list
3. curl -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=assignment-1_2021-09-09" https://api.example.com:5000/get_snapshot_file_list


```
user@host:~$  curl -H "X-Api-Key: 1234567" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=assignment-1_2021-09-09" https://api.example.com:5000/get_snapshot_file_list
["assignment-1.ipynb","assignment-2.ipynb","exercise-1.ipynb","practice/practice-1.ipynb","practice/practice-2.ipynb","assignment-1-grades.html"]
user@host:~$
```

#

### Get Snapshot Zip File

Retrieves a zip file of a students snapshot with the specified STUDENT_ID and SNAPSHOT_NAME Post headers.

##### API URI: https://{HOST}:{PORT}/get_snapshot_zip

##### API Return HTTP Codes:
- *200* Success with a POST Response
- *406* Failure Missing Data, with a POST Response.
- *404* Failure Not Found with a POST Response.

#### Required Headers & Post Variables:

<table>
    <tr>
        <td><strong>X-Api-Key</strong></td>
        <td>Header Variable</td>
        <td>The API Key is Provided by UBC IT</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>STUDENT_ID</strong></td>
        <td>Post Variable</td>
        <td>The Student's Canvas ID</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>SNAPSHOT_NAME</strong></td>
        <td>Post Variable</td>
        <td>The Name of the Snapshot</td>
    </tr>
</table>


#### Curl Command Call Examples:

*In the following example(s) we will use HEADER variable __X-Api-Key__ with a value of '12345', and a __Student_ID__ POST variable with a value of '31387714', a __SNAPSHOT_NAME__ POST variable with a value of 'assignment-1_2021-09-09', and a URL of __https://api.example.com:5000/get_snapshot_zip__*

1. curl -OJ -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_NAME=assignment-1_2021-09-09" https://api.example.com:5000/get_snapshot_zip
2. curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=assignment-1_2021-09-09" https://api.example.com:5000/get_snapshot_zip
3. curl -OJ -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=assignment-1_2021-09-09" https://api.example.com:5000/get_snapshot_zip


```
user@host:~$  curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=assignment-1_2021-09-09" https://api.example.com:5000/get_snapshot_zip
curl: Saved to filename '31387714_assignment-1_2021-09-09.zip'
user@host:~$
```


#

### Get Snapshot File

Retrieves a Snapshot file of from a students snapshot with the specified STUDENT_ID SNAPSHOT_NAME, & SNAPSHOT_FILENAME Post headers.

##### API URI: https://{HOST}:{PORT}/get_snapshot_file

##### API Return HTTP Codes:
- *200* Success with a POST Response
- *406* Failure Missing Data, with a POST Response.
- *404* Failure Not Found with a POST Response.


#### Required Headers & Post Variables:

<table>
    <tr>
        <td><strong>X-Api-Key</strong></td>
        <td>Header Variable</td>
        <td>The API Key is Provided by UBC IT</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>STUDENT_ID</strong></td>
        <td>Post Variable</td>
        <td>The Student's Canvas ID</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>SNAPSHOT_NAME</strong></td>
        <td>Post Variable</td>
        <td>The Name of the Snapshot</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>SNAPSHOT_FILENAME</strong></td>
        <td>Post Variable</td>
        <td>The Name and Location of the Snapshot file being downloaded</td>
    </tr>
</table>

#### Curl Command Call Examples:

*In the following example(s) we will use HEADER variable __X-Api-Key__ with a value of '12345', and a __Student_ID__ POST variable with a value of '31387714', a __SNAPSHOT_NAME__ POST variable with a value of 'assignment-1_2021-09-09', a __SNAPSHOT_FILENAME__ Post variable with a value of 'practice/practice-1.ipynb', and a URL of __https://api.example.com:5000/get_snapshot_file__*

1. curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=12-08-2021" -d "SNAPSHOT_FILENAME=practice/practice-1.ipynb" https://api.example.com:5000/get_snapshot_file
2. curl -OJ -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=12-08-2021" -F "SNAPSHOT_FILENAME=practice/practice-1.ipynb" https://api.example.com:5000/get_snapshot_file
3. curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714&SNAPSHOT_NAME=12-08-2021&SNAPSHOT_FILENAME=practice/practice-1.ipynb" https://api.example.com:5000/get_snapshot_file
4. curl -OJ -H "X-Api-Key: 12345" --data "STUDENT_ID=31387714&SNAPSHOT_NAME=12-08-2021&SNAPSHOT_FILENAME=practice/practice-1.ipynb" https://api.example.com:5000/get_snapshot_file


```
user@host:~$  curl -OJ -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=12-08-2021" -d "SNAPSHOT_FILENAME=practice/practice-1.ipynb" https://api.example.com:5000/get_snapshot_file
curl: Saved to filename 'practice-1.ipynb'
user@host:~$
```


#

### Upload File To Student Home Directory

Upload a file to a students home directory with the specified STUDENT_ID SNAPSHOT_NAME Post Header, & an UPLOAD_FILE Binary Post header of a file. Can only upload files with .txt, .html, and .ipynb file extensions.

##### API URI: https://{HOST}:{PORT}/put_student_report

##### API Return HTTP Codes:
- *200* Success with a POST Response
- *406* Failure Missing Data, with a POST Response.
- *404* Failure Not Found with a POST Response.
- *417* Expectation Failed with a POST Response.


#### Required Headers & Post Variables:

<table>
    <tr>
        <td><strong>X-Api-Key</strong></td>
        <td>Header Variable</td>
        <td>The API Key is Provided by UBC IT</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>STUDENT_ID</strong></td>
        <td>Post Variable</td>
        <td>The Student's Canvas ID</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>UPLOAD_FILE</strong></td>
        <td>Post Variable</td>
        <td>The location and file to be uploaded, preceded by an @ symbol</td>
    </tr>
</table>

#### Curl Command Call Examples:

*In the following example(s) we will use HEADER variable __X-Api-Key__ with a value of '12345', and a __Student_ID__ POST variable with a value of '31387714', a POST variable called __UPLOAD_FILE__ with a binary value of a file '@/some/place/assignment-1-grades.html', and a URL of __https://api.example.com:5000/put_student_report__*

1. curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "UPLOAD_FILE=@assignment-1-grades.html" https://api.example.com:5000/put_student_report
2. curl -X POST -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "UPLOAD_FILE=@assignment-1-grades.html" https://api.example.com:5000/put_student_report
3. curl -X POST -H "X-Api-Key: 12345" -data "STUDENT_ID=31387714&UPLOAD_FILE=@assignment-1-grades.html" https://api.example.com:5000/put_student_report


```
user@host:~$  curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "UPLOAD_FILE=@assignment-1-grades.html" https://api.example.com:5000/put_student_report
Success - File Uploaded - assignment-1-grades.html
user@host:~$
```

#

### Create Snapshot for Student


#### Required Headers & Post Variables:

<table>
    <tr>
        <td><strong>X-Api-Key</strong></td>
        <td>Header Variable</td>
        <td>The API Key is Provided by UBC IT</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>STUDENT_ID</strong></td>
        <td>Post Variable</td>
        <td>The Student's Canvas ID</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>SNAPSHOT_NAME</strong></td>
        <td>Post Variable</td>
        <td>The Name of the Snapshot</td>
    </tr>
</table>

#### Curl Command Call Examples:

*In the following example(s) we will use HEADER variable __X-Api-Key__ with a value of '12345', a __Student_ID__ POST variable with a value of '31387714',  a __SNAPSHOT_NAME__ POST variable with a value of 'Assignment-1', and a URL of __https://api.example.com:5000/snapshot__*

1. curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_ID=31387714" -F "SNAPSHOT_NAME=Assignment-1" https://api.example.com:5000/snapshot
2. curl -X POST -H "X-Api-Key: 12345" -d "STUDENT_ID=31387714" -d "SNAPSHOT_NAME=Assignment-1" https://api.example.com:5000/snapshot
3. curl -X POST -H "X-Api-Key: 12345" -data "STUDENT_ID=31387714&SNAPSHOT_NAME=Assignment-1" https://api.example.com:5000/snapshot

```
user@host:~$  curl -X POST -H "X-Api-Key: 12345" -data "STUDENT_ID=31387714&SNAPSHOT_NAME=Assignment-1" https://api.example.com:5000/snapshot
"Success - Snapshot Created - assignment-1_2021-09-01 for Student: 31387714"
user@host:~$
```

#

### Create Snapshot for All Students

Creates a Snapshot of the all students home directories with a common name, with the SNAPSHOT_NAME Post Value. The current date is added on to the end of the SNAPSHOT_NAME value. Should only be triggered once an hour.

##### API URI: https://{HOST}:{PORT}/snapshot_all

##### API Return HTTP Codes:
- *200* Success with a POST Response
- *406* Failure Missing Data, with a POST Response.
- *404* Failure Not Found with a POST Response.


#### Required Headers & Post Variables:

<table>
    <tr>
        <td><strong>X-Api-Key</strong></td>
        <td>Header Variable</td>
        <td>The API Key is Provided by UBC IT</td>
    </tr>
    <tr></tr>
    <tr>
        <td><strong>SNAPSHOT_NAME</strong></td>
        <td>Post Variable</td>
        <td>The Name of the Snapshot</td>
    </tr>
</table>

#### Curl Command Call Examples:

*In the following example(s) we will use HEADER variable __X-Api-Key__ with a value of '12345', a __SNAPSHOT_NAME__ POST variable with a value of 'assignment-1-all', and a URL of __https://api.example.com:5000/snapshot_all__*

1. curl -X POST -H "X-Api-Key: 12345" -F "STUDENT_NAME=assignment-1-all" https://api.example.com:5000/snapshot_all
2. curl -X POST -H "X-Api-Key: 12345" -d "STUDENT_NAME=assignment-1-all" https://api.example.com:5000/snapshot_all
3. curl -X POST -H "X-Api-Key: 12345" -data "STUDENT_NAME=assignment-1-all" https://api.example.com:5000/snapshot_all

```
user@host:~$  curl -X POST -H "X-Api-Key: 12345" -d "STUDENT_NAME=assignment-1-all" https://api.example.com:5000/snapshot_all
"Success - Snapshot Created - assignment-1-all_2021-09-01 for All Students"
user@host:~$
```


## Environment Variables

<div>
  <table>
    <thead>
      <tr>
        <th>Environment Variable</th>
        <th>Required</th>
        <th>Default Value</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>DEBUG</td>
        <td align="center"></td>
        <td>TRUE</td>
        <td>Enables Debug output within the API code</td>
      </tr>
      <tr>
        <td>JUPYTER_API_PORT</td>
        <td align="center"></td>
        <td>5000</td>
        <td>The Port Number of the API</td>
      </tr>
      <tr>
        <td>JUPYTER_API_HOST</td>
        <td align="center"></td>
        <td>0.0.0.0</td>
        <td>The IP the API is being served on</td>
      </tr>
      <tr>
        <td>JUPYTER_API_KEY</td>
        <td align="center">&check; </td>
        <td>12345</td>
        <td>The API Key</td>
      </tr>
      <tr>
        <td>JNOTE_HOME</td>
        <td align="center">&check; </td>
        <td>{No Default Value}</td>
        <td>The location of Jupyter Notebooks' user Home directory</td>
      </tr>
      <tr>
        <td>JNOTE_SNAP</td>
        <td align="center">&check; </td>
        <td>{No Default Value}</td>
        <td>The location of Jupyter Notebooks final Snapshot directory</td>
      </tr>
      <tr>
        <td>JNOTE_INTSNAP</td>
        <td align="center">&check; </td>
        <td>{No Default Value}</td>
        <td>The location of Jupyter Notebooks internal Snapshot directory</td>
      </tr>
      <tr>
        <td>JNOTE_COURSE_CODE</td>
        <td align="center">&check; </td>
        <td>{No Default Value}</td>
        <td>The Course Code</td>
      </tr>
    </tbody>
  </table>
</div>


## Repo Files

## Jupyter Hub & Canvas LTI

  ### Requirements:
  1. The Jupyter user instances' home directory storage must be accessible to the API System via a mount point. Suggested Types include, NFS, AWS EFS via NFS, CephFS, CIFS, etc.
  2. The Canvas LTI Application needs to be setup in Public Mode in order to share the Canvas Student ID's with the API system.

  ### Canvas LTI Example

  <img src="https://github.com/ubc/jupyter-canvas-api/blob/master/LTI.png?raw=true" width="500"></img>

## Docker Deployments

## Virtual Machine Deployments

*This deployment has been tested on Ubuntu 20.04, however it should work with previous versions of Ubuntu and Debian.*

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

- The API needs to be run as Root, as such the Environment Variables need to be accessible by Root.
- On the Virtual Machine Deployment, the hourly rsync script is controlled by a SystemD Timer, rather than a cronjob. It should be simple to move back if desired.
- On the docker/kubernetes deployment the hourly rsync script is controlled via cron. A script is placed into /etc/cron.hourly, and the /etc/crontab for that directory is triggered on the 17th minute.
- When running the API call /snapshot_all there is a 1-hour cool down. If run sooner, it can take a long time to complete.

## Support

As this is a Proof of Concept project no support is going to be provided unless you are an Instructor or UBC Staff member participating in the trial.
