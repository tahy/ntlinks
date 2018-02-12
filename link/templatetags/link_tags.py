from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def get_add(context, value, name_get_parameter='page', exclude_vars=''):
    """мегаполезная шняга: формирует ссцыль для постранички, не трогает остальные get-параметры если они есть"""

    exclude_vars = exclude_vars.split(',')
    res_get = ''
    parameters = context['request'].GET

    for key in parameters:
        if key in exclude_vars: continue
        if key == name_get_parameter:
            res_get += '&' + key + '=' + str(value)
        else:
            for val in parameters.getlist(key):
                res_get += '&' + key + '=' + str(value)

    if not name_get_parameter in parameters:
        res_get += '&' + name_get_parameter + '=' + str(value)

    return u'?' + res_get[1:]