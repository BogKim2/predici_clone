Outputs와 Reports
==================

Generic Outputs
---------------

``OutputConfig.enabled_generic_outputs`` 로 계산할 scalar output을 선택한다.

지원되는 대표 output:

* ``Mn``
* ``Mw``
* ``PDI``
* ``M0``, ``M1``, ``M2``, ``M3``
* ``Mz``
* ``AMW``
* ``mass``
* ``conversion``
* ``temperature``
* ``pressure``
* ``heat_duty``
* ``MFI``

.. code-block:: python

   from predici_clone.api import OutputConfig, Project
   from predici_clone.engine import SimulationEngine
   from predici_clone.postprocess.generic_outputs import compute_generic_outputs

   project = Project(outputs=OutputConfig(enabled_generic_outputs=("Mn", "Mw", "PDI", "MFI")))
   result = SimulationEngine(project).run()
   outputs = compute_generic_outputs(result, project.outputs)

MWD/GPC
-------

GPC profile 변환은 chain length distribution을 molecular weight axis로 변환하고, 선택적으로
Gaussian convolution을 적용한다.

.. code-block:: python

   from predici_clone.postprocess.gpc import distribution_to_gpc_profile

   profile = distribution_to_gpc_profile(
       result.final_distribution,
       first_length=result.first_length,
       monomer_mw=100.0,
       mode="weight",
       log_axis=True,
       convolution_sigma=1.5,
   )

Report Export
-------------

.. code-block:: python

   from predici_clone.postprocess.moments_report import write_distribution_report

   write_distribution_report("distribution.csv", result.final_distribution)

GUI에서는 MWD chart를 PNG/PDF로 export할 수 있다.
