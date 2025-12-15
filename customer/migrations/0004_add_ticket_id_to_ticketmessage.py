# Generated manually to fix missing ticket_id column in customer_ticketmessage table
# This migration adds the column directly to the database since the state already has it

from django.db import connection, migrations


def add_ticket_column_forward(apps, schema_editor):
    """Add ticket_id column to customer_ticketmessage table"""
    with connection.cursor() as cursor:
        # Check if column already exists (SQLite doesn't support IF NOT EXISTS in ALTER TABLE)
        cursor.execute("PRAGMA table_info(customer_ticketmessage)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'ticket_id' not in columns:
            # Add the column (SQLite syntax - for other DBs, this would need to be adjusted)
            cursor.execute("ALTER TABLE customer_ticketmessage ADD COLUMN ticket_id INTEGER NULL;")


def add_ticket_column_reverse(apps, schema_editor):
    """Remove ticket_id column - SQLite doesn't support DROP COLUMN easily"""
    # SQLite doesn't easily support DROP COLUMN, so we'll leave it
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0003_add_user_id_to_review'),
    ]

    operations = [
        migrations.RunPython(add_ticket_column_forward, add_ticket_column_reverse),
    ]

