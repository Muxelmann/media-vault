import os
import av
import json
import time
from PIL import Image, ImageSequence, ImageFile
from flask import abort, send_file, url_for

ImageFile.LOAD_TRUNCATED_IMAGES = True

VIDEO_SUFFIX = ('mov', 'mp4', 'm4v')
IMAGE_SUFFIX = ('jpeg', 'jpg', 'png', 'gif')


class Item:
    DATA_PATH = None
    THUMB_PATH = None
    THUMB_MIN_SIZE = 200
    THUMB_FRAMES_COUNT = 30
    FAV_LIST_PATH = None
    FAV_LIST = None
    SEARCH = {
        'keyword': None,
        'results': None,
        'duration': 0.0
    }

    @classmethod
    def update_fav_list(cls) -> None:
        """Saves the current value of FAV_LIST to the FAV_LIST_PATH.

        Saving is not performed if either of these values is `None`.
        """
        if cls.FAV_LIST is None or cls.FAV_LIST_PATH is None:
            return
        with open(cls.FAV_LIST_PATH, 'w') as f:
            json.dump(cls.FAV_LIST, f)

    @classmethod
    def get_favorites_list(cls) -> list['Item']:
        """Produces a list of favorite items.

        Returns:
            list[Item]: The list of favorite items
        """
        if cls.FAV_LIST is None:
            return []

        item_list = [
            Item(content_path) for content_path in cls.FAV_LIST
        ]
        return item_list

    @classmethod
    def search(cls, keyword: str) -> None:
        Item.SEARCH['keyword'] = keyword
        search_start_time = time.time()
        results = []

        for root, dirs, files in os.walk(Item.DATA_PATH):
            for dir in [d for d in dirs if d[0] != '.' and d[0] != '@']:
                dirname = dir.lower()
                if keyword in dirname:
                    result = os.path.join(root, dir)
                    results.append(
                        Item(result.replace(Item.DATA_PATH, '')[1:])
                    )

            for file in [f for f in files if f[0] != '.' and f[0] != '@']:
                filename = os.path.splitext(file)[0].lower()
                if keyword in filename:
                    result = os.path.join(root, file)
                    results.append(
                        Item(result.replace(Item.DATA_PATH, '')[1:])
                    )
        search_end_time = time.time()
        Item.SEARCH['results'] = results
        Item.SEARCH['duration'] = search_end_time - search_start_time

    @classmethod
    def get_search_results(cls) -> list['Item']:
        return Item.SEARCH['results']

    @classmethod
    def get_searched_keyword(cls) -> str:
        return Item.SEARCH['keyword']

    @classmethod
    def get_search_duration(cls) -> str:
        return Item.SEARCH['duration']

    def __init__(self, content_path: str, find_neighbors: bool = False) -> None:
        self.content_path = content_path

        # Generate full path to content
        self.full_path = os.path.join(Item.DATA_PATH, content_path)
        self.thumb_path = os.path.join(Item.THUMB_PATH, content_path)
        self.poster_path = None  # only for video

        # Extract file information and set thumb and poster paths
        self.folder, self.file_name = os.path.split(content_path)
        self.name, self.suffix = os.path.splitext(self.file_name)
        self.suffix = self.suffix[1:].lower()
        self.type = 'unknown'
        self.size = 0
        if self.suffix == '':
            self.type = 'folder'
        elif self.suffix in IMAGE_SUFFIX:
            self.type = 'image'
            self.size = os.path.getsize(self.full_path)
        elif self.suffix in VIDEO_SUFFIX:
            self.type = 'video'
            self.size = os.path.getsize(self.full_path)
            self.poster_path = os.path.join(os.path.split(
                self.thumb_path)[0], f'{self.name}.png')

        # For size information
        if self.size > 2**30:
            self.size //= 2**30
            self.size_unit = 'GB'
        elif self.size > 2**20:
            self.size //= 2**20
            self.size_unit = 'MB'
        elif self.size > 2**10:
            self.size //= 2**10
            self.size_unit = 'kB'

        # Get favorite status
        if not os.path.exists(self.FAV_LIST_PATH):
            Item.FAV_LIST = []
            Item.update_fav_list()
        else:
            with open(self.FAV_LIST_PATH) as f:
                new_fav_list = json.load(f)
                Item.FAV_LIST = new_fav_list

        self.is_favorite = self.content_path in Item.FAV_LIST

        # Get neighboring information for going to next and previous
        if find_neighbors:
            self.previous_neighbor = None
            self.next_neighbor = None

            content_in_folder = Item(self.folder).content_list
            idx = content_in_folder.index(self)

            if idx > 0:
                self.previous_neighbor = content_in_folder[idx - 1]
            if idx < len(content_in_folder) - 1:
                self.next_neighbor = content_in_folder[idx + 1]

    def set_favorite(self, is_favorite: bool) -> None:
        self.is_favorite = is_favorite
        if self.is_favorite:
            if self.content_path not in Item.FAV_LIST:
                Item.FAV_LIST.append(self.content_path)
                Item.update_fav_list()
        else:
            if self.content_path in Item.FAV_LIST:
                Item.FAV_LIST.remove(self.content_path)
                Item.update_fav_list()

    def __lt__(self, other: 'Item') -> bool:
        return self.name < other.name

    def __eq__(self, other: 'Item') -> bool:
        return self.content_path == other.content_path

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
            for f in os.listdir(self.full_path) if f[0] != '.' and f[0] != '@'
        ]
        item_list.sort()
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

        if not os.path.exists(self.thumb_path) and not self.make_thumb():
            return abort(500)

        return send_file(self.thumb_path)

    def make_thumb(self) -> bool:
        """Generates thumbs for a given media file.


        If a file exists at the full path, a thumb version thereof will be stored at teh thumb path.
        If the thumb file already exists, it is not overwritten.

        TODO: maybe try class av.video.reformatter.VideoReformatter instead of keyframe based re-encoding

        Returns:
            bool: True if thumbnail was successfully generated
        """
        # Make folder structure to save thumb
        base_path = os.path.split(self.thumb_path)[0]
        if not os.path.exists(base_path):
            try:
                os.makedirs(base_path)
            except FileExistsError:
                pass

        # If thumb already exists, send it
        if os.path.exists(self.thumb_path):
            return True

        # Generate thumb
        if self.type == 'video':
            with av.open(self.full_path) as in_container:
                with av.open(self.thumb_path, 'w') as out_container:

                    # Test if a video is present
                    if len(in_container.streams.video) == 0:
                        return False

                    # Get input stream
                    in_stream = in_container.streams.video[0]

                    # Only extract subset of frames i.e. Keyframes
                    # in_stream.codec_context.skip_frame = "NONKEY"

                    # Rescale smaller dimension to THUMB_MIN_SIZE
                    old_height = in_stream.codec_context.height
                    old_width = in_stream.codec_context.width

                    aspect_ratio = old_width / old_height
                    if aspect_ratio > 1:
                        new_height = Item.THUMB_MIN_SIZE
                        new_width = int(Item.THUMB_MIN_SIZE * aspect_ratio)
                    else:
                        new_height = int(Item.THUMB_MIN_SIZE / aspect_ratio)
                        new_width = Item.THUMB_MIN_SIZE

                    if new_height % 2 != 0:
                        new_height += 1
                    if new_width % 2 != 0:
                        new_width += 1

                    # out_stream = out_container.add_stream(template=in_stream)
                    codec_name = in_stream.codec_context.name
                    out_stream = out_container.add_stream(
                        codec_name, str(1))
                    out_stream.width = new_width
                    out_stream.height = new_height
                    out_stream.pix_fmt = in_stream.codec_context.pix_fmt

                    def linspace(a, b, n=100):
                        if n < 2:
                            return b
                        diff = (float(b) - a)/(n - 1)
                        return [diff * i + a for i in range(n)]

                    for offset in linspace(0, in_container.duration, Item.THUMB_FRAMES_COUNT):
                        in_container.seek(int(offset))
                        in_frame = next(in_container.decode(in_stream))
                        img = in_frame.to_image().resize((new_width, new_height))

                        # Note: to_image and from_image is not required in this specific example.
                        out_frame = av.VideoFrame.from_image(img)
                        out_packet = out_stream.encode(
                            out_frame)  # Encode video frame
                        # "Mux" the encoded frame (add the encoded frame to MP4 file).
                        out_container.mux(out_packet)

                    # Flush the encoder
                    out_packet = out_stream.encode(None)
                    out_container.mux(out_packet)

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
                        self.thumb_path,
                        save_all=True,
                        append_images=frames[1:],
                        optimize=True,
                        loop=0
                    )

                else:
                    out_img = img.resize((new_width, new_height))
                    out_img.save(self.thumb_path)

        return self.thumb_path

    @property
    def poster_url(self) -> str:
        return url_for('get_content', content_path=self.content_path, poster=True)

    @property
    def poster(self) -> str:
        """Sends a poster image (like thumbnail) for videos.
        This property is only available for video!

        Returns:
            str: Flask response string of `send_file()`
        """

        if self.type != 'video':
            return abort(404)

        if not os.path.exists(self.poster_path) and not self.make_poster():
            return abort(500)

        return send_file(self.poster_path)

    def make_poster(self) -> bool:
        """Generates a poster for a video

        Returns:
            bool: True if poster file is successfully generated
        """

        if self.type != 'video':
            return False

        if not os.path.exists(self.thumb_path) and not self.make_thumb():
            return False

        with av.open(self.thumb_path) as container:

            # Test if a video is present
            if len(container.streams.video) == 0:
                return False

            # Get video stream
            stream = container.streams.video[0]

            # Cannot seek to middle frame immediately, since it may not be a keyframe

            # Get frames
            for idx, frame in enumerate(container.decode(stream)):
                # When half way point is reached
                if idx <= Item.THUMB_FRAMES_COUNT / 2:
                    continue
                # Convert to image and save
                frame.to_image().save(self.poster_path)
                break

            return True

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
