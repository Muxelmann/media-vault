import os
# import subprocess
import av
from PIL import Image, ImageSequence, ImageFile
from flask import abort, send_file, url_for

ImageFile.LOAD_TRUNCATED_IMAGES = True

VIDEO_SUFFIX = ('mov', 'mp4', 'm4v')
IMAGE_SUFFIX = ('jpeg', 'jpg', 'png', 'gif')


class Item:
    DATA_PATH = None
    THUMB_PATH = None
    THUMB_MIN_SIZE = 200

    def __init__(self, content_path: str) -> None:
        self.content_path = content_path

        # Generate full path to content and path to thumbnail
        self.full_path = os.path.join(Item.DATA_PATH, content_path)
        self.thumb_path = os.path.join(Item.THUMB_PATH, content_path)

        # Extract file information
        self.file_name = os.path.basename(self.full_path)
        self.name, self.suffix = os.path.splitext(self.file_name)
        self.suffix = self.suffix[1:].lower()
        if self.suffix in IMAGE_SUFFIX:
            self.type = 'image'
        elif self.suffix in VIDEO_SUFFIX:
            self.type = 'video'
        else:
            self.type = 'unknown'

    def __lt__(self, other: 'Item') -> bool:
        return self.name < other.name

    @property
    def is_dir(self) -> bool:
        return os.path.isdir(self.full_path)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.full_path)

    @property
    def content_list(self) -> list['Item']:
        """Gets a list of all files in a directory.

        Args:
            full_path (str): full path e.g. starting with `/user/...` to the directory

        Returns:
            list[str]: the list of file/directory names at full path
        """
        item_list = [
            Item(os.path.join(self.content_path, f))
            for f in os.listdir(self.full_path) if f[0] != '.'
        ]
        return item_list

    @property
    def thumb_url(self) -> str:
        return url_for('get_content', content_path=self.content_path, thumb=True)

    @property
    def thumb(self) -> str:
        """Sends a thumb version of the actual media file.

        If file is a dir (i.e., not a file as such), the function returns a 404 error response.

        If the thumb does not exist, it will be generated upon first call.
        If media file is a dir (i.e., not a file as such), the function returns a 404 error response.
        The thumb of a video file is stored as a PNG, despite the file suffix in the URL indicating e.g., MP4.

        Returns:
            str: Flask response string of `send_file()`
        """

        if not self.exists:
            return abort(404)

        actual_thumb_path = self.make_thumb()
        if actual_thumb_path is None:
            return abort(500)

        return send_file(actual_thumb_path)

    @property
    def raw_url(self) -> str:
        return url_for('get_content', content_path=self.content_path, raw=True)

    @property
    def raw(self) -> str:
        """Sends the actual media file.

        If file is a dir (i.e., not a file as such), the function returns a 404 error response.

        Returns:
            str: Flask response string of `send_file()`
        """
        if not os.path.isfile(self.full_path):
            return abort(404)
        return send_file(self.full_path)

    def make_thumb(self) -> str | None:
        """Generates thumbs for a given media file.

        If a file exists at the full path, a thumb version thereof will be stored at teh thumb path.
        If the thumb file already exists, it is not overwritten.

        Returns:
            str | None: Path to the actual thumbnail or None if it cannot be generated
        """
        # Make folder structure to save thumb
        base_path = os.path.split(self.thumb_path)[0]
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        actual_thumb_path = None

        if self.type == 'video':
            # Thumbnail of video is an animated gif
            actual_thumb_path = os.path.splitext(self.thumb_path)[0] + '.gif'
        elif self.type == 'image':
            # Thumbnail of image is same type
            actual_thumb_path = self.thumb_path
        else:
            return None

        # If thumb already exists, send it
        if os.path.exists(actual_thumb_path):
            return actual_thumb_path

        # Generate thumb
        if self.type == 'video':
            with av.open(self.full_path) as container:
                # Test if a video is present
                if len(container.streams.video) == 0:
                    return False

                # Only extract subset of frames i.e. Keyframes
                stream = container.streams.video[0]
                stream.codec_context.skip_frame = "NONKEY"

                # Rescale smaller dimension to THUMB_MIN_SIZE
                old_height = stream.codec_context.height
                old_width = stream.codec_context.width

                aspect_ratio = old_width / old_height
                if aspect_ratio > 1:
                    new_height = Item.THUMB_MIN_SIZE
                    new_width = int(Item.THUMB_MIN_SIZE * aspect_ratio)
                else:
                    new_height = int(Item.THUMB_MIN_SIZE / aspect_ratio)
                    new_width = Item.THUMB_MIN_SIZE

                thumb_frames = []
                for frame in container.decode(stream):
                    thumb_frames.append(
                        frame.to_image().resize((new_width, new_height))
                    )

                thumb_frames[0].save(
                    actual_thumb_path,
                    save_all=True,
                    append_images=thumb_frames[1:],
                    optimize=True,
                    duration=len(thumb_frames)*5,
                    loop=0
                )

        elif self.type == 'image':
            with Image.open(self.full_path) as img:

                # Rescale smaller dimension to THUMB_MIN_SIZE
                aspect_ratio = img.width / img.height
                if aspect_ratio > 1:
                    new_height = Item.THUMB_MIN_SIZE
                    new_width = int(Item.THUMB_MIN_SIZE * aspect_ratio)
                else:
                    new_height = int(Item.THUMB_MIN_SIZE / aspect_ratio)
                    new_width = Item.THUMB_MIN_SIZE

                # If the image is an animated GIF, convert all frames
                if hasattr(img, 'is_animated') and img.is_animated:
                    frames = ImageSequence.Iterator(img)
                    frames = [f.resize((new_width, new_height))
                              for f in frames]
                    out_img = frames[0]
                    out_img.info = img.info
                    out_img.save(
                        actual_thumb_path,
                        save_all=True,
                        append_images=frames[1:],
                        optimize=True,
                        loop=0
                    )

                else:
                    out_img = img.resize((new_width, new_height))
                    out_img.save(actual_thumb_path)

        return actual_thumb_path
