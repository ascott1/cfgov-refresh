from itertools import chain
from wagtail.wagtailcore.blocks.stream_block import StreamValue


class Handler(object):
    def __init__(self, page, request):
        self.page = page
        self.request = request

    def handle(self, context):
        raise NotImplementedError

    # Retrieves the stream values on a page from it's Streamfield
    def get_streamfield_blocks(self):
        blocks_dict = {}
        for key, value in vars(self.page).iteritems():
            if type(value) is StreamValue:
                blocks_dict.update({key: value})
        return blocks_dict
