# buggy-race-server

This is the central repo in the _Buggy Racing_ project.

> **WORK-IN-PROGRESS** _May 2023_  
> We're currently running the Buggy Racing project (for the fourth year) at
> Royal Holloway, Department of Computer Science  
> **We're aiming for a public release in June!**


## About the project

The project requires students to develop a Python Flask web app that lets them
edit a racing buggy. It produces JSON data describing the buggy which they can
upload to the central race server. Races are run offline and the results posted
on the server; the results are irrelevant to the students' success — they
are being assessed on the quality of the editor they have built.

We provide the skeleton of their editor
([buggy-race-editor](https://github.com/buggyrace/buggy-race-editor))
and a **set of tasks** for them to complete. How thoroughly they complete
the tasks is up to them, but the tasks are grouped in phases, and they _must_
complete the phases in the given order. The final task (phase 6) is completely
wild-carded (_do anything_), but in fact most of the tasks allow considerable
variation in how thoroughly they are implemented. This approach accommodates
students who are relatively new to programming as well as those who are
already confident programmers.

> If you're running a Buggy Race project, you will need to fork and customise
> the editor repo before sharing it with your students. 

### Structure of the project software

There are three repos:

* [buggy-race-server](https://github.com/buggyrace/buggy-race-server)
  (this repo)  
  Contains a Flask web app that accepts students' racing buggy specifications
  as JSON data, manages login/setup, and provides information both on the
  server itself (racing specs) and supporting information/explanations (the
  "tech notes").

* [buggy-race-editor](https://github.com/buggyrace/buggy-race-editor)  
  Contains the skeleton Flask web app that runs the Racing Buggy editor that
  every student is given, and which they must develop according to the tasks.

* [buggy-race-about](https://github.com/buggyrace/buggy-race-about)  
  Contains full documentation both for the server software and how to run the
  project (currently in draft, so this is not available yet)

## History

We first ran this project for the CS1999 (CompSci Foundation year at RHUL)
in term 3, 2020. Now we're working on making it configurable and customisable
for other institutions to use.

