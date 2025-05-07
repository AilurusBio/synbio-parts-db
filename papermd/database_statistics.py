import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from contextlib import contextmanager
import logging
from datetime import datetime

# Configure logging and plotting style
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12

# Create figures directory
FIGURE_DIR = Path("papermd/figures")
FIGURE_DIR.mkdir(exist_ok=True)

@contextmanager
def get_connection():
    """Create a database connection context manager"""
    conn = None
    try:
        db_path = Path("streamlit_version/data/parts.db")
        conn = sqlite3.connect(db_path)
        yield conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        yield None
    finally:
        if conn is not None:
            conn.close()

def get_basic_stats():
    """Get basic database statistics"""
    with get_connection() as conn:
        if conn is None:
            return None
        
        cursor = conn.cursor()
        stats = {}
        
        # Get total parts
        cursor.execute("SELECT COUNT(*) FROM parts")
        stats["total_parts"] = cursor.fetchone()[0]
        
        # Get type statistics
        cursor.execute("SELECT DISTINCT type_level_1 FROM parts WHERE type_level_1 IS NOT NULL")
        stats["categories"] = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT type_level_2 FROM parts WHERE type_level_2 IS NOT NULL")
        stats["sub_types"] = [row[0] for row in cursor.fetchall()]
        
        # Get source statistics
        cursor.execute("SELECT DISTINCT source_collection FROM parts WHERE source_collection IS NOT NULL")
        stats["sources"] = [row[0] for row in cursor.fetchall()]
        
        return stats

def get_sequence_stats():
    """Get sequence statistics"""
    with get_connection() as conn:
        if conn is None:
            return None
        
        cursor = conn.cursor()
        
        # Get sequence length statistics
        cursor.execute("""
            SELECT 
                MIN(LENGTH(sequence)) as min_length,
                MAX(LENGTH(sequence)) as max_length,
                AVG(LENGTH(sequence)) as avg_length,
                COUNT(*) as total_sequences
            FROM parts 
            WHERE sequence IS NOT NULL
        """)
        return cursor.fetchone()

def get_type_distribution():
    """Get type distribution statistics"""
    with get_connection() as conn:
        if conn is None:
            return None
        
        query = """
            SELECT 
                type_level_1,
                COUNT(*) as count,
                AVG(LENGTH(sequence)) as avg_length,
                MIN(LENGTH(sequence)) as min_length,
                MAX(LENGTH(sequence)) as max_length
            FROM parts 
            WHERE type_level_1 IS NOT NULL
            GROUP BY type_level_1
            ORDER BY count DESC
        """
        return pd.read_sql_query(query, conn)

def get_source_stats():
    """Get source statistics"""
    with get_connection() as conn:
        if conn is None:
            return None
        
        query = """
            SELECT 
                source_collection,
                COUNT(*) as count,
                COUNT(DISTINCT type_level_1) as type_count,
                AVG(LENGTH(sequence)) as avg_length
            FROM parts 
            WHERE source_collection IS NOT NULL
            GROUP BY source_collection
            ORDER BY count DESC
        """
        return pd.read_sql_query(query, conn)

