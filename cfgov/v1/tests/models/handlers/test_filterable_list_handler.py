import mock
from unittest import TestCase
from ....models.handlers.filterable_list_handler import FilterableListHandler


class TestFilterableListHandler(TestCase):
    def setUp(self):
        self.page = mock.Mock()
        self.request = mock.Mock()
        self.handler = FilterableListHandler(self.page, self.request)

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_filter_blocks')
    def test_handle_calls_get_filter_blocks(self, mock_get_filter_blocks):
        mock_get_filter_blocks.return_value = False
        self.handler.handle({})
        assert mock_get_filter_blocks.called

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_filter_blocks')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.process_filters')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_forms')
    def test_handle_calls_get_forms(self, mock_get_forms, mock_process_filters, mock_get_filter_blocks):
        self.handler.handle({})
        assert mock_get_forms.called

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_filter_blocks')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.process_filters')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_forms')
    def test_handle_calls_process_filters(self, mock_get_forms, mock_process_filters, mock_get_filter_blocks):
        self.handler.handle({})
        assert mock_process_filters.called

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_filter_blocks')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.process_filters')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_forms')
    def test_handle_calls_get_forms(self, mock_get_forms, mock_process_filters, mock_get_filter_blocks):
        self.handler.handle({})
        assert mock_get_forms.called

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_filter_blocks')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.process_filters')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_forms')
    def test_handle_sets_context(self, mock_get_forms, mock_process_filters, mock_get_filter_blocks):
        context = {}
        self.handler.handle(context)
        for key in ['filters', 'get_secondary_nav_items', 'has_active_filters']:
            assert key in context.keys()

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_streamfield_blocks')
    def test_get_filter_blocks_calls_get_streamfield_blocks(self, mock_get_sf_blocks):
        self.handler.get_filter_blocks()
        assert mock_get_sf_blocks.called

    @mock.patch('v1.models.handlers.Handler.get_streamfield_blocks')
    def test_get_filter_blocks_returns_list_of_tuples(self, mock_get_sf_blocks):
        block = mock.Mock()
        block.block_type = 'filter_controls'
        mock_get_sf_blocks.return_value = {'key': [block]}
        result = self.handler.get_filter_blocks()
        assert type(result) is list
        assert type(result[0]) is tuple
        assert result[0][0] == 0
        assert result[0][1] == block

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.process_form_data')
    def test_get_forms_calls_get_filter_form_class_on_block_class(self, mock_process_form_data):
        block = mock.Mock()
        mock_form_class = mock.Mock()
        block.block.get_filter_form_class.return_value = mock_form_class
        block_tuples = [(0, block)]
        self.handler.get_forms(block_tuples)
        assert block.block.get_filter_form_class.called

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.process_form_data')
    def test_get_forms_calls_process_form_data_with_form_class_and_form_id(self, mock_process_form_data):
        block = mock.Mock()
        mock_form_class = mock.Mock()
        block.block.get_filter_form_class.return_value = mock_form_class
        block_tuples = [(0, block)]
        mock_process_form_data.return_value = 'test'
        self.handler.get_forms(block_tuples)
        mock_process_form_data.assert_called_with(mock_form_class, 0)

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.process_form_data')
    def test_get_forms_instantiates_form(self, mock_process_form_data):
        block = mock.Mock()
        mock_form_class = mock.Mock()
        block.block.get_filter_form_class.return_value = mock_form_class
        block_tuples = [(0, block)]
        mock_process_form_data.return_value = 'test'
        self.handler.get_forms(block_tuples)
        mock_form_class.assert_called_with('test', parent=self.page.parent(), hostname=self.request.site.hostname)

    def test_process_form_data_raises_exception_for_form_class_without_declared_fields(self):
        mock_form_class = 'not a form class'
        with self.assertRaises(AttributeError) as ae:
            self.handler.process_form_data(mock_form_class, 0)

    def test_process_form_data_adds_declared_field_as_key(self):
        mock_form_class = mock.Mock()
        mock_form_class.declared_fields = ['topics']
        data = self.handler.process_form_data(mock_form_class, 0)
        assert 'topics' in data

    def test_process_form_data_adds_field_value_from_request(self):
        mock_form_class = mock.Mock()
        mock_form_class.declared_fields = ['topics', 'date']
        data = self.handler.process_form_data(mock_form_class, 0)
        self.request.GET.getlist.assert_called_with('filter0_topics', [])
        self.request.GET.get.assert_called_with('filter0_date', '')

    def test_process_filters_returns_filters_context(self):
        result = self.handler.process_filters([], [])
        assert 'forms' in result
        assert 'page_sets' in result

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.results_per_page')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_page_set')
    def test_process_filters_calls_is_valid_for_each_form(self, mock_getpageset, mock_resultsperpage):
        forms = [mock.Mock(), mock.Mock()]
        block_tuples = [mock.MagicMock(), mock.MagicMock()]
        self.handler.process_filters(forms, block_tuples)
        for form in forms:
            assert form.is_valid.called

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.results_per_page')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_page_set')
    def test_process_filters_calls_results_per_page(self, mock_getpageset, mock_resultsperpage):
        block_tuples = [mock.MagicMock()]
        self.handler.process_filters([mock.Mock()], block_tuples)
        mock_resultsperpage.assert_called_with(block_tuples[0][1])

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.results_per_page')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_page_set')
    def test_process_filters_calls_generate_query_on_form(self, mock_getpageset, mock_resultsperpage):
        form = mock.Mock()
        block_tuples = [mock.MagicMock()]
        self.handler.process_filters([form], block_tuples)
        assert form.generate_query.called

    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.results_per_page')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_page_set')
    def test_process_filters_calls_get_page_set(self, mock_getpageset, mock_resultsperpage):
        form = mock.Mock()
        block_tuples = [mock.MagicMock()]
        self.handler.process_filters([form], block_tuples)
        assert mock_getpageset.called

    @mock.patch('v1.models.handlers.filterable_list_handler.Paginator')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.results_per_page')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_page_set')
    def test_process_filters_instantiates_Paginator_with_page_set_and_limit(self, mock_getpageset, mock_resultsperpage, mock_paginator):
        mock_getpageset.return_value = 'page set'
        mock_resultsperpage.return_value = '1'
        form = mock.Mock()
        block_tuples = [mock.MagicMock()]
        self.handler.process_filters([form], block_tuples)
        mock_paginator.assert_called_with('page set', '1')

    @mock.patch('v1.models.handlers.filterable_list_handler.Paginator')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.results_per_page')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_page_set')
    def test_process_filters_gets_page_number_from_request(self, mock_getpageset, mock_resultsperpage, mock_paginator):
        form = mock.Mock()
        block_tuples = [mock.MagicMock()]
        paginator = mock.Mock()
        mock_paginator.return_value = paginator
        self.handler.process_filters([form], block_tuples)
        self.request.GET.get.assert_called_with('page')

    @mock.patch('v1.models.handlers.filterable_list_handler.Paginator')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.results_per_page')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_page_set')
    def test_process_filters_calls_paginators_page_fn(self, mock_getpageset, mock_resultsperpage, mock_paginator):
        form = mock.Mock()
        block_tuples = [mock.MagicMock()]
        paginator = mock.Mock()
        mock_paginator.return_value = paginator
        self.handler.process_filters([form], block_tuples)
        assert paginator.page.called

    @mock.patch('v1.models.handlers.filterable_list_handler.ContentType')
    @mock.patch('v1.models.handlers.filterable_list_handler.Paginator')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.results_per_page')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_page_set')
    def test_process_filters_calls_none_for_invalid_form(self, mock_getpageset, mock_resultsperpage, mock_paginator, mock_contenttype):
        form = mock.Mock()
        form.is_valid.return_value = False
        block_tuples = [mock.MagicMock()]
        paginator = mock.Mock()
        mock_paginator.return_value = paginator
        self.handler.process_filters([form], block_tuples)
        assert mock_contenttype.objects.none.called

    @mock.patch('v1.models.handlers.filterable_list_handler.ContentType')
    @mock.patch('v1.models.handlers.filterable_list_handler.Paginator')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.results_per_page')
    @mock.patch('v1.models.handlers.filterable_list_handler.FilterableListHandler.get_page_set')
    def test_process_filters_instantiates_Paginator_for_invalid_form(self, mock_getpageset, mock_resultsperpage, mock_paginator, mock_contenttype):
        form = mock.Mock()
        form.is_valid.return_value = False
        block_tuples = [mock.MagicMock()]
        paginator = mock.Mock()
        mock_paginator.return_value = paginator
        self.handler.process_filters([form], block_tuples)
        assert mock_paginator.called

    @mock.patch('v1.models.handlers.filterable_list_handler.ContentType')
    def test_get_page_set_gets_abstractfilterpage_content_type(self, mock_contenttype):
        self.handler.get_page_set(mock.Mock(), mock.Mock())
        mock_contenttype.objects.get.assert_called_with(app_label='v1', model='abstractfilterpage')

    @mock.patch('v1.models.handlers.filterable_list_handler.ContentType')
    def test_get_page_set_calls_model_class_on_contenttype(self, mock_contenttype):
        page_ct = mock.Mock()
        mock_contenttype.objects.get.return_value = page_ct
        self.handler.get_page_set(mock.Mock(), mock.Mock())
        assert page_ct.model_class.called

    @mock.patch('v1.models.handlers.filterable_list_handler.ContentType')
    def test_get_page_set_calls_filtering_functions(self, mock_contenttype):
        page_ct = mock.Mock()
        mock_contenttype.objects.get.return_value = page_ct
        self.handler.get_page_set(mock.Mock(), mock.Mock())
        page_ct.model_class().objects.child_of.assert_called_with(self.page)
        assert page_ct.model_class().objects.child_of().distinct.called
        assert page_ct.model_class().objects.child_of().distinct().live_shared.called
        assert page_ct.model_class().objects.child_of().distinct().live_shared().filter.called
        assert page_ct.model_class().objects.child_of().distinct().live_shared().filter().order_by.called

    def test_results_per_page(self):
        block = mock.MagicMock()
        result = self.handler.results_per_page(block)
        assert result == block.value['results_limit']
