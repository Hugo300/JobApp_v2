"""
Database migration script to remove skills and industry-related tables and columns
Run this script to clean up the database after removing skills functionality
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Simple Flask app for migration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def check_table_exists(connection, table_name):
    """Check if a table exists in the database"""
    result = connection.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
    ), {"table_name": table_name})
    return result.fetchone() is not None

def check_column_exists(connection, table_name, column_name):
    """Check if a column exists in a table"""
    result = connection.execute(text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result]
    return column_name in columns

def drop_table_if_exists(connection, table_name):
    """Drop a table if it exists"""
    if check_table_exists(connection, table_name):
        connection.execute(text(f"DROP TABLE {table_name}"))
        print(f"✓ Dropped table: {table_name}")
        return True
    else:
        print(f"  Table {table_name} does not exist, skipping")
        return False

def remove_column_if_exists(connection, table_name, column_name):
    """Remove a column from a table if it exists (SQLite limitation workaround)"""
    if not check_table_exists(connection, table_name):
        print(f"  Table {table_name} does not exist, skipping column removal")
        return False
        
    if not check_column_exists(connection, table_name, column_name):
        print(f"  Column {column_name} does not exist in {table_name}, skipping")
        return False
    
    print(f"✓ Found column {column_name} in {table_name}")
    
    # For SQLite, we need to recreate the table without the column
    # This is a simplified approach - in production, you'd want to preserve all data
    if table_name == 'job_application' and column_name in ['extracted_skills', 'industry_id']:
        # Get current table structure
        result = connection.execute(text(f"PRAGMA table_info({table_name})"))
        columns = []
        for row in result:
            col_name = row[1]
            col_type = row[2]
            col_notnull = row[3]
            col_default = row[4]
            col_pk = row[5]
            
            # Skip the column we want to remove
            if col_name == column_name:
                continue
                
            col_def = f"{col_name} {col_type}"
            if col_pk:
                col_def += " PRIMARY KEY"
            elif col_notnull:
                col_def += " NOT NULL"
            if col_default is not None:
                col_def += f" DEFAULT {col_default}"
                
            columns.append(col_def)
        
        if columns:
            # Create new table without the column
            new_table_sql = f"CREATE TABLE {table_name}_new ({', '.join(columns)})"
            connection.execute(text(new_table_sql))
            
            # Copy data (excluding the removed column)
            result = connection.execute(text(f"PRAGMA table_info({table_name})"))
            remaining_columns = [row[1] for row in result if row[1] != column_name]
            
            if remaining_columns:
                columns_str = ', '.join(remaining_columns)
                connection.execute(text(f"""
                    INSERT INTO {table_name}_new ({columns_str})
                    SELECT {columns_str} FROM {table_name}
                """))
            
            # Drop old table and rename new one
            connection.execute(text(f"DROP TABLE {table_name}"))
            connection.execute(text(f"ALTER TABLE {table_name}_new RENAME TO {table_name}"))
            
            print(f"✓ Removed column {column_name} from {table_name}")
            return True
    
    elif table_name == 'user_data' and column_name == 'skills':
        # Similar process for user_data table
        result = connection.execute(text(f"PRAGMA table_info({table_name})"))
        columns = []
        for row in result:
            col_name = row[1]
            col_type = row[2]
            col_notnull = row[3]
            col_default = row[4]
            col_pk = row[5]
            
            # Skip the skills column
            if col_name == 'skills':
                continue
                
            col_def = f"{col_name} {col_type}"
            if col_pk:
                col_def += " PRIMARY KEY"
            elif col_notnull:
                col_def += " NOT NULL"
            if col_default is not None:
                col_def += f" DEFAULT {col_default}"
                
            columns.append(col_def)
        
        if columns:
            # Create new table without the skills column
            new_table_sql = f"CREATE TABLE {table_name}_new ({', '.join(columns)})"
            connection.execute(text(new_table_sql))
            
            # Copy data (excluding the skills column)
            result = connection.execute(text(f"PRAGMA table_info({table_name})"))
            remaining_columns = [row[1] for row in result if row[1] != 'skills']
            
            if remaining_columns:
                columns_str = ', '.join(remaining_columns)
                connection.execute(text(f"""
                    INSERT INTO {table_name}_new ({columns_str})
                    SELECT {columns_str} FROM {table_name}
                """))
            
            # Drop old table and rename new one
            connection.execute(text(f"DROP TABLE {table_name}"))
            connection.execute(text(f"ALTER TABLE {table_name}_new RENAME TO {table_name}"))
            
            print(f"✓ Removed column {column_name} from {table_name}")
            return True
    
    return False

def remove_skills_and_industry_data():
    """Remove all skills and industry-related tables and columns"""
    print("Removing skills and industry-related database objects...")
    
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                # Start a transaction
                trans = connection.begin()
                
                try:
                    # Tables to drop (in order to handle foreign key constraints)
                    tables_to_drop = [
                        'category_item',
                        'category', 
                        'skill_blacklist'
                    ]
                    
                    # Drop tables
                    dropped_tables = 0
                    for table in tables_to_drop:
                        if drop_table_if_exists(connection, table):
                            dropped_tables += 1
                    
                    # Remove columns from existing tables
                    removed_columns = 0
                    
                    # Remove extracted_skills column from job_application
                    if remove_column_if_exists(connection, 'job_application', 'extracted_skills'):
                        removed_columns += 1
                    
                    # Remove industry_id column from job_application  
                    if remove_column_if_exists(connection, 'job_application', 'industry_id'):
                        removed_columns += 1
                    
                    # Remove skills column from user_data
                    if remove_column_if_exists(connection, 'user_data', 'skills'):
                        removed_columns += 1
                    
                    # Commit the transaction
                    trans.commit()
                    
                    print(f"\n✓ Successfully removed {dropped_tables} tables and {removed_columns} columns")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            print(f"✗ Error removing skills and industry data: {str(e)}")
            return False

def verify_cleanup():
    """Verify that the cleanup was successful"""
    print("\nVerifying cleanup...")
    
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                # Check that tables were removed
                tables_to_check = ['category', 'category_item', 'skill_blacklist']
                for table in tables_to_check:
                    if check_table_exists(connection, table):
                        print(f"✗ Table {table} still exists")
                        return False
                    else:
                        print(f"✓ Table {table} successfully removed")
                
                # Check that columns were removed
                columns_to_check = [
                    ('job_application', 'extracted_skills'),
                    ('job_application', 'industry_id'),
                    ('user_data', 'skills')
                ]
                
                for table, column in columns_to_check:
                    if check_table_exists(connection, table):
                        if check_column_exists(connection, table, column):
                            print(f"✗ Column {column} still exists in {table}")
                            return False
                        else:
                            print(f"✓ Column {column} successfully removed from {table}")
                    else:
                        print(f"  Table {table} does not exist")
                
                # Show remaining table structures
                print("\nRemaining table structures:")
                for table in ['job_application', 'user_data']:
                    if check_table_exists(connection, table):
                        result = connection.execute(text(f"PRAGMA table_info({table})"))
                        columns = [row[1] for row in result]
                        print(f"  {table}: {', '.join(columns)}")
                
                return True
                
        except Exception as e:
            print(f"✗ Error verifying cleanup: {str(e)}")
            return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("JobApp_v2 - Remove Skills and Industry Migration")
    print("=" * 60)
    
    # Remove skills and industry data
    success = remove_skills_and_industry_data()
    
    if success:
        # Verify the cleanup
        success = verify_cleanup()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("All skills and industry-related database objects have been removed.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ Migration failed!")
        print("Please check the errors above and try again.")
        print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
