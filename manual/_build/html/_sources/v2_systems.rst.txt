Version 2 Systems
=================

Reaction Steps and Chemistry
----------------------------

The reaction PatternFinder contains 95 declarative step families spanning polymer reactions,
general kinetics, phase operations, transport, and population-balance PDE operators. Controlled
radical, step-growth, crosslinking, functional-group, penultimate, and N-monomer helpers are in
``predici_clone.kinetics``.

Monte Carlo
-----------

``predici_clone.montecarlo`` provides chain ensembles, seeded Gillespie events, MC indices,
Galerkin-field interpolation, tau-leaping, topology and gyration analysis, sequence-length
analysis, backward coupling, and ensemble persistence.

PSD, Emulsion, and Multiphase Models
------------------------------------

``predici_clone.psd`` implements finite-volume profiles and conservative growth, nucleation,
breakage, agglomeration, and MSMPR operations. ``predici_clone.emulsion`` provides Smith-Ewart
radical populations, compartment factors, rho-c state, entry/exit, and three-phase partitioning.
Multiphase inventories and equilibrium, kinetic transfer, and precipitation steps are available
under ``predici_clone.reactor`` and ``predici_clone.kinetics.phase_steps``.

Thermodynamics and Data
-----------------------

``predici_clone.thermo`` contains Peng-Robinson fugacity, density, PT flash, and XML property
package configuration. XML parameter databases, parameter/module sets, fitting diagnostics,
replay, initial-data reuse, optimal control, variation, PID, and interoperability modules support
the corresponding Advanced workspace tabs.
