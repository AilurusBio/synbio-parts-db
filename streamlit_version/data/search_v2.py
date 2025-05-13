import pandas as pd
from pathlib import Path
import lancedb
from sentence_transformers import SentenceTransformer
import argparse
import requests
import json
import os
import numpy as np
from openai import OpenAI
import time
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)

class SemanticSearch:
    def __init__(self):
        logger.critical("--- SemanticSearch Initialization START ---")
        start_time = time.time()
        logger.critical("INIT_STEP_000: Starting SemanticSearch initialization.")
        
        # 获取项目根目录（当前文件所在目录的父目录的父目录）
        self.root_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.root_dir / "streamlit_version" / "data"
        self.db_path = self.data_dir / "parts.lance"
        self.cache_dir = self.data_dir / "models"
        
        # Define source_collection mapping
        self.source_mapping = {
            "iGEM registry": "igem",
            "iGEM": "igem",
            "igem": "igem",
            "laboratory": "lab",
            "lab": "lab",
            "addgene": "addgene",
            "snapgene": "snapgene",
            "yunzhou": "yunzhou"
        }
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}. Please run init_db.py first.")
        
        model_dir = self.cache_dir / "models--sentence-transformers--all-MiniLM-L6-v2"
        if not model_dir.exists():
            raise FileNotFoundError(f"Model not found at {model_dir}. Please run download_model.py first.")
        
        # Connect to LanceDB
        logger.critical(f"INIT_STEP_004: Connecting to LanceDB at '{self.db_path}'.")
        self.db = lancedb.connect(self.db_path)
        logger.critical(f"INIT_STEP_005: LanceDB connection object obtained: {type(self.db)}")
        
        # Open the LanceDB table
        table_name = "embeddings"
        logger.critical(f"INIT_STEP_006: Attempting to open LanceDB table '{table_name}'.")
        try:
            self.table = self.db.open_table(table_name)
            logger.critical(f"INIT_STEP_006A: LanceDB table '{table_name}' opened successfully. Schema: {self.table.schema}")
        except Exception as e:
            logger.critical(f"INIT_STEP_006B: Failed to open LanceDB table '{table_name}'.", exc_info=True)
            try:
                available_tables = self.db.table_names()
                logger.error(f"Available tables in DB: {available_tables}")
            except Exception as list_e:
                logger.error(f"Could not list tables in DB: {list_e}")
            raise RuntimeError(f"Failed to open LanceDB table '{table_name}'. Error: {e}") from e
        
        # Initialize model with error handling
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Try to load the model with explicit device setting
                import torch
                device = 'cpu'  # Force CPU usage to avoid CUDA issues
                
                logger.critical(f"INIT_STEP_002: Initializing SentenceTransformer model 'all-MiniLM-L6-v2' on device '{device}'.")
                self.model = SentenceTransformer(
                    'all-MiniLM-L6-v2',
                    cache_folder=str(self.cache_dir),
                    local_files_only=True,
                    device=device
                )
                logger.critical(f"INIT_STEP_003: SentenceTransformer model loaded successfully.")
                break  # Successfully loaded the model
            except NotImplementedError as e:
                if "Cannot copy out of meta tensor" in str(e):
                    # This is likely a resource contention issue
                    retry_count += 1
                    logger.critical(f"Meta tensor error, retrying ({retry_count}/{max_retries})...")
                    time.sleep(1)  # Wait a bit before retrying
                else:
                    # Some other NotImplementedError
                    raise
            except Exception as e:
                logger.critical(f"Error loading model: {str(e)}")
                raise
        
        if retry_count >= max_retries:
            raise RuntimeError("Failed to load model after multiple attempts. Please restart the application.")
        
        # Initialize DeepSeek API client
        self.client = OpenAI(
            base_url="https://api.deepseek.com",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        logger.critical("--- SemanticSearch Initialization FINISHED Successfully ---")
    
    def optimize_query(self, query: str) -> dict:
        """Optimize query using DeepSeek API with JSON response format"""
        try:
            system_prompt = """You are a professional synthetic biology expert specializing in plasmid design and genome engineering.
            Your task is to optimize search queries for a biological parts database.
            
            Please analyze the input query and return a JSON object with the following structure:
            {
                "original_query": "the input query",
                "optimized_query": "the optimized query in English",
                "explanation": "brief explanation of the optimization",
                "key_terms": ["list", "of", "key", "biological", "terms"],
                "organism": "target organism if specified",
                "part_type": "type of biological part",
                "filters": {
                    "include_types": ["list", "of", "part", "types", "to", "include"],
                    "exclude_types": ["list", "of", "part", "types", "to", "exclude"],
                    "include_sources": ["list", "of", "sources", "to", "include"],
                    "exclude_sources": ["list", "of", "sources", "to", "exclude"]
                }
            }
            
            Requirements:
            1. Keep the optimized query concise and focused on key features
            2. Use proper biological terminology
            3. Always respond in English
            4. Include relevant organism or strain information if present
            5. Identify the type of biological part being searched for
            6. Extract any filtering requirements from the query (e.g., "only promoters", "not from igem")"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]

            # 记录请求内容
            logger.info("\n" + "=" * 50)
            logger.info("QUERY OPTIMIZATION REQUEST")
            logger.info("=" * 50)
            logger.info(f"Query: '{query}'")
            logger.info("=" * 50)
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                response_format={
                    'type': 'json_object'
                },
                temperature=0.3,  # 使用较低的温度以获得更稳定的结果
                max_tokens=500  # 限制输出长度
            )
            
            # 记录语言模型的原始返回内容
            logger.info("\n" + "=" * 50)
            logger.info("RAW LLM RESPONSE")
            logger.info("=" * 50)
            logger.info(json.dumps(response.model_dump(), indent=2))
            logger.info("=" * 50)
            
            # 从响应中提取JSON内容
            content = response.choices[0].message.content
            
            try:
                # 尝试解析JSON响应
                result = json.loads(content)
                
                # 打印详细的优化结果日志
                logger.info("\n" + "=" * 50)
                logger.info("QUERY OPTIMIZATION DETAILS")
                logger.info("=" * 50)
                logger.info(f"Original Query: '{query}'")
                logger.info(f"Optimized Query: '{result.get('optimized_query', query)}'")
                
                if result.get("explanation"):
                    logger.info(f"\nExplanation: {result.get('explanation')}")
                    
                if result.get("key_terms"):
                    logger.info(f"\nKey Terms: {', '.join(result.get('key_terms', []))}")
                    
                if result.get("part_type"):
                    logger.info(f"\nPart Type: {result.get('part_type')}")
                    
                if result.get("organism"):
                    logger.info(f"\nOrganism: {result.get('organism')}")
                
                if result.get("filters"):
                    filters = result.get("filters", {})
                    logger.info("\nFilters:")
                    if filters.get("include_types"):
                        logger.info(f"  Include Types: {', '.join(filters.get('include_types', []))}")
                    if filters.get("exclude_types"):
                        logger.info(f"  Exclude Types: {', '.join(filters.get('exclude_types', []))}")
                    if filters.get("include_sources"):
                        logger.info(f"  Include Sources: {', '.join(filters.get('include_sources', []))}")
                    if filters.get("exclude_sources"):
                        logger.info(f"  Exclude Sources: {', '.join(filters.get('exclude_sources', []))}")
                
                logger.info("=" * 50)
                
                # 返回结果
                return {
                    "status": "success",
                    "original_query": query,
                    "optimized_query": result.get("optimized_query", query),
                    "explanation": result.get("explanation", "Query has been optimized for vector similarity search"),
                    "key_terms": result.get("key_terms", []),
                    "part_type": result.get("part_type", ""),
                    "organism": result.get("organism", ""),
                    "filters": result.get("filters", {
                        "include_types": [],
                        "exclude_types": [],
                        "include_sources": [],
                        "exclude_sources": []
                    })
                }
            except json.JSONDecodeError as e:
                logger.error(f"\nError parsing JSON response: {e}")
                logger.info(f"Raw content: {content}")
                # 如果无法解析JSON，尝试提取优化后的查询
                # 尝试从文本中提取查询
                optimized_query = query
                explanation = "Failed to parse JSON response"
                
                # 尝试从文本中提取可能的优化查询
                if '"optimized_query"' in content:
                    try:
                        # 尝试使用正则表达式提取
                        import re
                        match = re.search(r'"optimized_query"\s*:\s*"([^"]+)"', content)
                        if match:
                            optimized_query = match.group(1)
                    except:
                        pass
                
                return {
                    "status": "partial_success",
                    "original_query": query,
                    "optimized_query": optimized_query,
                    "explanation": explanation,
                    "key_terms": [],
                    "part_type": "",
                    "organism": "",
                    "filters": {
                        "include_types": [],
                        "exclude_types": [],
                        "include_sources": [],
                        "exclude_sources": []
                    }
                }
                
        except Exception as e:
            logger.error(f"Query optimization failed: {str(e)}")
            # 返回错误信息
            return {
                "status": "error",
                "original_query": query,
                "optimized_query": query,  # 失败时使用原始查询
                "explanation": "Failed to optimize query",
                "error_message": str(e),
                "key_terms": [],
                "part_type": "",
                "organism": "",
                "filters": {
                    "include_types": [],
                    "exclude_types": [],
                    "include_sources": [],
                    "exclude_sources": []
                }
            }
        except Exception as e:
            logger.error(f"Query optimization failed: {str(e)}")
            return {
                "status": "error",
                "original_query": query,
                "optimized_query": query,
                "error_message": str(e)
            }
    
    def search(self, query: str, top_k: int = 5, optimize: bool = False, 
              types: list = None, source_collections: list = None) -> dict:
        """Execute semantic search with filters"""
        start_time = time.time()
        response = {
            "query": query,
            "optimize": optimize,
            "top_k": top_k,
            "filters": {
                "types": types,
                "source_collections": source_collections
            },
            "results": []
        }
        
        # Store optimization result for later use
        optimization_result = None
        
        if optimize:
            optimization_result = self.optimize_query(query)
            response["optimization"] = optimization_result
            
            if optimization_result["status"] == "success":
                # 只使用优化后的查询文本，不使用过滤条件
                query = optimization_result["optimized_query"]
                
                # 记录部件类型和生物体信息（仅用于日志记录）
                part_type = optimization_result.get("part_type", "")
                organism = optimization_result.get("organism", "")
                if part_type or organism:
                    logger.info(f"\nDetected context: Part Type={part_type}, Organism={organism}")
                    logger.info("Note: Using vector similarity search instead of explicit filtering")
        
        # Calculate query vector
        query_embedding = self.model.encode([query])[0]
        
        # Build query conditions
        where = []
        if types:
            type_conditions = []
            for t in types:
                # Use different matching rules based on source_collection
                if source_collections and 'igem' in source_collections:
                    # igem data uses type_level_1 and type_level_2
                    if t.lower() == 'promoter':
                        type_conditions.extend([
                            "type_level_1 = 'DNA Elements'",
                            "type_level_2 = 'Regulatory'",
                            "name LIKE '%promoter%'"
                        ])
                    else:
                        type_conditions.extend([
                            f"type_level_1 = '{t}'",
                            f"type_level_2 = '{t}'"
                        ])
                else:
                    # Other data uses type field
                    type_conditions.append(f"type = '{t}'")
            where.append(f"({' OR '.join(type_conditions)})")
            
        if source_collections:
            source_list = ", ".join([f"'{s}'" for s in source_collections])
            where.append(f"source_collection IN ({source_list})")
        
        # Handle exclusion conditions from optimization
        if optimize and optimization_result and optimization_result["status"] == "success":
            filters = optimization_result.get("filters", {})
            
            # Handle excluded sources
            if filters.get("exclude_sources"):
                exclude_sources = [self.source_mapping.get(s.lower(), s) for s in filters["exclude_sources"]]
                source_list = ", ".join([f"'{s}'" for s in exclude_sources])
                where.append(f"source_collection NOT IN ({source_list})")
                
            # Handle excluded types
            if filters.get("exclude_types"):
                exclude_conditions = []
                for t in filters["exclude_types"]:
                    exclude_conditions.append(f"type != '{t}'")
                    exclude_conditions.append(f"type_level_1 != '{t}'")
                    exclude_conditions.append(f"type_level_2 != '{t}'")
                where.append(f"({' AND '.join(exclude_conditions)})")
        
        # Execute search
        if where:
            where_clause = " AND ".join(where)
            logger.info(f"\nDebug - SQL where clause: {where_clause}")
            results = self.table.search(query_embedding).where(where_clause).limit(top_k).to_list()
        else:
            results = self.table.search(query_embedding).limit(top_k).to_list()
        
        # 打印搜索结果详情
        logger.info("\n" + "=" * 50)
        logger.info("SEARCH RESULTS DETAILS")
        logger.info("=" * 50)
        logger.info(f"Final Query Used: '{query}'")
        logger.info(f"Number of Results: {len(results)}")
        
        # 添加结果到响应
        for i, result in enumerate(results, 1):
            # 打印每个结果的详细信息
            logger.info(f"\nResult #{i}:")
            logger.info(f"  Name: {result['name']}")
            logger.info(f"  Type: {result['type']}")
            logger.info(f"  Source: {result.get('source_collection', 'Unknown')}")
            logger.info(f"  Similarity: {float(result['_distance']):.4f}")
            
            # 添加到响应对象
            response["results"].append({
                'name': result['name'],
                'type': result['type'],
                'description': result['description'],
                'source_collection': result.get('source_collection', ''),
                'source_name': result.get('source_name', ''),
                'similarity': float(result['_distance'])
            })
        
        logger.info("=" * 50)
        logger.info(f"Search completed in {time.time() - start_time:.2f} seconds")
        return response
    
    def ask_question(self, question: str, top_k: int = 5, chat_history: list = None, stream_handler=None, temp_parts_data=None, temp_parts_embeddings=None) -> dict:
        """Answer questions based on the biological parts database, considering chat history.
        
        Args:
            question: The user's question
            top_k: Number of relevant parts to retrieve
            chat_history: Previous conversation history
            stream_handler: Optional callback function to handle streaming responses
            temp_parts_data: Optional list of temporary parts data uploaded by the user
            temp_parts_embeddings: Optional list of embeddings for temporary parts
        """
        start_time = time.time()
        
        # 1. Convert current question to vector for database search
        question_embedding = self.model.encode([question])[0]
        
        # 2. Search for relevant parts
        if temp_parts_data and temp_parts_embeddings and len(temp_parts_data) == len(temp_parts_embeddings):
            # 2a. If temporary parts are provided, use them for search
            logger.info(f"Using {len(temp_parts_data)} temporary uploaded parts for search")
            
            # Calculate similarity scores between question and each temporary part
            similarities = []
            for i, embedding in enumerate(temp_parts_embeddings):
                # Calculate cosine similarity
                similarity = np.dot(question_embedding, embedding) / (np.linalg.norm(question_embedding) * np.linalg.norm(embedding))
                similarities.append((i, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Take top_k results
            top_results = similarities[:top_k]
            
            # Prepare results in the expected format
            results = []
            for idx, similarity in top_results:
                part = temp_parts_data[idx]
                result = {
                    "name": part["name"],
                    "type": part["type"],
                    "description": part["description"],
                    "source_collection": part["source"],
                    "similarity": similarity
                }
                results.append(result)
        else:
            # 2b. Otherwise, use the database search
            results = self.table.search(question_embedding).limit(top_k).to_list()
        
        # 3. Build context from retrieved parts
        context_parts = []
        for result in results:
            context_parts.append(
                f"Part Name: {result['name']}\n"
                f"Type: {result['type']}\n"
                f"Source: {result.get('source_collection', 'Unknown')}\n"
                f"Description: {result['description']}\n"
            )
        
        db_context = "\n\n".join(context_parts)
        
        # 4. Prepare messages for DeepSeek API
        # System prompt (unchanged)
        system_message = {
            "role": "system", 
            "content": "You are a professional synthetic biology assistant specialized in explaining biological parts and their functions. Provide accurate, scientific answers based only on the information provided from the database context. If the user asks a follow-up question, use the provided chat history to understand the context of their current question."
        }
        
        # Initialize messages list with system prompt
        api_messages = [system_message]
        
        # Add chat history if provided
        if chat_history:
            for historical_message in chat_history:
                # Ensure we only pass 'role' and 'content' from history
                api_messages.append({
                    "role": historical_message.get("role"),
                    "content": historical_message.get("content")
                })
        
        # Construct the user prompt with database context and current question
        user_prompt_content = f"""Here is information about biological parts relevant to the current question:

{db_context}

Based on the information above, AND considering our previous conversation if relevant, please answer the following question: {question}

If you cannot find the answer in the provided information, please state that you cannot answer and suggest that the user try a different question or provide more details.
"""
        
        api_messages.append({"role": "user", "content": user_prompt_content})
        
        # Debug printing (can be removed in production)
        logger.info("\n" + "=" * 50)
        logger.info("QUESTION ANSWERING WITH HISTORY")
        logger.info("=" * 50)
        logger.info(f"Current Question: '{question}'")
        logger.info(f"Using {len(results)} relevant parts as DB context")
        if chat_history:
            logger.info(f"Including {len(chat_history)} messages from chat history.")
        logger.info(f"API Messages Payload: {api_messages}")
        logger.info("=" * 50)
        
        # 处理流式响应
        if stream_handler:
            # 使用流式模式
            logger.info("Using streaming mode for response generation")
            full_answer = ""
            
            # 创建流式响应
            stream_response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=api_messages,
                temperature=0.3,
                max_tokens=1000,
                stream=True  # 启用流式响应
            )
            
            # 处理流式响应
            for chunk in stream_response:
                if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    if content:
                        full_answer += content
                        # 调用回调函数处理流式内容
                        stream_handler(content)
            
            answer = full_answer
        else:
            # 使用非流式模式
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=api_messages,
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
        
        # Sample sequences for different part types (for visualization demo)
        sample_sequences = {
            "promoter": "TTGACAATTAATCATCGGCTCGTATAATGTGTGGAATTGTGAGCGGATAACAATTTCACACAGGAAACAGCTATGACCATGATTACGGATTCACTGGCCGTCGTTTTACAACGTCGTGACTGGGAAAACCCTGGCGTTACCCAACTTAATCGCCTTGCAGCACATCCCC",
            "terminator": "CGCATAACCCTTGGGGCCTCTAAACGGGTCTTGAGGGGTTTTTTGCTGAAAGGAGGAACTATATGCGCTCATACGATATGAACGTTGAGACTGCCGCTGAGTTATCAGCTGTGAACGACATTCTGGCGTCTATCGGTGAACCTCCGGTATCAACGCTGGAAGGTGACGCTAACGCAGATGCAGCGAACGCTCGGCGTATTCTCAACAAGATTAACCGACAGATTCAA",
            "RBS": "AGGAGGAAAAACATATGAAACGCAAGAGCTTCAACGAGCGCCTGCAGAAAGCCGGCGAAGCGCTGCGCGAAGCGCTGCGTGAAGAGCTGCGTGCGGCGCGTCTGCGTGCGGCGCGTCGTGCGGCGAAACGTCTGCGTGCGGCGAAACGTCTGCGTGCGGCGCGTCGTGCGGCGAAACGTCTGCGTGCGGCGAAACGTCTGCGTGCGGCGCGTCGTGCGGCGAAACGTCTGCGTGCGGCGAAACGT",
            "CDS": "ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAGTTCAGCGTGTCCGGCGAGGGCGAGGGCGATGCCACCTACGGCAAGCTGACCCTGAAGTTCATCTGCACCACCGGCAAGCTGCCCGTGCCCTGGCCCACCCTCGTGACCACCCTGACCTACGGCGTGCAGTGCTTCAGCCGCTACCCCGACCACATGAAGCAGCACGACTTCTTCAAGTCCGCCATGCCCGAAGGCTACGTCCAGGAGCGCACCATCTTCTTCAAGGACGACGGCAACTACAAGACCCGCGCCGAGGTGAAGTTCGAGGGCGACACCCTGGTGAACCGCATCGAGCTGAAGGGCATCGACTTCAAGGAGGACGGCAACATCCTGGGGCACAAGCTGGAGTACAACTACAACAGCCACAACGTCTATATCATGGCCGACAAGCAGAAGAACGGCATCAAGGTGAACTTCAAGATCCGCCACAACATCGAGGACGGCAGCGTGCAGCTCGCCGACCACTACCAGCAGAACACCCCCATCGGCGACGGCCCCGTGCTGCTGCCCGACAACCACTACCTGAGCACCCAGTCCGCCCTGAGCAAAGACCCCAACGAGAAGCGCGATCACATGGTCCTGCTGGAGTTCGTGACCGCCGCCGGGATCACTCTCGGCATGGACGAGCTGTACAAGTAA",
            "origin": "TTAATTAATTTAAATTTACCTTTAATTAAATTAATTAATTCGATACCCAGCTGGCAATTCCGACGTCTAAGAAACCATTATTATCATGACATTAACCTATAAAAATAGGCGTATCACGAGGCAGAATTTCAGATAAAAAAAATCCTTAGCTTTCGCTAAGGATGATTTCTGCACCTGCACCAGTCAGTAAAACGACGGCCAGTAGTCAAAAGCCTCCGACCGGAGGCTTTTGACTTGGTTCAGGTGGAGTGGGAG",
            "plasmid": "GACGGATCGGGAGATCTCCCGATCCCCTATGGTGCACTCTCAGTACAATCTGCTCTGATGCCGCATAGTTAAGCCAGTATCTGCTCCCTGCTTGTGTGTTGGAGGTCGCTGAGTAGTGCGCGAGCAAAATTTAAGCTACAACAAGGCAAGGCTTGACCGACAATTGCATGAAGAATCTGCTTAGGGTTAGGCGTTTTGCGCTGCTTCGCGATGTACGGGCCAGATATACGCGTTGACATTGATTATTGACTAGTTATTAATAGTAATCAATTACGGGGTCATTAGTTCATAGCCCATATATGGAGTTCCGCGTTACATAACTTACGGTAAATGGCCCGCCTGGCTGACCGCCCAACGACCCCCGCCCATTGACGTCAATAATGACGTATGTTCCCATAGTAACGCCAATAGGGACTTTCCATTGACGTCAATGGGTGGAGTATTTACGGTAAACTGCCCACTTGGCAGTACATCAAGTGTATCATATGCCAAGTACGCCCCCTATTGACGTCAATGACGGTAAATGGCCCGCCTGGCATTATGCCCAGTACATGACCTTATGGGACTTTCCTACTTGGCAGTACATCTACGTATTAGTCATCGCTATTACCATGGTGATGCGGTTTTGGCAGTACATCAATGGGCGTGGATAGCGGTTTGACTCACGGGGATTTCCAAGTCTCCACCCCATTGACGTCAATGGGAGTTTGTTTTGGCACCAAAATCAACGGGACTTTCCAAAATGTCGTAACAACTCCGCCCCATTGACGCAAATGGGCGGTAGGCGTGTACGGTGGGAGGTCTATATAAGCAGAGCTCTCTGGCTAACTAGAGAACCCACTGCTTAACTGGCTTATCGAAATTAATACGACTCACTATAGGGAGACCCAAGCTGGCTAGCGTTTAAACTTAAGCTTGGTACCGAGCTCGGATCCACTAGTCCAGTGTGGTGGAATTCTGCAGATATCCAGCACAGTGGCGGCCGCTCGAGTCTAGAGGGCCCGTTTAAACCCGCTGATCAGCCTCGACTGTGCCTTCTAGTTGCCAGCCATCTGTTGTTTGCCCCTCCCCCGTGCCTTCCTTGACCCTGGAAGGTGCCACTCCCACTGTCCTTTCCTAATAAAATGAGGAAATTGCATCGCATTGTCTGAGTAGGTGTCATTCTATTCTGGGGGGTGGGGTGGGGCAGGACAGCAAGGGGGAGGATTGGGAAGACAATAGCAGGCATGCTGGGGATGCGGTGGGCTCTATGGCTTCTGAGGCGGAAAGAACCAGCTGGGGCTCTAGGGGGTATCCCCACGCGCCCTGTAGCGGCGCATTAAGCGCGGCGGGTGTGGTGGTTACGCGCAGCGTGACCGCTACACTTGCCAGCGCCCTAGCGCCCGCTCCTTTCGCTTTCTTCCCTTCCTTTCTCGCCACGTTCGCCGGCTTTCCCCGTCAAGCTCTAAATCGGGGGCTCCCTTTAGGGTTCCGATTTAGTGCTTTACGGCACCTCGACCCCAAAAAACTTGATTAGGGTGATGGTTCACGTAGTGGGCCATCGCCCTGATAGACGGTTTTTCGCCCTTTGACGTTGGAGTCCACGTTCTTTAATAGTGGACTCTTGTTCCAAACTGGAACAACACTCAACCCTATCTCGGTCTATTCTTTTGATTTATAAGGGATTTTGCCGATTTCGGCCTATTGGTTAAAAAATGAGCTGATTTAACAAAAATTTAACGCGAATTAATTCTGTGGAATGTGTGTCAGTTAGGGTGTGGAAAGTCCCCAGGCTCCCCAGCAGGCAGAAGTATGCAAAGCATGCATCTCAATTAGTCAGCAACCAGGTGTGGAAAGTCCCCAGGCTCCCCAGCAGGCAGAAGTATGCAAAGCATGCATCTCAATTAGTCAGCAACCATAGTCCCGCCCCTAACTCCGCCCATCCCGCCCCTAACTCCGCCCAGTTCCGCCCATTCTCCGCCCCATGGCTGACTAATTTTTTTTATTTATGCAGAGGCCGAGGCCGCCTCTGCCTCTGAGCTATTCCAGAAGTAGTGAGGAGGCTTTTTTGGAGGCCTAGGCTTTTGCAAAAAGCTCCCGGGAGCTTGTATATCCATTTTCGGATCTGATCAAGAGACAGGATGAGGATCGTTTCGCATGATTGAACAAGATGGATTGCACGCAGGTTCTCCGGCCGCTTGGGTGGAGAGGCTATTCGGCTATGACTGGGCACAACAGACAATCGGCTGCTCTGATGCCGCCGTGTTCCGGCTGTCAGCGCAGGGGCGCCCGGTTCTTTTTGTCAAGACCGACCTGTCCGGTGCCCTGAATGAACTGCAGGACGAGGCAGCGCGGCTATCGTGGCTGGCCACGACGGGCGTTCCTTGCGCAGCTGTGCTCGACGTTGTCACTGAAGCGGGAAGGGACTGGCTGCTATTGGGCGAAGTGCCGGGGCAGGATCTCCTGTCATCTCACCTTGCTCCTGCCGAGAAAGTATCCATCATGGCTGATGCAATGCGGCGGCTGCATACGCTTGATCCGGCTACCTGCCCATTCGACCACCAAGCGAAACATCGCATCGAGCGAGCACGTACTCGGATGGAAGCCGGTCTTGTCGATCAGGATGATCTGGACGAAGAGCATCAGGGGCTCGCGCCAGCCGAACTGTTCGCCAGGCTCAAGGCGCGCATGCCCGACGGCGAGGATCTCGTCGTGACCCATGGCGATGCCTGCTTGCCGAATATCATGGTGGAAAATGGCCGCTTTTCTGGATTCATCGACTGTGGCCGGCTGGGTGTGGCGGACCGCTATCAGGACATAGCGTTGGCTACCCGTGATATTGCTGAAGAGCTTGGCGGCGAATGGGCTGACCGCTTCCTCGTGCTTTACGGTATCGCCGCTCCCGATTCGCAGCGCATCGCCTTCTATCGCCTTCTTGACGAGTTCTTCTGAGCGGGACTCTGGGGTTCGAAATGACCGACCAAGCGACGCCCAACCTGCCATCACGAGATTTCGATTCCACCGCCGCCTTCTATGAAAGGTTGGGCTTCGGAATCGTTTTCCGGGACGCCGGCTGGATGATCCTCCAGCGCGGGGATCTCATGCTGGAGTTCTTCGCCCACCCCAACTTGTTTATTGCAGCTTATAATGGTTACAAATAAAGCAATAGCATCACAAATTTCACAAATAAAGCATTTTTTTCACTGCATTCTAGTTGTGGTTTGTCCAAACTCATCAATGTATCTTATCATGTCTGTATACCGTCGACCTCTAGCTAGAGCTTGGCGTAATCATGGTCATAGCTGTTTCCTGTGTGAAATTGTTATCCGCTCACAATTCCACACAACATACGAGCCGGAAGCATAAAGTGTAAAGCCTGGGGTGCCTAATGAGTGAGCTAACTCACATTAATTGCGTTGCGCTCACTGCCCGCTTTCCAGTCGGGAAACCTGTCGTGCCAGCTGCATTAATGAATCGGCCAACGCGCGGGGAGAGGCGGTTTGCGTATTGGGCGCTCTTCCGCTTCCTCGCTCACTGACTCGCTGCGCTCGGTCGTTCGGCTGCGGCGAGCGGTATCAGCTCACTCAAAGGCGGTAATACGGTTATCCACAGAATCAGGGGATAACGCAGGAAAGAACATGTGAGCAAAAGGCCAGCAAAAGGCCAGGAACCGTAAAAAGGCCGCGTTGCTGGCGTTTTTCCATAGGCTCCGCCCCCCTGACGAGCATCACAAAAATCGACGCTCAAGTCAGAGGTGGCGAAACCCGACAGGACTATAAAGATACCAGGCGTTTCCCCCTGGAAGCTCCCTCGTGCGCTCTCCTGTTCCGACCCTGCCGCTTACCGGATACCTGTCCGCCTTTCTCCCTTCGGGAAGCGTGGCGCTTTCTCAATGCTCACGCTGTAGGTATCTCAGTTCGGTGTAGGTCGTTCGCTCCAAGCTGGGCTGTGTGCACGAACCCCCCGTTCAGCCCGACCGCTGCGCCTTATCCGGTAACTATCGTCTTGAGTCCAACCCGGTAAGACACGACTTATCGCCACTGGCAGCAGCCACTGGTAACAGGATTAGCAGAGCGAGGTATGTAGGCGGTGCTACAGAGTTCTTGAAGTGGTGGCCTAACTACGGCTACACTAGAAGGACAGTATTTGGTATCTGCGCTCTGCTGAAGCCAGTTACCTTCGGAAAAAGAGTTGGTAGCTCTTGATCCGGCAAACAAACCACCGCTGGTAGCGGTTTTTTTGTTTGCAAGCAGCAGATTACGCGCAGAAAAAAAGGATCTCAAGAAGATCCTTTGATCTTTTCTACGGGGTCTGACGCTCAGTGGAACGAAAACTCACGTTAAGGGATTTTGGTCATGAGATTATCAAAAAGGATCTTCACCTAGATCCTTTTAAATTAAAAATGAAGTTTTAAATCAATCTAAAGTATATATGAGTAAACTTGGTCTGACAGTTACCAATGCTTAATCAGTGAGGCACCTATCTCAGCGATCTGTCTATTTCGTTCATCCATAGTTGCCTGACTCCCCGTCGTGTAGATAACTACGATACGGGAGGGCTTACCATCTGGCCCCAGTGCTGCAATGATACCGCGAGACCCACGCTCACCGGCTCCAGATTTATCAGCAATAAACCAGCCAGCCGGAAGGGCCGAGCGCAGAAGTGGTCCTGCAACTTTATCCGCCTCCATCCAGTCTATTAATTGTTGCCGGGAAGCTAGAGTAAGTAGTTCGCCAGTTAATAGTTTGCGCAACGTTGTTGCCATTGCTACAGGCATCGTGGTGTCACGCTCGTCGTTTGGTATGGCTTCATTCAGCTCCGGTTCCCAACGATCAAGGCGAGTTACATGATCCCCCATGTTGTGCAAAAAAGCGGTTAGCTCCTTCGGTCCTCCGATCGTTGTCAGAAGTAAGTTGGCCGCAGTGTTATCACTCATGGTTATGGCAGCACTGCATAATTCTCTTACTGTCATGCCATCCGTAAGATGCTTTTCTGTGACTGGTGAGTACTCAACCAAGTCATTCTGAGAATAGTGTATGCGGCGACCGAGTTGCTCTTGCCCGGCGTCAATACGGGATAATACCGCGCCACATAGCAGAACTTTAAAAGTGCTCATCATTGGAAAACGTTCTTCGGGGCGAAAACTCTCAAGGATCTTACCGCTGTTGAGATCCAGTTCGATGTAACCCACTCGTGCACCCAACTGATCTTCAGCATCTTTTACTTTCACCAGCGTTTCTGGGTGAGCAAAAACAGGAAGGCAAAATGCCGCAAAAAAGGGAATAAGGGCGACACGGAAATGTTGAATACTCATACTCTTCCTTTTTCAATATTATTGAAGCATTTATCAGGGTTATTGTCTCATGAGCGGATACATATTTGAATGTATTTAGAAAAATAAACAAATAGGGGTTCCGCGCACATTTCCCCGAAAAGTGCCACCTGACGTC"
        }
        
        # 5. Return results
        result = {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "name": result["name"],
                    "type": result["type"],
                    "source": result.get("source_collection", "Unknown"),
                    "similarity": float(result["_distance"]),
                    # Add sample sequence based on part type for visualization
                    "sequence": sample_sequences.get(result["type"].lower(), sample_sequences.get("plasmid")),
                    "description": result.get("description", "")
                } for result in results
            ],
            "execution_time": time.time() - start_time
        }
            
        logger.info(f"Question answered in {result['execution_time']:.2f} seconds")
        return result

def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(description='Biological Parts Semantic Search Tool')
    parser.add_argument('query', type=str, help='Search query text')
    parser.add_argument('--top_k', type=int, default=5, help='Number of results to return (default: 5)')
    parser.add_argument('--output', type=str, help='Output file path (optional)')
    parser.add_argument('--optimize', action='store_true', help='Use DeepSeek to optimize query')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--type', nargs='+', help='Filter by part type (e.g., --type promoter terminator)')
    parser.add_argument('--source', nargs='+', help='Filter by source collection (e.g., --source igem addgene)')
    
    args = parser.parse_args()
    
    # Switch to project root directory
    root_dir = Path(__file__).parent.parent.parent
    os.chdir(root_dir)
    
    searcher = SemanticSearch()
    results = searcher.search(
        args.query, 
        top_k=args.top_k, 
        optimize=args.optimize,
        types=args.type,
        source_collections=args.source
    )
    
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        if args.optimize and "optimization" in results:
            opt = results["optimization"]
            if opt != results["query"]:
                print(f"\nOriginal query: {results['query']}")
                print(f"Optimized query: {opt}")
            else:
                print(f"\nQuery optimization failed: {opt}")
        
        print("\nSearch Results:")
        for i, result in enumerate(results["results"], 1):
            print(f"\n{i}. Similarity: {result['similarity']:.4f}")
            print(f"Name: {result['name']}")
            print(f"Type: {result['type']}")
            if result.get('source_collection'):
                print(f"Source: {result['source_collection']}")
            print(f"Description: {result['description'][:200]}...")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {args.output}")
    
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()