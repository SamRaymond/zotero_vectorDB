from pyzotero import zotero
import PyPDF2
import fitz
import io


library_id=13430765
library_type='user'
api_key='vHmUznIPjWKTexYMGeGFLhSC'
zot = zotero.Zotero(library_id, library_type, api_key)
zitem = zot.top(limit=1)
item = zitem[0]
paper_id=item['key']
# we've retrieved the latest five top-level items in our library
# we can print each item's item type and ID
attachments = zot.children(paper_id)
pdf_content = zot.file(attachments[0]['key'])

# Create a PDF file reader object using an in-memory binary stream
pdf_stream = io.BytesIO(pdf_content)
pdf_reader = PyPDF2.PdfReader(pdf_stream)

# Create an image extractor with Fitx/PyMuPDF
pdf_document_fitz = fitz.open("pdf_document.pdf", pdf_stream)

for page_number in range(len(pdf_document_fitz)):
    page = pdf_document_fitz.load_page(page_number)
    image_list = page.get_images()

    for image_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = pdf_document_fitz.extract_image(xref)
        image_bytes = base_image["image"]

        image_filename = f"image{page_number+1}_{image_index+1}.png"
        with open(image_filename, "wb") as image_file:
            image_file.write(image_bytes)
exit(0)

num_pages = len(pdf_reader.pages)
document_text = []
for page in pdf_reader.pages:
    # document_text.append(pdf_reader.pages[0].extract_text())
    document_text.append(page.extract_text())

print(document_text)



exit()
print(item['data']['title'])
print(item['links']['attachment'])
print(item['meta'].keys())

# Get pdf link:
pdf_link = item['links']['attachment']['href']
print(pdf_link)
# Download the pdf:
pdf_content = zot.file(pdf_link)



# Now, you can use pdf_reader to perform various operations. For example:

# Print the number of pages
print(f"Number of pages: {pdf_reader.getNumPages()}")

# Read text from a specific page
page = pdf_reader.getPage(0)  # Get the first page
print(page.extractText())
