import csv
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from peewee import ModelSelect

def export_to_csv(query, filename, fields):
    """
    Export a Peewee query to a CSV file.
    :param query: Peewee ModelSelect query
    :param filename: Output filename
    :param fields: List of field names (strings) to export
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(fields)
            
            # Write data
            for row in query:
                row_data = []
                for field in fields:
                    # Handle nested objects (ForeignKey) or properties
                    val = getattr(row, field, "")
                    # If it's a model instance (ForeignKey), try to get name or id
                    if hasattr(val, 'name'):
                        val = val.name
                    elif hasattr(val, 'id'):
                        val = val.id
                    row_data.append(str(val))
                writer.writerow(row_data)
        return True, "Export successful"
    except Exception as e:
        return False, str(e)

def export_to_pdf(query, filename, title, fields):
    """
    Export a Peewee query to a PDF file.
    :param query: Peewee ModelSelect query
    :param filename: Output filename
    :param title: Title of the PDF report
    :param fields: List of field names (strings) to export
    """
    try:
        doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()

        # Title
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Spacer(1, 12))

        # Table Data
        data = [fields] # Header
        for row in query:
            row_data = []
            for field in fields:
                val = getattr(row, field, "")
                if hasattr(val, 'name'):
                    val = val.name
                elif hasattr(val, 'id'):
                    val = val.id
                # Wrap long text
                row_data.append(str(val)[:50]) 
            data.append(row_data)

        # Table Style
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        doc.build(elements)
        return True, "Export successful"
    except Exception as e:
        return False, str(e)

def import_from_csv(model, filename, field_map):
    """
    Import data from CSV to a Peewee model.
    :param model: Peewee Model class
    :param filename: Input CSV filename
    :param field_map: Dictionary mapping CSV headers to Model fields
    """
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                data = {}
                for csv_header, model_field in field_map.items():
                    if csv_header in row:
                        val = row[csv_header]
                        # Basic type conversion could go here if needed
                        if val:
                            data[model_field] = val
                
                if data:
                    model.create(**data)
                    count += 1
            return True, f"Imported {count} records"
    except Exception as e:
        return False, str(e)
