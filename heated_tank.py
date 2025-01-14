import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

# Default parameters (unchanged)
default_params = {
    'V': 5,
    'Q_in_out': 0.1,
    'lamda': 2.3e6,
    'rho': 1000,
    'Cp': 4200,
    'Tin': 15,
    'Tset': 40,
    'Qmax': 10,
    'Qmin': 0,
    't_sim': 3600,
    'Umax': 10,
    'Umin': 0,
    'Kp': 0.05,
    'Tp': 0.1,
    'Ti': 1,
    'Td': 0.1
}

# Simulation function (unchanged)
def simulate_system(params):
    V = params['V']
    F_in_out = params['Q_in_out']
    lamda = params['lamda']
    rho = params['rho']
    Cp = params['Cp']
    T_in = params['Tin']
    Tset = params['Tset']
    Qmax = params['Qmax']
    Qmin = params['Qmin']
    end_time = params['t_sim']
    Umax = params['Umax']
    Umin = params['Umin']
    K_p = params['Kp']
    time_step = params['Tp']
    T_i = params['Ti']
    T_d = params['Td']

    K_i = K_p * (time_step / T_i)
    K_d = K_p * (T_d / time_step)

    T = [T_in]
    t_time = [0]
    Q = [0]
    error = [Tset - T[0]]
    integral_error = [0]
    derivative_error = [0]
    u = [0]

    num_steps = int(end_time / time_step)

    for n in range(1, num_steps + 1):
        t_time.append(n * time_step)
        error.append(Tset - T[-1])
        integral_error.append(integral_error[-1] + error[-1] * time_step)
        derivative_error.append((error[-1] - error[-2]) / time_step if n > 1 else 0)

        u.append(K_p * error[-1] + K_i * integral_error[-1] + K_d * derivative_error[-1])
        Q.append(min(Qmax, max(0, ((Qmax - Qmin) / (Umax - Umin)) * (u[-1] - Umin) + Qmin)))

        T.append(T[-1] + (time_step / V) * ((lamda * Q[-1] / (rho * Cp)) + F_in_out * (T_in - T[-1])))

    return t_time, T, Q

# Dash app initialization
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H1("Zbiornik ogrzewany parą wodną | Symulacja regulatora PID"),
    html.Div([
        html.Div([
            html.Label("Wzmocnienie proporcjonalne (Kp):"),
            dcc.Slider(
                id='Kp-slider',
                min=0.01,
                max=1,
                step=0.01,
                value=default_params['Kp'],
                marks={i/10: str(i/10) for i in range(11)}
            ),
            html.Label("Czas całkowania (Ti):"),
            dcc.Slider(
                id='Ti-slider',
                min=0.1,
                max=10,
                step=0.1,
                value=default_params['Ti'],
                marks={i: str(i) for i in range(1, 11)}
            ),
            html.Label("Czas różniczkowania (Td):"),
            dcc.Slider(
                id='Td-slider',
                min=0.01,
                max=10,
                step=0.1,
                value=default_params['Td'],
                marks={i: str(i) for i in range(1, 11)}
            ),
            html.Label("Temperatura zadana (Tset):"),
            dcc.Slider(
                id='Tset-slider',
                min=10,
                max=100,
                step=1,
                value=default_params['Tset'],
                marks={i: str(i) for i in range(10, 101, 10)}
            ),
            html.Div([
                html.Button('Uruchom symulację', id='run-button', style = {'visibility': 'hidden'}, n_clicks=0)
            ]),
            html.Div(id='current-slider-values', style={'margin-top': '20px', 'font-weight': 'bold'}),
            html.Div(id='previous-slider-values', style={'margin-top': '10px'}),
        ], style={'width': '30%', 'padding': '20px'}),

        html.Div([
            dcc.Graph(id='temp-graph'),
            dcc.Graph(id='Q-graph'),
        ], style={'width': '70%', 'padding': '20px'}),
    ], style={'display': 'flex'}),
    dcc.Store(id='previous-temp-data', data={'t': [], 'T': [], 'Tset': []}),
    dcc.Store(id='previous-Q-data', data={'t': [], 'Q': []}),
    dcc.Store(id='previous-slider-settings', data={'Kp': default_params['Kp'], 'Ti': default_params['Ti'], 'Td': default_params['Td'], 'Tset': default_params['Tset']}),
])


@app.callback(
    [Output('temp-graph', 'figure'),
     Output('Q-graph', 'figure'),
     Output('previous-temp-data', 'data'),
     Output('previous-Q-data', 'data'),
     Output('previous-slider-settings', 'data'),
     Output('current-slider-values', 'children'),
     Output('previous-slider-values', 'children')],
    [Input('run-button', 'n_clicks')],
    [Input('Kp-slider', 'value'),
     Input('Ti-slider', 'value'),
     Input('Td-slider', 'value'),
     Input('Tset-slider', 'value')],
    [State('previous-temp-data', 'data'),
     State('previous-Q-data', 'data'),
     State('previous-slider-settings', 'data')]
)
def update_graphs(n_clicks, Kp, Ti, Td, Tset, previous_temp_data, previous_Q_data, previous_slider_settings):
    params = default_params.copy()
    params['Kp'] = Kp
    params['Ti'] = Ti
    params['Td'] = Td
    params['Tset'] = Tset

    t_time, T, Q = simulate_system(params)

    temp_fig = {
        'data': [
            go.Scatter(x=t_time, y=T, mode='lines', name='Temperatura (T)', line={'color': 'blue'}),
            go.Scatter(x=t_time, y=[Tset] * len(t_time), mode='lines', name='Temperatura zadana (Tset)', line={'color': 'red', 'dash': 'dash'}),
            go.Scatter(x=previous_temp_data['t'], y=previous_temp_data['T'], mode='lines', name='Poprzednia Temperatura (T)', line={'color': 'blue', 'dash': 'dot'}),
            go.Scatter(x=previous_temp_data['t'], y=[previous_temp_data['Tset']] * len(previous_temp_data['t']), mode='lines', name='Poprzednia Temperatura Zadana (Tset)', line={'color': 'red', 'dash': 'dot'}),
        ],
        'layout': go.Layout(
            title="Temperatura w czasie",
            xaxis={'title': 'Czas (s)'},
            yaxis={'title': 'Temperatura (°C)'},
            template='plotly_white',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
    }

    Q_fig = {
        'data': [
            go.Scatter(x=t_time, y=Q, mode='lines', name='Przepływ ciepła (Q)', line={'color': 'green'}),
            go.Scatter(x=previous_Q_data['t'], y=previous_Q_data['Q'], mode='lines', name='Poprzedni Przepływ ciepła (Q)', line={'color': 'green', 'dash': 'dot'}),
        ],
        'layout': go.Layout(
            title="Przepływ ciepła w czasie",
            xaxis={'title': 'Czas (s)'},
            yaxis={'title': 'Przepływ ciepła (kg/s)'},
            template='plotly_white',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
    }

    current_values = f"Aktualne wartości: Kp={Kp}, Ti={Ti}, Td={Td}, Tset={Tset}"
    previous_values = f"Poprzednie wartości: Kp={previous_slider_settings['Kp']}, Ti={previous_slider_settings['Ti']}, Td={previous_slider_settings['Td']}, Tset={previous_slider_settings['Tset']}"

    return (temp_fig, Q_fig, 
            {'t': t_time, 'T': T, 'Tset': Tset}, 
            {'t': t_time, 'Q': Q}, 
            {'Kp': Kp, 'Ti': Ti, 'Td': Td, 'Tset': Tset}, 
            current_values, previous_values)


if __name__ == '__main__':
    app.run_server(debug=True)
