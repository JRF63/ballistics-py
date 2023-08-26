import math
import matplotlib.pyplot as plt
import numpy as np
from numpy import linalg
from scipy.interpolate import make_interp_spline

G7 = [(0.00, 0.1198),
        (0.05, 0.1197),
        (0.10, 0.1196),
        (0.15, 0.1194),
        (0.20, 0.1193),
        (0.25, 0.1194),
        (0.30, 0.1194),
        (0.35, 0.1194),
        (0.40, 0.1193),
        (0.45, 0.1193),
        (0.50, 0.1194),
        (0.55, 0.1193),
        (0.60, 0.1194),
        (0.65, 0.1197),
        (0.70, 0.1202),
        (0.725, 0.1207),
        (0.75, 0.1215),
        (0.775, 0.1226),
        (0.80, 0.1242),
        (0.825, 0.1266),
        (0.85, 0.1306),
        (0.875, 0.1368),
        (0.90, 0.1464),
        (0.925, 0.1660),
        (0.95, 0.2054),
        (0.975, 0.2993),
        (1.0, 0.3803),
        (1.025, 0.4015),
        (1.05, 0.4043),
        (1.075, 0.4034),
        (1.10, 0.4014),
        (1.125, 0.3987),
        (1.15, 0.3955),
        (1.20, 0.3884),
        (1.25, 0.3810),
        (1.30, 0.3732),
        (1.35, 0.3657),
        (1.40, 0.3580),
        (1.50, 0.3440),
        (1.55, 0.3376),
        (1.60, 0.3315),
        (1.65, 0.3260),
        (1.70, 0.3209),
        (1.75, 0.3160),
        (1.80, 0.3117),
        (1.85, 0.3078),
        (1.90, 0.3042),
        (1.95, 0.3010),
        (2.00, 0.2980),
        (2.05, 0.2951),
        (2.10, 0.2922),
        (2.15, 0.2892),
        (2.20, 0.2864),
        (2.25, 0.2835),
        (2.30, 0.2807),
        (2.35, 0.2779),
        (2.40, 0.2752),
        (2.45, 0.2725),
        (2.50, 0.2697),
        (2.55, 0.2670),
        (2.60, 0.2643),
        (2.65, 0.2615),
        (2.70, 0.2588),
        (2.75, 0.2561),
        (2.80, 0.2533),
        (2.85, 0.2506),
        (2.90, 0.2479),
        (2.95, 0.2451),
        (3.00, 0.2424),
        (3.10, 0.2368),
        (3.20, 0.2313),
        (3.30, 0.2258),
        (3.40, 0.2205),
        (3.50, 0.2154),
        (3.60, 0.2106),
        (3.70, 0.2060),
        (3.80, 0.2017),
        (3.90, 0.1975),
        (4.00, 0.1935),
        (4.20, 0.1861),
        (4.40, 0.1793),
        (4.60, 0.1730),
        (4.80, 0.1672),
        (5.00, 0.1618)]

def cd(a, b, c, m):
    smooth = 0.5 + 0.5 * np.tanh(c * (m - 1))
    # return a * (1 - smooth) + b / m**0.5 * smooth
    t1 = a
    # t2 = b / m**0.5
    b1 = 0
    b2 = -0.04
    t2 = b / (m + b1) ** 0.5 + b2
    return t1 * (1 - smooth) + t2 * smooth

def siacci(v):
    return 1/v**2 * 0.896 * (
            0.284746 * v
            - 224.221
            + ((0.234396 * v -  223.754)**2 + 209.043)**0.5
            + (0.019161 * v * (v - 984.261))/(371 + (v/656.174)**10) )

def siacci2(v):
    s = 1e-10
    if v > 2600:
        a = 7.6090480
        p = 1.55
    elif v > 1800:
        a = 7.0961978
        p = 1.7
    elif v > 1370:
        a = 6.1192596
        p = 2
    elif v > 1230:
        a = 2.9809023
        p = 3
    elif v > 970:
        a = 6.8018712
        p = 5
        s = 1e-20
    elif v > 790:
        a = 2.7734430
        p = 3
    else:
        a = 5.6698914
        p = 2
    return (a * s) * v**p

def siacci1(vp):
    if (vp > 4200):
        a = 1.29081656775919e-09
        p = 3.24121295355962
    elif (vp > 3000):
        a = 0.0171422231434847
        p = 1.27907168025204
    elif (vp > 1470):
        a = 2.33355948302505e-03
        p = 1.52693913274526
    elif (vp > 1260):
        a = 7.97592111627665e-04
        p = 1.67688974440324
    elif (vp > 1110):
        a = 5.71086414289273e-12
        p = 4.3212826264889
    elif (vp > 960):
        a = 3.02865108244904e-17 
        p = 5.99074203776707
    elif (vp > 670):
        a = 7.52285155782535e-06
        p = 2.1738019851075
    elif (vp > 540):
        a = 1.31766281225189e-05
        p = 2.08774690257991
    else:
        a = 1.34504843776525e-05
        p = 2.08702306738884
    return a * vp**p

def numerical_solve(v0, bc, dist, cd_func):
    dt = 1 / 60

    temp = 59
    pressure = 29.92
    rh = 50
    wv_pressure = 0.50

    v_sound = 49.0223*(temp + 459.67)**0.5
    v_sound *= 1 + 0.0014 * rh * wv_pressure / 29.92

    density_air_std = 0.0764742
    density_air = (pressure / 29.92) * (518.67 / (temp + 459.67)) * density_air_std
    density_air *= 1 - 0.00378 * rh * wv_pressure / 29.92
    
    def cd_star(speed):
        m = speed / v_sound
        result = density_air * math.pi * cd_func(m) / (1152.0 * bc)
        # print('>', m, density_air, cd_func(m), result)
        return result

    x = np.array([0.0, 0.0, 0.0])
    g = np.array([0.0, 0.0, -32.17405])
    v = v0
    t = 0.0
    while x[0] < 3 * dist:
        speed = linalg.norm(v)

        # Runge-Kutta 4th order
        # k1 = -cd_star(speed) * speed * v + g
        # y = v + k1/2 * dt
        # speed = linalg.norm(y)
        # k2 = -cd_star(speed) * speed * y + g
        # y = v + k2/2 * dt
        # speed = linalg.norm(y)
        # k3 = -cd_star(speed) * speed * y + g
        # y = v + k3 * dt
        # speed = linalg.norm(y)
        # k4 = -cd_star(speed) * speed * y + g
        # v += (k1 + 2*k2 + 2*k3 + k4) * dt / 6

        dv = (-cd_star(speed) * speed * v + g) 
        v += dv * dt

        x += v * dt
        t += dt

    return x, v

def main():
    # m = np.linspace(0.01, 5, 100)
    # a = 0.1198
    # b = 0.49
    # c = 20
    # y = cd(a, b, c, m)

    b_spline = make_interp_spline(*zip(*G7), k=3)

    v0 = np.array([2970, 0.0, 0.0])
    bc = 0.371
    mass = 62
    dist = 2000 # feet

    x, v = numerical_solve(v0, bc, dist, b_spline)
    print(12 * x[2], linalg.norm(v))

    # shooterscalculator
    # -1643.64 in, 1057 ft/s
    # Hornady
    # -1670.2 in, 1049 ft/s

main()
