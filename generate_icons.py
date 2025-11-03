
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, is_maskable=False):
    """Create a PWA icon with the Advanced Bots Creator logo"""
    # Create base image with gradient background
    img = Image.new('RGB', (size, size), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect
    for i in range(size):
        color = (26 + int(i * 0.1), 26 + int(i * 0.1), 46 + int(i * 0.2))
        draw.line([(0, i), (size, i)], fill=color)
    
    # Calculate sizes
    if is_maskable:
        # Maskable icons need safe zone (80% of icon size in center)
        padding = int(size * 0.1)
        logo_size = int(size * 0.8)
    else:
        padding = int(size * 0.1)
        logo_size = int(size * 0.8)
    
    # Draw robot icon using shapes
    robot_size = logo_size
    x_offset = (size - robot_size) // 2
    y_offset = (size - robot_size) // 2
    
    # Robot head (rounded rectangle)
    head_color = '#0d6efd'
    head_margin = robot_size // 6
    draw.rounded_rectangle(
        [x_offset + head_margin, y_offset + head_margin, 
         x_offset + robot_size - head_margin, y_offset + robot_size - head_margin],
        radius=robot_size // 8,
        fill=head_color
    )
    
    # Robot eyes
    eye_size = robot_size // 10
    eye_y = y_offset + robot_size // 3
    eye_color = '#ffffff'
    
    # Left eye
    draw.ellipse(
        [x_offset + robot_size // 3 - eye_size, eye_y,
         x_offset + robot_size // 3 + eye_size, eye_y + eye_size * 2],
        fill=eye_color
    )
    
    # Right eye
    draw.ellipse(
        [x_offset + 2 * robot_size // 3 - eye_size, eye_y,
         x_offset + 2 * robot_size // 3 + eye_size, eye_y + eye_size * 2],
        fill=eye_color
    )
    
    # Robot antenna
    antenna_width = robot_size // 20
    antenna_height = robot_size // 8
    draw.rectangle(
        [x_offset + robot_size // 2 - antenna_width, y_offset + head_margin - antenna_height,
         x_offset + robot_size // 2 + antenna_width, y_offset + head_margin],
        fill='#ffc107'
    )
    
    # Antenna ball
    ball_size = robot_size // 12
    draw.ellipse(
        [x_offset + robot_size // 2 - ball_size, y_offset + head_margin - antenna_height - ball_size,
         x_offset + robot_size // 2 + ball_size, y_offset + head_margin - antenna_height + ball_size],
        fill='#ffc107'
    )
    
    return img

def main():
    # Create icons directory
    icons_dir = 'static/icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    # Standard icon sizes
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    print("Generating PWA icons...")
    
    # Generate standard icons
    for size in sizes:
        icon = create_icon(size, is_maskable=False)
        filename = f'{icons_dir}/icon-{size}x{size}.png'
        icon.save(filename, 'PNG')
        print(f"Created {filename}")
    
    # Generate maskable icons
    for size in [192, 512]:
        icon = create_icon(size, is_maskable=True)
        filename = f'{icons_dir}/maskable-icon-{size}x{size}.png'
        icon.save(filename, 'PNG')
        print(f"Created {filename}")
    
    print("\n✅ All PWA icons generated successfully!")
    print("Icons are saved in the 'static/icons' directory")

if __name__ == '__main__':
    main()
