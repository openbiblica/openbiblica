import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
import werkzeug.utils
import base64

from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo.addons.web.controllers.main import binary_content


class WebsiteBiblicaAjax(http.Controller):

    def read_file(self, content_id=0):
        status, headers, content = binary_content(model='open.content', id=content_id, field='files',
                                                  env=request.env(user=SUPERUSER_ID))
        if status == 304:
            response = werkzeug.wrappers.Response(status=status, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200:
            response = request.not_found()
        else:
            filename = request.env['open.content'].sudo().search([('id', '=', content_id)]).name
            content_base64 = base64.b64decode(content)
            name = [('Content-Disposition', 'attachment; filename=' + filename + '.usfm;')]
            response = request.make_response(content_base64, name)
        return response

    @http.route(['/c/file/<int:content_id>'], type='http', auth="public")
    def download_file(self, content_id=0):
        response = self.read_file(content_id)
        return response

    @http.route(['/get/langs'], type='json', auth="public", website=True)
    def languages_data(self):
        bibs = request.env['open.biblica'].sudo().search([])
        lngs = request.env['res.lang'].sudo().search([('id', 'in', bibs.mapped('lang_id.id'))])
        vals = [{'id': lang.id, 'name': lang.name} for lang in lngs]
        return vals

    @http.route(['/get/bibles'], type='json', auth="public", methods=['POST'], website=True)
    def bibles_data(self, **kwargs):
        if not kwargs.get('lang_id'):
            return None
        bibs = request.env['open.biblica'].sudo().search([('lang_id', '=', int(kwargs.get('lang_id')))])
        vals = [{'id': bible.id, 'name': bible.name} for bible in bibs]
        return vals

    @http.route(['/get/book'], type='json', auth="public", methods=['POST'], website=True)
    def books_data(self, **kwargs):
        if not kwargs.get('bible_id'):
            return None
        books = request.env['open.content'].sudo().search([('biblica_id', '=', int(kwargs.get('bible_id')))])
        vals = [{'id': book.id, 'name': book.name} for book in books]
        return vals

    @http.route(['/get/part'], type='json', auth="public", methods=['POST'], website=True)
    def parts_data(self, **kwargs):
        if not kwargs.get('book_id'):
            return None
        parts = request.env['open.part'].sudo().search([('content_id', '=', int(kwargs.get('book_id')))])
        vals = []
        for part in parts:
            if part.children_ids:
                for chapter in part.children_ids:
                    vals += [{'id': chapter.id, 'name': chapter.name}]
            else:
                vals += [{'id': part.id, 'name': part.name}]
        return vals

    @http.route(['/get/verse'], type='json', auth="public", methods=['POST'], website=True)
    def verses_data(self, **kwargs):
        if not kwargs.get('part_id'):
            return None
        verses = request.env['open.line'].sudo().search([('part_id.id', '=', int(kwargs.get('part_id'))),
                                                         ('verse', '!=', ' ')])
        vals = [{'id': verse.id, 'name': verse.verse} for verse in verses]
        return vals

    @http.route(['/get/subcontent'], type='json', auth="public", methods=['POST'], website=True)
    def subcontents_data(self, **kwargs):
        if not kwargs.get('content_id'):
            return None
        subcontents = request.env['open.subcontent'].sudo().search([
            ('content_id.id', '=', int(kwargs.get('content_id')))])
        vals = [{'id': subcontent.id, 'name': subcontent.name} for subcontent in subcontents]
        return vals

    @http.route(['/add/subcontent'], type='json', auth="user", methods=['POST'], website=True)
    def add_subcontents(self, **kwargs):
        if not kwargs.get('content_id'):
            return None
        user_id = request.env.user
        content_id = request.env['open.content'].sudo().search([("id", "=", int(kwargs.get('content_id')))])
        if content_id.create_id == user_id:
            seq = len(content_id.subcontent_ids) + 1
            request.env['open.subcontent'].sudo().create({
                'content_id': content_id.id,
                'create_id': user_id.id,
                'name': kwargs.get('name'),
                'sequence': seq,
            })
        return

    @http.route(['/get/chapter'], type='json', auth="public", methods=['POST'], website=True)
    def chapters_data(self, **kwargs):
        if not kwargs.get('content_id'):
            return None
        chapters = request.env['open.part'].sudo().search([
            ('content_id.id', '=', int(kwargs.get('content_id')))])
        vals = [{'id': chapter.id, 'name': chapter.name} for chapter in chapters]
        return vals

    @http.route(['/add/chapter'], type='json', auth="user", methods=['POST'], website=True)
    def add_chapters(self, **kwargs):
        if not kwargs.get('content_id'):
            return
        user_id = request.env.user
        content_id = request.env['open.content'].sudo().search([("id", "=", int(kwargs.get('content_id')))])
        if content_id.create_id == user_id:
            seq = len(content_id.part_ids) + 1
            request.env['open.part'].sudo().create({
                'content_id': content_id.id,
                'create_id': user_id.id,
                'name': kwargs.get('name'),
                'sequence': seq,
                'forum_id': content_id.forum_id.id,
            })
        return

    @http.route(['/get/dictionary'], type='json', auth="public", methods=['POST'], website=True)
    def dictionary_data(self, **kwargs):
        word_id = request.env['open.word'].sudo().search([('id', '=', int(kwargs.get('word_id')))])
        dict_ids = request.env['open.meaning'].sudo().search([
            ('id', 'in', word_id.dictionary_ids.ids),
            ('lang_id', '=', int(kwargs.get('lang_id')))
        ])
        # dict_ids = word_id.dictionary_ids.search([('lang_id', '=', int(kwargs.get('lang_id')))])
        vals = [{'name': dict_id.name} for dict_id in dict_ids]
        return vals

    @http.route(['/add/dictionary'], type='json', auth="user", methods=['POST'], website=True)
    def add_dictionary(self, **kwargs):
        if not kwargs.get('dict_id'):
            return
        word_id = request.env['open.word'].sudo().search([('id', '=', int(kwargs.get('word_id')))])
        lang_id = request.env['res.lang'].sudo().search([('id', '=', int(kwargs.get('lang_id')))])
        meaning = kwargs.get('dict_id').lower()
        dict_id = request.env['open.meaning'].sudo().search([
            ('name', '=', meaning), ("lang_id", "=", lang_id.id)])
        if not dict_id:
            dict_id = request.env['open.meaning'].create({
                'name': meaning,
                'lang_id': lang_id.id,
            })
        word_id.update({
            'dictionary_ids': [(4, dict_id.id)]
        })
        return

    @http.route(['/un_dict/<model("open.meaning"):dict_id>/<model("open.word"):word_id>'], type='http', auth='user', website=True)
    def un_dictionary(self, dict_id=0, word_id=0):
        word_id.update({
            'dictionary_ids': [(3, dict_id.id)]
        })
        return request.redirect(request.httprequest.referrer)

