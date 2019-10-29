from odoo import http, modules, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug


class WebsiteDictionary(http.Controller):
    _items_per_page = 20

    @http.route(['/dict/',
                 '/dict/page/<int:page>',
                 '/dict/<model("res.lang"):lg_id>',
                 '/dict/<model("res.lang"):lg_id>/page/<int:page>',
                 ], type='http', auth="public", website=True, csrf=False)
    def dictionary(self, lg_id=None, page=1, keyword='', sorting=None, **kwargs):
        if request.env.user.has_group('base.group_portal') or request.env.user.has_group('base.group_user'):
            if kwargs.get('add_word'):
                if kwargs.get('add_dict'):
                    if kwargs.get('add_lang'):
                        lang_id = request.env['res.lang'].search([("id", "=", kwargs.get('add_lang'))])
                        meaning = kwargs.get('add_dict').lower()
                        dict_id = request.env['open.meaning'].search([
                            ('name', '=', meaning), ("lang_id", "=", lang_id.id)])
                        if not dict_id:
                            dict_id = request.env['open.meaning'].create({
                                'name': meaning,
                                'lang_id': lang_id.id,
                            })
                        request.env['open.word'].search([('id', '=', kwargs.get('add_word'))]).update({'dictionary_ids': [(4, dict_id.id)]})

            if kwargs.get('rm_word'):
                if kwargs.get('rm_dict'):
                    dict_id = request.env['open.meaning'].search([('id', '=', (kwargs.get('rm_dict')))])
                    request.env['open.word'].search([('id', '=', kwargs.get('rm_word'))]).update({'dictionary_ids': [(3, dict_id.id)]})

        if kwargs.get('lgs_id'):
            lg_id = request.env['res.lang'].search([("id", "=", kwargs.get('lgs_id'))])

        if not lg_id:
            lg_id = request.env['res.lang'].search([("name", "=", "English")])

        words = request.env['open.word']
        exclude = ('(', ')', ',', ',)', ',-', ',-⸃', ',]', ',⸃', ',⸆', '-', '-.', '-;', '-⸃', '.', '.-', '.]', '.]]',
                   '.⸃', '.⸆', '.⸆]]', ';', ';)', ';-', ';⸃', '[', ']', '·', '·)', '·-', '·⸃', '⸂', '⸃', '⸆', '⸆,', '⸆.'
                   '⸆;', '᾽')
        domain = [('name', '!=', exclude)]
        if sorting:
            try:
                words._generate_order_by(sorting, None)
            except ValueError:
                sorting = False
        else:
            sorting = 'name'

        url_args = {'sorting': sorting}
        if keyword:
            domain += [('name', 'ilike', keyword)]
            url_args['keyword'] = keyword
        domain += [('name', 'ilike', keyword)]
        url = '/dict/%s' % slug(lg_id)
        values = {}
        total = words.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._items_per_page,
            url_args=url_args,
        )
        results = words.search(domain, offset=(page - 1) * self._items_per_page, limit=self._items_per_page, order=sorting)
        values.update({
            'user_id': request.env.user,
            'lgs': request.env['res.lang'].search([]),
            'lg_id': lg_id,
            'keyword': keyword,
            'results': results,
            'pager': pager,
            'total': total,
            # 'sorting': sorting
        })
        return request.render("transliterate.dictionary", values)

