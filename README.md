# Instructor API for the JupyterHub and Canvas Cluster POC

## Description

An API to interact with the POC JupyterHub Cluster and Canvas for Instructors. 

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


## Repo Files

## Enviroment Variables

## Docker Deployments

## Virtual Machine Deployments

## Kubernetes Pod Deployments

## Support

As this is a Proof of Concept project no support is going to be provided unless you are an Instructor or UBC Staff member participating in the Cluster trial.

That being said, feel free to contact Rahim Khoja <rahim.khoja@ubc.ca> in the offchance he feels like providing additional support.  
