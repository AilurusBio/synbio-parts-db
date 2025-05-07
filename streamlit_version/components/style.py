import streamlit as st

def init_page_config():
    """初始化页面配置"""
    st.set_page_config(
        page_title="MCP Server API",
        page_icon="🧬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def apply_global_styles():
    """应用全局样式"""
    st.markdown("""
    <style>
    /* 全局样式 */
    .stApp {
        background-color: #f5f5f5;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 标题样式 */
    h1 {
        color: #1f77b4;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    h2 {
        color: #2c3e50;
        margin-top: 2rem;
    }
    
    /* 按钮样式 */
    .stButton>button {
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1565c0;
    }
    
    /* 代码块样式 */
    .json {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #dee2e6;
    }
    
    /* API 端点样式 */
    .api-endpoint {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* 侧边栏样式 */
    .sidebar .sidebar-content {
        background-color: #2c3e50;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def create_sidebar():
    """创建侧边栏导航"""
    with st.sidebar:
        st.title("MCP Server")
        st.markdown("---")
        st.markdown("### 导航")
        page = st.radio(
            "选择页面",
            ["API 文档", "API 测试", "数据库统计"]
        )
    return page

def create_api_endpoint_card(title, endpoint, description, example_request=None, example_response=None):
    """创建 API 端点卡片"""
    st.markdown(f"""
    <div class="api-endpoint">
    <h3>{title}</h3>
    <pre><code>{endpoint}</code></pre>
    <p>{description}</p>
    """, unsafe_allow_html=True)
    
    if example_request:
        st.markdown("""
        <h4>请求示例：</h4>
        <div class="json">
        """, unsafe_allow_html=True)
        st.json(example_request)
        st.markdown("</div>", unsafe_allow_html=True)
        
    if example_response:
        st.markdown("""
        <h4>响应示例：</h4>
        <div class="json">
        """, unsafe_allow_html=True)
        st.json(example_response)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True) 