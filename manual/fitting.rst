Parameter Estimation
====================

지원 workflow
-------------

1. 실험 CSV 로드
2. observation column과 model output 매핑
3. trimming window 설정
4. parameter bounds 설정
5. global search 또는 local least-squares 실행
6. covariance/correlation/condition diagnostics 확인
7. uncertainty sampling 또는 multi-experiment fitting 실행

Local Fitting 예시
------------------

.. code-block:: python

   from predici_clone.postprocess.parameter_estimation import (
       FittingProblem,
       OutputTarget,
       ParameterSpec,
       fit_generic_parameters,
   )

   problem = FittingProblem(
       project=project,
       parameters=(ParameterSpec(name="GP_kp", initial=0.08, lower=0.001, upper=1.0),),
       targets=(OutputTarget(name="mass", value=1.0, weight=1.0),),
   )
   result = fit_generic_parameters(problem)

Sensitivity
-----------

지원되는 sensitivity/global search 도구:

* finite-difference style sensitivity
* sigma-point sensitivity
* Monte Carlo sensitivity
* grid variation for up to three parameters
* differential evolution
* dual annealing

Shooting Control
----------------

Automation API의 ``activate_detailed_iteration`` 은 target output에 맞게 generic parameter를 조정한다.

.. code-block:: python

   from predici_clone.api import activate_detailed_iteration

   shooting = activate_detailed_iteration(
       project,
       target_output="mass",
       target_value=0.5,
       tune_parameter="GP_kp",
       initial=0.08,
       lower=0.001,
       upper=1.0,
   )
