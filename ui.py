import streamlit as st
from streamlit_drawable_canvas import st_canvas
from helper import get_image_description, generate_image_from_text
from PIL import Image
import base64
from io import BytesIO

STYLES = [
    "Photorealistic and Digital art", "Oil painting", "Watercolor",
    "Pencil sketch", "Anime", "Comic book", "Abstract",
    "Impressionist", "Pop art"
]

def skeleton_loader():
    return """
    <div class="skeleton-loader"></div>
    <style>
        .skeleton-loader {
            width: 512px;
            height: 512px;
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
        }
        @keyframes loading {
            0% {
                background-position: 200% 0;
            }
            100% {
                background-position: -200% 0;
            }
        }
    </style>
    """

def bordered_placeholder():
    return """
    <div class="bordered-placeholder"></div>
    <style>
        .bordered-placeholder {
            width: 512px;
            height: 512px;
            border: 2px dashed #cccccc;
        }
    </style>
    """

def get_image_download_link(img, filename, text):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}">{text}</a>'
    return href

def main():
    st.set_page_config(layout="wide", page_title="Sketch to Realistic Image Converter")

    st.title("Sketch to Realistic Image Converter")

    if 'canvas_result' not in st.session_state:
        st.session_state.canvas_result = None

    col_input, col_controls, col_output = st.columns([2, 1, 2])

    with col_input:
        st.subheader("Draw your sketch or upload an image")
        
        uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            st.session_state.canvas_result = type('obj', (object,), {'image_data': image})
        else:
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",
                stroke_width=3,
                stroke_color="#000000",
                background_color="#FFFFFF",
                height=512,
                width=512,
                drawing_mode="freedraw",
                key="canvas",
            )
            
            if canvas_result.image_data is not None:
                st.session_state.canvas_result = canvas_result

    with col_controls:
        st.subheader("Image Details")
        selected_style = st.selectbox("Select output style", STYLES)
        additional_info = st.text_input("Enter Additional information that specify the actions")
        
        description_button = st.button(
            "Generate Description" if 'description' not in st.session_state else "Regenerate Description", 
            use_container_width=True
        )
        
        generate_button = st.button("Generate Image", use_container_width=True)
        loading_placeholder = st.empty()

    with col_output:
        st.subheader("Generated Realistic Image")
        output_placeholder = st.empty()
        
        description_placeholder = st.empty()
        
        if 'realistic_image' in st.session_state:
            output_placeholder.image(st.session_state.realistic_image, caption="Generated Realistic Image", width=512)
            
            result = st.session_state.realistic_image

            st.markdown(get_image_download_link(result, "generated_image.png", "Download Generated Image"), unsafe_allow_html=True)
        else:
            output_placeholder.markdown(bordered_placeholder(), unsafe_allow_html=True)

    if description_button:
        if st.session_state.canvas_result is not None and st.session_state.canvas_result.image_data is not None:
            loading_placeholder.text("Generating description...")
            
            if isinstance(st.session_state.canvas_result.image_data, Image.Image):
                img = st.session_state.canvas_result.image_data
            else:
                img = Image.fromarray(st.session_state.canvas_result.image_data.astype('uint8'), 'RGBA')
            img = img.convert('RGB')
            
            base_description = get_image_description(img, additional_info, selected_style)
            
            prompt = f"{base_description} \n Style: {selected_style}"
            
            st.session_state.description = prompt
            
            loading_placeholder.empty()
            st.success("Description generated successfully!")
        else:
            st.warning("Please draw something on the canvas or upload an image first!")

    if 'description' in st.session_state:
        st.session_state.description = description_placeholder.text_area(
            "Image Description (edit if needed)", 
            st.session_state.description, 
            height=150
        )

    if generate_button:
        if st.session_state.canvas_result is not None and st.session_state.canvas_result.image_data is not None:
            if 'description' not in st.session_state:
                st.warning("Please generate a description first!")
            else:
                loading_placeholder.text("Generating...")
                
                output_placeholder.markdown(skeleton_loader(), unsafe_allow_html=True)
                
                if isinstance(st.session_state.canvas_result.image_data, Image.Image):
                    img = st.session_state.canvas_result.image_data
                else:
                    img = Image.fromarray(st.session_state.canvas_result.image_data.astype('uint8'), 'RGBA')
                img = img.convert('RGB')
                
                try:
                    realistic_image = generate_image_from_text(st.session_state.description, img)

                    if realistic_image is None:
                        raise Exception("Image generation returned None")

                    st.session_state.realistic_image = realistic_image
                    output_placeholder.image(realistic_image, caption="Generated Realistic Image", width=512)

                    st.markdown(get_image_download_link(realistic_image, "generated_image.png", "Download Generated Image"), unsafe_allow_html=True)

                    loading_placeholder.empty()
                    st.success("Image generated successfully!")
                except Exception as e:
                    loading_placeholder.empty()
                    output_placeholder.markdown(bordered_placeholder(), unsafe_allow_html=True)
                    st.error(f"Error generating image: {str(e)}")
        else:
            st.warning("Please draw something on the canvas or upload an image first!")

if __name__ == "__main__":
    main()
