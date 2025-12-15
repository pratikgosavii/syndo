# Generated manually to fix missing user_id column in customer_review table
# This migration adds the column directly to the database since the state already has it

from django.db import connection, migrations


def add_user_column_forward(apps, schema_editor):
    """Add user_id column to customer_review table"""
    with connection.cursor() as cursor:
        # Check if column already exists (SQLite doesn't support IF NOT EXISTS in ALTER TABLE)
        cursor.execute("PRAGMA table_info(customer_review)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'user_id' not in columns:
            # Add the column (SQLite syntax - for other DBs, this would need to be adjusted)
            cursor.execute("ALTER TABLE customer_review ADD COLUMN user_id INTEGER NULL;")


def add_user_column_reverse(apps, schema_editor):
    """Remove user_id column - SQLite doesn't support DROP COLUMN easily"""
    # SQLite doesn't easily support DROP COLUMN, so we'll leave it
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0002_cart_product_cart_user_favourite_product_and_more'),
    ]

    operations = [
        migrations.RunPython(add_user_column_forward, add_user_column_reverse),
    ]

