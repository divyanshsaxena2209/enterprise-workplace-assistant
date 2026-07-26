from reportlab.pdfgen import canvas

c = canvas.Canvas("test_valid.pdf")
c.drawString(100, 750, "Hello World from valid PDF!")
c.save()
