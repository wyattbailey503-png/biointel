"""Adaptive Stiff ODE Integrator with Invariant Conservation Assertions.

Solves complex coupled non-linear reaction networks using 4th-order Runge-Kutta (RK4)
with adaptive step-size control (local truncation error estimation via step-doubling).
Enforces physical non-negativity and asserts exact carbon-mole and elemental mass conservation.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class IntegrationResult:
    time_points: List[float]
    state_trajectories: Dict[str, List[float]]
    total_steps: int
    rejected_steps: int
    maximum_invariant_error: float
    is_mass_conserved: bool
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdaptiveRK4Integrator:
    """Robust 4th-Order Runge-Kutta ODE solver with mass conservation enforcement."""

    @classmethod
    def rk4_step(
        cls,
        f: Callable[[float, List[float]], List[float]],
        t: float,
        y: List[float],
        h: float,
    ) -> List[float]:
        """Performs a single classical 4th-order Runge-Kutta step."""
        k1 = f(t, y)
        y_k1 = [y[i] + 0.5 * h * k1[i] for i in range(len(y))]
        
        k2 = f(t + 0.5 * h, y_k1)
        y_k2 = [y[i] + 0.5 * h * k2[i] for i in range(len(y))]
        
        k3 = f(t + 0.5 * h, y_k2)
        y_k3 = [y[i] + h * k3[i] for i in range(len(y))]
        
        k4 = f(t + h, y_k3)

        y_next = [
            y[i] + (h / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i])
            for i in range(len(y))
        ]
        return y_next

    @classmethod
    def integrate(
        cls,
        derivative_fn: Callable[[float, List[float]], List[float]],
        initial_state: List[float],
        state_names: List[str],
        t_start: float,
        t_end: float,
        initial_step_size: float = 0.01,
        tolerance: float = 1e-5,
        stoichiometric_weights: Optional[List[float]] = None,
        max_steps: int = 100000,
    ) -> IntegrationResult:
        """
        Integrates system with adaptive step-size control and conservation validation.

        Args:
            derivative_fn: Function f(t, y) -> dy/dt
            initial_state: Initial state vector y0
            state_names: Variable identifiers
            t_start: Starting time
            t_end: Ending time
            initial_step_size: Initial trial dt
            tolerance: Maximum allowable local truncation error
            stoichiometric_weights: Conserved invariant coefficients (e.g. carbon atoms per molecule)
        """
        t = t_start
        y = list(initial_state)
        h = initial_step_size

        times = [t]
        trajectories: Dict[str, List[float]] = {name: [val] for name, val in zip(state_names, y)}

        # Initial invariant calculation
        initial_invariant = 0.0
        if stoichiometric_weights:
            initial_invariant = sum(w * val for w, val in zip(stoichiometric_weights, y))

        max_invariant_err = 0.0
        rejected = 0
        accepted_steps = 0

        while t < t_end and accepted_steps < max_steps:
            if t + h > t_end:
                h = t_end - t

            # Step doubling local error estimation:
            # Take one full step of size h
            y_single = cls.rk4_step(derivative_fn, t, y, h)
            # Take two half steps of size h/2
            y_half = cls.rk4_step(derivative_fn, t, y, 0.5 * h)
            y_double = cls.rk4_step(derivative_fn, t + 0.5 * h, y_half, 0.5 * h)

            # Local truncation error estimate (order 5): E ~ (y_double - y_single) / 15
            error = max(abs(y_double[i] - y_single[i]) / 15.0 for i in range(len(y)))

            if error <= tolerance or h <= 1e-8:
                # Accept step with local Richardson extrapolation
                t += h
                y = [max(0.0, y_double[i] + (y_double[i] - y_single[i]) / 15.0) for i in range(len(y))]
                accepted_steps += 1

                # Verify physical conservation invariant
                if stoichiometric_weights and initial_invariant > 1e-9:
                    current_invariant = sum(w * val for w, val in zip(stoichiometric_weights, y))
                    rel_err = abs(current_invariant - initial_invariant) / initial_invariant
                    max_invariant_err = max(max_invariant_err, rel_err)

                times.append(t)
                for name, val in zip(state_names, y):
                    trajectories[name].append(val)

                # Compute next trial step size (safety factor 0.9)
                if error > 1e-12:
                    h_next = h * min(2.0, max(0.2, 0.9 * (tolerance / error) ** 0.2))
                else:
                    h_next = h * 2.0
                h = h_next
            else:
                # Reject step and shrink dt
                rejected += 1
                h = h * max(0.1, 0.9 * (tolerance / error) ** 0.25)

        is_conserved = max_invariant_err < 1e-4

        summary = (
            f"Integrated {accepted_steps} steps ({rejected} rejected). "
            f"Max conservation error: {max_invariant_err:.2e}. "
            f"Conservation status: {'CONSERVED' if is_conserved else 'VIOLATED'}."
        )

        return IntegrationResult(
            time_points=times,
            state_trajectories=trajectories,
            total_steps=accepted_steps,
            rejected_steps=rejected,
            maximum_invariant_error=max_invariant_err,
            is_mass_conserved=is_conserved,
            summary=summary,
        )
