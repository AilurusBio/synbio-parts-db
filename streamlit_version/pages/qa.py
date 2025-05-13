# -*- coding: utf-8 -*-
# Title: Question & Answer

import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import sys
from pathlib import Path
import streamlit as st
import time
import logging
import pandas as pd
import io
import base64
import matplotlib.pyplot as plt
import re
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import SeqFeature, FeatureLocation
from datetime import datetime

# Add main directory to system path
sys.path.append(str(Path(__file__).parent.parent))

# Import shared functionality from utils
from utils import get_connection

# Import search functionality from data directory
# 使用utils中的全局缓存函数
from utils import get_semantic_search_instance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize semantic search as a singleton
_searcher_instance = None

@st.cache_resource
def get_searcher():
    """
    获取或初始化SemanticSearch实例
    """
    try:
        # 使用全局缓存的SemanticSearch实例
        logger.info("Getting cached SemanticSearch instance")
        searcher = get_semantic_search_instance()
        
        # 确保table属性存在
        if not hasattr(searcher, 'table'):
            logger.warning("SemanticSearch instance does not have 'table' attribute. Attempting to initialize it.")
            try:
                if hasattr(searcher, 'db'):
                    searcher.table = searcher.db.open_table("embeddings")
                    logger.info("Successfully initialized 'table' attribute.")
                else:
                    logger.error("SemanticSearch instance does not have 'db' attribute. Cannot initialize 'table'.")
            except Exception as table_e:
                logger.error(f"Error initializing table: {str(table_e)}")
                raise
        
        return searcher
    except Exception as e:
        st.error(f"Error initializing search: {str(e)}")
        logger.error(f"Error initializing search: {str(e)}", exc_info=True)
        raise

# --- Session state initialization ---
def initialize_chat_history():
    # Initialize chat history if it doesn't exist or needs reset
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your biological parts assistant. Ask me anything about biological parts, promoters, terminators, and more."}
        ]
    if "thinking" not in st.session_state:
        st.session_state.thinking = False
    if "current_parts" not in st.session_state:
        st.session_state.current_parts = []
    # --- NEW: Initialize current_question_text for the text_area ---
    if "current_question_text" not in st.session_state:
        st.session_state.current_question_text = ""
    logger.info("Chat session state initialized/verified.")

# --- Define the three sample questions for buttons ---
SAMPLE_QUESTIONS_FOR_BUTTONS = [
    "What are strong constitutive promoters for E. coli?",
    "What are the most efficient terminators for bacteria?",
    "What are the best plasmid backbones for protein expression?"
]

def format_sequence(sequence, line_length=60):
    """Formats a sequence string with line breaks."""
    return '\n'.join(sequence[i:i+line_length] for i in range(0, len(sequence), line_length))

# 可视化函数已移除

def export_chat_to_text(messages):
    """Exports chat history to a text file, including sequences."""
    content = "SynVectorDB Chat History\n"
    content += "========================\n\n"
    for msg in messages:
        timestamp = msg.get('timestamp', 'N/A') # Assuming timestamp is stored
        role = msg['role'].capitalize()
        message_content = msg['content'].replace('\n', ' ')
        content += f"[{timestamp}] {role}: {message_content}\n"
        # --- BEGIN MODIFICATION: Add sequences to export ---
        if msg['role'] == 'assistant' and 'sources' in msg and msg['sources']:
            content += "  Sources:\n"
            for idx, source in enumerate(msg['sources']):
                content += f"    {idx+1}. Name: {source.get('name', 'N/A')}\n"
                content += f"       Type: {source.get('type', 'N/A')}\n"
                content += f"       Similarity: {source.get('similarity', 'N/A'):.4f}\n"
                if source.get('description'):
                    content += f"       Description: {source['description']}\n"
                if source.get('sequence'):
                    content += f"       Sequence: {source['sequence']}\n"
            content += "\n"
        # --- END MODIFICATION ---
    return content

