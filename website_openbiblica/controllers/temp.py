# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
import werkzeug.utils
import logging
import base64
import json

from odoo import http, modules, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.web.controllers.main import binary_content
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WebsiteBiblica(http.Controller):
    _items_per_page = 20

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
            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            response = request.make_response(content_base64, headers)
        return response

    def _del_line(self, line_id):
        line_id.unlink()
        return

    def _del_text(self, text_id):
        text_id.unlink()
        return

    def _del_part(self, part_id):
        for child_id in part_id.children_ids:
            self._del_part(child_id)
        request.env['open.line'].sudo().search([("part_id", "=", part_id.id)]).unlink()
        part_id.unlink()
        return

    def _del_content(self, content_id):
        for part_id in content_id.part_ids:
            self._del_part(part_id)
        content_id.unlink()
        return

    def _del_section(self, section_id):
        if section_id.text_ids:
            for text_id in section_id.text_ids:
                self._del_text(text_id)
        section_id.unlink()
        return

    def _del_biblica(self, biblica_id):
        if biblica_id.cover_ids:
            request.env['open.cover'].sudo().search([("biblica_id", "=", biblica_id.id)]).unlink()
        if biblica_id.section_ids:
            for section_id in biblica_id.section_ids:
                self._del_section(section_id)
        if biblica_id.content_ids:
            for content_id in biblica_id.content_ids:
                self._del_content(content_id)
        biblica_id.unlink()
        return

    def _add_word(self, texts, content_id):
        texts = texts.strip(r'\ft').strip(r'\fqa*').strip(r'\fqa').strip(r'\f')
        words = texts.split(' ')
        for word in words:
            word = word.strip('<>? \'",./;[]=-`~!@#$%^&*()\_+1234567890{}|').lower()
            if not request.env['open.word'].sudo().search(
                    [('name', '=', word), ('lang_id', '=', content_id.lang_id.id)]):
                request.env['open.word'].sudo().create({
                    'name': word,
                    'lang_id': content_id.lang_id.id,
                    'forum_id': content_id.forum_id.id
                })
        return

    def _insert_content(self, content, content_id, user_id, values):
        # raise UserError(content)
        style = values.get('style')
        align = values.get('align')
        insert_paragraph = values.get('insert_paragraph')
        if content_id.part_ids:
            last_part = request.env['open.part'].search([('content_id', '=', content_id.id)])[-1]
            part_sequence = last_part.sequence + 1
            if last_part.parent_id:
                major_part_id = last_part.parent_id
            else:
                major_part_id = None
        else:
            major_part_id = None
            part_sequence = 1
        line_sequence = 1
        chapter = values.get('chapter')
        verse = values.get('verse')

        for line in content:

            head, _, texts = line.partition(" ")

            # CONTENT
            if head == '\id':
                content_id['title_id'] = texts
            elif head == '\ide':
                content_id['title_ide'] = texts
            elif head == '\mt':
                content_id['name'] = texts
            elif head == '\h':
                content_id['description'] = texts
            elif head == r'\toc1':
                content_id['title'] = texts
            elif head == r'\toc2':
                content_id['title_short'] = texts
            elif head == r'\toc3':
                content_id['title_abrv'] = texts
            # PART

            elif head == '\ms':
                major_part_id = request.env['open.part'].sudo().create({
                    'name': texts,
                    'sequence': part_sequence,
                    'create_id': user_id.id,
                    'content_id': content_id.id,
                    'forum_id': content_id.forum_id.id,
                })
                part_sequence += 1
            elif head == '\c':
                c, _, temp = texts.partition(" ")
                if c != ' ':
                    chapter = c
                part_id = request.env['open.part'].sudo().create({
                    'name': texts,
                    'sequence': part_sequence,
                    'create_id': user_id.id,
                    'forum_id': content_id.forum_id.id,
                })
                texts = temp
                part_sequence += 1
                line_sequence = 1
                if major_part_id:
                    part_id.sudo().update({'parent_id': major_part_id.id})
                else:
                    part_id.sudo().update({'content_id': content_id.id})

            # LINE

            elif head == r'\v':
                v, _, texts = texts.partition(" ")
                if v != ' ':
                    verse = v
                request.env['open.line'].sudo().create({
                    'content': texts,
                    'sequence': line_sequence,
                    'create_id': user_id.id,
                    'chapter': chapter,
                    'verse': verse,
                    'part_id': part_id.id,
                    'insert_paragraph': insert_paragraph,
                    'style': style,
                    'forum_id': part_id.forum_id.id,
                })
                line_sequence += 1
                insert_paragraph = False
            elif head == '\d' or head == r'\f':
                request.env['open.line'].sudo().create({
                    'content': texts,
                    'sequence': line_sequence,
                    'create_id': user_id.id,
                    'part_id': part_id.id,
                    'insert_paragraph': insert_paragraph,
                    'style': style,
                    'forum_id': part_id.forum_id.id,
                })
                line_sequence += 1
                insert_paragraph = False
            elif head == '\q' or head == '\q1' or head == '\q2' or head == '\q3':
                style = 'italic'
                if texts:
                    request.env['open.line'].sudo().create({
                        'content': texts,
                        'sequence': line_sequence,
                        'create_id': user_id.id,
                        'part_id': part_id.id,
                        'insert_paragraph': insert_paragraph,
                        'style': style
                    })
                line_sequence += 1
                insert_paragraph = False
            elif head == '\m':
                insert_paragraph = False
                if texts:
                    request.env['open.line'].sudo().create({
                        'content': texts,
                        'sequence': line_sequence,
                        'create_id': user_id.id,
                        'part_id': part_id.id,
                        'insert_paragraph': insert_paragraph,
                        'style': style,
                        'forum_id': part_id.forum_id.id,
                    })
                    line_sequence += 1
            elif head == '\qs':
                texts = texts.strip('\qs ').strip('\qs*')
                request.env['open.line'].sudo().create({
                    'content': texts,
                    'sequence': line_sequence,
                    'create_id': user_id.id,
                    'part_id': part_id.id,
                    'insert_paragraph': insert_paragraph,
                    'style': style,
                    'forum_id': part_id.forum_id.id,
                })
                line_sequence += 1
                insert_paragraph = False

            # COMMANDS

            elif head == '\s5':
                style = 'normal'
            elif head == '\p':
                insert_paragraph = True
            elif head == r'\nb':
                insert_paragraph = False
            # if texts:
            #     self._add_word(texts, content_id)

        next_values = {
            'style': style,
            'align': align,
            'insert_paragraph': insert_paragraph,
            'chapter': chapter,
            'verse': verse,
            'content_id': content_id,
        }
        if major_part_id:
            next_values.update({'major_part_id': major_part_id.id})
        return next_values

    def _add_line_source(self, line_id, source_id):
        line_id.update({
            'source_id': source_id.id,
            'source_ids': [(4, source_id.id)]
        })
        return

    def _remove_line_source(self, line_id, source_id):
        if line_id.source_id == source_id:
            line_id['source_id'] = None
        line_id.update({
            'source_ids': [(3, source_id.id)]
        })
        return

    def _add_text_source(self, text_id, source_id):
        text_id.update({
            'source_id': source_id.id,
            'source_ids': [(4, source_id.id)]
        })
        return

    def _remove_text_source(self, text_id, source_id):
        if text_id.source_id == source_id:
            text_id['source_id'] = None
        text_id.update({
            'source_ids': [(3, source_id.id)]
        })
        return

    def _add_part_source(self, part_id, source_id):
        part_id.update({
            'source_id': source_id.id,
            'source_ids': [(4, source_id.id)]
        })
        if source_id.line_ids:
            for s_line_id in source_id.line_ids:
                line_id = request.env['open.line'].sudo().search([('part_id', '=', part_id.id), ('sequence', '=', s_line_id.sequence)])
                if not line_id:
                    line_id = request.env['open.line'].sudo().create({
                        'content': ' ',
                        'chapter': s_line_id.chapter,
                        'verse': s_line_id.verse,
                        'chapter_alt': s_line_id.chapter_alt,
                        'verse_alt': s_line_id.verse_alt,
                        'verse_char': s_line_id.verse_char,
                        'is_title': s_line_id.is_title,
                        'sequence': s_line_id.sequence,
                        'part_id': part_id.id,
                        'create_id': part_id.create_id.id,
                        'forum_id': part_id.forum_id.id,
                    })
                self._add_line_source(line_id, s_line_id)
        if source_id.children_ids:
            for c_source_id in source_id.children_ids:
                c_part_id = request.env['open.part'].sudo().search([('parent_id', '=', part_id.id), ('sequence', '=', c_source_id.sequence)])
                if not c_part_id:
                    c_part_id = request.env['open.part'].sudo().create({
                        'name': c_source_id.name,
                        'sequence': c_source_id.sequence,
                        'parent_id': part_id.id,
                        'create_id': part_id.create_id.id,
                        'forum_id': part_id.forum_id.id,
                    })
                self._add_part_source(c_part_id, c_source_id)
        return

    def _remove_part_source(self, part_id, source_id):
        if part_id.source_id == source_id:
            part_id['source_id'] = None
        part_id.update({
            'source_ids': [(3, source_id.id)]
        })

        if part_id.line_ids:
            for line_id in part_id.line_ids:
                s_line_id = request.env['open.line'].sudo().search(
                    [('part_id', '=', source_id.id), ('sequence', '=', line_id.sequence)])
                self._remove_line_source(line_id, s_line_id)

        if part_id.children_ids:
            for c_part_id in part_id.children_ids:
                c_source_id = request.env['open.part'].sudo().search([('parent_id', '=', source_id.id), ('sequence', '=', c_part_id.sequence)])
                if c_source_id:
                    self._remove_part_source(c_part_id, c_source_id)
        return

    def _add_section_source(self, section_id, source_id):
        section_id.update({
            'source_id': source_id.id,
            'source_ids': [(4, source_id.id)]
        })
        if source_id.text_ids:
            for s_text_id in source_id.text_ids:
                text_id = request.env['open.text'].sudo().search([('section_id', '=', section_id.id), ('sequence', '=', s_text_id.sequence)])
                if not text_id:
                    text_id = request.env['open.text'].sudo().create({
                        'content': ' ',
                        'sequence': s_text_id.sequence,
                        'create_id': section_id.create_id.id,
                        'forum_id': section_id.forum_id.id,
                        'section_id': section_id.id,
                    })
                self._add_text_source(text_id, s_text_id)
        return

    def _remove_section_source(self, section_id, source_id):
        if section_id.source_id == source_id:
            section_id['source_id'] = None
        section_id.update({
            'source_ids': [(3, source_id.id)]
        })
        if section_id.text_ids:
            for text_id in section_id.text_ids:
                s_text_id = request.env['open.text'].sudo().search(
                    [('section_id', '=', source_id.id), ('sequence', '=', text_id.sequence)])
                self._remove_text_source(text_id, s_text_id)
        return

    def _add_content_source(self, content_id, source_id):
        content_id.update({
            'source_id': source_id.id,
            'source_ids': [(4, source_id.id)]
        })
        if source_id.part_ids:
            for s_part_id in source_id.part_ids:
                part_id = request.env['open.part'].sudo().search([('content_id', '=', content_id.id), ('sequence', '=', s_part_id.sequence)])
                if not part_id:
                    part_id = request.env['open.part'].sudo().create({
                        'name': s_part_id.name,
                        'sequence': s_part_id.sequence,
                        'content_id': content_id.id,
                        'create_id': content_id.create_id.id,
                        'forum_id': content_id.forum_id.id,
                    })
                self._add_part_source(part_id, s_part_id)
        return

    def _remove_content_source(self, content_id, source_id):
        if content_id.source_id == source_id:
            content_id['source_id'] = None
        content_id.update({
            'source_ids': [(3, source_id.id)]
        })

        if content_id.part_ids:
            for part_id in content_id.part_ids:
                s_part_id = request.env['open.part'].sudo().search(
                    [('content_id', '=', source_id.id), ('sequence', '=', part_id.sequence)])
                self._remove_part_source(part_id, s_part_id)
        return

    def _add_biblica_source(self, biblica_id, source_id):
        biblica_id.update({
            'source_id': source_id.id,
            'source_ids': [(4, source_id.id)]
        })
        if source_id.section_ids:
            for s_section_id in source_id.section_ids:
                section_id = request.env['open.section'].sudo().search([('biblica_id', '=', biblica_id.id), ('sequence', '=', s_section_id.sequence)])
                if not section_id:
                    section_id = request.env['open.section'].sudo().create({
                        'name': s_section_id.name,
                        'sequence': s_section_id.sequence,
                        'biblica_id': biblica_id.id,
                        'create_id': biblica_id.create_id.id,
                        'forum_id': biblica_id.forum_id.id,
                    })
                self._add_section_source(section_id, s_section_id)
        if source_id.content_ids:
            for s_content_id in source_id.content_ids:
                content_id = request.env['open.content'].sudo().search([('biblica_id', '=', biblica_id.id), ('sequence', '=', s_content_id.sequence)])
                if not content_id:
                    content_id = request.env['open.content'].sudo().create({
                        'name': s_content_id.name,
                        'sequence': s_content_id.sequence,
                        'bundle': s_content_id.bundle,
                        'biblica_id': biblica_id.id,
                        'create_id': biblica_id.create_id.id,
                        'forum_id': biblica_id.forum_id.id,
                    })
                self._add_content_source(content_id, s_content_id)
        return

    def _remove_biblica_source(self, biblica_id, source_id):
        if biblica_id.source_id == source_id:
            biblica_id['source_id'] = None
        biblica_id.update({
            'source_ids': [(3, source_id.id)]
        })

        if biblica_id.section_ids:
            for section_id in biblica_id.section_ids:
                s_section_id = request.env['open.section'].sudo().search(
                    [('biblica_id', '=', source_id.id), ('sequence', '=', section_id.sequence)])
                self._remove_section_source(section_id, s_section_id)
        if biblica_id.content_ids:
            for content_id in biblica_id.content_ids:
                s_content_id = request.env['open.content'].sudo().search(
                    [('biblica_id', '=', source_id.id), ('sequence', '=', content_id.sequence)])
                self._remove_content_source(content_id, s_content_id)
        return

    @http.route(['/install/usfm/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def install_usfm(self, content_id=0):
        user_id = request.env.user
        if content_id.create_id == user_id:
            status, headers, content = binary_content(model='open.content', id=content_id.id, field='files',
                                                          env=request.env(user=SUPERUSER_ID))
            content = base64.b64decode(content).decode('utf-8')
            content, mid, rest = content.partition("\c")
            rest = mid + rest
            content = content.splitlines()
            if content_id.part_ids:
                for part_id in content_id.part_ids:
                    self._del_part(part_id)

            values = {
                'style': 'normal',
                'align': 'default',
                'insert_paragraph': False,
                'chapter': 0,
                'verse': 0,
                'major_part_id': None
            }

            n_values = self._insert_content(content, content_id, user_id, values)

            if rest:
                rest = rest.encode('utf-8')
                content_id.update({
                    'rest': base64.b64encode(rest)
                })
                return request.render("website_openbiblica.install_next", n_values)
            else:
                content_id.update({'rest': None})
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/install/next/usfm/'], type='http', auth="user", website=True)
    def next_usfm(self, **kwargs):
        user_id = request.env.user
        content_id = request.env['open.content'].sudo().search([('id', '=', kwargs.get('content_id'))])
        if content_id.create_id == user_id:
            content = kwargs.get('next_content')
            empty, chapter, rest = content.partition("\c")
            content, mid, rest = rest.partition("\c")
            next_content = mid + rest
            content = chapter + content
            content = content.splitlines()

            values = {
                'style': kwargs.get('style'),
                'align': kwargs.get('align'),
                'insert_paragraph': kwargs.get('insert_paragraph'),
                'part_sequence': kwargs.get('part_sequence'),
                'line_sequence': kwargs.get('line_sequence'),
                'chapter': kwargs.get('chapter'),
                'verse': kwargs.get('verse'),
                'major_part_id': kwargs.get('major_part_id')
            }

            n_values = self._insert_content(content, content_id, user_id, values)
            n_values.update({
                'next_content': next_content,
                'content_id': content_id.id,
            })

            if next_content:
                return request.render("website_openbiblica.install_next", n_values)
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/install/continue/usfm/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def cont_install_usfm(self, content_id=0, **kwargs):
        user_id = request.env.user
        if content_id.create_id == user_id:
            status, headers, content = binary_content(model='open.content', id=content_id.id, field='rest',
                                                          env=request.env(user=SUPERUSER_ID))
            content = base64.b64decode(content).decode('utf-8')
            empty, chapter, text = content.partition("\c")
            content, mid, rest = text.partition("\c")
            rest = mid + rest
            content = chapter + content
            content = content.splitlines()

            # values = {
            #     'style': kwargs.get('style'),
            #     'align': kwargs.get('align'),
            #     'insert_paragraph': kwargs.get('insert_paragraph'),
            #     'part_sequence': kwargs.get('part_sequence'),
            #     'line_sequence': kwargs.get('line_sequence'),
            #     'chapter': kwargs.get('chapter'),
            #     'verse': kwargs.get('verse'),
            #     'major_part_id': kwargs.get('major_part_id')
            # }

            n_values = self._insert_content(content, content_id, user_id, kwargs)

            if rest:
                rest = rest.encode('utf-8')
                content_id.update({
                    'rest': base64.b64encode(rest)
                })
                return request.render("website_openbiblica.install_next", n_values)
            else:
                content_id.update({'rest': None})
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/search/',
                 '/search/page/<int:page>',
                 '/search/<string:search>',
                 ], type='http', auth="public", website=True, csrf=False)
    def search(self, page=1, search='', sorting=None, **kwargs):
        if kwargs.get('search_item'):
            search += kwargs.get('search_item')
        user = request.env.user
        lines = request.env['open.line']
        domain = []
        url_args = {}
        values = {}
        if search:
            search = search.replace('.', ' ')
            url_args['search'] = search
            values['search'] = search
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]
        if sorting:
            # check that sorting is valid
            # retro-compatibily for V8 and google links
            try:
                lines._generate_order_by(sorting, None)
                url_args['sorting'] = sorting
            except ValueError:
                sorting = False
        total = lines.search_count(domain)
        pager = request.website.pager(
            url='/search',
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
            'search_item': search,
            'total': total
        })
        return request.render("website_openbiblica.view_search", values)

    @http.route('/get_biblica', type='json', auth='public', website=True)
    def get_biblica(self):
        bibs = request.env['open.biblica'].sudo().search([])
        lngs = request.env['res.lang'].sudo().search([('id', 'in', biblicas.mapped('lang_id.id'))])
        values = {"bibs": bibs, 'lngs': lngs}
        return values

    @http.route('/biblicas', type='http', auth="public", website=True, csrf=False)
    def biblicas(self):
        values = {
            'biblicas': request.env['open.biblica'].sudo().search([]),
        }
        return request.render("website_openbiblica.biblicas", values)

    @http.route('/create/biblica', type='http', auth="user", website=True)
    def create_biblica(self):
        values = {
            'languages': request.env['res.lang'].sudo().search([]),
        }
        return request.render("website_openbiblica.biblica_form", values)

    @http.route(['/save/biblica'], type='http', auth="user", methods=['POST'], website=True)
    def save_biblica(self, **kwargs):
        user_id = request.env.user
        if kwargs.get('language_name'):
            lang_id = request.env['res.lang'].create({
                'name': kwargs.get('language_name'),
                'code': kwargs.get('language_code'),
                'iso_code': kwargs.get('language_iso_code'),
                'direction': kwargs.get('direction'),
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

    @http.route(['/biblica/<model("open.biblica"):biblica_id>'], type='http', auth="public", website=True, csrf=False)
    def view_biblica(self, biblica_id=0, **kwargs):
        biblicas = request.env['open.biblica'].sudo().search([])
        languages = request.env['res.lang'].sudo().search([('id', 'in', biblicas.mapped('lang_id.id'))])
        if kwargs.get('src_id'):
            source_id = request.env['open.biblica'].search([("id", "=", kwargs.get('src_id'))])
        else:
            source_id = biblica_id.source_id
        values = {
            'user_id': request.env.user,
            'biblica_id': biblica_id,
            'source_id': source_id,
            'languages': languages,
            'biblicas': biblicas,
        }
        return request.render("website_openbiblica.view_biblica", values)

    @http.route('/edit/biblica', type='http', auth="user", website=True)
    def edit_biblica(self, **kwargs):
        biblica_id = request.env['open.biblica'].search([("id", "=", kwargs.get('biblica_id'))])
        if biblica_id.create_id == request.env.user:
            values = {
                'biblica_id': biblica_id,
                'languages': request.env['res.lang'].sudo().search([]),
            }
            return request.render("website_openbiblica.biblica_form", values)
        else:
            return request.redirect(request.httprequest.referrer)

    @http.route(['/remove/b/<model("open.biblica"):biblica_id>'], type='http', auth='user', website=True)
    def remove_biblica(self, biblica_id=0):
        user_id = request.env.user
        if biblica_id.create_id == user_id:
            self._del_biblica(biblica_id)
        return request.redirect('/biblicas')

    @http.route(['/add/cover'], type='http', auth="user", website=True)
    def add_cover(self, **kwargs):
        biblica_id = request.env['open.biblica'].sudo().search([('id', '=', kwargs.get('biblica_id'))])
        user_id = request.env.user
        if biblica_id.create_id == user_id:
            sequence = len(biblica_id.cover_ids) + 1
            image = kwargs.get('images').read()
            request.env['open.cover'].sudo().create({
                'name': kwargs.get('name'),
                'sequence': sequence,
                'create_id': user_id.id,
                'forum_id': biblica_id.forum_id.id,
                'biblica_id': biblica_id.id,
                'images': base64.b64encode(image),
            })
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/c/img/<int:cover_id>'], type='http', auth="public", website=True, sitemap=False)
    def load_image(self, cover_id=0):
        status, headers, content = binary_content(model='open.cover', id=cover_id, field='images',
                                                  default_mimetype='image/png', env=request.env(user=SUPERUSER_ID))
        if not content:
            img_path = modules.get_module_resource('web', 'static/src/img', 'placeholder.png')
            with open(img_path, 'rb') as f:
                image = f.read()
            content = base64.b64encode(image)
        if status == 304:
            return werkzeug.wrappers.Response(status=304)
        image_base64 = base64.b64decode(content)
        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status = str(status)
        return response

    @http.route(['/up/cover/<model("open.cover"):cover_id>'], type='http', auth="user", website=True)
    def up_cover(self, cover_id=0):
        user_id = request.env.user
        biblica_id = cover_id.biblica_id
        if cover_id.create_id == user_id:
            if cover_id.sequence != 1:
                seq = cover_id.sequence
                pseq = seq - 1
                prev = request.env['open.cover'].sudo().search(
                    [('biblica_id', '=', biblica_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                cover_id.update({'sequence': pseq})
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/down/cover/<model("open.cover"):cover_id>'], type='http', auth="user", website=True)
    def down_cover(self, cover_id=0):
        user_id = request.env.user
        biblica_id = cover_id.biblica_id
        if cover_id.create_id == user_id:
            if cover_id.sequence != len(biblica_id.cover_ids):
                seq = cover_id.sequence
                pseq = seq + 1
                prev = request.env['open.cover'].sudo().search(
                    [('biblica_id', '=', biblica_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                cover_id.update({'sequence': pseq})
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/remove/cover/<model("open.cover"):cover_id>'], type='http', auth="user", website=True)
    def remove_cover(self, cover_id=0):
        user_id = request.env.user
        biblica_id = cover_id.biblica_id
        if cover_id.create_id == user_id:
            seq = cover_id.sequence
            next_covers = request.env['open.cover'].sudo().search(
                [('biblica_id', '=', biblica_id.id), ('sequence', '>', seq)])
            cover_id.unlink()
            for cover in next_covers:
                nseq = cover.sequence - 1
                cover.update({'sequence': nseq})
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/edit/cover/<model("open.cover"):cover_id>'], type='http', auth="user", website=True)
    def edit_cover(self, cover_id=0):
        user_id = request.env.user
        biblica_id = cover_id.biblica_id
        if cover_id.create_id == user_id:
            values = {
                'cover_id': cover_id,
                'biblica_id': biblica_id,
            }
            return request.render("website_openbiblica.edit_cover", values)
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/save/cover'], type='http', auth="user", website=True)
    def save_cover(self, **kwargs):
        cover_id = request.env['open.cover'].sudo().search([('id', '=', kwargs.get('cover_id'))])
        biblica_id = cover_id.biblica_id
        user_id = request.env.user
        if cover_id.create_id == user_id:
            image = kwargs.get('images').read()
            cover_id.update({
                'name': kwargs.get('name'),
                'images': base64.b64encode(image),
            })
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/add/section'], type='http', auth="user", website=True)
    def add_section(self, **kwargs):
        biblica_id = request.env['open.biblica'].sudo().search([('id', '=', kwargs.get('biblica_id'))])
        user_id = request.env.user
        if biblica_id.create_id == user_id:
            sequence = len(biblica_id.section_ids) + 1
            section_id = request.env['open.section'].sudo().create({
                'name': kwargs.get('name'),
                'sequence': sequence,
                'create_id': user_id.id,
                'forum_id': biblica_id.forum_id.id,
                'biblica_id': biblica_id.id,
            })
        return request.redirect('/section/%s' % slug(section_id))

    @http.route(['/section/<model("open.section"):section_id>'], type='http', auth="public", website=True, csrf=False)
    def view_section(self, section_id=0):
        biblica_id = section_id.biblica_id
        seq = section_id.sequence
        prev_id = request.env['open.section'].sudo().search(
            [('biblica_id', '=', biblica_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['open.section'].sudo().search(
            [('biblica_id', '=', biblica_id.id), ('sequence', '=', seq + 1)])
        values = {
            'user_id': request.env.user,
            'section_id': section_id,
            'biblica_id': biblica_id,
            'prev_id': prev_id,
            'next_id': next_id,
            'source_id': section_id.source_id,
        }
        return request.render("website_openbiblica.view_section", values)

    @http.route(['/up/section/<model("open.section"):section_id>'], type='http', auth="user", website=True)
    def up_section(self, section_id=0):
        user_id = request.env.user
        s_type = section_id.type
        biblica_id = section_id.biblica_id
        if section_id.create_id == user_id:
            if section_id.sequence != 1:
                seq = section_id.sequence
                pseq = seq - 1
                prev = request.env['open.section'].sudo().search(
                    [('biblica_id', '=', biblica_id.id), ('type', '=', s_type), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                section_id.update({'sequence': pseq})
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/down/section/<model("open.section"):section_id>'], type='http', auth="user", website=True)
    def down_section(self, section_id=0):
        user_id = request.env.user
        s_type = section_id.type
        biblica_id = section_id.biblica_id
        if section_id.create_id == user_id:
            if section_id.sequence != len(biblica_id.section_ids):
                seq = section_id.sequence
                pseq = seq + 1
                prev = request.env['open.section'].sudo().search(
                    [('biblica_id', '=', biblica_id.id), ('type', '=', s_type), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                section_id.update({'sequence': pseq})
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/remove/section/<model("open.section"):section_id>'], type='http', auth="user", website=True)
    def remove_section(self, section_id=0):
        user_id = request.env.user
        s_type = section_id.type
        biblica_id = section_id.biblica_id
        if section_id.create_id == user_id:
            seq = section_id.sequence
            next_sections = request.env['open.section'].sudo().search(
                [('biblica_id', '=', biblica_id.id), ('type', '=', s_type), ('sequence', '>', seq)])
            self._del_section(section_id)
            for section in next_sections:
                nseq = section.sequence - 1
                section.update({'sequence': nseq})
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/edit/section/<model("open.section"):section_id>'], type='http', auth="user", website=True)
    def edit_section(self, section_id=0):
        user_id = request.env.user
        biblica_id = section_id.biblica_id
        if section_id.create_id == user_id:
            values = {
                'section_id': section_id,
                'biblica_id': biblica_id,
            }
            return request.render("website_openbiblica.edit_section", values)
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/save/section'], type='http', auth="user", website=True)
    def save_section(self, **kwargs):
        section_id = request.env['open.section'].sudo().search([('id', '=', kwargs.get('section_id'))])
        user_id = request.env.user
        if section_id.create_id == user_id:
            section_id.update({
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
            })
        return request.redirect('/section/%s' % slug(section_id))

    @http.route(['/add/text'], type='http', auth="user", website=True)
    def add_text(self, **kwargs):
        section_id = request.env['open.section'].sudo().search([('id', '=', kwargs.get('section_id'))])
        user_id = request.env.user
        if section_id.create_id == user_id:
            sequence = len(section_id.text_ids) + 1
            request.env['open.text'].sudo().create({
                'content': kwargs.get('content'),
                'sequence': sequence,
                'create_id': user_id.id,
                'forum_id': section_id.forum_id.id,
                'section_id': section_id.id,
            })
        return request.redirect('/section/%s' % slug(section_id))

    @http.route(['/edit/text'], type='http', auth="user", website=True)
    def edit_text(self, **kwargs):
        text_id = request.env['open.text'].sudo().search([('id', '=', kwargs.get('text_id'))])
        user_id = request.env.user
        section_id = text_id.section_id
        if text_id.create_id == user_id:
            text_id.update({
                'content': kwargs.get('content'),
            })
        return request.redirect('/section/%s' % slug(section_id))

    @http.route(['/remove/text/<model("open.text"):text_id>'], type='http', auth="user", website=True)
    def remove_text(self, text_id=0):
        user_id = request.env.user
        section_id = text_id.section_id
        if text_id.create_id == user_id:
            self._del_text(text_id)
        return request.redirect('/section/%s' % slug(section_id))

    @http.route(['/add/content'], type='http', auth="user", website=True)
    def add_content(self, **kwargs):
        biblica_id = request.env['open.biblica'].sudo().search([('id', '=', kwargs.get('biblica_id'))])
        user_id = request.env.user
        if biblica_id.create_id == user_id:
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
                    'forum_id': biblica_id.forum_id.id,
                    'biblica_id': biblica_id.id,
                })
            if kwargs.get('files'):
                files = kwargs.get('files').read()
                content_id.update({
                    'files': base64.b64encode(files)
                })
            return request.redirect('/content/%s' % slug(content_id))
        else:
            return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/content/<model("open.content"):content_id>'], type='http', auth="public", website=True, csrf=False)
    def view_content(self, content_id=0, **kwargs):
        contents = request.env['open.content'].sudo().search([])
        biblicas = request.env['open.biblica'].sudo().search([('id', 'in', contents.mapped('biblica_id.id'))])
        languages = request.env['res.lang'].sudo().search([('id', 'in', biblicas.mapped('lang_id.id'))])
        biblica_id = content_id.biblica_id
        seq = content_id.sequence
        prev_id = request.env['open.content'].sudo().search(
            [('biblica_id', '=', biblica_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['open.content'].sudo().search(
            [('biblica_id', '=', biblica_id.id), ('sequence', '=', seq + 1)])
        if kwargs.get('src_id'):
            source_id = request.env['open.content'].search([("id", "=", kwargs.get('src_id'))])
        else:
            source_id = content_id.source_id
        values = {
            'user_id': request.env.user,
            'content_id': content_id,
            'biblica_id': biblica_id,
            'prev_id': prev_id,
            'next_id': next_id,
            'source_id': source_id,
            'biblicas': biblicas,
            'languages': languages,
            'contents': contents,
        }
        return request.render("website_openbiblica.view_content", values)

    @http.route(['/c/file/<int:content_id>'], type='http', auth="public")
    def load_file(self, content_id=0):
        response = self.read_file(content_id)
        return response

    @http.route(['/up/content/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def up_content(self, content_id=0):
        user_id = request.env.user
        biblica_id = content_id.biblica_id
        if content_id.create_id == user_id:
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
        user_id = request.env.user
        biblica_id = content_id.biblica_id
        if content_id.create_id == user_id:
            if content_id.sequence != len(biblica_id.content_ids):
                seq = content_id.sequence
                pseq = seq + 1
                prev = request.env['open.content'].sudo().search(
                    [('biblica_id', '=', biblica_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                content_id.update({'sequence': pseq})
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/remove/content/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def remove_content(self, content_id=0):
        user_id = request.env.user
        biblica_id = content_id.biblica_id
        if content_id.create_id == user_id:
            seq = content_id.sequence
            next_contents = request.env['open.content'].sudo().search(
                [('biblica_id', '=', biblica_id.id), ('sequence', '>', seq)])
            self._del_content(content_id)
            for content in next_contents:
                nseq = content.sequence - 1
                content.update({'sequence': nseq})
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/edit/content/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def edit_content(self, content_id=0):
        user_id = request.env.user
        biblica_id = content_id.biblica_id
        if content_id.create_id == user_id:
            values = {
                'content_id': content_id,
                'biblica_id': biblica_id,
            }
            return request.render("website_openbiblica.content_form", values)
        return request.redirect('/biblica/%s' % slug(biblica_id))

    @http.route(['/add/part'], type='http', auth='user', website=True)
    def add_part(self, **kwargs):
        user_id = request.env.user
        content_id = request.env['open.content'].sudo().search([("id", "=", kwargs.get('content_id'))])
        if content_id.create_id == user_id:
            if kwargs.get('parent_id'):
                parent_id = request.env['open.part'].sudo().search([("id", "=", kwargs.get('parent_id'))])
                seq = len(parent_id.children_ids) + 1
                request.env['open.part'].sudo().create({
                    'name': kwargs.get('name'),
                    'sequence': seq,
                    'parent_id': parent_id.id,
                    'create_id': user_id.id,
                    'forum_id': content_id.forum_id.id,
                })
            else:
                seq = len(content_id.part_ids) + 1
                request.env['open.part'].sudo().create({
                    'name': kwargs.get('name'),
                    'sequence': seq,
                    'content_id': content_id.id,
                    'create_id': user_id.id,
                    'forum_id': content_id.forum_id.id,
                })
        return request.redirect(request.httprequest.referrer)

    @http.route(['/up/part/<model("open.part"):part_id>'], type='http', auth="user", website=True)
    def up_part(self, part_id=0):
        user_id = request.env.user
        content_id = part_id.content_id
        if part_id.parent_id:
            content_id = part_id.parent_id.content_id
        if part_id.create_id == user_id:
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
        user_id = request.env.user
        content_id = part_id.content_id
        if part_id.parent_id:
            content_id = part_id.parent_id.content_id
        if part_id.create_id == user_id:
            if part_id.sequence != len(content_id.part_ids):
                seq = part_id.sequence
                pseq = seq + 1
                prev = request.env['open.part'].sudo().search(
                    [('content_id', '=', content_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                part_id.update({'sequence': pseq})
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/remove/part/<model("open.part"):part_id>'], type='http', auth="user", website=True)
    def remove_part(self, part_id=0):
        user_id = request.env.user
        if part_id.parent_id:
            parent_id = part_id.parent_id
            content_id = parent_id.content_id
        else:
            content_id = part_id.content_id
        if part_id.create_id == user_id:
            seq = part_id.sequence
            if parent_id:
                next_parts = request.env['open.part'].sudo().search(
                    [('parent_id', '=', parent_id.id), ('sequence', '>', seq)])
            else:
                next_parts = request.env['open.part'].sudo().search(
                    [('content_id', '=', content_id.id), ('sequence', '>', seq)])
            self._del_part(part_id)
            for part in next_parts:
                nseq = part.sequence - 1
                part.update({'sequence': nseq})
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/edit/part'], type='http', auth="user", website=True)
    def edit_part(self, **kwargs):
        part_id = request.env['open.part'].sudo().search([('id', '=', kwargs.get('part_id'))])
        user_id = request.env.user
        content_id = part_id.content_id
        if part_id.parent_id:
            content_id = part_id.parent_id.content_id
        if part_id.create_id == user_id:
            part_id.update({
                'name': kwargs.get('name'),
            })
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/part/<model("open.part"):part_id>'], type='http', auth="public", website=True, csrf=False)
    def view_part(self, part_id=0, **kwargs):
        contents = request.env['open.content'].sudo().search([])
        biblicas = request.env['open.biblica'].sudo().search([('id', 'in', contents.mapped('biblica_id.id'))])
        languages = request.env['res.lang'].sudo().search([('id', 'in', biblicas.mapped('lang_id.id'))])
        seq = part_id.sequence
        if part_id.parent_id:
            parent_id = part_id.parent_id
            prev_id = request.env['open.part'].sudo().search(
                [('parent_id', '=', parent_id.id), ('sequence', '=', seq - 1)])
            next_id = request.env['open.part'].sudo().search(
                [('parent_id', '=', parent_id.id), ('sequence', '=', seq + 1)])
            content_id = parent_id.content_id
        else:
            parent_id = None
            content_id = part_id.content_id
            prev_id = request.env['open.part'].sudo().search(
                [('content_id', '=', content_id.id), ('sequence', '=', seq - 1)])
            next_id = request.env['open.part'].sudo().search(
                [('content_id', '=', content_id.id), ('sequence', '=', seq + 1)])
        biblica_id = content_id.biblica_id
        if kwargs.get('src_id'):
            source_id = request.env['open.part'].search([("id", "=", kwargs.get('src_id'))])
        else:
            source_id = part_id.source_id
        if source_id.parent_id:
            s_parent_id = source_id.parent_id
            s_content_id = s_parent_id.content_id
        else:
            s_parent_id = None
            s_content_id = source_id.content_id
        s_biblica_id = s_content_id.biblica_id

        values = {
            'user_id': request.env.user,
            'part_id': part_id,
            'parent_id': parent_id,
            'content_id': content_id,
            'biblica_id': biblica_id,
            'prev_id': prev_id,
            'next_id': next_id,
            'source_id': source_id,
            's_parent_id': s_parent_id,
            's_content_id': s_content_id,
            's_biblica_id': s_biblica_id,
            'biblicas': biblicas,
            'languages': languages,
            'contents': contents,
        }
        return request.render("website_openbiblica.view_part", values)

    @http.route(['/add/line'], type='http', auth='user', website=True)
    def add_line(self, **kwargs):
        user_id = request.env.user
        part_id = request.env['open.part'].sudo().search([("id", "=", kwargs.get('part_id'))])
        seq = len(part_id.line_ids) + 1
        if part_id.create_id == user_id:
            if part_id.parent_id:
                content_id = part_id.parent_id.content_id
            else:
                content_id = part_id.content_id
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
                'forum_id': part_id.forum_id.id,
            })
            # self._add_word(line_id.name, content_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/up/line/<model("open.line"):line_id>'], type='http', auth="user", website=True)
    def up_line(self, line_id=0):
        user_id = request.env.user
        part_id = line_id.part_id
        if line_id.create_id == user_id:
            if line_id.sequence != 1:
                seq = line_id.sequence
                pseq = seq - 1
                prev = request.env['open.line'].sudo().search([('part_id', '=', part_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                line_id.update({'sequence': pseq})
        return request.redirect('/part/%s' % slug(part_id))

    @http.route(['/down/line/<model("open.line"):line_id>'], type='http', auth="user", website=True)
    def down_line(self, line_id=0):
        user_id = request.env.user
        part_id = line_id.part_id
        if line_id.create_id == user_id:
            if line_id.sequence != len(part_id.line_ids):
                seq = line_id.sequence
                pseq = seq + 1
                prev = request.env['open.line'].sudo().search([('part_id', '=', part_id.id), ('sequence', '=', pseq)])
                prev.update({'sequence': seq})
                line_id.update({'sequence': pseq})
        return request.redirect('/part/%s' % slug(part_id))

    @http.route(['/remove/line/<model("open.line"):line_id>'], type='http', auth="user", website=True)
    def remove_line(self, line_id=0):
        user_id = request.env.user
        part_id = line_id.part_id
        if line_id.create_id == user_id:
            seq = line_id.sequence
            next_lines = request.env['open.line'].sudo().search([('part_id', '=', part_id.id), ('sequence', '>', seq)])
            self._del_line(line_id)
            for line in next_lines:
                nseq = line.sequence - 1
                line.update({'sequence': nseq})
        return request.redirect('/part/%s' % slug(part_id))

    @http.route(['/edit/line'], type='http', auth="user", website=True)
    def edit_line(self, **kwargs):
        line_id = request.env['open.line'].sudo().search([('id', '=', kwargs.get('line_id'))])
        user_id = request.env.user
        if line_id.create_id == user_id:
            line_id.update({
                'content': kwargs.get('content'),
                'chapter': kwargs.get('chapter'),
                'verse': kwargs.get('verse'),
                'chapter_alt': kwargs.get('chapter_alt'),
                'verse_alt': kwargs.get('verse_alt'),
                'verse_char': kwargs.get('verse_char'),
                'is_title': kwargs.get('is_title'),
            })
            if line_id.part_id.parent_id:
                content_id = line_id.part_id.parent_id.content_id
            else:
                content_id = line_id.part_id.content_id
            # self._add_word(line_id.name, content_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/line/<model("open.line"):line_id>'], type='http', auth="public", website=True, csrf=False)
    def view_line(self, line_id=0, **kwargs):
        contents = request.env['open.content'].sudo().search([])
        biblicas = request.env['open.biblica'].sudo().search([('id', 'in', contents.mapped('biblica_id.id'))])
        languages = request.env['res.lang'].sudo().search([('id', 'in', biblicas.mapped('lang_id.id'))])
        part_id = line_id.part_id
        if part_id.parent_id:
            parent_id = part_id.parent_id
            content_id = parent_id.content_id
        else:
            parent_id = None
            content_id = part_id.content_id
        biblica_id = content_id.biblica_id

        seq = line_id.sequence
        prev_id = request.env['open.line'].sudo().search(
            [('part_id', '=', part_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['open.line'].sudo().search(
            [('part_id', '=', part_id.id), ('sequence', '=', seq + 1)])

        if kwargs.get('src_id'):
            source_id = request.env['open.line'].search([("id", "=", kwargs.get('src_id'))])
        else:
            source_id = line_id.source_id
        s_part_id = source_id.part_id
        if s_part_id.parent_id:
            s_parent_id = s_part_id.parent_id
            s_content_id = s_parent_id.content_id
        else:
            s_parent_id = None
            s_content_id = s_part_id.content_id
        s_biblica_id = s_content_id.biblica_id

        values = {
            'user_id': request.env.user,
            'line_id': line_id,
            'part_id': part_id,
            'parent_id': parent_id,
            'content_id': content_id,
            'biblica_id': biblica_id,
            'prev_id': prev_id,
            'next_id': next_id,
            'source_id': source_id,
            's_part_id': s_part_id,
            's_parent_id': s_parent_id,
            's_content_id': s_content_id,
            's_biblica_id': s_biblica_id,
            'biblicas': biblicas,
            'languages': languages,
            'contents': contents,
        }
        return request.render("website_openbiblica.view_line", values)

    @http.route(['/allsources/line/<model("open.line"):line_id>'], type='http', auth="public", website=True, csrf=False)
    def view_line_sources(self, line_id=0, **kwargs):
        contents = request.env['open.content'].sudo().search([])
        biblicas = request.env['open.biblica'].sudo().search([('id', 'in', contents.mapped('biblica_id.id'))])
        languages = request.env['res.lang'].sudo().search([('id', 'in', biblicas.mapped('lang_id.id'))])
        part_id = line_id.part_id
        if part_id.parent_id:
            parent_id = part_id.parent_id
            content_id = parent_id.content_id
        else:
            parent_id = None
            content_id = part_id.content_id
        biblica_id = content_id.biblica_id

        seq = line_id.sequence
        prev_id = request.env['open.line'].sudo().search(
            [('part_id', '=', part_id.id), ('sequence', '=', seq - 1)])
        next_id = request.env['open.line'].sudo().search(
            [('part_id', '=', part_id.id), ('sequence', '=', seq + 1)])

        values = {
            'user_id': request.env.user,
            'line_id': line_id,
            'part_id': part_id,
            'parent_id': parent_id,
            'content_id': content_id,
            'biblica_id': biblica_id,
            'prev_id': prev_id,
            'next_id': next_id,
            'biblicas': biblicas,
            'languages': languages,
            'contents': contents,
        }
        return request.render("website_openbiblica.view_line_sources", values)

    @http.route(['/add/l/source/<model("open.line"):line_id>/<model("open.line"):source_id>'], type='http',
                auth='user', website=True)
    def add_line_source(self, line_id=0, source_id=0):
        user_id = request.env.user
        if line_id.create_id == user_id:
            self._add_line_source(line_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/remove/l/source/<model("open.line"):line_id>/<model("open.line"):source_id>'], type='http',
                auth='user', website=True)
    def remove_line_source(self, line_id=0, source_id=0):
        user_id = request.env.user
        if line_id.create_id == user_id:
            self._remove_line_source(line_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/add/t/source/<model("open.text"):text_id>/<model("open.text"):source_id>'], type='http',
                auth='user', website=True)
    def add_text_source(self, text_id=0, source_id=0):
        user_id = request.env.user
        if text_id.create_id == user_id:
            self._add_text_source(text_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/remove/t/source/<model("open.text"):text_id>/<model("open.text"):source_id>'], type='http',
                auth='user', website=True)
    def remove_text_source(self, text_id=0, source_id=0):
        user_id = request.env.user
        if text_id.create_id == user_id:
            self._remove_text_source(text_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/add/p/source/<model("open.part"):part_id>/<model("open.part"):source_id>'], type='http',
                auth='user', website=True)
    def add_part_source(self, part_id=0, source_id=0):
        user_id = request.env.user
        if part_id.create_id == user_id:
            self._add_part_source(part_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/remove/p/source/<model("open.part"):part_id>/<model("open.part"):source_id>'], type='http',
                auth='user', website=True)
    def remove_part_source(self, part_id=0, source_id=0):
        user_id = request.env.user
        if part_id.create_id == user_id:
            self._remove_part_source(part_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/add/c/source'], type='http', auth='user', website=True)
    def add_content_source(self, **kwargs):
        content_id = request.env['open.content'].search([("id", "=", kwargs.get('content_id'))])
        user_id = request.env.user
        if content_id.create_id == user_id:
            source_id = request.env['open.content'].search([("id", "=", kwargs.get('con_id'))])
            self._add_content_source(content_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/remove/c/source/<model("open.content"):content_id>/<model("open.content"):source_id>'], type='http',
                auth='user', website=True)
    def remove_content_source(self, content_id=0, source_id=0):
        user_id = request.env.user
        if content_id.create_id == user_id:
            self._remove_content_source(content_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/add/s/source/<model("open.section"):section_id>/<model("open.section"):source_id>'], type='http',
                auth='user', website=True)
    def add_section_source(self, section_id=0, source_id=0):
        user_id = request.env.user
        if section_id.create_id == user_id:
            self._add_section_source(section_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/remove/s/source/<model("open.section"):section_id>/<model("open.section"):source_id>'], type='http',
                auth='user', website=True)
    def remove_section_source(self, section_id=0, source_id=0):
        user_id = request.env.user
        if section_id.create_id == user_id:
            self._remove_section_source(section_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/add/b/source/'], type='http', auth='user', website=True)
    def add_biblica_source(self, **kwargs):
        biblica_id = request.env['open.biblica'].search([("id", "=", kwargs.get('biblica_id'))])
        user_id = request.env.user
        if biblica_id.create_id == user_id:
            source_id = request.env['open.biblica'].search([("id", "=", kwargs.get('bib_id'))])
            self._add_biblica_source(biblica_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/remove/b/source/<model("open.biblica"):biblica_id>/<model("open.biblica"):source_id>'], type='http',
                auth='user', website=True)
    def remove_biblica_source(self, biblica_id=0, source_id=0):
        user_id = request.env.user
        if biblica_id.create_id == user_id:
            self._remove_biblica_source(biblica_id, source_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/comment/b/<model("open.biblica"):biblica_id>',
                 '/comment/c/<model("open.content"):content_id>',
                 '/comment/p/<model("open.part"):part_id>',
                 '/comment/l/<model("open.line"):line_id>',
                 ], type='http', auth="user", methods=['POST'], website=True)
    def post_biblica_comment(self, biblica_id=0, **kwargs):
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


