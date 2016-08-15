from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.contenttypes.models import ContentType

from . import Handler
from ...util.util import get_secondary_nav_items, has_active_filters


class FilterableListHandler(Handler):
    def handle(self, context):
        block_tuples = self.get_filter_blocks()
        if block_tuples:
            forms = self.get_forms(block_tuples)
            context['filters'] = self.process_filters(forms, block_tuples)
            context['get_secondary_nav_items'] = get_secondary_nav_items
            context['has_active_filters'] = has_active_filters

    def get_filter_blocks(self):
        block_tuples = []
        blocks_dict = self.get_streamfield_blocks()
        for blocks_list in blocks_dict.values():
            for form_id, block in enumerate(blocks_list):
                if block.block_type == 'filter_controls':
                    block_tuples.append((form_id, block))
        return block_tuples

    def get_forms(self, block_tuples):
        forms = []
        for form_id, block in block_tuples:
            form_class = block.block.get_filter_form_class(block)
            form_data = self.process_form_data(form_class, form_id)
            forms.append(form_class(form_data, parent=self.page.parent(),
                                    hostname=self.request.site.hostname))
        return forms

    def process_form_data(self, form_class, form_id):
        try:
            fields = getattr(form_class, 'declared_fields')
        except AttributeError as e:
            raise e
        data = {}
        for field in fields:
            request_field_name = 'filter' + str(form_id) + '_' + field
            if field in ['categories', 'topics', 'authors']:
                data[field] = self.request.GET.getlist(request_field_name, [])
            else:
                data[field] = self.request.GET.get(request_field_name, '')
        return data

    def process_filters(self, forms, block_tuples):
        filters = {'forms': forms, 'page_sets': []}

        for form, block_tuple in zip(forms, block_tuples):
            limit = self.results_per_page(block_tuple[1])
            if form.is_valid():
                query = form.generate_query()
                page_set = self.get_page_set(query, self.request.site.hostname)
                paginator = Paginator(page_set, limit)
                page = self.request.GET.get('page')

                # Get the page number in the request and get the page from the
                # paginator to serve.
                try:
                    pages = paginator.page(page)
                except PageNotAnInteger:
                    pages = paginator.page(1)
                except EmptyPage:
                    pages = paginator.page(paginator.num_pages)

                filters['page_sets'].append(pages)
            else:
                empty_page_set = ContentType.objects.none()
                paginator = Paginator(empty_page_set, limit)
                filters['page_sets'].append(paginator.page(1))

            filters['forms'].append(form)

        return filters

    def get_page_set(self, query, hostname):
        filterpage_ct = ContentType.objects.get(app_label='v1',
                                                model='abstractfilterpage')
        children = filterpage_ct.model_class().objects.child_of(self.page)
        children = children.distinct().live_shared(hostname).filter(query)
        return children.order_by('-date_published')

    def results_per_page(self, block):
        return block.value['results_limit']
