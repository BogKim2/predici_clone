from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PIDController:
    kp: float
    ki: float = 0.0
    kd: float = 0.0
    setpoint: float = 0.0
    output_limits: tuple[float | None, float | None] = (None, None)
    integral: float = 0.0
    previous_error: float | None = None

    def update(self, measured: float, dt: float) -> float:
        if dt <= 0:
            raise ValueError("PID dt must be positive")
        error = self.setpoint - float(measured)
        derivative = 0.0 if self.previous_error is None else (error - self.previous_error) / dt
        candidate_integral = self.integral + error * dt
        output = self.kp * error + self.ki * candidate_integral + self.kd * derivative
        lower, upper = self.output_limits
        clipped = output
        if lower is not None:
            clipped = max(clipped, lower)
        if upper is not None:
            clipped = min(clipped, upper)
        if clipped == output:
            self.integral = candidate_integral
        self.previous_error = error
        return float(clipped)


def pid_namespace(controllers: dict[str, PIDController], measurements: dict[str, float], dt: float) -> dict[str, object]:
    return {"pid": lambda name: controllers[name].update(measurements[name], dt)}
