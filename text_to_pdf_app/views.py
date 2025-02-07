import os
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.pdfgen import canvas
from django.core.files.storage import default_storage
from django.conf import settings
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter

@csrf_exempt
def index(request):
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        font_size = int(request.POST.get('font_size', 12))
        font_color = request.POST.get('font_color', '#000000')  # Default black
        signature = request.POST.get('signature', '')
        orientation = request.POST.get('orientation', 'portrait')  # Get page orientation
        
        # Generate default filename from first 3 words
        default_filename = "_".join(text.split()[:3]) if text else "output"
        filename = request.POST.get('filename', default_filename) + ".pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        
        with default_storage.open(filepath, 'wb') as pdf_file:
            pdf = canvas.Canvas(pdf_file)
            
            # Set the page size based on orientation
            if orientation == 'landscape':
                page_width, page_height = 11 * 72, 8.5 * 72  # Landscape size in points
            else:
                page_width, page_height = 8.5 * 72, 11 * 72  # Portrait size in points
            pdf.setPageSize((page_width, page_height))
            
            pdf.setFont("Helvetica", font_size)
            pdf.setFillColor(HexColor(font_color))  # Convert hex to color
            
            # Initial positioning for text
            x_position = 100
            y_position = page_height - 100  # Start from the top of the page
            line_height = font_size + 2

            # Function to handle text wrapping and pagination
            def draw_wrapped_text(text, x, y, max_width):
                text_object = pdf.beginText(x, y)
                text_object.setFont("Helvetica", font_size)
                text_object.setFillColor(HexColor(font_color))
                text_object.setTextOrigin(x, y)
                
                # Split the text into lines that fit within the max width
                words = text.split(' ')
                current_line = ''
                
                for word in words:
                    test_line = current_line + ' ' + word if current_line else word
                    width = pdf.stringWidth(test_line, "Helvetica", font_size)
                    
                    if width < max_width:
                        current_line = test_line
                    else:
                        text_object.textLine(current_line)
                        current_line = word  # Start a new line with the current word

                if current_line:
                    text_object.textLine(current_line)  # Draw the last line
                
                pdf.drawText(text_object)
                return text_object.getY()

            # Function to handle pagination
            def handle_page_break(y_position):
                if y_position < 100:  # If the text is too close to the bottom of the page, create a new page
                    pdf.showPage()
                    pdf.setFont("Helvetica", font_size)
                    pdf.setFillColor(HexColor(font_color))
                    return page_height - 100  # Reset the y-position to the top of the new page
                return y_position

            # Draw the main text
            y_position = draw_wrapped_text(text, x_position, y_position, page_width - 2 * x_position)
            y_position = handle_page_break(y_position)
            
            # Draw the signature if available
            if signature:
                y_position -= line_height
                signature_text = f"Signed by: {signature}"
                y_position = draw_wrapped_text(signature_text, x_position, y_position, page_width - 2 * x_position)
            
            pdf.save()
        
        with default_storage.open(filepath, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    
    return render(request, 'index.html')