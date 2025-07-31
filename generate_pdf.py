from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
import io
import csv
import datetime

BASELINE_OFFSET_INCHES = 0.1584  # approx. 11pt
POINTS_PER_INCH = 72


def generate_pdf(data, base_pdf_path, csv_path, output_path):
    # Read CSV for field positions
    field_positions = []
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            field_positions.append({
                'field': row['field'],
                'text': data.get(row['field'], row['text']),
                'x': float(row['x_in']) * POINTS_PER_INCH,
                'y': (11 - (float(row['y_in']) + BASELINE_OFFSET_INCHES)) * POINTS_PER_INCH
            })

    # Create overlay PDF in memory
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)

    for field in field_positions:
        c.setFont("Helvetica", 11)
        c.drawString(field['x'], field['y'], field['text'])

    c.save()
    packet.seek(0)

    # Merge overlay with base PDF
    overlay = PdfReader(packet)
    base = PdfReader(open(base_pdf_path, "rb"))
    writer = PdfWriter()

    base_page = base.pages[0]
    base_page.merge_page(overlay.pages[0])
    writer.add_page(base_page)

    with open(output_path, "wb") as f:
        writer.write(f)


# Example usage (for testing)
if __name__ == "__main__":
    sample_data = {
        "Transaction number": "0000312345",
        "Authorization code": "654321",
        "Response code": "027",
        "Space number": "41952",
        "Start of session": "10:21",
        "End of session": "11:20",
        "Top date line": "Thu, Aug 1, 2025 at 12:05 PM"
    }
    generate_pdf(
        data=sample_data,
        base_pdf_path="base_receipt.pdf",
        csv_path="Mobicite_Placeholder_Locations.csv",
        output_path="output_receipt.pdf"
    )
