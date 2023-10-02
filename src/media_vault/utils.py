import os
import subprocess
from PIL import Image, ImageSequence, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

def get_file_list(full_path: str) -> list[str]:
    """Gets a list of all files in a directory.

    Args:
        full_path (str): full path e.g. starting with `/user/...` to the directory

    Returns:
        list[str]: the list of file/directory names at full path
    """
    file_list = [f for f in os.listdir(full_path) if f[0] != '.']
    file_list.sort()
    return file_list

def make_thumb(full_path: str, thumb_path: str) -> None:
    """Generates thumbs for a given media file.

    If a file exists at the full path, a thumb version thereof will be stored at teh thumb path.
    If the thumb file already exists, it is not overwritten.

    Args:
        full_path (str): full path e.g. starting with `/user/...` to the actual media file
        thumb_path (str): full path e.g. starting with `/tmp/...` to where the thumb file is (to be) stored
    """
    # Make folder structure to save thumb
    base_path = os.path.split(thumb_path)[0]
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    # Generate thumb
    if os.path.splitext(full_path)[1].lower() in ['.mp4', '.m4v']:
        subprocess.call([
            'ffmpeg',
            '-i', full_path,
            '-ss', '00:00:00.000',
            '-vframes', '1',
            '-y',
            thumb_path
        ])
    else:
        with Image.open(full_path) as img:

            aspect_ratio = img.width / img.height
            if aspect_ratio > 1:
                new_height = 200
                new_width = int(200 * aspect_ratio)
            else:
                new_height = int(200 / aspect_ratio)
                new_width = 200
                
            if hasattr(img, "is_animated") and img.is_animated:
                frames = ImageSequence.Iterator(img)
                frames = [f.resize((new_width, new_height)) for f in frames]
                out_img = frames[0]
                out_img.info = img.info
                out_img.save(thumb_path, save_all=True, append_images=frames[1:], optimize=True)

            else:
                out_img = img.resize((new_width, new_height))
                out_img.save(thumb_path)

def get_neighbors(full_path: str, content_path: str) -> list[str | None]:
    """Gets the two neighboring content paths for a given file.

    If no previous or next neighbor is available, `None` is returned instead.
    E.g. for the first element (`[0]`), the previous neighbor is `None`, and
    for the last element (`[N-1]`), the next neighbor is `None`.

    Args:
        full_path (str): full path e.g. starting with `/user/...` to the actual media file
        content_path (str): path to media file according to URL

    Returns:
        list[str | None]: List of neighbors' content paths or `None`
    """
    content_dir_path, _ = os.path.split(content_path)
    full_dir_path, file_name = os.path.split(full_path)
    file_list = get_file_list(full_dir_path)
    idx = file_list.index(file_name)

    previous_content_path, next_content_path = None, None
    
    if idx > 0:
        previous_content_path = os.path.join(content_dir_path, file_list[idx-1])

    if idx < len(file_list) - 1:
        next_content_path = os.path.join(content_dir_path, file_list[idx+1])
    
    return [previous_content_path, next_content_path]

def make_dir(full_path: str) -> None | str:
    """Generates a directory at the specified path.

    Args:
        full_path (str): full path e.g. starting with `/user/...` to the directory to be generated
    
    Returns:
        str | None: Returns an error string if directory already exists at the specified path
    """
    if os.path.exists(full_path) and os.path.isdir(full_path):
        return "Directory already exists."
    
    os.makedirs(full_path)
    return None
