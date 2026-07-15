Manual Reproduction Suite
=========================

The headless manual suite runs without the desktop GUI and writes HTML and Markdown reports.

.. code-block:: powershell

   python -m test_manuals --list
   python -m test_manuals --smoke
   python -m test_manuals --all
   python -m test_manuals --pdf "PrediciPSD_Tutorial_2017"
   python -m test_manuals --feature montecarlo
   python -m test_manuals --milestone M42

The registry covers 39 feature-bearing PDFs. ``ListOfDocuments.pdf`` is an index and the root
``Predici11_Tutorials.pdf`` is a duplicate, so neither creates a separate scenario.
