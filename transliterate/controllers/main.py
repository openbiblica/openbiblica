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
    def dictionary(self, lg_id=None, page=1, keyword='', src_id='', sorting=None, **kwargs):
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

        if src_id:
            domain += [('lang_id.code', '=', src_id)]
            url_args['src_id'] = src_id

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
        })
        return request.render("transliterate.dictionary", values)

    @http.route(['/compute/frequency'], type='http', auth="user", website=True)
    def compute_frequency(self, **kwargs):
        if not request.env.user.has_group('website.group_website_publisher'):
            return request.redirect('/')
        words = request.env['open.word']
        exclude = ('(', ')', ',', ',)', ',-', ',-⸃', ',]', ',⸃', ',⸆', '-', '-.', '-;', '-⸃', '.', '.-', '.]', '.]]',
                   '.⸃', '.⸆', '.⸆]]', ';', ';)', ';-', ';⸃', '[', ']', '·', '·)', '·-', '·⸃', '⸂', '⸃', '⸆', '⸆,', '⸆.'
                   '⸆;', '᾽')
        word = words.search([('name', '!=', exclude), ('frequency', '=', -1)])[0]
        values = {
            'word': word
        }
        return request.render("transliterate.compute", values)

    @http.route(['/compute/f'], type='json', auth="user", methods=['POST'], website=True)
    def compute_f(self, **kwargs):
        if not kwargs.get('word_id'):
            return
        word_id = request.env['open.word'].sudo().search([('id', '=', int(kwargs.get('word_id')))])
        word_id['frequency'] = len(word_id.point_ids)
        words = request.env['open.word']
        exclude = ('(', ')', ',', ',)', ',-', ',-⸃', ',]', ',⸃', ',⸆', '-', '-.', '-;', '-⸃', '.', '.-', '.]', '.]]',
                   '.⸃', '.⸆', '.⸆]]', ';', ';)', ';-', ';⸃', '[', ']', '·', '·)', '·-', '·⸃', '⸂', '⸃', '⸆', '⸆,', '⸆.'
                   '⸆;', '᾽')
        if words.search([('name', '!=', exclude), ('frequency', '=', -1)]):
            word = words.search([('name', '!=', exclude), ('frequency', '=', -1)])[0]
            value = {'word_id': word.id,
                     'name': word_id.name,
                     'frequency': word_id.frequency}
        else:
            value = {}
        return value

    @http.route(['/new/language'], type='http', auth="user", website=True)
    def new_language(self, **kwargs):
        if not request.env.user:
            return request.redirect('/')
        return request.render("transliterate.new_lang")

    @http.route(['/save/language'], type='http', auth="user", website=True)
    def save_language(self, **kwargs):
        if not request.env.user:
            return request.redirect('/')
        if not kwargs.get('language_name'):
            return request.redirect(request.httprequest.referrer)
        request.env['res.lang'].create({
            'name': kwargs.get('language_name'),
            'code': kwargs.get('language_code'),
            'iso_code': kwargs.get('language_iso_code'),
            'direction': kwargs.get('direction'),
            'active': True
        })
        return request.redirect('/dict')

    @http.route(['/meaning/<model("open.meaning"):meaning_id>'],
                type='http', auth="public", website=True, csrf=False)
    def view_meaning(self, meaning_id=0):
        similar_ids = request.env['open.meaning'].search([
            ('name', 'ilike', meaning_id.name),
            ('id', '!=', meaning_id.id),
            ("lang_id", "=", meaning_id.lang_id.id)])
        values = {
            'meaning_id': meaning_id,
            'similar_ids': similar_ids,
        }
        return request.render("transliterate.view_meaning", values)

