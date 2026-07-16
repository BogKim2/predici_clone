User Guide
==========

This guide provides the shortest end-to-end path from a fresh checkout to a simulation,
a saved project, and a verified installation. The focused chapters linked throughout the
guide contain the complete reference material.

Scope and intended use
----------------------

``predici_clone`` is an open research and validation implementation of PREDICI-style
polymer-reaction workflows. It provides a desktop application and a Python API, but it
does not reproduce proprietary PREDICI algorithms or guarantee compatibility with
commercial PREDICI project files.

The current release is 2.0.0 and requires Python 3.11 or newer. Windows is the primary
supported environment for the GUI and packaged executable.

Install from a checkout
-----------------------

Open PowerShell in the directory where the repository should be stored, then run:

.. code-block:: powershell

   git clone https://github.com/BogKim2/predici_clone.git
   cd predici_clone
   python -m pip install -e .

An editable install makes the ``predici-clone`` and ``predici-manuals`` commands
available while keeping source changes immediately active. If a console command is not
on ``PATH``, use its module form shown below.

Verify the installation without opening the interactive application:

.. code-block:: powershell

   python -m predici_clone.app.main --smoke

See :doc:`installation` for dependency and documentation-build details.

Run a first GUI simulation
--------------------------

Start the desktop application:

.. code-block:: powershell

   predici-clone

Equivalent module command:

.. code-block:: powershell

   python -m predici_clone.app.main

Use this basic workflow:

1. Open the **Simulation** workspace and choose a reactor and integration horizon.
2. Review the reaction model and recipe in **Model Builder** and **Recipe Editor**.
3. Select **Run** on the toolbar.
4. Check scalar values on **Dashboard** and distributions in **MWD Viewer**.
5. Save the project and export the result from the **File** menu or toolbar.

Long simulations run in a worker so the interface remains responsive. Use **Stop** to
request cancellation at the next solver checkpoint. See :doc:`gui` for every workspace,
editor, output view, and fitting control.

Run a first API simulation
--------------------------

The public project schema and simulation engine can be used without the GUI:

.. code-block:: python

   from predici_clone.api import IntegrationControl, Project, ReactorConfig, Recipe
   from predici_clone.engine import SimulationEngine

   project = Project(
       reactor=ReactorConfig(kind="Batch", nmax=80),
       recipe=Recipe(
           integration=IntegrationControl(t_final=10.0, output_points=50)
       ),
   )

   result = SimulationEngine(project).run()
   if not result.success:
       raise RuntimeError(result.message)

   print(result.final_moments.mn)
   print(result.final_moments.mw)
   print(result.final_moments.pdi)

Save and load a project with the public I/O functions:

.. code-block:: python

   from pathlib import Path

   from predici_clone.api import load_project, save_project

   path = Path("project.predici.json")
   save_project(project, path)
   restored = load_project(path)

The :doc:`projects` chapter describes the schema and validation behavior. See :doc:`api`
for the generated API reference and :doc:`outputs` for result inspection and export.

Run included workflows
----------------------

The repository includes complete scripts that can also serve as API templates:

.. code-block:: powershell

   python .\examples\tutorial_polyethylene_basic.py
   python .\examples\tutorial_oregonator.py
   python .\examples\industrial_semibatch_cstr.py
   python .\examples\automation_full_workflow.py

The tutorial scripts exercise a polyethylene workflow and a general-kinetics Oregonator
model. The industrial script compares semi-batch and CSTR conditions. The automation
script demonstrates project creation, simulation, and result export. More guided examples
are in :doc:`tutorials`.

Reproduce manual scenarios
--------------------------

The manual reproduction suite runs numerical scenarios associated with 39 source
documents. It operates headlessly and writes HTML, Markdown, JSON, and CSV reports.

List the registered scenarios and coverage:

.. code-block:: powershell

   python -m test_manuals --list

Run the fast subset or the complete suite:

.. code-block:: powershell

   python -m test_manuals --smoke
   python -m test_manuals --all

Create the complete split report set used by this repository:

.. code-block:: powershell

   python -m test_manuals --all --split --output .\test_manual_result

The command returns 0 when every selected scenario passes, 1 when a scenario fails, and
2 for invalid command-line usage. See :doc:`manual_suite` for filters, expected-range
checks, report layouts, and per-document runners.

Verify changes
--------------

Run the automated tests from the repository root:

.. code-block:: powershell

   python -m pytest -q

Build this manual and fail on any Sphinx warning:

.. code-block:: powershell

   python -m pip install -r manual\requirements.txt
   sphinx-build -b html -W manual manual\_build\html
   Start-Process .\manual\_build\html\index.html

Published v2 verification and benchmark summaries are described in :doc:`validation`.

Build the Windows executable
----------------------------

Install PyInstaller and build from the repository root:

.. code-block:: powershell

   python -m pip install pyinstaller
   pyinstaller --noconfirm --clean packaging\pyinstaller_predici_clone.spec
   .\dist\PrediciClone\PrediciClone.exe --smoke

For the complete packaging verification, run:

.. code-block:: powershell

   .\scripts\packaging_smoke_test_v2.ps1

See :doc:`packaging` for artifact layout and smoke-test behavior.

Troubleshooting
---------------

``No module named predici_clone`` or ``No module named test_manuals``
   Confirm that PowerShell is in the repository root and repeat
   ``python -m pip install -e .`` using the same Python interpreter that runs the command.

``predici-clone`` is not recognized
   The Python scripts directory is not on ``PATH``. Run
   ``python -m predici_clone.app.main`` instead.

The GUI cannot open in a server or CI environment
   Use ``python -m predici_clone.app.main --smoke`` for the offscreen check and run model
   workflows through the Python API or manual reproduction suite.

The manual build reports a missing ``sphinx-build``
   Install ``manual\requirements.txt`` with the active Python interpreter, then retry.

A manual-reproduction filter selects no scenarios
   Run ``python -m test_manuals --list`` and copy the exact feature or milestone value.

Next references
---------------

* :doc:`v2_systems` summarizes the v2 chemistry, Monte Carlo, PSD, emulsion, and
  thermodynamic systems.
* :doc:`fitting` covers experiment import and parameter estimation.
* :doc:`architecture` describes package boundaries and execution flow.
* :doc:`extending` explains how to add models and outputs.
* :doc:`glossary` defines common polymer and solver terms.
