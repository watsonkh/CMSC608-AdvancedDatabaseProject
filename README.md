CMSC 608 Project
====================

This repository contains the code for the semester project of CMSC 608, Advanced Databases. The project implements a receipe database system, as presented in the final weeks of classes. It is implemented as a Flask web application, using PostgreSQL with _pgvector_ for vector storage and similarity search.

A full report can be found at [report.pdf](deliverables/report.pdf).

## Execution
While the application can be configured manually from its elements, the ideal user experience is to run it in Docker.

* Download the project with:
  `git clone git@github.com:watsonkh/CMSC608-AdvancedDatabaseProject.git`
* Change directory into the project directory:
  `cd CMSC608-AdvancedDatabaseProject`
* Build and start the Docker container:
  `docker-compose up --build`
* Navigate to the application:
  [http://localhost:5000/](http://localhost:5000/)

The container can be stopped with [Ctrl-C], or from another terminal with the command:

  `docker-compose down`

To close the container and clear the database entirely, use:

  `docker-compose down -v`