def export_chat_to_markdown(messages):
    """Exports chat history to a Markdown file, including sequences."""
    content = "# SynVectorDB Chat History\n\n"
    for msg in messages:
        timestamp = msg.get('timestamp', 'N/A')
        role_cap = msg['role'].capitalize()
        avatar = "🧑‍💻" if role_cap == "User" else "🧬"
        content += f"**{avatar} {role_cap}** ({timestamp}):\n"
        content += f"> {msg['content']}\n\n"
        # --- BEGIN MODIFICATION: Add sequences to export ---
        if msg['role'] == 'assistant' and 'sources' in msg and msg['sources']:
            content += "**Sources:**\n"
            for idx, source in enumerate(msg['sources']):
                content += f"*   **{idx+1}. Name:** {source.get('name', 'N/A')} (**Type:** {source.get('type', 'N/A')}) - **Similarity:** {source.get('similarity', 'N/A'):.4f}\n"
                if source.get('description'):
                    content += f"    *   **Description:** {source['description']}\n"
                if source.get('sequence'):
                    content += f"    *   **Sequence:**\n        ```\n        {source['sequence']}\n        ```\n"
            content += "\n"
        # --- END MODIFICATION ---
    return content

def generate_fasta_content(parts):
    fasta_strings = []
    for part in parts:
        if part.get('sequence') and part.get('name'):
            # Basic name cleaning for FASTA header (replace spaces, etc.)
            header_name = part['name'].replace(' ', '_').replace('/', '_').replace('\\', '_') 
            fasta_strings.append(f">{header_name}")
            fasta_strings.append(part['sequence'])
    return "\n".join(fasta_strings)

