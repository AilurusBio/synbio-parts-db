import sqlite3
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

def read_sqlite_data():
    db_path = Path(__file__).parent / "parts.db"
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql_query("SELECT * FROM parts", conn)
    conn.close()
    return df

def convert_to_parquet():
    # 读取数据
    df = read_sqlite_data()
    
    # 确保所有列都是字符串类型
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
    
    # 转换为parquet格式
    table = pa.Table.from_pandas(df)
    output_path = Path(__file__).parent / "parts.parquet"
    pq.write_table(table, str(output_path))
    
    print(f"数据已成功转换并保存到: {output_path}")

if __name__ == "__main__":
    convert_to_parquet() 