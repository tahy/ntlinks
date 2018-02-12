from django.shortcuts import render
from django import forms
from django.shortcuts import get_object_or_404
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.base import RedirectView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template.loader import render_to_string

from link.models import Link


def make_page_for_cbv(request, object_list, **kwargs):
    """Хелпер для быстрой генерации постранички
        Дефолтный рендер процессор и шаблон формирует ссылки безопасные для прочих get параметров
        Использование:
            - views.py:
                page = make_page(request, Item.objects.all(), count_per_page=2, page_get_parameter='item_page')
            - шаблон:
                <!-- список итемов -->
                - for item in page.object_list
                    = item
                <!-- ссылки на постраничку -->
                = page.render
        Список возможных параметров - смотреть в коде в словаре default
    """

    # значения по умолчанию
    default = {
        'count_per_page': request.session.get('item_per_page', 10),  #количество записей на страницу
        'page_range': 3,  #диапазон страниц
        'page_get_parameter': 'page',  #гет параметр отвечающий за значение текущей страницы
        'render_processor': None,  #рендер процессор (функция, которая рендерит шаблон постранички)
        'template': 'utils/_paginator.html',  #шаблон постранички
    }

    #инициализация параметров
    default.update(kwargs)
    paginator = Paginator(object_list, default['count_per_page'])

    try:
        page = int(request.GET.get(default['page_get_parameter'], '1'))
    except ValueError:
        page = 1

    try:
        page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages)

    def render_processor(request, page, **kwargs):
        """Процессор рендеринга, на случай необходимости
            расширения функционала постранички пишется отдельная функция для рендеринга
            (а то заебали, блеадь, в каждом проекте своя ебнутая постраничка и куда ни ткнись ни хуя не работает)"""

        return render_to_string(
            kwargs['template'],
            {
                'request': request,
                'page': page,
                'page_range': (lambda d, s, e: d[s:e])(range(1, page.paginator.num_pages + 1),
                                                       (lambda n: n >= 0 and n or 0)(
                                                           page.number - 1 - kwargs['page_range']),
                                                       page.number + kwargs['page_range']),
                'page_get_parameter': kwargs['page_get_parameter'],
                'count_per_page': request.session.get('item_per_page', 10)
            })

    def renderer():
        """Формируем замыкание на параметры конкретного пагинатора (необходимо для работы внешнего render_processor-а)"""
        return (callable(default['render_processor']) and default['render_processor'] or render_processor)(request,
                                                                                                           page,
                                                                                                           **default)

    #TODO: дописать возможность передачи рендерера по названию в виде 'app.package.module.calable_object'
    paginator.render = renderer
    return paginator


class LinkForm(forms.Form):
    name = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)


class HomeView(CreateView):
    template_name = 'home.html'
    model = Link
    fields = ['name', 'source']

    def get_success_url(self):
        messages.success(self.request, 'Новая ссылка добавлена!')
        return reverse_lazy('info', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['links'] = Link.objects.order_by('-refer_count', '-created_at')[:20]
        return context


class ByLinkRedirectView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        link = get_object_or_404(Link, link_hash=kwargs['hash'])
        link.update_counter()
        return link.source


class LinkListView(ListView):
    model = Link
    template_name = 'index.html'
    paginate_by = 2

    def get_queryset(self):
        return super(LinkListView, self).get_queryset().order_by('-refer_count', '-created_at')

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True, page_range=10):
        return make_page_for_cbv(self.request, queryset, count_per_page=per_page, page_range=page_range)


class LinkDeleteView(DeleteView):
    model = Link
    success_url = reverse_lazy('index')


class LinkDetailView(DetailView):
    model = Link