def extract_features_from_description(description):
    """Extract potential features from part description"""
    features = []
    
    # Common feature patterns to look for
    patterns = {
        'promoter': [r'promoter', r'\bp\d+\b'],
        'terminator': [r'terminator', r'term'],
        'RBS': [r'rbs', r'ribosome\s+binding\s+site'],
        'CDS': [r'cds', r'coding\s+sequence', r'gene'],
        'origin': [r'origin', r'ori'],
    }
    
    # Simple position estimation based on sequence length
    # In a real implementation, you would parse this from actual annotations
    def estimate_positions(seq_len, feature_type):
        if feature_type == 'promoter':
            return 0, min(150, seq_len // 5)
        elif feature_type == 'terminator':
            return max(0, seq_len - 150), seq_len
        elif feature_type == 'RBS':
            return min(200, seq_len // 4), min(250, seq_len // 3)
        elif feature_type == 'CDS':
            return min(300, seq_len // 3), min(900, seq_len * 2 // 3)
        elif feature_type == 'origin':
            return max(0, seq_len * 2 // 3), seq_len
        return 0, min(100, seq_len // 4)  # Default
    
    # Check description against patterns
    if description:
        desc_lower = description.lower()
        for feature_type, patterns_list in patterns.items():
            for pattern in patterns_list:
                if re.search(pattern, desc_lower):
                    # This would be replaced with actual positions in real implementation
                    features.append((feature_type, *estimate_positions(1000, feature_type)))
                    break
    
    return features

def display_part_details(part):
    st.markdown(f"**Name**: {part['name']}")
    st.markdown(f"**Type**: {part['type']}")
    st.markdown(f"**Source**: {part['source']}")
    st.markdown(f"**Similarity**: {part['similarity']:.4f}")
    
    # Check if part has a sequence
    if 'sequence' in part and part['sequence']:
        with st.expander("View Sequence", expanded=False):
            # 序列可视化功能已移除
            st.write("序列数据可用，但可视化功能已禁用。")
            
            # Display formatted sequence
            try:
                formatted_seq = format_sequence(part['sequence'])
                st.code(formatted_seq, language='text')
            except NameError:
                st.code(part['sequence'], language='text')
                st.warning("Function 'format_sequence' not found. Displaying raw sequence.")
    
    st.markdown("---")

def main():
    # Page configuration for a cleaner chat interface
    st.set_page_config(
        page_title="Question & Answer",
        page_icon="🧬",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS to make the chat interface more modern
    st.markdown("""
    <style>
    /* 强制使用浅色主题，覆盖Streamlit的默认主题切换 */
    html, body, [class*="css"] {
        color: #262730 !important;
        background-color: #FFFFFF !important;
    }
    
    /* 全局样式 - 固定浅色主题 */
    .stApp {
        background-color: #f5f5f5 !important;
    }
    
    /* 确保所有文本使用深色 */
    .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, div {
        color: #262730 !important;
    }
    
    /* 确保侧边栏使用浅色背景 */
    .css-1d391kg, .css-1lcbmhc, .css-12oz5g7 {
        background-color: #F0F2F6 !important;
    }
    
    /* 确保按钮和输入框使用浅色主题 */
    .stButton>button, .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #FFFFFF !important;
        color: #262730 !important;
        border-color: #CCC !important;
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* 聊天容器样式 */
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: none !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    .stChatMessage.user {
        background-color: #e6f7ff !important;
    }
    
    .stChatMessage.assistant {
        background-color: #f0f2f5 !important;
    }
    
    /* 头像样式 */
    .stChatMessageAvatar {
        width: 2.5rem !important;
        height: 2.5rem !important;
        border-radius: 50% !important;
    }
    
    /* 输入区域样式 */
    .stChatInputContainer {
        padding: 0.5rem;
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
    }
    
    /* 右侧面板样式 */
    .part-card {
        border: 1px solid #d9d9d9;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        background-color: white;
        transition: all 0.3s ease;
    }
    
    .part-card:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    
    .part-title {
        font-weight: bold;
        color: #1890ff;
        margin-bottom: 8px;
        font-size: 16px;
    }
    
    /* 头部样式 */
    .chat-header {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        padding: 16px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .chat-header h1 {
        margin: 0;
        font-size: 24px;
        color: #1890ff;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* 自定义按钮样式 */
    div.stButton > button {
        background-color: #f0f2f5;
        color: #1890ff;
        border: 1px solid #d9d9d9;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        background-color: #e6f7ff;
        border-color: #1890ff;
    }
    
    div.stButton > button:focus {
        box-shadow: none;
    }
    
    /* 表单提交按钮样式 */
    .stButton>button[kind="primary"] {
        background-color: #1890ff;
        color: white;
    }
    
    .stButton>button[kind="primary"]:hover {
        background-color: #40a9ff;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize chat history
    initialize_chat_history()
    
    # Custom header with logo and tools
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.markdown(
            """
            <div class="chat-header">
                <h1>🧬 SynVectorDB Chat Assistant</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with header_col2:
        # Removed export functionality as per user request
        pass
    
    # 初始化会话状态变量
    if "use_local_parts" not in st.session_state:
        st.session_state.use_local_parts = False
    
    # 添加实验性功能选项
    st.checkbox("Use Local Parts Data (Experimental)", key="use_local_parts")
    
    # 只有在勾选了实验性功能选项时才显示上传功能
    if st.session_state.use_local_parts:
        with st.expander("Upload Local Parts Data (CSV)", expanded=False):
            st.markdown("**Upload your own parts data for temporary use in this session.**")
            st.markdown("CSV format requirements:")
            st.markdown("- One part per row")
            st.markdown("- First column: Part name")
            st.markdown("- Second column: Part type (optional)")
            st.markdown("- Third column: Part description (optional)")
            st.markdown("- Fourth column: Part sequence (optional)")
            
            # 添加示例文件下载功能
            example_file_path = "data/example_parts.csv"
            with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), example_file_path), "rb") as file:
                example_file_content = file.read()
            
            st.download_button(
                label="Download Example CSV",
                data=example_file_content,
                file_name="example_parts.csv",
                mime="text/csv",
                help="Download an example CSV file with the correct format"
            )
            
            uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="parts_csv_uploader")
            
            if uploaded_file is not None:
                # 初始化临时会话状态变量
                if "temp_parts_uploaded" not in st.session_state:
                    st.session_state.temp_parts_uploaded = False
                    st.session_state.temp_parts_data = []
                    st.session_state.temp_parts_embeddings = []
                
                if not st.session_state.temp_parts_uploaded:
                    try:
                        # 显示进度条
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # 读取CSV文件
                        status_text.text("Reading CSV file...")
                        df = pd.read_csv(uploaded_file)
                        progress_bar.progress(20)
                        
                        # 验证CSV格式
                        if len(df.columns) < 1:
                            st.error("CSV file must have at least one column for part names.")
                            return
                        
                        # 标准化列名
                        columns = list(df.columns)
                        column_map = {
                            columns[0]: "name"
                        }
                        
                        if len(columns) > 1:
                            column_map[columns[1]] = "type"
                        if len(columns) > 2:
                            column_map[columns[2]] = "description"
                        if len(columns) > 3:
                            column_map[columns[3]] = "sequence"
                        
                        df = df.rename(columns=column_map)
                        
                        # 确保必要的列存在
                        for col in ["type", "description", "sequence"]:
                            if col not in df.columns:
                                df[col] = ""
                        
                        progress_bar.progress(40)
                        status_text.text("Processing parts data...")
                        
                        # 准备数据
                        parts_data = []
                        for _, row in df.iterrows():
                            part = {
                                "name": str(row["name"]),
                                "type": str(row["type"]),
                                "description": str(row["description"]),
                                "sequence": str(row["sequence"]),
                                "source": "Uploaded CSV"
                            }
                            parts_data.append(part)
                        
                        progress_bar.progress(60)
                        status_text.text("Generating embeddings...")
                        
                        # 获取SemanticSearch实例
                        searcher = get_searcher()
                        
                        # 为每个元件生成嵌入向量
                        embeddings = []
                        for part in parts_data:
                            # 创建用于嵌入的文本
                            text = f"Name: {part['name']}\nType: {part['type']}\nDescription: {part['description']}"
                            # 生成嵌入向量
                            embedding = searcher.model.encode([text])[0]
                            embeddings.append(embedding)
                        
                        progress_bar.progress(90)
                        status_text.text("Finalizing...")
                        
                        # 保存到会话状态
                        st.session_state.temp_parts_data = parts_data
                        st.session_state.temp_parts_embeddings = embeddings
                        st.session_state.temp_parts_uploaded = True
                        
                        progress_bar.progress(100)
                        status_text.text(f"Successfully processed {len(parts_data)} parts!")
                        
                        # 显示上传的元件数据摘要
                        st.success(f"Uploaded {len(parts_data)} parts from CSV file.")
                        st.dataframe(df.head(5))
                        
                    except Exception as e:
                        st.error(f"Error processing CSV file: {str(e)}")
                        logger.error(f"CSV processing error: {str(e)}", exc_info=True)
                else:
                    # 已经上传过，显示摘要
                    st.success(f"Using {len(st.session_state.temp_parts_data)} uploaded parts.")
                    st.button("Clear uploaded parts", on_click=lambda: setattr(st.session_state, "temp_parts_uploaded", False))
    
    # Create a two-column layout with custom widths
    col1, col2 = st.columns([3, 1])
    
    # 右侧面板显示相关元件
    with col2:
        st.markdown("### Referenced Parts")
        if "current_parts" in st.session_state and st.session_state.current_parts:
            # 添加下载按钮
            parts = st.session_state.current_parts
            if any(part.get('sequence') for part in parts):
                # 生成FASTA内容
                fasta_content = generate_fasta_content(parts)
                if fasta_content:
                    st.download_button(
                        label="Download as FASTA",
                        data=fasta_content,
                        file_name=f"synvectordb_parts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.fasta",
                        mime="text/plain",
                        help="Download sequences of all referenced parts as a FASTA file"
                    )
            
            # 显示每个元件的详细信息
            for idx, part in enumerate(st.session_state.current_parts):
                with st.expander(f"{idx+1}. {part.get('name', 'Unknown Part')}"):
                    display_part_details(part)
        else:
            st.info("No parts referenced in the current conversation. Ask a question to see relevant parts.")
    
    with col1:
        # --- BEGIN MODIFICATION: Relocated 'thinking' block --- 
        # Check if we need to process a new question
        if st.session_state.thinking:
            if not st.session_state.messages:
                logger.warning("In 'thinking' state but no messages. Resetting.")
                st.session_state.thinking = False; st.rerun(); # return # Removed return to allow UI to draw

            last_message_in_session = st.session_state.messages[-1] if st.session_state.messages else None

            if last_message_in_session and not isinstance(last_message_in_session, dict):
                logger.error(f"Last message is not a dict: {last_message_in_session}. Resetting.")
                st.error("Message format error. Please try again.")
                st.session_state.thinking = False; st.rerun(); # return
            
            if last_message_in_session and last_message_in_session.get("role") == "user":
                current_question_content = last_message_in_session.get('content')
                if not isinstance(current_question_content, str):
                    logger.error(f"User message content is not a string: {current_question_content}. Message: {last_message_in_session}. Resetting.")
                    st.error("Message content error. Please try again.")
                    st.session_state.thinking = False; st.rerun(); # return
                else:
                    try:
                        searcher = get_searcher()
                        logger.info(f"Calling ask_question for: {current_question_content}")
                        
                        # Use chat history for context
                        history_for_context = st.session_state.messages[:-1]  # Exclude current question
                        
                        # 创建一个空的助手回复占位符
                        assistant_response = {
                            "role": "assistant",
                            "content": "",
                            "sources": [],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # 添加到消息列表
                        st.session_state.messages.append(assistant_response)
                        
                        # 创建一个空的消息容器用于流式输出
                        message_placeholder = st.empty()
                        
                        # 定义流式处理回调函数
                        def stream_handler(content_chunk):
                            # 更新会话状态中的内容
                            st.session_state.messages[-1]["content"] += content_chunk
                            # 更新显示的消息
                            message_placeholder.markdown(st.session_state.messages[-1]["content"])
                        
                        # 调用带有流式处理的ask_question
                        logger.info(f"Calling ask_question with streaming for: {current_question_content}")
                        
                        # 检查是否使用临时上传的元件数据
                        temp_parts_data = None
                        temp_parts_embeddings = None
                        if ("use_local_parts" in st.session_state and st.session_state.use_local_parts and
                            "temp_parts_uploaded" in st.session_state and st.session_state.temp_parts_uploaded):
                            temp_parts_data = st.session_state.temp_parts_data
                            temp_parts_embeddings = st.session_state.temp_parts_embeddings
                            logger.info(f"Using {len(temp_parts_data)} temporary uploaded parts for search")
                        
                        result = searcher.ask_question(
                            question=current_question_content,
                            top_k=5,  # Number of relevant parts to retrieve
                            chat_history=history_for_context,
                            stream_handler=stream_handler,  # 传递流式处理回调
                            temp_parts_data=temp_parts_data,
                            temp_parts_embeddings=temp_parts_embeddings
                        )
                        
                        # 更新sources信息
                        st.session_state.messages[-1]["sources"] = result["sources"]
                        st.session_state.thinking = False
                    except Exception as e:
                        logger.error(f"Error during search or LLM call: {e}", exc_info=True)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": f"🧬 Sorry, an error occurred: {e}", 
                            "sources": [], 
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    finally:
                        st.session_state.thinking = False
                        # st.rerun() # We will rerun implicitly by reaching end of script or by chat_input/button causing rerun
            elif last_message_in_session and last_message_in_session.get("role") == "assistant":
                logger.info("Last message was assistant, but in thinking state. Resetting.")
                st.session_state.thinking = False
                # st.rerun() # Allow UI to draw if needed
            elif last_message_in_session: # Malformed role or other issue
                logger.error(f"Last message has unknown role or is malformed: {last_message_in_session}. Resetting.")
                st.error("Message role error. Please try again.")
                st.session_state.thinking = False
                # st.rerun()
            # If st.session_state.thinking was true but no user message to process (e.g., cleared chat), 
            # it will be set to False above and the UI will draw normally.
        # --- END MODIFICATION: Relocated 'thinking' block --- 

        # Create a container for the chat messages
        chat_container = st.container()
        
        # Display chat messages using Streamlit's native chat components
        with chat_container:
            for message in st.session_state.messages:
                avatar = "👤" if message["role"] == "user" else "🧬"
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])
                    # Check if it's an assistant message and has sources
                    if message["role"] == "assistant" and "sources" in message and message["sources"]:
                        with st.expander("View Sources and Details"): # Outer Expander
                            for idx, source in enumerate(message["sources"]):
                                st.markdown(f"**{idx+1}. Name:** {source.get('name', 'N/A')} (**Type:** {source.get('type', 'N/A')}) - **Similarity:** {source.get('similarity', 'N/A'):.4f}")
                                if source.get('description'):
                                    st.markdown(f"**Description:** {source['description']}")
                                if source.get('sequence'):
                                    seq = source['sequence']
                                    
                                    # 显示序列数据
                                    st.write("**Sequence data:**")
                                    try:
                                        # 使用format_sequence函数格式化序列
                                        formatted_seq = format_sequence(seq)
                                        st.code(formatted_seq, language='text')
                                    except Exception as e:
                                        # 如果格式化失败，直接显示原始序列
                                        st.code(seq, language='text')
                                        st.warning(f"Could not format sequence: {e}")
            
            # Show thinking animation if needed
            if "thinking" in st.session_state and st.session_state.thinking:
                with st.chat_message("assistant", avatar="🧬"):
                    st.markdown("⏳ Searching database and generating answer...")
                    
                    # Get the last user message
                    last_user_message = next((m["content"] for m in reversed(st.session_state.messages) 
                                          if m["role"] == "user"), None)
                    
                    if last_user_message:
                        try:
                            searcher = get_searcher()
                            # --- BEGIN MODIFICATION: Prepare chat history for context --- 
                            # Take last N messages (e.g., 6, for 3 user/assistant turns) excluding the current user message
                            # Ensure we only pass 'role' and 'content'
                            history_to_pass = []
                            if len(st.session_state.messages) > 1: # if there's more than just the current user message
                                # Slice to get up to the last 6 messages *before* the current user's message
                                # The current user's message is st.session_state.messages[-1]
                                start_index = max(0, len(st.session_state.messages) - 1 - 6) # Go back 6 from message before current
                                end_index = len(st.session_state.messages) - 1 # Up to message before current
                                relevant_history = st.session_state.messages[start_index:end_index]
                                for msg in relevant_history:
                                    history_to_pass.append({"role": msg.get("role"), "content": msg.get("content")})
                            # --- END MODIFICATION ---
                            
                            result = searcher.ask_question(
                                question=last_user_message['content'],  # Correctly pass the content string
                                top_k=5,
                                chat_history=history_to_pass # Pass the prepared history
                            )
                            answer = result["answer"]
                            sources = result["sources"]
                            
                            # Add assistant response to chat history
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": answer,
                                "sources": sources,
                                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
                            })
                            st.session_state.current_parts = sources
                        except Exception as e:
                            logger.error(f"Error during search: {e}", exc_info=True)
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": f"Sorry, an error occurred: {e}",
                                "sources": [],
                                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
                            })
                        finally:
                            # Processing finished, set thinking to False
                            st.session_state.thinking = False
                            # Rerun to display the new message and stop spinner
                            st.rerun()
                    else:
                        # If there's no last user message but we are in thinking state, something is wrong.
                        # Reset thinking state to avoid loop.
                        st.session_state.thinking = False
                        st.rerun() # Rerun to clear the thinking state
        
        # --- Sample Question Buttons --- 
        st.markdown("**Or try a sample question:**")
        button_cols = st.columns(len(SAMPLE_QUESTIONS_FOR_BUTTONS))
        for idx, sample_q in enumerate(SAMPLE_QUESTIONS_FOR_BUTTONS):
            if button_cols[idx].button(sample_q, key=f"sample_q_{idx}", help=f"Click to use: {sample_q}"):
                # --- MODIFIED: Update text_area content, don't submit directly ---
                st.session_state.current_question_text = sample_q
                st.rerun() # Rerun to update the text_area
        # --- END Sample Question Buttons ---

        # --- REPLACED st.chat_input with st.text_area and st.button ---
        # Chat input using st.text_area and a submit button
        user_input = st.text_area(
            "Ask your question about biological parts...", 
            value=st.session_state.current_question_text, 
            key="question_text_area",
            height=100,
            placeholder="Type your question here or select a sample above."
        )
        
        if st.button("💬 Ask Question", key="ask_question_button", type="primary"):
            prompt = user_input # Get text from text_area
            if prompt: # Ensure there is a prompt
                st.session_state.messages.append({
                    "role": "user", 
                    "content": prompt, 
                    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
                })
                st.session_state.thinking = True
                st.session_state.current_question_text = "" # Clear text area after submission
                st.rerun() # Rerun to process the new message and clear input
            else:
                st.warning("Please enter a question.")
        # --- END REPLACEMENT ---

    with col2:
        # Parts reference panel
        st.markdown("### Referenced Parts")
        
        # --- MOVED UP: FASTA Download Button for Referenced Parts ---
        if st.session_state.current_parts:
            fasta_data = generate_fasta_content(st.session_state.current_parts) 
            if fasta_data: # Only show button if there's data to download
                st.download_button(
                    label="Download Referenced Parts (FASTA)",
                    data=fasta_data,
                    file_name=f"referenced_parts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.fasta",
                    mime="text/plain", # FASTA is plain text
                    key="fasta_download_main_moved_up"
                )
            else:
                st.caption("No sequences in referenced parts to download as FASTA.")
        # --- END MOVED UP ---
        
        if not st.session_state.current_parts:
            st.caption("Referenced parts will appear here after you ask a question.")
            st.markdown("""
            This section provides:
            - Part Name and Type
            - Sequence (if available)
            """)

        if st.session_state.current_parts:
            for i, part in enumerate(st.session_state.current_parts):
                with st.container(): # Using st.container for each part
                    st.markdown(f"<div style='border: 1px solid #e0e0e0; border-radius: 5px; padding: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                    st.markdown(f"**{part.get('name', 'Unknown Part')}** (Type: {part.get('type', 'N/A')})")
                    if 'sequence' in part and part['sequence']:
                        st.code(format_sequence(part.get('sequence', 'N/A')), language='text')
                    else:
                        st.caption("No sequence available.")
                    st.markdown("</div>", unsafe_allow_html=True)
        
        # Add a button to clear chat history with custom styling
        st.markdown('<div style="text-align: center; margin-top: 20px;">', unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat", key="clear_chat", type="secondary", use_container_width=True):
            # --- MODIFIED: Ensure current_question_text is also reset --- 
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I'm your biological parts assistant. Ask me anything about biological parts, promoters, terminators, and more."}
            ]
            st.session_state.current_parts = []
            st.session_state.thinking = False # Reset thinking state
            st.session_state.current_question_text = "" # Reset question input text field
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
