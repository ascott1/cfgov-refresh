from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.contenttypes.models import ContentType

from . import Handler
from ...forms import FilterableListForm, EventArchiveFilterForm, \
    ActivityLogFilterForm, NewsroomFilterForm
from ...models import CFGOVPage, AbstractFilterPage
from ...util.ref import choices_for_page_type
from ...util.util import get_secondary_nav_items, has_active_filters


class FilterableListHandler(Handler):
    def __init__(self, *args, **kwargs):
        super(FilterableListHandler, self).__init__(*args, **kwargs)

    def handle(self, block_tuples):
        forms = self._get_forms(block_tuples)
        self.context['filters'] = self._process_filters(forms, block_tuples)
        self.context['get_secondary_nav_items'] = get_secondary_nav_items
        self.context['has_active_filters'] = has_active_filters

    def _get_forms(self, block_tuples):
        forms = []
        for form_id, block in block_tuples:
            form_class = self._get_filter_form_class()
            form_data = self._process_form_data(form_class, form_id)
            forms.append(form_class(form_data, parent=self.page.parent(),
                                    hostname=self.request.site.hostname))
        return forms

    def _get_filter_form_class(self):
        return FilterableListForm

    def _process_form_data(self, form_class, form_id):
        fields = getattr(form_class, 'declared_fields', {})
        data = {}
        for field in fields:
            request_field_name = 'filter' + str(form_id) + '_' + field
            if field in ['categories', 'topics', 'authors']:
                data[field] = self.request.GET.getlist(request_field_name, [])
            else:
                data[field] = self.request.GET.get(request_field_name, '')
        return data

    def _process_filters(self, forms, block_tuples):
        filters = {'forms': forms, 'page_sets': []}

        for form, block_tuple in zip(forms, block_tuples):
            limit = self._results_per_page(block_tuple[1])
            if form.is_valid():
                page_set = self.get_page_set(form)
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

    def _results_per_page(self, block):
        return block.value['results_limit']

    def get_page_set(self, form):
        # AbstractFilterPage = self._get_filter_page_model()
        query = form._generate_query()
        page_set = AbstractFilterPage.objects.child_of(self.page).filter(query)
        page_set = page_set.live_shared(self.request.site.hostname).distinct()
        return page_set.order_by('-date_published')

    # def _get_filter_page_model(self):
    #     ct = ContentType.objects.get(app_label='v1',
    #                                  model='abstractfilterpage')
    #     return ct.model_class()


class EventArchiveHandler(FilterableListHandler):
    def _get_filter_form_class(self):
        return EventArchiveFilterForm


class NewsroomHandler(FilterableListHandler):
    def _get_filter_form_class(self):
        return NewsroomFilterForm

    def get_page_set(self, form):
        categories = form.cleaned_data.get('categories', [])
        query = form._get_page_queries(categories)
        page_set = AbstractFilterPage.objects.filter(query)
        page_set = page_set.live_shared(self.request.site.hostname)
        return page_set.order_by('-date_published')

    def _get_page_queries(self, categories):
        get_blog, only_blog = self._if_and_only_blog(categories)
        newsroom_q = self._get_newsroom_query(only_blog)
        blog_q = self._get_blog_query(get_blog).distinct()
        return newsroom_q | blog_q

    def _if_and_only_blog(categories):
        get_blog = True
        only_blog = False
        if categories:
            if 'blog' not in categories:
                get_blog = False
            else:
                if len(categories) == 1:
                    only_blog = True
        return get_blog, only_blog

    def _get_newsroom_query(only_blog):
        if not only_blog:
            newsroom_q = AbstractFilterPage.objects.child_of_q(self)
            return newsroom_q & self.generate_query()

    def _get_blog_query(get_blog):
        if get_blog:
            try:
                del self.cleaned_data['categories']
                blog = CFGOVPage.objects.get(slug='blog')
                blog_q = AbstractFilterPage.objects.child_of_q(blog)
                return blog_q & self.generate_query()
            except CFGOVPage.DoesNotExist:
                print 'Blog does not exist'


class ActivityLogHandler(FilterableListHandler):
    def _get_filter_form_class(self):
        return ActivityLogFilterForm

    def get_page_set(self, form):
        queries = {}
        selections = {}
        categories = form.cleaned_data.get('categories', [])
        categories_copy = list(categories)
        
        import pdb; pdb.set_trace()
        selections = self._process_categories(categories)
        self._set_newsroom_query(form, categories, categories_copy, queries)
        self._set_blog_and_report_queries(form, selections, queries)
    
        return self._process_queries(queries, hostname)

    # Set filter selections for Blog and Report and process categories
    def _process_categories(self, categories):
        selections = {'blog': False, 'research-reports': False}
        for category in selections.keys():
            if not categories or category in categories:
                selections[category] = True
        for selection, is_selected in selections.items():
            if is_selected and selection in categories:
                del categories[categories.index(selection)]
        return selections

    # Set Newsroom query if Newsroom category(s) selected
    def _set_newsroom_query(self, form, categories, categories_copy, queries):
        newsroom_choices = [c[0] for c in choices_for_page_type('newsroom')]
        is_newsroom_category = map(lambda x: x in newsroom_choices, categories)
        if not categories_copy or is_newsroom_category:
            try:
                parent = CFGOVPage.objects.get(slug='newsroom')
                query = AbstractFilterPage.objects.child_of_q(parent)
                query &= form._generate_query()
                queries['newsroom'] = query
            except CFGOVPage.DoesNotExist:
                print 'Newsroom does not exist'

    # Set Blog and Report queries if they were selected
    def _set_blog_and_report_queries(self, form, selections, queries):
        del self.cleaned_data['categories']
        for slug, is_selected in selections.items():
            if is_selected:
                try:
                    parent = CFGOVPage.objects.get(slug=slug)
                    childof = AbstractFilterPage.objects.child_of_q(parent)
                    queries.update({
                        slug: childof & form._generate_query()
                    })
                except CFGOVPage.DoesNotExist:
                    print slug, 'does not exist'

    # OR all selected queries together
    def _process_queries(self, queries, hostname):
        final_q = reduce(lambda x, y: x | y, queries.values())
        page_set = AbstractFilterPage.objects.filter(final_q)
        page_set = page_set.live_shared(hostname).distinct()
        return page_set.order_by('-date_published')
