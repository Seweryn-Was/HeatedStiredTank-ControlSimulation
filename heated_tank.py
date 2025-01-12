import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State


# Funkcja do symulacji
def run_simulation(T_set, K_p, K_i, K_d):
    A = 1.0  # Cross-sectional area of the tank (m^2)
    rho = 997  # Density of the fluid (kg/m^3)
    c_p = 4186  # Specific heat capacity of water (J/(kg·K))
    F_in = 0.1  # Inlet flow rate (m^3/s)
    F_out = 0.1  # Outlet flow rate (m^3/s)
    T_in = 60  # Inlet temperature (°C)
    T_out = 20  # Outlet temperature (°C)
    t_p = 0.1  # Time step (s)

    # Simulation parameters
    end_time = 16000  # End time (s)
    num_steps = int(end_time / t_p)  # Number of steps
    time = np.arange(0, end_time, t_p)  # Time array

    # Initialize arrays
    T = np.zeros(num_steps)  # Temperature array
    h = np.zeros(num_steps)  # Height array
    error = np.zeros(num_steps)  # Error array
    integral_error = 0  # Initialize integral error
    previous_error = 0  # Initialize previous error for derivative calculation

    # Initial conditions
    T[0] = T_out  # Initial temperature (°C)
    h[0] = 1.0  # Initial height (m)

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

        # Update temperature
        dT = (F_in / rho) * (T_in - T[n]) + (Q / (rho * c_p)) - (F_out / rho) * (T[n] - T_out)
        T[n + 1] = T[n] + dT * t_p

        # Update height
        h[n + 1] = h[n] + ((F_in - F_out) / A) * t_p

    return time, T, h


# Tworzenie aplikacji Dash
app = dash.Dash(__name__)

# Layout aplikacji
app.layout = html.Div([
    html.H1("PID Control for Stirred Tank Heater"),

    # Sliders for adjusting parameters
    html.Div([
        html.Label("Setpoint Temperature (°C)"),
        dcc.Slider(
            id='T_set_slider',
            min=20,
            max=90,
            step=0.1,
            value=99.5,
            marks={i: f'{i}' for i in range(20, 101, 10)}
        ),
    ]),

    html.Div([
        html.Label("Proportional Gain (K_p)"),
        dcc.Slider(
            id='K_p_slider',
            min=1000,
            max=10000,
            step=100,
            value=3200,
            marks={i: f'{i}' for i in range(1000, 10001, 1000)}
        ),
    ]),

    html.Div([
        html.Label("Integral Gain (K_i)"),
        dcc.Slider(
            id='K_i_slider',
            min=1,
            max=50,
            step=1,
            value=7.7,
            marks={i: f'{i}' for i in range(1, 51, 10)}
        ),
    ]),

    html.Div([
        html.Label("Derivative Gain (K_d)"),
        dcc.Slider(
            id='K_d_slider',
            min=50000,
            max=200000,
            step=5000,
            value=101000,
            marks={i: f'{i}' for i in range(50000, 200001, 50000)}
        ),
    ]),

    # Przyciski do uruchomienia symulacji
    html.Div([
        html.Button('Run Simulation', id='run_button', n_clicks=0),
    ], style={'margin': '20px'}),

    # Component to store the previous temperature
    dcc.Store(id='T_previous_store', data=np.zeros(int(16000 / 0.1))),

    # Graph for the simulation
    dcc.Graph(id='simulation_graph'),
])


# Callback to update the graph based on slider values and button click
@app.callback(
    [Output('simulation_graph', 'figure'),
     Output('T_previous_store', 'data')],
    [
        Input('run_button', 'n_clicks'),
    ],
    [
        State('T_set_slider', 'value'),
        State('K_p_slider', 'value'),
        State('K_i_slider', 'value'),
        State('K_d_slider', 'value'),
        State('T_previous_store', 'data')
    ]
)
def update_graph(n_clicks, T_set, K_p, K_i, K_d, T_previous):
    # Symulacja powinna zostać uruchomiona tylko po kliknięciu przycisku
    if n_clicks == 0:
        return go.Figure(), T_previous  # Zwracamy pusty wykres na początku, dopóki przycisk nie zostanie kliknięty

    # Uruchomienie symulacji z wybranymi parametrami po kliknięciu przycisku
    time, T, h = run_simulation(T_set, K_p, K_i, K_d)

    # Tworzenie wykresów (subplots)
    fig = make_subplots(
        rows=2, cols=1,  # 2 wiersze, 1 kolumna
        subplot_titles=('Temperature in Stirred Tank Heater with PID Control', 'Liquid Height in Stirred Tank')
    )

    # Wykres poprzedniej temperatury
    fig.add_trace(go.Scatter(x=time, y=T_previous, mode='lines', name='Previous temperature in tank (°C)',
                             line=dict(color='blue', dash='dash')), row=1, col=1)
    # Wykres temperatury
    fig.add_trace(go.Scatter(x=time, y=T, mode='lines', name='Temperature in tank (°C)', line=dict(color='red')), row=1,
                  col=1)
    fig.add_trace(go.Scatter(x=time, y=[T_set] * len(time), mode='lines', name=f'Setpoint {T_set}°C',
                             line=dict(color='green', dash='dash')), row=1, col=1)

    # Wykres wysokości
    fig.add_trace(go.Scatter(x=time, y=h, mode='lines', name='Height (m)', line=dict(color='blue')), row=2, col=1)

    # Ustawienia układu wykresu
    fig.update_layout(
        height=800,  # Zwiększamy wysokość dla lepszej widoczności
        title_text="Stirred Tank Heater with PID Control",
        xaxis_title="Time (s)",
        template='plotly_dark',
        showlegend=True
    )

    # Etykiety osi dla wykresów
    fig.update_xaxes(title_text="Time (s)", row=1, col=1)
    fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
    fig.update_yaxes(title_text="Height (m)", row=2, col=1)

    # Aktualizacja zmiennej T_previous
    T_previous = T.copy()

    return fig, T_previous


# Uruchomienie aplikacji Dash
if __name__ == '__main__':
    app.run_server(debug=True)
