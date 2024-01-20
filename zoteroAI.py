import PyPDF2
import fitz
import openai
from openai import OpenAI
import requests
import io, os, base64, time
from PIL import Image
from tqdm import tqdm
from pyzotero import zotero

client = OpenAI()

# TODO: secure access info
library_id=13430765
library_type='user'
api_key='vHmUznIPjWKTexYMGeGFLhSC'
# raise Exception("The 'openai.api_key' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(api_key=os.environ['OPENAI_API_KEY'])'")
OpenAI(api_key=os.environ['OPENAI_API_KEY'])
print("Connecting to Zotero libray...")
zot = zotero.Zotero(library_id, library_type, api_key)

# TODO: Manage multiple files/collections
zitems = zot.top(limit=5)
# zitem = zot.collection('Darwin',limit=1)
item = zitems[4] #0-50, 1-8, 2-50, 3-65, 4-5
paper_id=item['key']
# we've retrieved the latest five top-level items in our library
# we can print each item's item type and ID
attachments = zot.children(paper_id)
pdf_content = zot.file(attachments[0]['key'])

# Create a PDF file reader object using an in-memory binary stream
pdf_stream = io.BytesIO(pdf_content)
pdf_reader = PyPDF2.PdfReader(pdf_stream)

# Create an image extractor with Fitx/PyMuPDF
pdf_document_fitz = fitz.open("_.pdf", pdf_stream)

paper_name = item['data']['title'].replace(" ", "")


if not os.path.exists("./papers"):
    os.makedirs("./papers")
if not os.path.exists(f"./papers/{paper_name}"):
    os.makedirs(f"./papers/{paper_name}")
    os.makedirs(f"./papers/{paper_name}/figs/")



print("Finding Figures...")
fig_idx = 1
for page_number in tqdm(range(len(pdf_document_fitz)),desc=f"Getting Figures",leave=True):
    page = pdf_document_fitz.load_page(page_number)
    image_list = page.get_images()

    for img in tqdm(page.get_images(full=True), desc=f"Reading Figure {fig_idx}", leave=False):
        xref = img[0]
        base_image = pdf_document_fitz.extract_image(xref)
        image_bytes = base_image["image"]
        image_filename = f"./papers/{paper_name}/figs/figure_{fig_idx}_pp{page_number+1}.png"
        fig_idx+=1
        with open(image_filename, "wb") as image_file:
            image_file.write(image_bytes)

print(f"Found {fig_idx} figures!")

num_pages = len(pdf_reader.pages)
document_text = []
print("Stripping Text...")
idx=0
for page in tqdm(pdf_reader.pages,desc="Reading Pages", leave=True):
    # document_text.append(pdf_reader.pages[0].extract_text())
    obj = {"page":{idx+1},"text":{page.extract_text()}}
    idx+=1
    document_text.append(obj)

text_filename = f"./papers/{paper_name}/raw_text.txt"
with open(text_filename, "w") as text:
    text.write(str(document_text))


time.sleep(5)

def image_to_base64(image_path):
    with Image.open(image_path) as image:
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

# Assuming you have a list of image paths
image_paths = f"./papers/{paper_name}/figs/"
files_in_directory = os.listdir(image_paths)

base64_images = [image_to_base64(f"./papers/{paper_name}/figs/{path}") for path  in files_in_directory]


def describe_figure(base64_image):
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
    }

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "This is an image from an academic work, please describe it appropriately."
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/PNG;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 500
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    return response.json()['choices'][0]['message']['content']


# def describe_image(base64_image):
#     response = client.images.generate(  # Specify the correct model name
#     prompt=f"This is an image from an academic work, please describe it appropriately.",
#     n=1)
#     return response

print("Writing Vision Transformer Outputs")
descriptions = [describe_figure(image) for image in tqdm(base64_images,desc='Sending Figs to GPT4-V')]


figs_desc_filename = f"./papers/{paper_name}/fig_descriptions_text.txt"
with open(figs_desc_filename, "w") as text:
    text.write(str(descriptions))
print("Finished Processing Article\n")
