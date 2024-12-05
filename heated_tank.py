import numpy as np
import matplotlib.pyplot as plt

# Parameters
A = 1.0             # Cross-sectional area of the tank (m^2)
rho = 997           # Density of the fluid (kg/m^3)
c_p = 4186          # Specific heat capacity of water (J/(kg·K))
F_in = 0.1          # Inlet flow rate (m^3/s)
F_out = 0.1         # Outlet flow rate (m^3/s)
T_in = 60           # Inlet temperature (°C)
T_out = 20          # Outlet temperature (°C)
t_p = 0.1           # Time step (s)

U_min = 0.0
U_max = 5.0
Q_min = 0
Q_max = 3000  

T_set = 99.5          # Desired temperature setpoint (°C)
K_p = 3200          # Proportional gain (W/°C)
K_i = 7.7           # Integral gain (W/(°C·s))
K_d = 101000         # Derivative gain (W·s/°C)

# Simulation parameters
end_time = 16000       # End time (s)
num_steps = int(end_time / t_p)  # Number of steps
time = np.arange(0, end_time, t_p)  # Time array

# Initialize arrays
T = np.zeros(num_steps)   # Temperature array
h = np.zeros(num_steps)   # Height array
error = np.zeros(num_steps)  # Error array
integral_error = 0         # Initialize integral error
previous_error = 0         # Initialize previous error for derivative calculation

# Initial conditions
T[0] = T_out               # Initial temperature (°C)
h[0] = 1.0                 # Initial height (m)

for n in range(num_steps - 1):
    # uchyb regulacji
    error[n] = T_set - T[n]
    
    # Integral term
    integral_error += error[n] * t_p
    
    # Derivative term
    derivative_error = (error[n] - previous_error) / t_p if n > 0 else 0
    previous_error = error[n]
    
    # PID control
    Q = K_p * error[n] + K_i * integral_error + K_d * derivative_error
    # U = min(U_max,max(U_min,U_pi))
    
    # Q = (Q_max - Q_min) / (U_max - U_min) * (U - U_min) + Q_min

    # Update temperature
    dT = (F_in / rho) * (T_in - T[n]) + (Q / (rho * c_p)) - (F_out / rho) * (T[n] - T_out)
    T[n + 1] = T[n] + dT * t_p
    
    # Update height
    h[n + 1] = h[n] + ((F_in - F_out) / A) * t_p

# Plotting results
plt.figure(figsize=(12, 6))

# Temperature plot
plt.subplot(2, 1, 1)
plt.plot(time, T, label='Temperature in tank[°C]', color='red')
plt.axhline(T_set, color='green', linestyle='--', label= str(T_set) + '[°C] Setpoint')
plt.title('Temperature in Stirred Tank Heater with PID Control')
plt.xlabel('Time (s)')
plt.ylabel('Temperature (°C)')
plt.grid()
plt.legend()

# Height plot
plt.subplot(2, 1, 2)
plt.plot(time, h, label='Height (m)', color='blue')
plt.title('Liquid Height in Stirred Tank')
plt.xlabel('Time (s)')
plt.ylabel('Height (m)')
plt.grid()
plt.legend()

plt.tight_layout()
plt.show()
