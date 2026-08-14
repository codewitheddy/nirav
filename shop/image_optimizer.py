"""
Image Optimization Utilities for POPSHOP.KE
Provides multiple strategies for ultra-fast image loading
"""
from PIL import Image
import io
import base64
from django.core.files.uploadedfile import InMemoryUploadedFile


class ImageOptimizer:
    """
    Comprehensive image optimization for web delivery
    """
    
    @staticmethod
    def optimize_image(image_file, max_width=800, max_height=800, quality=85, format='JPEG'):
        """
        Optimize an image file for web delivery
        
        Args:
            image_file: Django UploadedFile or PIL Image
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            quality: JPEG quality (1-100)
            format: Output format (JPEG, WebP, PNG)
        
        Returns:
            Optimized image file
        """
        try:
            # Open image
            if isinstance(image_file, InMemoryUploadedFile):
                img = Image.open(image_file)
            else:
                img = image_file
            
            # Convert RGBA to RGB for JPEG
            if img.mode in ('RGBA', 'LA', 'P') and format == 'JPEG':
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Calculate new dimensions maintaining aspect ratio
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            
            if format == 'WebP':
                img.save(output, format='WebP', quality=quality, method=6)
            elif format == 'JPEG':
                img.save(output, format='JPEG', quality=quality, optimize=True, progressive=True)
            else:
                img.save(output, format=format, optimize=True)
            
            output.seek(0)
            
            return output
            
        except Exception as e:
            print(f"Image optimization error: {e}")
            return None
    
    @staticmethod
    def create_thumbnail(image_file, size=(300, 300), quality=80):
        """
        Create a thumbnail version of an image
        
        Args:
            image_file: Image file
            size: Tuple of (width, height)
            quality: JPEG quality
        
        Returns:
            Thumbnail image
        """
        return ImageOptimizer.optimize_image(
            image_file,
            max_width=size[0],
            max_height=size[1],
            quality=quality
        )
    
    @staticmethod
    def generate_srcset(image_url, sizes=[400, 800, 1200]):
        """
        Generate srcset string for responsive images.
        Returns the image URL as-is since we serve local media files.
        """
        if not image_url:
            return ""
        return f"{image_url} 1x"
    
    @staticmethod
    def get_blur_placeholder(image_file, size=(20, 20)):
        """
        Generate a tiny blurred placeholder for progressive loading
        
        Args:
            image_file: Image file
            size: Placeholder size (very small)
        
        Returns:
            Base64 encoded placeholder
        """
        try:
            img = Image.open(image_file)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Apply blur
            img = img.filter(Image.BLUR)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=50)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/jpeg;base64,{img_str}"
        except:
            return None
    
    @staticmethod
    def get_image_dimensions(image_file):
        """
        Get image dimensions without loading full image
        
        Args:
            image_file: Image file
        
        Returns:
            Tuple of (width, height)
        """
        try:
            img = Image.open(image_file)
            return img.size
        except:
            return (0, 0)


def get_optimized_image_html(image_url, alt_text, width=None, height=None, lazy=True, class_name=""):
    """
    Generate optimized image HTML with all performance features
    
    Args:
        image_url: Image URL
        alt_text: Alt text for accessibility
        width: Image width
        height: Image height
        lazy: Enable lazy loading
        class_name: CSS class
    
    Returns:
        HTML string
    """
    if not image_url:
        return ""
    
    # Generate srcset for responsive images
    srcset = ImageOptimizer.generate_srcset(image_url)
    
    # Build HTML
    html_parts = ['<img']
    
    if lazy:
        html_parts.append('loading="lazy"')
        html_parts.append('decoding="async"')
    
    html_parts.append(f'src="{image_url}"')
    
    if srcset:
        html_parts.append(f'srcset="{srcset}"')
        html_parts.append('sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"')
    
    html_parts.append(f'alt="{alt_text}"')
    
    if width:
        html_parts.append(f'width="{width}"')
    if height:
        html_parts.append(f'height="{height}"')
    
    if class_name:
        html_parts.append(f'class="{class_name}"')
    
    html_parts.append('>')
    
    return ' '.join(html_parts)
