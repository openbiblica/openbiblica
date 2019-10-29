# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
import werkzeug.utils
import logging
import base64
import json
import re

from odoo import http, modules, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.web.controllers.main import binary_content
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WebsiteBiblica(http.Controller):
    _items_per_page = 20
    _comment_per_page = 5
    _verse_per_page = 10

    @http.route(['/search/',
                 '/search/page/<int:page>',
                 '/search/lang/<int:s_lang>',
                 '/search/key/<string:keyword>/lang/<int:s_lang>',
                 ], type='http', auth="public", website=True, csrf=False)
    def search(self, page=1, search='', sorting=None, keyword=None, s_lang=None, **kwargs):
        if keyword:
            search = keyword

        if not s_lang:
            s_lang = request.env['res.lang'].search([("name", "=", "English")]).id

        if not search:
            if kwargs.get('verse_id'):
                return request.redirect('/line/%s' % slug(request.env['open.line'].sudo().search([('id', '=', kwargs.get('verse_id'))])))
            elif kwargs.get('part_id'):
                return request.redirect('/part/%s' % slug(request.env['open.part'].sudo().search([('id', '=', kwargs.get('part_id'))])))
            elif kwargs.get('book_id'):
                return request.redirect('/content/%s' % slug(request.env['open.content'].sudo().search([('id', '=', kwargs.get('book_id'))])))
            elif kwargs.get('bible_id'):
                return request.redirect('/biblica/%s' % slug(request.env['open.biblica'].sudo().search([('id', '=', kwargs.get('bible_id'))])))
            elif kwargs.get('language_id'):
                return request.redirect('/language/%s' % slug(request.env['res.lang'].sudo().search([('id', '=', kwargs.get('language_id'))])))
            else:
                return request.redirect(request.httprequest.referrer)
        user = request.env.user
        lines = request.env['open.line']
        domain = []
        url = '/search'
        # url = '/search/%s/%s' % (keyword, s_lang)
        url_args = {}
        values = {}

        if kwargs.get('verse_id'):
            line_id = request.env['open.line'].sudo().search([('verse', '=', kwargs.get('verse_id'))])
            url_args['id'] = line_id.id
            values['id'] = line_id.id
            domain += [('id', '=', line_id.id)]
        elif kwargs.get('part_id'):
            part_id = request.env['open.part'].sudo().search([('id', '=', kwargs.get('part_id'))])
            url_args['part_id'] = part_id.id
            values['part_id'] = part_id.id
            domain += [('part_id', '=', part_id.id)]
        elif kwargs.get('book_id'):
            content_id = request.env['open.content'].sudo().search([('id', '=', kwargs.get('book_id'))])
            url_args['content_id'] = content_id.id
            values['content_id'] = content_id.id
            domain += [('content_id', '=', content_id.id)]
        elif kwargs.get('bible_id'):
            biblica_id = request.env['open.biblica'].sudo().search([('id', '=', kwargs.get('biblica_id'))])
            url_args['biblica_id'] = biblica_id.id
            values['biblica_id'] = biblica_id.id
            domain += [('biblica_id', '=', biblica_id.id)]
        elif kwargs.get('language_id'):
            lang_id = request.env['res.lang'].sudo().search([('id', '=', kwargs.get('language_id'))])
            url_args['lang_id'] = lang_id.id
            values['lang_id'] = lang_id.id
            domain += [('lang_id', '=', lang_id.id)]

        if search:
            search = search.replace('.', ' ')
            url_args['search'] = search
            values['search'] = search
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]
        # if sorting:
        #     # check that sorting is valid
        #     # retro-compatibily for V8 and google links
        #     try:
        #         lines._generate_order_by(sorting, None)
        #         url_args['sorting'] = sorting
        #     except ValueError:
        #         sorting = False
        total = lines.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._items_per_page,
            url_args=url_args,
        )
        results = lines.search(domain, offset=(page - 1) * self._items_per_page, limit=self._items_per_page,
                               order=sorting)

        values.update({
            'user': user,
            'results': results,
            'sorting': sorting,
            'pager': pager,
            'search': search,
            'total': total,
            's_lang': s_lang,
        })
        return request.render("website_openbiblica.view_search", values)

    @http.route(['/language/<model("res.lang"):lang_id>',
                 '/language/<model("res.lang"):lang_id>/page/<int:page>'],
                type='http', auth="public", website=True, csrf=False)
    def view_language(self, lang_id=None, page=1, **kwargs):
        biblicas = request.env['open.biblica'].search([('lang_id', '=', lang_id.id)])
        topic = request.env['forum.post'].search([('name', '=', lang_id.name), ('first', '=', True)])
        posts = request.env['forum.post']
        domain = [('name', '=', lang_id.name), ('first', '=', False)]
        url_args = {}
        url = '/lang/%s' % lang_id.id
        values = {}
        total = posts.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._comment_per_page,
            url_args=url_args,
        )
        results = posts.search(domain, offset=(page - 1) * self._comment_per_page, limit=self._comment_per_page)

        values.update({
            'user_id': request.env.user,
            'lang_id': lang_id,
            'biblicas': biblicas,
            'results': results,
            'pager': pager,
            'total': total,
            'topic': topic,
        })
        return request.render("website_openbiblica.view_lang", values)

    # BIBLICA

    @http.route(['/biblica/<model("open.biblica"):biblica_id>',
                 '/biblica/<model("open.biblica"):biblica_id>/page/<int:page>'],
                type='http', auth="public", website=True, csrf=False)
    def view_biblica(self, biblica_id=0, page=1):
        topic = request.env['forum.post'].search([('biblica_id', '=', biblica_id.id), ('first', '=', True)])
        posts = request.env['forum.post']
        domain = [('biblica_id', '=', biblica_id.id), ('first', '=', False)]
        url_args = {}
        url = '/biblica/%s' % biblica_id.id
        values = {}
        total = posts.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._comment_per_page,
            url_args=url_args,
        )
        results = posts.search(domain, offset=(page - 1) * self._comment_per_page, limit=self._comment_per_page)

        values.update({
            'user_id': request.env.user,
            'biblica_id': biblica_id,
            'results': results,
            'pager': pager,
            'total': total,
            'topic': topic,
        })
        return request.render("website_openbiblica.view_biblica", values)

    @http.route('/create/biblica', type='http', auth="user", website=True)
    def biblica_editor(self):
        values = {
            'languages': request.env['res.lang'].sudo().search([]),
        }
        return request.render("website_openbiblica.biblica_editor", values)

    @http.route('/biblicas', type='http', auth="public", website=True, csrf=False)
    def biblicas(self):
        values = {
            'interlinears': request.env['open.biblica'].sudo().search([('is_interlinear', '=', True)]),
            'biblicas': request.env['open.biblica'].sudo().search([('is_interlinear', '=', False)]),
        }
        return request.render("website_openbiblica.biblicas", values)

    @http.route(['/save/biblica'], type='http', auth="user", methods=['POST'], website=True)
    def save_biblica(self, **kwargs):
        user_id = request.env.user
        if kwargs.get('language_name'):
            lang_id = request.env['res.lang'].create({
                'name': kwargs.get('language_name'),
                'code': kwargs.get('language_code'),
                'iso_code': kwargs.get('language_iso_code'),
                'direction': kwargs.get('direction'),
                'active': True
            })
        elif kwargs.get('lang_id'):
            lang_id = request.env['res.lang'].search([("id", "=", kwargs.get('lang_id'))])
        else:
            return request.redirect(request.httprequest.referrer)
        forum_id = request.env['forum.forum'].search([("name", "=", lang_id.name)])
        if not forum_id:
            forum_id = request.env['forum.forum'].create({'name': lang_id.name})
        if kwargs.get('biblica_id'):
            biblica_id = request.env['open.biblica'].search([("id", "=", kwargs.get('biblica_id'))])
            if biblica_id.create_id != user_id:
                return request.redirect('/my/home')
            biblica_id.update({
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'lang_id': lang_id.id,
                'forum_id': forum_id.id,
            })
        else:
            biblica_id = request.env['open.biblica'].sudo().create({
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'create_id': user_id.id,
                'lang_id': lang_id.id,
                'forum_id': forum_id.id,
            })
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/comment/b/<model("open.biblica"):biblica_id>'], type='http', auth="user", methods=['POST'], website=True)
    def post_biblica_comment(self, biblica_id=0, **kwargs):
        if not kwargs.get('content'):
            return request.redirect(request.httprequest.referrer)
        forum_id = biblica_id.forum_id
        parent_id = request.env['forum.post'].search([("biblica_id", "=", biblica_id.id), ("first", "=", True)])
        if not parent_id:
            parent_id = request.env['forum.post'].create({
                'forum_id': forum_id.id,
                'name': biblica_id.name,
                'content': biblica_id.name,
                'post_type': 'discussion',
                'biblica_id': biblica_id.id,
                'first': True,
            })
        request.env['forum.post'].create({
            'forum_id': forum_id.id,
            'name': parent_id.name,
            'content': kwargs.get('content'),
            'post_type': 'discussion',  # tde check in selection field
            'parent_id': parent_id.id,
            'biblica_id': biblica_id.id,
        })
        return request.redirect(request.httprequest.referrer)

    @http.route('/edit/biblica', type='http', auth="user", website=True)
    def edit_biblica(self, **kwargs):
        biblica_id = request.env['open.biblica'].search([("id", "=", kwargs.get('biblica_id'))])
        if biblica_id.create_id == request.env.user:
            values = {
                'biblica_id': biblica_id,
                'languages': request.env['res.lang'].sudo().search([]),
            }
            return request.render("website_openbiblica.biblica_editor", values)
        else:
            return request.redirect(request.httprequest.referrer)

    # CONTENT

    @http.route(['/add/content'], type='http', auth="user", website=True)
    def add_content(self, **kwargs):
        biblica_id = request.env['open.biblica'].sudo().search([('id', '=', kwargs.get('biblica_id'))])
        if biblica_id.create_id == request.env.user:
            contents = request.env['open.content'].sudo().search([('biblica_id', '=', biblica_id.id)])
            sequence = len(contents) + 1
            values = {
                'biblica_id': biblica_id,
                'sequence': sequence,
                'name': kwargs.get('name'),
                'languages': request.env['res.lang'].sudo().search([]),
            }
            return request.render("website_openbiblica.content_form", values)
        else:
            return request.redirect(request.httprequest.referrer)

    @http.route(['/save/content'], type='http', auth="user", website=True)
    def save_content(self, **kwargs):
        biblica_id = request.env['open.biblica'].sudo().search([('id', '=', kwargs.get('biblica_id'))])
        user_id = request.env.user
        if biblica_id.create_id == user_id:
            if kwargs.get('content_id'):
                content_id = request.env['open.content'].sudo().search([('id', '=', kwargs.get('content_id'))])
                content_id.update({
                    'name': kwargs.get('name'),
                    'description': kwargs.get('description'),
                    'title_id': kwargs.get('title_id'),
                    'title_ide': kwargs.get('title_ide'),
                    'title': kwargs.get('title'),
                    'title_short': kwargs.get('title_short'),
                    'title_abrv': kwargs.get('title_abrv'),
                    'bundle': kwargs.get('bundle'),
                })
            else:
                content_id = request.env['open.content'].sudo().create({
                    'name': kwargs.get('name'),
                    'description': kwargs.get('description'),
                    'title_id': kwargs.get('title_id'),
                    'title_ide': kwargs.get('title_ide'),
                    'title': kwargs.get('title'),
                    'title_short': kwargs.get('title_short'),
                    'title_abrv': kwargs.get('title_abrv'),
                    'bundle': kwargs.get('bundle'),
                    'sequence': kwargs.get('sequence'),
                    'create_id': user_id.id,
                    'biblica_id': biblica_id.id,
                })
            if content_id.files:
                content_id.files = None
            if kwargs.get('files'):
                files = kwargs.get('files').read()
                content_id.update({
                    'files': base64.b64encode(files)
                })
            return request.redirect('/content/%s' % slug(content_id))
        else:
            return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/content/<model("open.content"):content_id>',
                 '/content/<model("open.content"):content_id>/page/<int:page>'],
                type='http', auth="public", website=True, csrf=False)
    def view_content(self, content_id=0, page=1):
        topic = request.env['forum.post'].search([('content_id', '=', content_id.id), ('first', '=', True)])
        posts = request.env['forum.post']
        domain = [('content_id', '=', content_id.id), ('first', '=', False)]
        url_args = {}
        url = '/content/%s' % content_id.id
        values = {}
        total = posts.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._comment_per_page,
            url_args=url_args,
        )
        results = posts.search(domain, offset=(page - 1) * self._comment_per_page, limit=self._comment_per_page)

        biblica_id = content_id.biblica_id

        seq = content_id.sequence
        prev_id = request.env['open.content'].sudo().search(
            [('biblica_id', '=', biblica_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['open.content'].sudo().search(
            [('biblica_id', '=', biblica_id.id), ('sequence', '=', seq + 1)])

        part_ids = request.env['open.part'].search([('content_id', '=', content_id.id), ('subcontent_id', '=', None)])

        values.update({
            'user_id': request.env.user,
            'content_id': content_id,
            'biblica_id': biblica_id,
            'part_ids': part_ids,
            'prev_id': prev_id,
            'next_id': next_id,
            'results': results,
            'pager': pager,
            'total': total,
            'topic': topic,
        })
        return request.render("website_openbiblica.view_content", values)

    @http.route(['/up/content/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def up_content(self, content_id=0):
        biblica_id = content_id.biblica_id
        if content_id.create_id == request.env.user:
            if content_id.sequence != 1:
                seq = content_id.sequence
                pseq = seq - 1
                prev = request.env['open.content'].sudo().search(
                    [('biblica_id', '=', biblica_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                content_id.update({'sequence': pseq})
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/down/content/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def down_content(self, content_id=0):
        biblica_id = content_id.biblica_id
        if content_id.create_id == request.env.user:
            if content_id.sequence != len(biblica_id.content_ids):
                seq = content_id.sequence
                pseq = seq + 1
                prev = request.env['open.content'].sudo().search(
                    [('biblica_id', '=', biblica_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                content_id.update({'sequence': pseq})
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/edit/content/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def edit_content(self, content_id=0):
        biblica_id = content_id.biblica_id
        if content_id.create_id == request.env.user:
            values = {
                'content_id': content_id,
                'biblica_id': biblica_id,
            }
            return request.render("website_openbiblica.content_form", values)
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/comment/c/<model("open.content"):content_id>'], type='http', auth="user", methods=['POST'], website=True)
    def post_content_comment(self, content_id=0, **kwargs):
        if not kwargs.get('content'):
            return request.redirect(request.httprequest.referrer)
        forum_id = content_id.forum_id
        parent_id = request.env['forum.post'].search([("content_id", "=", content_id.id), ("first", "=", True)])
        if not parent_id:
            parent_id = request.env['forum.post'].create({
                'forum_id': forum_id.id,
                'name': content_id.biblica_id.name + ' ' + content_id.name,
                'content': content_id.name,
                'post_type': 'discussion',
                'content_id': content_id.id,
                'first': True,
            })
        request.env['forum.post'].create({
            'forum_id': forum_id.id,
            'name': parent_id.name,
            'content': kwargs.get('content'),
            'post_type': 'discussion',  # tde check in selection field
            'parent_id': parent_id.id,
            'content_id': content_id.id,
        })
        return request.redirect(request.httprequest.referrer)

    # PART

    @http.route(['/part/<model("open.part"):part_id>',
                 '/part/<model("open.part"):part_id>/<model("res.lang"):lg_id>',
                 '/part/<model("open.part"):part_id>/<int:line>/<int:page>',
                 '/part/p/<model("open.part"):part_id>/<model("res.lang"):lg_id>/<int:line>',
                 '/part/p/<model("open.part"):part_id>/<model("res.lang"):lg_id>/<int:line>/page/<int:page>',
                 '/part/l/<model("open.part"):part_id>/<model("res.lang"):lg_id>/<int:page>',
                 '/part/l/<model("open.part"):part_id>/<model("res.lang"):lg_id>/<int:page>/page/<int:line>',
                 ], type='http', auth="public", website=True, csrf=False)
    def view_part(self, lg_id=None, part_id=0, page=1, line=1, **kwargs):
        seq = part_id.sequence
        prev_id = request.env['open.part'].sudo().search(
            [('content_id', '=', part_id.content_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['open.part'].sudo().search(
            [('content_id', '=', part_id.content_id.id), ('sequence', '=', seq + 1)])

        if kwargs.get('select_lang'):
            s_lang = request.env['res.lang'].sudo().search([('id', '=', kwargs.get('select_lang'))]).id
        elif lg_id:
            s_lang = lg_id.id
        else:
            if not part_id.source_id:
                s_lang = request.env['res.lang'].search([("name", "=", "English")]).id
            else:
                s_lang = part_id.lang_id.id

        if kwargs.get('select_source'):
            source = request.env['open.part'].sudo().search(
                [('content_id.id', '=', kwargs.get('select_source')), ('sequence', '=', seq)])
        else:
            source = part_id.source_id

        main_lines = request.env['open.line']
        if source and len(source.line_ids) > len(part_id.line_ids):
            line_domain = [('part_id', '=', source.id)]
        else:
            line_domain = [('part_id', '=', part_id.id)]

        values = {}
        line_url_args = {}
        line_url = '/part/l/%s/%s/%s' % (slug(part_id), s_lang, page)
        line_total = main_lines.search_count(line_domain)
        line_pager = request.website.pager(
            url=line_url,
            total=line_total,
            page=line,
            step=self._verse_per_page,
            url_args=line_url_args,
        )
        line_results = main_lines.search(line_domain, offset=(line - 1) * self._verse_per_page, limit=self._verse_per_page)

        topic = request.env['forum.post'].search([('part_id', '=', part_id.id), ('first', '=', True)])
        posts = request.env['forum.post']
        domain = [('part_id', '=', part_id.id), ('first', '=', False)]
        url_args = {}
        url = '/part/p/%s/%s/%s' % (slug(part_id), s_lang, line)
        total = posts.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._comment_per_page,
            url_args=url_args,
        )
        results = posts.search(domain, offset=(page - 1) * self._comment_per_page, limit=self._comment_per_page)

        values.update({
            'user_id': request.env.user,
            's_lang': s_lang,
            'langs': request.env['res.lang'].sudo().search([]),
            'source_id': source,
            'part_id': part_id,
            'content_id': part_id.content_id,
            'biblica_id': part_id.biblica_id,
            'prev_id': prev_id,
            'next_id': next_id,
            'line_results': line_results,
            'line_pager': line_pager,
            'line_total': line_total,
            'main_lines': main_lines,
            'results': results,
            'pager': pager,
            'total': total,
            'topic': topic,
            'page': page,
            'line': line,
        })
        return request.render("website_openbiblica.view_part", values)

    @http.route(['/add/part'], type='http', auth='user', website=True)
    def add_part(self, **kwargs):
        user_id = request.env.user
        content_id = request.env['open.content'].sudo().search([("id", "=", kwargs.get('content_id'))])
        if content_id.create_id == user_id:
            seq = len(content_id.part_ids) + 1
            part_id = request.env['open.part'].sudo().create({
                'name': kwargs.get('name'),
                'sequence': seq,
                'content_id': content_id.id,
                'create_id': user_id.id,
            })
            if kwargs.get('subcontent_id'):
                part_id.update({'subcontent_id': kwargs.get('subcontent_id')})
        return request.redirect(request.httprequest.referrer)

    @http.route(['/up/part/<model("open.part"):part_id>'], type='http', auth="user", website=True)
    def up_part(self, part_id=0):
        content_id = part_id.content_id
        if part_id.create_id == request.env.user:
            if part_id.sequence != 1:
                seq = part_id.sequence
                pseq = seq - 1
                prev = request.env['open.part'].sudo().search(
                    [('content_id', '=', content_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                part_id.update({'sequence': pseq})
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/down/part/<model("open.part"):part_id>'], type='http', auth="user", website=True)
    def down_part(self, part_id=0):
        content_id = part_id.content_id
        if part_id.create_id == request.env.user:
            if part_id.sequence != len(content_id.part_ids):
                seq = part_id.sequence
                pseq = seq + 1
                prev = request.env['open.part'].sudo().search(
                    [('content_id', '=', content_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                part_id.update({'sequence': pseq})
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/edit/part'], type='http', auth="user", website=True)
    def edit_part(self, **kwargs):
        part_id = request.env['open.part'].sudo().search([('id', '=', kwargs.get('part_id'))])
        content_id = part_id.content_id
        if part_id.create_id == request.env.user:
            part_id.update({
                'name': kwargs.get('name'),
            })
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/move/part'], type='http', auth="user", website=True)
    def move_part(self, **kwargs):
        part_id = request.env['open.part'].sudo().search([('id', '=', kwargs.get('part_id'))])
        content_id = part_id.content_id
        if part_id.create_id == request.env.user:
            part_id.update({
                'subcontent_id': kwargs.get('subcontent_id'),
            })
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/comment/p/<model("open.part"):part_id>'], type='http', auth="user", methods=['POST'], website=True)
    def post_part_comment(self, part_id=0, **kwargs):
        if not kwargs.get('content'):
            return request.redirect(request.httprequest.referrer)
        forum_id = part_id.forum_id
        parent_id = request.env['forum.post'].search([("part_id", "=", part_id.id), ("first", "=", True)])
        if not parent_id:
            name = part_id.content_id.biblica_id.name + ' ' + part_id.content_id.name + ' chapter ' + part_id.name
            parent_id = request.env['forum.post'].create({
                'forum_id': forum_id.id,
                'name': name,
                'content': name,
                'post_type': 'discussion',
                'part_id': part_id.id,
                'first': True,
            })
        request.env['forum.post'].create({
            'forum_id': forum_id.id,
            'name': parent_id.name,
            'content': kwargs.get('content'),
            'post_type': 'discussion',  # tde check in selection field
            'parent_id': parent_id.id,
            'part_id': part_id.id,
        })
        return request.redirect(request.httprequest.referrer)

    @http.route(['/up/chapter'], type='http', auth="user", website=True)
    def up_chapter(self, **kwargs):
        user_id = request.env.user
        part_id = request.env['open.part'].sudo().search([("id", "=", int(kwargs.get('part_id')))])
        content_id = part_id.content_id
        if part_id.create_id == user_id:
            if part_id.sequence != 1:
                seq = part_id.sequence
                pseq = seq - 1
                prev = request.env['open.part'].sudo().search(
                    [('content_id', '=', content_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                part_id.update({'sequence': pseq})
        return

    # SUB CONTENT

    @http.route(['/subcontent/<model("open.subcontent"):subcontent_id>',
                 '/subcontent/<model("open.subcontent"):subcontent_id>/page/<int:page>'],
                type='http', auth="public", website=True, csrf=False)
    def view_subcontent(self, subcontent_id=0, page=1, **kwargs):
        topic = request.env['forum.post'].search([('subcontent_id', '=', subcontent_id.id), ('first', '=', True)])
        posts = request.env['forum.post']
        domain = [('subcontent_id', '=', subcontent_id.id), ('first', '=', False)]
        url_args = {}
        url = '/subcontent/%s' % subcontent_id.id
        values = {}
        total = posts.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._comment_per_page,
            url_args=url_args,
        )
        results = posts.search(domain, offset=(page - 1) * self._comment_per_page, limit=self._comment_per_page)

        seq = subcontent_id.sequence
        prev_id = request.env['open.subcontent'].sudo().search(
            [('content_id', '=', subcontent_id.content_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['open.subcontent'].sudo().search(
            [('content_id', '=', subcontent_id.content_id.id), ('sequence', '=', seq + 1)])

        values.update({
            'user_id': request.env.user,
            'subcontent_id': subcontent_id,
            'content_id': subcontent_id.content_id,
            'biblica_id': subcontent_id.biblica_id,
            'prev_id': prev_id,
            'next_id': next_id,
            'results': results,
            'pager': pager,
            'total': total,
            'topic': topic,
        })
        return request.render("website_openbiblica.view_subcontent", values)

    @http.route(['/add/subcontent'], type='http', auth='user', website=True)
    def add_subcontent(self, **kwargs):
        user_id = request.env.user
        content_id = request.env['open.content'].sudo().search([("id", "=", kwargs.get('content_id'))])
        if content_id.create_id == user_id:
            seq = len(content_id.subcontent_ids) + 1
            request.env['open.subcontent'].sudo().create({
                'name': kwargs.get('name'),
                'sequence': seq,
                'content_id': content_id.id,
                'create_id': user_id.id,
            })
        return request.redirect(request.httprequest.referrer)

    @http.route(['/up/subcontent/<model("open.subcontent"):subcontent_id>'], type='http', auth="user", website=True)
    def up_subcontent(self, subcontent_id=0):
        content_id = subcontent_id.content_id
        if subcontent_id.create_id == request.env.user:
            if subcontent_id.sequence != 1:
                seq = subcontent_id.sequence
                pseq = seq - 1
                prev = request.env['open.subcontent'].sudo().search(
                    [('content_id', '=', content_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                subcontent_id.update({'sequence': pseq})
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/down/subcontent/<model("open.subcontent"):subcontent_id>'], type='http', auth="user", website=True)
    def down_subcontent(self, subcontent_id=0):
        content_id = subcontent_id.content_id
        if subcontent_id.create_id == request.env.user:
            if subcontent_id.sequence != len(content_id.subcontent_ids):
                seq = subcontent_id.sequence
                pseq = seq + 1
                prev = request.env['open.subcontent'].sudo().search(
                    [('content_id', '=', content_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                subcontent_id.update({'sequence': pseq})
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/edit/subcontent'], type='http', auth="user", website=True)
    def edit_subcontent(self, **kwargs):
        subcontent_id = request.env['open.subcontent'].sudo().search([('id', '=', kwargs.get('subcontent_id'))])
        content_id = subcontent_id.content_id
        if subcontent_id.create_id == request.env.user:
            subcontent_id.update({
                'name': kwargs.get('name'),
            })
        return request.redirect('/content/%s' % slug(content_id))

    # LINE

    @http.route(['/line/<model("open.line"):line_id>',
                 '/line/<model("open.line"):line_id>/<int:lang_id>',
                 '/line/<model("open.line"):line_id>/<int:lang_id>/page/<int:page>'
                 ], type='http', auth="public", website=True, csrf=False)
    def view_line(self, line_id=0, page=1, lang_id=None, **kwargs):
        if kwargs.get('select_lang'):
            s_lang = request.env['res.lang'].sudo().search([('id', '=', kwargs.get('select_lang'))]).id
        elif lang_id:
            s_lang = lang_id
        else:
            if not line_id.source_id:
                s_lang = request.env['res.lang'].search([("name", "=", "English")]).id
            else:
                s_lang = line_id.lang_id.id

        topic = request.env['forum.post'].search([('line_id', '=', line_id.id),('first', '=', True)])
        posts = request.env['forum.post']
        domain = [('line_id', '=', line_id.id), ('first', '=', False)]
        url_args = {}
        url = '/line/%s/%s' % (line_id.id, s_lang)
        values = {}
        total = posts.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._comment_per_page,
            url_args=url_args,
        )
        results = posts.search(domain, offset=(page - 1) * self._comment_per_page, limit=self._comment_per_page)

        seq = line_id.sequence
        prev_id = request.env['open.line'].sudo().search(
            [('part_id', '=', line_id.part_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['open.line'].sudo().search(
            [('part_id', '=', line_id.part_id.id), ('sequence', '=', seq + 1)])

        if kwargs.get('select_source'):
            source = request.env['open.line'].sudo().search([
                ('content_id.id', '=', kwargs.get('select_source')),
                ('part_id.sequence', '=', line_id.part_id.sequence),
                ('sequence', '=', seq)])
        else:
            source = line_id.source_id

        values.update({
            'user_id': request.env.user,
            's_lang': s_lang,
            'langs': request.env['res.lang'].sudo().search([]),
            'source_id': source,
            'line_id': line_id,
            'part_id': line_id.part_id,
            'content_id': line_id.content_id,
            'biblica_id': line_id.biblica_id,
            'prev_id': prev_id,
            'next_id': next_id,
            'results': results,
            'pager': pager,
            'total': total,
            'topic': topic,
        })
        return request.render("website_openbiblica.view_line", values)

    @http.route(['/add/line'], type='http', auth='user', website=True)
    def add_line(self, **kwargs):
        user_id = request.env.user
        part_id = request.env['open.part'].sudo().search([("id", "=", kwargs.get('part_id'))])
        seq = len(part_id.line_ids) + 1
        if part_id.create_id == user_id:
            line_id = request.env['open.line'].sudo().create({
                'content': kwargs.get('content'),
                'chapter': kwargs.get('chapter'),
                'verse': kwargs.get('verse'),
                'chapter_alt': kwargs.get('chapter_alt'),
                'verse_alt': kwargs.get('verse_alt'),
                'verse_char': kwargs.get('verse_char'),
                'is_title': kwargs.get('is_title'),
                'sequence': seq,
                'part_id': part_id.id,
                'create_id': user_id.id,
            })
            if part_id.is_interlinear:
                self._interlinearing_line(line_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/up/line/<model("open.line"):line_id>'], type='http', auth="user", website=True)
    def up_line(self, line_id=0):
        part_id = line_id.part_id
        if line_id.create_id == request.env.user:
            if line_id.sequence != 1:
                seq = line_id.sequence
                pseq = seq - 1
                prev = request.env['open.line'].sudo().search([('part_id', '=', part_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                line_id.update({'sequence': pseq})
        return request.redirect('/part/%s' % slug(part_id))

    @http.route(['/down/line/<model("open.line"):line_id>'], type='http', auth="user", website=True)
    def down_line(self, line_id=0):
        part_id = line_id.part_id
        if line_id.create_id == request.env.user:
            if line_id.sequence != len(part_id.line_ids):
                seq = line_id.sequence
                pseq = seq + 1
                prev = request.env['open.line'].sudo().search([('part_id', '=', part_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                line_id.update({'sequence': pseq})
        return request.redirect('/part/%s' % slug(part_id))

    @http.route(['/edit/line'], type='http', auth="user", website=True)
    def edit_line(self, **kwargs):
        line_id = request.env['open.line'].sudo().search([('id', '=', kwargs.get('line_id'))])
        if line_id.create_id == request.env.user:
            line_id.update({
                'content': kwargs.get('content'),
                'chapter': kwargs.get('chapter'),
                'verse': kwargs.get('verse'),
                'chapter_alt': kwargs.get('chapter_alt'),
                'verse_alt': kwargs.get('verse_alt'),
                'verse_char': kwargs.get('verse_char'),
                'is_title': kwargs.get('is_title'),
            })
            if line_id.is_interlinear:
                self._interlinearing_line(line_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/comment/l/<model("open.line"):line_id>'], type='http', auth="user", methods=['POST'], website=True)
    def post_line_comment(self, line_id=0, **kwargs):
        if not kwargs.get('content'):
            return request.redirect(request.httprequest.referrer)
        forum_id = line_id.forum_id
        parent_id = request.env['forum.post'].search([("line_id", "=", line_id.id), ("first", "=", True)])
        if not parent_id:
            name = line_id.part_id.content_id.biblica_id.name + ' ' + line_id.part_id.content_id.name + ' ' + line_id.chapter + ' : ' + line_id.verse
            parent_id = request.env['forum.post'].create({
                'forum_id': forum_id.id,
                'name': name,
                'content': name,
                'post_type': 'discussion',
                'line_id': line_id.id,
                'first': True,
            })
        request.env['forum.post'].create({
            'forum_id': forum_id.id,
            'name': parent_id.name,
            'content': kwargs.get('content'),
            'post_type': 'discussion',  # tde check in selection field
            'parent_id': parent_id.id,
            'line_id': line_id.id,
        })
        return request.redirect(request.httprequest.referrer)

    # WORD

    @http.route(['/word/<model("open.word"):word_id>',
                 '/word/<model("open.word"):word_id>/page/<int:page>',
                 '/word/<model("open.word"):word_id>/lang/<int:lang_id>',
                 '/word/<model("open.word"):word_id>/lang/<int:lang_id>/page/<int:page>',
                 '/word/<model("open.word"):word_id>/lang/<int:lang_id>/line/<int:line_id>',
                 '/word/<model("open.word"):word_id>/lang/<int:lang_id>/line/<int:line_id>/page/<int:page>',
                 ], type='http', auth="public", website=True, csrf=False)
    def view_word(self, word_id=0, lang_id=None, line_id=0, page=1):
        user_id = request.env.user
        # user_lang = user_id.lang
        topic = request.env['forum.post'].search([('word_id', '=', word_id.id), ('first', '=', True)])
        posts = request.env['forum.post']
        domain = [('word_id', '=', word_id.id), ('first', '=', False)]
        url_args = {}
        url = '/word/%s' % word_id.id
        values = {}
        total = posts.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._comment_per_page,
            url_args=url_args,
        )
        results = posts.search(domain, offset=(page - 1) * self._comment_per_page, limit=self._comment_per_page)

        # description_ids = word_id.description_ids.search([('lang_id', '=', user_lang)])
        # dictionary_ids = word_id.dictionary_ids.search([('lang_id', '=', user_lang)])
        #
        if lang_id:
            s_lang = lang_id
        else:
            s_lang = request.env['res.lang'].search([("name", "=", "English")]).id
        dictionary_ids = word_id.dictionary_ids.search([('lang_id', '=', s_lang)])

        values.update({
            'user_id': user_id,
            # 'user_lang': user_lang,
            'languages': request.env['res.lang'].sudo().search([]),
            'word_id': word_id,
            's_lang': s_lang,
            'line_id': line_id,
            # 'description_ids': description_ids,
            'dictionary_ids': dictionary_ids,
            'results': results,
            'pager': pager,
            'total': total,
            'topic': topic,
        })
        return request.render("website_openbiblica.view_word", values)

    @http.route(['/comment/w/<model("open.word"):word_id>'], type='http', auth="user", methods=['POST'], website=True)
    def post_word_comment(self, word_id=0, **kwargs):
        if not kwargs.get('content'):
            return request.redirect(request.httprequest.referrer)
        forum_id = word_id.forum_id
        parent_id = request.env['forum.post'].search([("word_id", "=", word_id.id), ("first", "=", True)])
        if not parent_id:
            name = word_id.name
            parent_id = request.env['forum.post'].create({
                'forum_id': forum_id.id,
                'name': name,
                'content': name,
                'post_type': 'discussion',
                'word_id': word_id.id,
                'first': True,
            })
        request.env['forum.post'].create({
            'forum_id': forum_id.id,
            'name': parent_id.name,
            'content': kwargs.get('content'),
            'post_type': 'discussion',  # tde check in selection field
            'parent_id': parent_id.id,
            'word_id': word_id.id,
        })
        return request.redirect(request.httprequest.referrer)

    @http.route(['/add/attribute/<model("open.word"):word_id>'], type='http', auth="user", methods=['POST'], website=True)
    def add_word_attribute(self, word_id=0, **kwargs):
        lang_id = request.env['res.lang'].sudo().search([('id', '=', kwargs.get('select_language'))])
        if kwargs.get('word_description'):
            request.env['open.description'].create({
                'lang_id': lang_id.id,
                'create_id': request.env.user.id,
                'name': kwargs.get('word_description'),
                'word_id': word_id.id,
            })
        if kwargs.get('word_dictionary'):
            dict_id = request.env['open.meaning'].search([("name", "=", kwargs.get('word_dictionary')), ("lang_id", "=", lang_id.id)])
            if not dict_id:
                dict_id = request.env['open.meaning'].create({
                    'name': kwargs.get('word_dictionary'),
                    'lang_id': lang_id.id,
                    'create_id': request.env.user.id,
                })
            word_id.update({
                'dictionary_ids': [(4, dict_id.id)]
            })
        return request.redirect(request.httprequest.referrer)

    @http.route(['/point/<model("open.point"):point_id>',
                 # '/point/<model("open.point"):point_id>/page/<int:page>',
                 '/point/<model("open.point"):point_id>/<model("open.line"):line_id>',
                 '/point/<model("open.point"):point_id>/<model("open.line"):line_id>/<int:lang_id>',
                 '/point/<model("open.point"):point_id>/<model("open.line"):line_id>/<int:lang_id>/page/<int:page>',
                 # '/point/<model("open.point"):point_id>/lang/<int:lang_id>',
                 # '/point/<model("open.point"):point_id>/lang/<int:lang_id>/page/<int:page>',
                 ], type='http', auth="public", website=True, csrf=False)
    def view_point(self, point_id=0, lang_id=None, page=1, line_id=None):
        if lang_id:
            s_lang = lang_id
        else:
            s_lang = request.env['res.lang'].search([("name", "=", "English")]).id
        word_id = point_id.word_id
        user_id = request.env.user
        # user_lang = user_id.lang
        topic = request.env['forum.post'].search([('word_id', '=', word_id.id), ('first', '=', True)])
        posts = request.env['forum.post']
        domain = [('word_id', '=', word_id.id), ('first', '=', False)]
        url_args = {}
        url = '/point/%s/%s/%s' % (slug(point_id), slug(line_id), s_lang)
        values = {}
        total = posts.search_count(domain)
        pager = request.website.pager(
            url=url,
            total=total,
            page=page,
            step=self._comment_per_page,
            url_args=url_args,
        )
        results = posts.search(domain, offset=(page - 1) * self._comment_per_page, limit=self._comment_per_page)

        dictionary_ids = word_id.dictionary_ids.search([('lang_id', '=', s_lang)])

        seq = point_id.sequence
        prev_id = request.env['open.point'].sudo().search(
            [('line_id', '=', point_id.line_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['open.point'].sudo().search(
            [('line_id', '=', point_id.line_id.id), ('sequence', '=', seq + 1)])

        if not line_id:
            line_id = point_id.line_id

        values.update({
            'user_id': user_id,
            # 'user_lang': user_lang,
            'languages': request.env['res.lang'].sudo().search([]),
            'point_id': point_id,
            'word_id': word_id,
            'prev_id': prev_id,
            'next_id': next_id,
            's_lang': s_lang,
            'line_id': line_id,
            'dictionary_ids': dictionary_ids,
            'results': results,
            'pager': pager,
            'total': total,
            'topic': topic,
        })
        return request.render("website_openbiblica.view_point", values)