def plot_type_distribution(type_dist):
    """Generate type distribution plots"""
    # Pie chart of part types
    plt.figure(figsize=(12, 8))
    plt.pie(type_dist['count'], labels=type_dist['type_level_1'], autopct='%1.1f%%')
    plt.title('Distribution of Part Types')
    plt.savefig(FIGURE_DIR / 'type_distribution_pie.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Bar plot of average lengths by type
    plt.figure(figsize=(12, 6))
    sns.barplot(data=type_dist, x='type_level_1', y='avg_length')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Part Type')
    plt.ylabel('Average Length (bp)')
    plt.title('Average Sequence Length by Part Type')
    plt.savefig(FIGURE_DIR / 'type_length_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_source_distribution(source_stats):
    """Generate source distribution plots"""
    # Bar plot of part counts by source
    plt.figure(figsize=(12, 6))
    sns.barplot(data=source_stats, x='source_collection', y='count')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Source')
    plt.ylabel('Number of Parts')
    plt.title('Distribution of Parts by Source')
    plt.savefig(FIGURE_DIR / 'source_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Bar plot of type diversity by source
    plt.figure(figsize=(12, 6))
    sns.barplot(data=source_stats, x='source_collection', y='type_count')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Source')
    plt.ylabel('Number of Part Types')
    plt.title('Part Type Diversity by Source')
    plt.savefig(FIGURE_DIR / 'source_type_diversity.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_sequence_length_distribution():
    """Generate sequence length distribution plot"""
    with get_connection() as conn:
        if conn is None:
            return
        
        # Get sequence lengths
        query = "SELECT LENGTH(sequence) as length FROM parts WHERE sequence IS NOT NULL"
        lengths_df = pd.read_sql_query(query, conn)
        
        # Plot histogram
        plt.figure(figsize=(12, 6))
        sns.histplot(data=lengths_df, x='length', bins=50)
        plt.xlabel('Sequence Length (bp)')
        plt.ylabel('Count')
        plt.title('Distribution of Sequence Lengths')
        plt.savefig(FIGURE_DIR / 'sequence_length_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()

def generate_markdown_report():
    """Generate markdown report with all statistics"""
    
    # Get all statistics
    basic_stats = get_basic_stats()
    seq_stats = get_sequence_stats()
    type_dist = get_type_distribution()
    source_stats = get_source_stats()
    
    if not all([basic_stats, seq_stats, type_dist is not None, source_stats is not None]):
        logger.error("Failed to get all required statistics")
        return
    
    # Generate plots
    logger.info("Generating plots...")
    plot_type_distribution(type_dist)
    plot_source_distribution(source_stats)
    plot_sequence_length_distribution()
    
    # Create markdown content
    table_template = r"""# Database Statistics Report
Generated on: {date}

## Overview
- **Total Parts**: {total_parts}
- **Functional Categories**: {categories}
- **Subtypes**: {subtypes}
- **Data Sources**: {sources}

## Sequence Statistics
- **Total Sequences**: {seq_total}
- **Minimum Length**: {seq_min} bp
- **Maximum Length**: {seq_max} bp
- **Average Length**: {seq_avg:.2f} bp

![Sequence Length Distribution](figures/sequence_length_distribution.png)

## Type Distribution
The database contains the following part types:

| Type | Count | Average Length (bp) | Min Length (bp) | Max Length (bp) |
|------|-------|-------------------|----------------|----------------|
{type_table}

![Type Distribution](figures/type_distribution_pie.png)
![Average Length by Type](figures/type_length_distribution.png)

## Source Distribution
Distribution of parts across different sources:

| Source | Part Count | Type Count | Average Length (bp) |
|--------|------------|------------|-------------------|
{source_table}

![Source Distribution](figures/source_distribution.png)
![Type Diversity by Source](figures/source_type_diversity.png)

## Category Details
Main functional categories in the database:
{categories_list}

## Subtype Details
Available subtypes in the database:
{subtypes_list}

## Data Sources
Data is collected from the following sources:
{sources_list}
"""
    
    # Format tables
    type_table = type_dist.apply(lambda row: f"| {row['type_level_1']} | {row['count']} | {row['avg_length']:.2f} | {row['min_length']} | {row['max_length']} |", axis=1).str.cat(sep='\n')
    source_table = source_stats.apply(lambda row: f"| {row['source_collection']} | {row['count']} | {row['type_count']} | {row['avg_length']:.2f} |", axis=1).str.cat(sep='\n')
    
    # Format lists
    categories_list = ', '.join(f"**{cat}**" for cat in basic_stats['categories'])
    subtypes_list = ', '.join(f"**{subtype}**" for subtype in basic_stats['sub_types'])
    sources_list = ', '.join(f"**{source}**" for source in basic_stats['sources'])
    
    # Fill template
    md_content = table_template.format(
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        total_parts=basic_stats['total_parts'],
        categories=len(basic_stats['categories']),
        subtypes=len(basic_stats['sub_types']),
        sources=len(basic_stats['sources']),
        seq_total=seq_stats[3],
        seq_min=seq_stats[0],
        seq_max=seq_stats[1],
        seq_avg=seq_stats[2],
        type_table=type_table,
        source_table=source_table,
        categories_list=categories_list,
        subtypes_list=subtypes_list,
        sources_list=sources_list
    )
    
    # Save to file
    output_path = Path("papermd/database_statistics.md")
    output_path.write_text(md_content, encoding='utf-8')
    logger.info(f"Statistics report saved to {output_path}")

if __name__ == "__main__":
    generate_markdown_report() 