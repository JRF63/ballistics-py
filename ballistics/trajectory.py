from .environment import *
from .integration import *

import numpy as np
from scipy.interpolate import make_interp_spline
from scipy.integrate import solve_ivp

MAX_SIMULATION_TIME = 20.0
ACCEL_GRAVITY = np.array([0.0, 0.0, -32.17405])

CUSTOM_ODE_SOLVERS = {
    'EulerMethod': EulerMethod,
    'TwoStepAdamsBashforth': TwoStepAdamsBashforth,
    'HeunsMethod': HeunsMethod,
    'BeemansAlgorithm': BeemansAlgorithm,
    'RungeKuttaMethod': RungeKuttaMethod
}


def parse_drag_table(filename: str):
    table = []
    with open(filename) as f:
        for line in f:
            table.append(tuple(map(float, line.strip().split())))
    return table


class PointMassTrajectory:

    def __init__(self, table: list[(float, float)]) -> None:
        self.cd_func = make_interp_spline(*zip(*table), k=3)

    def calculate_acceleration(
        self,
        v: np.ndarray,
        v_sound: float,
        bc: float,
        density_air: float,
        wind: np.ndarray
    ) -> np.ndarray:

        # 8 * 144, the 144 comes from converting in2 to ft2
        k = 1152.0

        vw = v - wind
        speed = np.linalg.norm(vw)
        m = speed / v_sound
        cd_star = density_air * np.pi * self.cd_func(m) / (k * bc)
        decel = -cd_star * speed * vw + ACCEL_GRAVITY
        return decel

    def solve_for_initial_velocity(
        self,
        x0: np.ndarray,
        muzzle_speed: float,
        bc: float,
        zero_range: float,
        zero_elevation: float,
        wind: np.ndarray = np.zeros(3),
        temp: float = 59.0,
        pressure: float = 29.92,
        rh: float = 0.0,
        method: str = 'RK45'
    ) -> (float, float):

        MAX_CONVERGENCE_STEPS = 100
        CONVERGENCE_EPSILON = 1e-5

        def range_reached(t: float, y: np.ndarray):
            return y[0] - zero_range

        range_reached.terminal = True

        # Initial guess of vertical angle
        ver_angle = np.arctan(zero_elevation / zero_range)
        ver_angle_low = ver_angle - np.radians(60)
        ver_angle_high = ver_angle + np.radians(60)

        hor_angle = 0.0
        hor_angle_left = -np.radians(60)
        hor_angle_right = np.radians(60)

        ver_angle_old = float('NaN')
        hor_angle_old = float('NaN')

        # Solve for vertical angle
        converged = [False, False]
        for _ in range(MAX_CONVERGENCE_STEPS):
            if all(converged):
                break

            ver_angle = (ver_angle_low + ver_angle_high) / 2.0
            hor_angle = (hor_angle_left + hor_angle_right) / 2.0

            if ver_angle == ver_angle_old and hor_angle == hor_angle_old:
                break

            ver_angle_old = ver_angle
            hor_angle_old = hor_angle

            v_guess = muzzle_speed * np.array([
                np.cos(ver_angle) * np.cos(hor_angle),
                np.sin(hor_angle),
                np.sin(ver_angle) * np.cos(hor_angle)
            ])

            result = self.calculate_trajectory(
                x0,
                v_guess,
                bc,
                wind,
                temp,
                pressure,
                rh,
                method,
                events=range_reached
            )

            if not result.y_events:
                raise Exception('Unable to solve for firing angle')

            drop = result.y_events[0][0, 2]

            # Second zero should be attained at the specified distance
            if abs(drop - zero_elevation) < CONVERGENCE_EPSILON:
                converged[0] = True
            else:
                # Lost convergence, retry again with larger bounds
                if converged[0]:
                    converged[0] = False
                    ver_angle_high += ver_angle_high - ver_angle
                    ver_angle_low += ver_angle_low - ver_angle

                if drop > zero_elevation:
                    # Aiming too high
                    ver_angle_high = ver_angle
                else:
                    # Aiming too low
                    ver_angle_low = ver_angle

            deflection = result.y_events[0][0, 1]

            if abs(deflection) < CONVERGENCE_EPSILON:
                converged[1] = True
            else:
                if converged[1]:
                    converged[1] = False
                    hor_angle_right += hor_angle_right - hor_angle
                    hor_angle_left += hor_angle_left - hor_angle

                if deflection > 0.0:
                    # Aiming too far to the right
                    hor_angle_right = hor_angle
                else:
                    # Aiming too far to the left
                    hor_angle_left = hor_angle
        else:
            raise Exception('Solution for firing angle failed to converge')

        return ver_angle, hor_angle

    def calculate_trajectory(
        self,
        x0: np.ndarray,
        v0: np.ndarray,
        bc: float,
        wind: np.ndarray = np.zeros(3),
        temp: float = 59.0,
        pressure: float = 29.92,
        rh: float = 0.0,
        method: str = 'RK45',
        t_eval=None,
        events=None,
        ranges=None,
    ):
        method = CUSTOM_ODE_SOLVERS.get(method, method)

        density_air = air_density(temp, pressure, rh, 0.0)
        v_sound = speed_sound(temp, rh, 0.0)

        y0 = np.concatenate((x0, v0))

        def fun(t: float, y: np.ndarray):
            pos_derivative = y[3:]
            vel_derivative = self.calculate_acceleration(
                y[3:], v_sound, bc, density_air, wind)
            return np.concatenate((pos_derivative, vel_derivative))
        
        if ranges is not None:
            if events is None:
                events = [lambda t, y, r=r: y[0] - r for r in ranges]
                # Stop on the last range
                events[-1].terminal = True

        result = solve_ivp(
            fun,
            (0.0, MAX_SIMULATION_TIME),
            y0,
            method=method,
            t_eval=t_eval,
            events=events
        )

        return result
