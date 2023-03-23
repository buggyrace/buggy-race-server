# buggy-race-server

This is the central (staff, private) repo in the "Buggy Racing" project.

**WORK-IN-PROGRESS** _Spring 2023_

## About the project

The project requires students to develop a Python Flask web app that lets them
edit a racing buggy. It produces JSON data
describing the buggy which they can upload to the central race server. Races
happen every night; the results are irrelevant to the student's success — they
are marked on the quality of the editor they have built.

We provide the skeleton of their editor
([buggy-race-editor](https://github.com/buggyrace/buggy-race-editor))
and a **set of tasks** for them to complete. How thoroughly they complete
the tasks is up to them, but the tasks are grouped in phases, and they _must_
complete the phases in the given order. The final task (phase 6) is completely
wild-carded (_do anything_), but most of the tasks are actually open-ended.


### Structure of the project software

There are two code repos:

* [buggy-race-server](https://github.com/buggyrace/buggy-race-server) (this repo)

  Contains a Flask web app that accepts students' racing buggy specifications
  as JSON data, manages login/setup, and publishes information both on the
  server itself (racing specs) and as GitHub pages (the "tech notes").

* [buggy-race-editor](https://github.com/buggyrace/buggy-race-editor)

   Contains the skeleton Flask web app that runs the Racing Buggy editor that
   every student is given, and which they must develop according to the tasks.

## History

This project was first run for the CS1999 (CompSci Foundation year at RHUL)
in term 3, 2020.

