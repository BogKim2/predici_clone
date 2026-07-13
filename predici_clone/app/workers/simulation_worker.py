from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from predici_clone.api.project_schema import Project
from predici_clone.engine import SimulationCallbacks, SimulationEngine


class SimulationWorker(QObject):
    progress = Signal(float)
    step_done = Signal(object)
    finished = Signal(object)
    error = Signal(str)
    log = Signal(str)

    def __init__(self, project: Project) -> None:
        super().__init__()
        self._project = project
        self._stop_requested = False

    @Slot()
    def run(self) -> None:
        try:
            result = SimulationEngine(self._project).run(
                callbacks=SimulationCallbacks(
                    on_log=self.log.emit,
                    on_progress=self.progress.emit,
                    on_step=self.step_done.emit,
                    should_stop=lambda: self._stop_requested,
                )
            )
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))

    @Slot()
    def request_stop(self) -> None:
        self._stop_requested = True
