import io
import torch
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from PIL import Image
from diffusers import QwenImageEditPipeline

app = FastAPI(title="Qwen Image Edit API")

# Initialize pipeline globally
print("Loading pipeline...")
pipeline = QwenImageEditPipeline.from_pretrained("Qwen/Qwen-Image-Edit")
pipeline.to(torch.bfloat16)
pipeline.to("cuda")
pipeline.set_progress_bar_config(disable=True)
print("Pipeline loaded successfully")

def image_edit(image: Image.Image, prompt: str) -> Image.Image:
    """Core image editing logic using the Qwen model."""
    inputs = {
        "image": image,
        "prompt": prompt,
        "generator": torch.manual_seed(0),
        "true_cfg_scale": 4.0,
        "negative_prompt": "blurry, low quality",
        "num_inference_steps": 10,
    }
    
    with torch.inference_mode():
        output = pipeline(**inputs)
        return output.images[0]

@app.post("/edit-image/")
async def edit_image_api(
    file: UploadFile = File(...), 
    prompt: str = Form(...)
):
    """
    API endpoint to edit an image based on a text prompt.
    Returns the edited image as a PNG file stream.
    """
    # 1. Read the uploaded file and convert to PIL Image
    contents = await file.read()
    input_image = Image.open(io.BytesIO(contents)).convert("RGB")
    
    # 2. Perform image editing
    output_image = image_edit(input_image, prompt)
    
    # 3. Convert result back to bytes for the response
    img_byte_arr = io.BytesIO()
    output_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return StreamingResponse(img_byte_arr, media_type="image/png")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4206)
