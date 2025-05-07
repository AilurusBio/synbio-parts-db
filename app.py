import dash
from dash import html, dcc, callback_context
import dash_bootstrap_components as dbc
from pymongo import MongoClient
from app.components.navbar import create_navbar
from app.components.parts_table import create_parts_table
from app.components.sequence_viewer import create_sequence_viewer
from app.components.stats_dashboard import create_stats_dashboard
from app.utils.sequence_analysis import analyze_dna_sequence, analyze_protein_sequence
import traceback
import logging
import argparse

# 配置命令行参数
parser = argparse.ArgumentParser(description='启动合成生物学零件数据库Web应用')
parser.add_argument('--port', type=int, default=8050, help='Web应用端口号')
parser.add_argument('--host', type=str, default='127.0.0.1', help='Web应用主机地址')
args = parser.parse_args()

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 初始化Dash应用
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# 添加错误处理
app.config.suppress_callback_exceptions = True

try:
    # 连接MongoDB
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    # 测试连接
    client.server_info()
    db = client['synbio_parts_db']
    parts_collection = db['parts']
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

# 应用布局
app.layout = html.Div([
    dcc.Store(id='error-store', storage_type='memory'),
    create_navbar(),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("合成生物学零件数据库", className="text-center my-4"),
                dcc.Tabs(id='tabs', value='browse', children=[
                    dcc.Tab(label='浏览零件', value='browse'),
                    dcc.Tab(label='序列分析', value='sequence'),
                    dcc.Tab(label='数据统计', value='stats'),
                ]),
                html.Div(id='tab-content'),
                html.Div(id='sequence-viewer-output'),
                html.Div(id='error-message')
            ])
        ])
    ], fluid=True)
])

# 错误消息回调
@app.callback(
    dash.dependencies.Output('error-message', 'children'),
    [dash.dependencies.Input('error-store', 'data')]
)
def display_error(error_data):
    if error_data:
        return dbc.Alert(error_data, color="danger")
    return ""

# 标签页内容回调
@app.callback(
    dash.dependencies.Output('tab-content', 'children'),
    [dash.dependencies.Input('tabs', 'value')]
)
def render_content(tab):
    try:
        if tab == 'browse':
            return create_parts_table(parts_collection)
        elif tab == 'sequence':
            return create_sequence_viewer()
        elif tab == 'stats':
            return create_stats_dashboard(parts_collection)
    except Exception as e:
        logger.error(f"Error in render_content: {str(e)}")
        logger.error(traceback.format_exc())
        return html.Div()

# 序列分析回调
@app.callback(
    dash.dependencies.Output('sequence-viewer-output', 'children'),
    [dash.dependencies.Input('sequence-analyze-btn', 'n_clicks')],
    [dash.dependencies.State('sequence-type', 'value'),
     dash.dependencies.State('sequence-input', 'value')]
)
def analyze_sequence(n_clicks, seq_type, sequence):
    if n_clicks is None or not sequence:
        return html.Div()
    
    try:
        if seq_type == 'dna':
            results = analyze_dna_sequence(sequence)
            return html.Div([
                html.H4("DNA序列分析结果"),
                html.P(f"序列长度: {results['length']}"),
                html.P(f"GC含量: {results['gc_content']}%"),
                html.P("反向互补序列:"),
                dbc.Textarea(value=results['reverse_complement'], readOnly=True, style={'height': '100px'}),
                html.P("转录序列:"),
                dbc.Textarea(value=results['transcription'], readOnly=True, style={'height': '100px'}),
                html.P("翻译序列:"),
                dbc.Textarea(value=results['translation'], readOnly=True, style={'height': '100px'})
            ])
        else:
            results = analyze_protein_sequence(sequence)
            return html.Div([
                html.H4("蛋白质序列分析结果"),
                html.P(f"序列长度: {results['length']}"),
                html.P(f"分子量: {results['molecular_weight']} Da"),
                html.H5("氨基酸组成:"),
                html.Div([
                    html.P(f"{aa}: {percentage}%" )
                    for aa, percentage in results['amino_acid_composition'].items()
                ])
            ])
    except Exception as e:
        logger.error(f"Error in analyze_sequence: {str(e)}")
        logger.error(traceback.format_exc())
        return html.Div([
            html.H4("错误", style={'color': 'red'}),
            html.P(str(e))
        ])

if __name__ == '__main__':
    logger.info(f"Starting server on {args.host}:{args.port}")
    app.run_server(
        host=args.host,
        port=args.port,
        debug=True,
        dev_tools_hot_reload=False
    ) 