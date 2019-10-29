# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import base64
import re

from odoo import http, modules, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.web.controllers.main import binary_content

_logger = logging.getLogger(__name__)


class WebsiteInstaller(http.Controller):

    def _sourcing(self, object_id, source_id):
        object_id.update({
            'source_id': source_id.id,
            'source_ids': [(4, source_id.id)]
        })
        return

    def _sourcing_b_c(self, biblica_id, s_content_id):
        content_id = request.env['open.content'].create({
            'name': s_content_id.name,
            'sequence': s_content_id.sequence,
            'bundle': s_content_id.bundle,
            'biblica_id': biblica_id.id,
            'create_id': biblica_id.create_id.id,
            'source_id': s_content_id.id,
            'source_ids': [(4, s_content_id.id)]
        })
        if content_id.files:
            content_id.files = None
        return content_id

    def _sourcing_c_p(self, content_id, s_part_id):
        part_id = request.env['open.part'].create({
            'name': s_part_id.name,
            'sequence': s_part_id.sequence,
            'content_id': content_id.id,
            'create_id': content_id.create_id.id,
            'source_id': s_part_id.id,
            'source_ids': [(4, s_part_id.id)]
        })
        return part_id

    def _sourcing_p_l(self, part_id, s_line_id):
        request.env['open.line'].create({
            'content': ' ',
            'chapter': s_line_id.chapter or False,
            'verse': s_line_id.verse or False,
            'chapter_alt': s_line_id.chapter_alt or False,
            'verse_alt': s_line_id.verse_alt or False,
            'verse_char': s_line_id.verse_char or False,
            'sequence': s_line_id.sequence,
            'part_id': part_id.id,
            'create_id': part_id.create_id.id,
            'source_id': s_line_id.id,
            'source_ids': [(4, s_line_id.id)]
        })
        return

    @http.route(['/submit/sourcing/'], type='json', auth="public", methods=['POST'], website=True)
    def submit_sourcing(self, **kwargs):
        content_id = request.env['open.content'].search([('id', '=', int(kwargs.get('content_id')))])
        s_part_id = request.env['open.part'].search([('id', '=', int(kwargs.get('s_part_id')))])
        if not request.env['open.part'].search([('content_id', '=', content_id.id),
                                                ('sequence', '=', s_part_id.sequence)]):
            part_id = self._sourcing_c_p(content_id, s_part_id)
        else:
            part_id = request.env['open.part'].search([('content_id', '=', content_id.id),
                                                       ('sequence', '=', s_part_id.sequence)])
            if part_id.source_id != s_part_id:
                self._sourcing(part_id, s_part_id)

        for s_line_id in s_part_id.line_ids:
            if not request.env['open.line'].search([('part_id', '=', part_id.id),
                                                    ('sequence', '=', s_line_id.sequence)]):
                self._sourcing_p_l(part_id, s_line_id)
            elif request.env['open.line'].search([('part_id', '=', part_id.id),
                                                  ('sequence', '=', s_line_id.sequence)]).source_id.id != s_line_id.id:
                self._sourcing(request.env['open.line'].search([('part_id', '=', part_id.id),
                                                                ('sequence', '=', s_line_id.sequence)]), s_line_id)

        if s_part_id.sequence < len(s_part_id.content_id.part_ids):
            vals = {
                's_part_id': request.env['open.part'].search([('content_id', '=', s_part_id.content_id.id),
                                                              ('sequence', '=', s_part_id.sequence + 1)]).id,
                'content_id': content_id.id,
                'biblica_id': kwargs.get('biblica_id'),
            }
            return vals

        if not kwargs.get('biblica_id'):
            vals = {
                'content_id': kwargs.get('content_id'),
            }
            return vals

        s_content_id = s_part_id.content_id
        while s_content_id.sequence < len(s_content_id.biblica_id.content_ids):
            next_s_content_id = request.env['open.content'].search([
                ('biblica_id', '=', s_content_id.biblica_id.id),
                ('sequence', '=', s_content_id.sequence + 1)])
            if not request.env['open.content'].search([('biblica_id', '=', content_id.biblica_id.id),
                                                       ('sequence', '=', next_s_content_id.sequence)]):
                next_content_id = self._sourcing_b_c(content_id.biblica_id, next_s_content_id)
            else:
                next_content_id = request.env['open.content'].search([('biblica_id', '=', content_id.biblica_id.id),
                                                                      ('sequence', '=', next_s_content_id.sequence)])
                if next_content_id.source_id != next_s_content_id:
                    self._sourcing(next_content_id, next_s_content_id)
            if not next_s_content_id.part_ids:
                s_content_id = next_s_content_id
                continue
            vals = {
                's_part_id': next_s_content_id.part_ids[0].id,
                'content_id': next_content_id.id,
                'biblica_id': kwargs.get('biblica_id'),
            }
            return vals
        vals = {
            'biblica_id': kwargs.get('biblica_id'),
        }
        return vals

    @http.route(['/sourcing/c'], type='http', auth="user", website=True)
    def sourcing_c(self, **kwargs):
        content_id = request.env['open.content'].search([('id', '=', kwargs.get('content_id'))])
        if content_id.create_id != request.env.user:
            return request.redirect('/content/%s' % slug(content_id))
        s_content_id = request.env['open.content'].search([('id', '=', kwargs.get('s_content_id'))])
        if content_id.source_id != s_content_id:
            self._sourcing(content_id, s_content_id)
        if not s_content_id.part_ids:
            return request.redirect('/content/%s' % slug(content_id))
        values = {
            's_part_id': s_content_id.part_ids[0].id,
            'content_id': content_id.id,
        }
        return request.render("website_openbiblica.sourcing", values)

    @http.route(['/sourcing/b'], type='http', auth="user", website=True)
    def sourcing_b(self, **kwargs):
        biblica_id = request.env['open.biblica'].search([('id', '=', kwargs.get('biblica_id'))])
        if biblica_id.create_id != request.env.user:
            return request.redirect('/biblica/%s' % slug(biblica_id))
        s_biblica_id = request.env['open.biblica'].search([('id', '=', kwargs.get('bible'))])
        if biblica_id.source_id != s_biblica_id:
            self._sourcing(biblica_id, s_biblica_id)
        if not s_biblica_id.content_ids:
            return request.redirect('/biblica/%s' % slug(biblica_id))
        for s_content_id in s_biblica_id.content_ids:
            if not request.env['open.content'].search([('biblica_id', '=', biblica_id.id),
                                                       ('sequence', '=', s_content_id.sequence)]):
                self._sourcing_b_c(biblica_id, s_content_id)
            else:
                if request.env['open.content'].search([('biblica_id', '=', biblica_id.id),
                                                       ('sequence', '=', s_content_id.sequence)]).source_id.id != s_content_id.id:
                    self._sourcing(request.env['open.content'].search([('biblica_id', '=', biblica_id.id),
                                                       ('sequence', '=', s_content_id.sequence)]), s_content_id)
        s_content_ids = [j for j in s_biblica_id.content_ids if j.part_ids]
        s_content_id = s_content_ids[0]
        if not s_content_id:
            return request.redirect('/biblica/%s' % slug(biblica_id))
        values = {
            's_part_id': s_content_id.part_ids[0].id,
            'content_id': request.env['open.content'].search([('biblica_id', '=', biblica_id.id),
                                                              ('sequence', '=', s_content_id.sequence)]).id,
            'biblica_id': biblica_id.id,
        }
        return request.render("website_openbiblica.sourcing", values)

    @http.route('/source/c/<int:content>', type='http', auth="user", website=True)
    def source_content(self, content=0):
        values = {
            'content_id': request.env['open.content'].search([('id', '=', content)]),
            'user_id': request.env.user,
        }
        return request.render("website_openbiblica.source_content", values)

    @http.route('/source/b/<int:biblica>', type='http', auth="user", website=True)
    def source_biblica(self, biblica=0):
        values = {
            'biblica_id': request.env['open.biblica'].search([('id', '=', biblica)]),
            'user_id': request.env.user,
        }
        return request.render("website_openbiblica.source_biblica", values)

    @http.route(['/transto/content'], type='http', auth='user', website=True)
    def transto_content(self, **kwargs):
        user_id = request.env.user
        if kwargs.get('content_id'):
            content_id = request.env['open.content'].search([("id", "=", kwargs.get('content_id'))])
            if content_id.create_id != user_id:
                return request.redirect(request.httprequest.referrer)

        elif kwargs.get('biblica_id'):
            biblica_id = request.env['open.biblica'].search([("id", "=", kwargs.get('biblica_id'))])
            if biblica_id.create_id != user_id:
                return request.redirect(request.httprequest.referrer)
            if not kwargs.get('content_name'):
                return request.redirect(request.httprequest.referrer)
            content_id = request.env['open.content'].create({
                'name': kwargs.get('content_name'),
                'sequence': len(biblica_id.content_ids) + 1,
                'biblica_id': biblica_id.id,
                'create_id': biblica_id.create_id.id,
            })

        else:
            if kwargs.get('lang_id'):
                lang_id = request.env['res.lang'].search([("id", "=", kwargs.get('lang_id'))])
            elif kwargs.get('language_name'):
                lang_id = request.env['res.lang'].create({
                    'name': kwargs.get('language_name'),
                    'code': kwargs.get('language_code'),
                    'iso_code': kwargs.get('language_iso_code'),
                    'direction': kwargs.get('direction'),
                    'active': True
                })
            else:
                return request.redirect(request.httprequest.referrer)

            forum_id = request.env['forum.forum'].search([("name", "=", lang_id.name)])
            if not forum_id:
                forum_id = request.env['forum.forum'].create({'name': lang_id.name})
            if not kwargs.get('name'):
                return request.redirect(request.httprequest.referrer)
            if not kwargs.get('content_name'):
                return request.redirect(request.httprequest.referrer)

            biblica_id = request.env['open.biblica'].create({
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'create_id': user_id.id,
                'lang_id': lang_id.id,
                'forum_id': forum_id.id,
            })
            content_id = request.env['open.content'].create({
                'name': kwargs.get('content_name'),
                'sequence': len(biblica_id.content_ids) + 1,
                'biblica_id': biblica_id.id,
                'create_id': biblica_id.create_id.id,
            })
        content_id.files = None
        source_id = request.env['open.content'].search([("id", "=", kwargs.get('s_content_id'))])
        if content_id.source_id != source_id:
            self._sourcing(content_id, source_id)
        if not source_id.part_ids:
            return request.redirect('/content/%s' % slug(content_id))
        s_part_id = source_id.part_ids[0]
        values = {
            's_part_id': s_part_id.id,
            'content_id': content_id.id,
        }
        return request.render("website_openbiblica.sourcing", values)

    def _copy_line_source(self, line_id, source_id):
        line_id.update({
            'content': source_id.content,
            'chapter': source_id.chapter,
            'chapter_alt': source_id.chapter_alt,
            'verse': source_id.verse,
            'verse_alt': source_id.verse_alt,
            'verse_char': source_id.verse_char,
            'style': source_id.style,
            'align': source_id.align,
            'insert_paragraph': source_id.insert_paragraph,
        })
        return

    def _copy_part_source(self, part_id, source_id):
        part_id.update({
            'name': source_id.name,
            'description': source_id.description,
        })
        return

    def _copy_content_source(self, content_id, source_id):
        content_id.update({
            'name': source_id.name,
            'description': source_id.description,
            'title_id': source_id.title_id,
            'title_ide': source_id.title_ide,
            'title_short': source_id.title_short,
            'title_abrv': source_id.title_abrv,
            'bundle': source_id.bundle,
        })
        return

    def _copy_biblica_source(self, biblica_id, source_id):
        biblica_id.update({
            'name': source_id.name,
            'description': source_id.description,
        })
        return

    def _copying_p_l(self, part_id, s_line_id):
        request.env['open.line'].create({
            'content': s_line_id.content,
            'chapter': s_line_id.chapter or False,
            'verse': s_line_id.verse or False,
            'chapter_alt': s_line_id.chapter_alt or False,
            'verse_alt': s_line_id.verse_alt or False,
            'verse_char': s_line_id.verse_char or False,
            'sequence': s_line_id.sequence,
            'part_id': part_id.id,
            'create_id': part_id.create_id.id,
            'source_id': s_line_id.id,
            'source_ids': [(4, s_line_id.id)]
        })
        return

    def _copying_c_p(self, content_id, s_part_id):
        part_id = request.env['open.part'].create({
            'name': s_part_id.name,
            'description': s_part_id.description,
            'sequence': s_part_id.sequence,
            'content_id': content_id.id,
            'create_id': content_id.create_id.id,
            'source_id': s_part_id.id,
            'source_ids': [(4, s_part_id.id)]
        })
        return part_id

    def _copying_b_c(self, biblica_id, s_content_id):
        content_id = request.env['open.content'].create({
            'name': s_content_id.name,
            'sequence': s_content_id.sequence,
            'description': s_content_id.description,
            'title_id': s_content_id.title_id,
            'title_ide': s_content_id.title_ide,
            'title_short': s_content_id.title_short,
            'title_abrv': s_content_id.title_abrv,
            'bundle': s_content_id.bundle,
            'biblica_id': biblica_id.id,
            'create_id': biblica_id.create_id.id,
            'source_id': s_content_id.id,
            'source_ids': [(4, s_content_id.id)]
        })
        if content_id.files:
            content_id.files = None
        return content_id

    @http.route(['/copying/source/'], type='json', auth="public", methods=['POST'], website=True)
    def copying_source(self, **kwargs):
        content_id = request.env['open.content'].search([('id', '=', int(kwargs.get('content_id')))])
        s_part_id = request.env['open.part'].search([('id', '=', int(kwargs.get('s_part_id')))])
        if not request.env['open.part'].search([('content_id', '=', content_id.id),
                                                       ('sequence', '=', s_part_id.sequence)]):
            part_id = self._copying_c_p(content_id, s_part_id)
        else:
            part_id = request.env['open.part'].search([
                ('content_id', '=', content_id.id),
                ('sequence', '=', s_part_id.sequence)])
            self._copy_part_source(part_id, s_part_id)

        for s_line_id in s_part_id.line_ids:
            if not request.env['open.line'].search([('part_id', '=', part_id.id),
                                                    ('sequence', '=', s_line_id.sequence)]):
                self._copying_p_l(part_id, s_line_id)
            else:
                self._copy_line_source(
                    request.env['open.line'].search([('part_id', '=', part_id.id),
                                                     ('sequence', '=', s_line_id.sequence)]), s_line_id)

        if s_part_id.sequence < len(s_part_id.content_id.part_ids):
            vals = {
                's_part_id': request.env['open.part'].search([('content_id', '=', s_part_id.content_id.id),
                                                              ('sequence', '=', s_part_id.sequence + 1)]).id,
                'content_id': content_id.id,
                'biblica_id': kwargs.get('biblica_id'),
            }
            return vals

        if not kwargs.get('biblica_id'):
            vals = {
                'content_id': kwargs.get('content_id'),
            }
            return vals

        s_content_id = s_part_id.content_id
        while s_content_id.sequence < len(s_content_id.biblica_id.content_ids):
            next_s_content_id = request.env['open.content'].search([
                ('biblica_id', '=', s_content_id.biblica_id.id),
                ('sequence', '=', s_content_id.sequence + 1)])
            if not request.env['open.content'].search([('biblica_id', '=', content_id.biblica_id.id),
                                                       ('sequence', '=', next_s_content_id.sequence)]):
                next_content_id = self._copying_b_c(content_id.biblica_id, next_s_content_id)
            else:
                next_content_id = request.env['open.content'].search([('biblica_id', '=', content_id.biblica_id.id),
                                                                      ('sequence', '=', next_s_content_id.sequence)])
                self._copy_content_source(next_content_id, next_s_content_id)
            if not next_s_content_id.part_ids:
                s_content_id = next_s_content_id
                continue
            vals = {
                's_part_id': next_s_content_id.part_ids[0].id,
                'content_id': next_content_id.id,
                'biblica_id': kwargs.get('biblica_id'),
            }
            return vals
        vals = {
            'biblica_id': kwargs.get('biblica_id'),
        }
        return vals

    @http.route(['/copy/c/source/<model("open.content"):content_id>/<model("open.content"):source_id>'], type='http',
                auth='user', website=True)
    def copy_content_source(self, content_id=0, source_id=0):
        if content_id.create_id != request.env.user:
            return request.redirect(request.httprequest.referrer)
        self._copy_content_source(content_id, source_id)
        if not source_id.part_ids:
            return request.redirect('/content/%s' % slug(content_id))
        values = {
            's_part_id': source_id.part_ids[0].id,
            'content_id': content_id.id,
        }
        return request.render("website_openbiblica.copying", values)

    @http.route(['/copy/b/source/<model("open.biblica"):biblica_id>/<model("open.biblica"):source_id>'], type='http',
                auth='user', website=True)
    def copy_biblica_source(self, biblica_id=0, source_id=0):
        if biblica_id.create_id != request.env.user:
            return request.redirect(request.httprequest.referrer)
        self._copy_biblica_source(biblica_id, source_id)
        if not source_id.content_ids:
            return request.redirect('/biblica/%s' % slug(biblica_id))

        for s_content_id in source_id.content_ids:
            if not request.env['open.content'].search([('biblica_id', '=', biblica_id.id),
                                                       ('sequence', '=', s_content_id.sequence)]):
                self._copying_b_c(biblica_id, s_content_id)
            else:
                self._copy_content_source(request.env['open.content'].search([('biblica_id', '=', biblica_id.id),
                                                                              ('sequence', '=', s_content_id.sequence)]), s_content_id)
        s_content_ids = [j for j in source_id.content_ids if j.part_ids]
        s_content_id = s_content_ids[0]
        if not s_content_id:
            return request.redirect('/biblica/%s' % slug(biblica_id))
        values = {
            's_part_id': s_content_id.part_ids[0].id,
            'content_id': request.env['open.content'].search([('biblica_id', '=', biblica_id.id), ('sequence', '=', s_content_id.sequence)]).id,
            'biblica_id': biblica_id.id,
        }
        return request.render("website_openbiblica.copying", values)

    @http.route(['/copy/p/source/<model("open.part"):part_id>/<model("open.part"):source_id>'], type='http',
                auth='user', website=True)
    def copy_part_source(self, part_id=0, source_id=0):
        if part_id.create_id != request.env.user:
            return request.redirect(request.httprequest.referrer)
        self._copy_part_source(part_id, source_id)
        if not source_id.line_ids:
            return request.redirect(request.httprequest.referrer)
        for s_line_id in source_id.line_ids:
            if not request.env['open.line'].search([('part_id', '=', part_id.id),
                                                    ('sequence', '=', s_line_id.sequence)]):
                self._copying_p_l(part_id, s_line_id)
            else:
                self._copy_line_source(request.env['open.line'].search([('part_id', '=', part_id.id),
                                                                        ('sequence', '=', s_line_id.sequence)]), s_line_id)
        return request.redirect(request.httprequest.referrer)

    @http.route(['/copy/l/source/<model("open.line"):line_id>/<model("open.line"):source_id>'], type='http',
                auth='user', website=True)
    def copy_line_source(self, line_id=0, source_id=0):
        if line_id.create_id == request.env.user:
            self._copy_line_source(line_id, source_id)
        return request.redirect(request.httprequest.referrer)

    def _remove_line_source(self, line_id, source_id):
        if line_id.source_id == source_id:
            line_id['source_id'] = None
        line_id.update({
            'source_ids': [(3, source_id.id)]
        })
        return

    def _remove_part_source(self, part_id, source_id):
        if part_id.source_id == source_id:
            part_id['source_id'] = None
        part_id.update({
            'source_ids': [(3, source_id.id)]
        })
        return

    def _remove_content_source(self, content_id, source_id):
        if content_id.source_id == source_id:
            content_id['source_id'] = None
        content_id.update({
            'source_ids': [(3, source_id.id)]
        })
        return

    def _remove_biblica_source(self, biblica_id, source_id):
        if biblica_id.source_id == source_id:
            biblica_id['source_id'] = None
        biblica_id.update({
            'source_ids': [(3, source_id.id)]
        })
        return

    @http.route(['/remove/source/'], type='json', auth="public", methods=['POST'], website=True)
    def remove_source(self, **kwargs):
        content_id = request.env['open.content'].search([('id', '=', int(kwargs.get('content_id')))])
        s_part_id = request.env['open.part'].search([('id', '=', int(kwargs.get('s_part_id')))])

        while request.env['open.part'].search([('content_id', '=', content_id.id),
                                               ('source_ids', 'in', s_part_id.id)]):
            part_id = request.env['open.part'].search([('content_id', '=', content_id.id),
                                            ('source_ids', 'in', s_part_id.id)])[0]
            for s_line_id in s_part_id.line_ids:
                while request.env['open.line'].search([('part_id', '=', part_id.id),
                                                        ('source_ids', 'in', s_line_id.id)]):
                    line_id = request.env['open.line'].search([('part_id', '=', part_id.id),
                                                        ('source_ids', 'in', s_line_id.id)])[0]
                    self._remove_line_source(line_id, s_line_id)
                    continue
            self._remove_part_source(part_id, s_part_id)
            continue

        if s_part_id.sequence < len(s_part_id.content_id.part_ids):
            vals = {
                's_part_id': request.env['open.part'].search([('content_id', '=', s_part_id.content_id.id),
                                                              ('sequence', '=', s_part_id.sequence + 1)]).id,
                'content_id': content_id.id,
                'biblica_id': kwargs.get('biblica_id'),
            }
            return vals

        s_content_id = s_part_id.content_id
        self._remove_content_source(content_id, s_content_id)

        if not kwargs.get('biblica_id'):
            vals = {
                'content_id': kwargs.get('content_id'),
            }
            return vals

        while request.env['open.content'].search([('biblica_id', '=', content_id.biblica_id.id),
                                                  ('source_ids', 'in', s_content_id.id)]):
            vals = {
                's_part_id': s_content_id.part_ids[0].id,
                'content_id': request.env['open.content'].search([('biblica_id', '=', content_id.biblica_id.id),
                                                                  ('source_ids', 'in', s_content_id.id)])[0].id,
                'biblica_id': kwargs.get('biblica_id'),
            }
            return vals

        while s_content_id.sequence < len(s_content_id.biblica_id.content_ids):
            next_s_content_id = request.env['open.content'].search([
                ('biblica_id', '=', s_content_id.biblica_id.id),
                ('sequence', '=', s_content_id.sequence + 1)])
            if not request.env['open.content'].search([('biblica_id', '=', content_id.biblica_id.id),
                                                       ('source_ids', 'in', next_s_content_id.id)]):
                continue
            next_content_id = request.env['open.content'].search([('biblica_id', '=', content_id.biblica_id.id),
                                                                  ('source_ids', 'in', next_s_content_id.id)])[0]
            if not next_s_content_id.part_ids:
                self._remove_content_source(next_content_id, next_s_content_id)
                continue
            vals = {
                's_part_id': next_s_content_id.part_ids[0].id,
                'content_id': next_content_id.id,
                'biblica_id': kwargs.get('biblica_id'),
            }
            return vals
        self._remove_biblica_source(content_id.biblica_id, s_content_id.biblica_id)
        vals = {
            'biblica_id': kwargs.get('biblica_id'),
        }
        return vals

    @http.route(['/remove/c/source/<model("open.content"):content_id>/<model("open.content"):source_id>'], type='http',
                auth='user', website=True)
    def remove_content_source(self, content_id=0, source_id=0):
        if content_id.create_id != request.env.user:
            return request.redirect(request.httprequest.referrer)
        if not source_id.part_ids:
            self._remove_content_source(content_id, source_id)
            return request.redirect('/content/%s' % slug(content_id))
        values = {
            's_part_id': source_id.part_ids[0].id,
            'content_id': content_id.id,
        }
        return request.render("website_openbiblica.remove_source", values)

    @http.route(['/remove/b/source/<model("open.biblica"):biblica_id>/<model("open.biblica"):source_id>'], type='http',
                auth='user', website=True)
    def remove_biblica_source(self, biblica_id=0, source_id=0):
        if biblica_id.create_id != request.env.user:
            return request.redirect(request.httprequest.referrer)
        if not source_id.content_ids:
            return request.redirect('/biblica/%s' % slug(biblica_id))

        s_content_id = source_id.content_ids[0]
        while s_content_id.sequence < len(source_id.content_ids) + 1:
            while request.env['open.content'].search([('biblica_id', '=', biblica_id.id),
                                                            ('source_ids', 'in', s_content_id.id)]):
                content_id = request.env['open.content'].search([('biblica_id', '=', biblica_id.id),
                                                                 ('source_ids', 'in', s_content_id.id)])[0]
                if s_content_id.part_ids:
                    values = {
                        's_part_id': s_content_id.part_ids[0].id,
                        'content_id': content_id.id,
                        'biblica_id': biblica_id.id,
                    }
                    return request.render("website_openbiblica.remove_source", values)
                self._remove_content_source(content_id, s_content_id)
                continue
            s_content_id = request.env['open.content'].search([('biblica_id', '=', s_content_id.biblica_id.id),
                                                               ('sequence', '=', s_content_id.sequence + 1)])
            continue
        self._remove_biblica_source(biblica_id, source_id)
        return request.redirect('/biblica/%s' % slug(biblica_id))

    def _del_line(self, line_id):
        request.env['open.point'].search([("line_id", "=", line_id.id)]).unlink()
        line_id.unlink()
        return

    def _del_part(self, part_id):
        request.env['open.point'].search([("part_id", "=", part_id.id)]).unlink()
        request.env['open.line'].search([("part_id", "=", part_id.id)]).unlink()
        part_id.unlink()
        return

    @http.route(['/remove/p/'], type='json', auth="public", methods=['POST'], website=True)
    def remove_p(self, **kwargs):
        part_id = request.env['open.part'].search([('id', '=', int(kwargs.get('part_id')))])
        request.env['open.point'].search([("part_id", "=", part_id.id)]).unlink()
        request.env['open.line'].search([("part_id", "=", part_id.id)]).unlink()
        content_id = part_id.content_id
        part_id.unlink()

        while content_id.part_ids:
            vals = {
                'part_id': content_id.part_ids[0].id,
                'biblica_id': kwargs.get('biblica_id'),
            }
            return vals

        biblica_id = content_id.biblica_id
        content_id.files = None
        content_id.unlink()

        if not kwargs.get('biblica_id'):
            vals = {
                'biblica_id': biblica_id.id,
            }
            return vals

        while biblica_id.content_ids:
            content_id = request.env['open.content'].search([('biblica_id', '=', biblica_id.id)])[0]
            if not content_id.part_ids:
                content_id.files = None
                content_id.unlink()
                continue
            vals = {
                'part_id': content_id.part_ids[0].id,
                'biblica_id': kwargs.get('biblica_id'),
            }
            return vals

        biblica_id.unlink()
        vals = {}
        return vals

    @http.route(['/remove/content/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def remove_content(self, content_id=0):
        if content_id.create_id == request.env.user:
            biblica_id = content_id.biblica_id
            seq = content_id.sequence
            next_contents = request.env['open.content'].search(
                [('biblica_id', '=', biblica_id.id), ('sequence', '>', seq)])
            for content in next_contents:
                nseq = content.sequence - 1
                content.update({'sequence': nseq})
            if content_id.part_ids:
                values = {
                    'part_id': content_id.part_ids[0].id,
                }
                return request.render("website_openbiblica.remove", values)
            content_id.files = None
            content_id.unlink()
            return request.redirect('/biblica/%s' % slug(biblica_id))
        return request.redirect('/')

    @http.route(['/remove/biblica/<model("open.biblica"):biblica_id>'], type='http', auth='user', website=True)
    def remove_biblica(self, biblica_id=0):
        if biblica_id.create_id == request.env.user:
            while biblica_id.content_ids:
                content_id = request.env['open.content'].search([('biblica_id', '=', biblica_id.id)])[0]
                if not content_id.part_ids:
                    content_id.files = None
                    content_id.unlink()
                    continue
                values = {
                    'part_id': content_id.part_ids[0].id,
                    'biblica_id': biblica_id.id,
                }
                return request.render("website_openbiblica.remove", values)
            biblica_id.unlink()
            return request.redirect('/my/home')
        return request.redirect('/')

    @http.route(['/remove/part/<model("open.part"):part_id>'], type='http', auth="user", website=True)
    def remove_part(self, part_id=0):
        content_id = part_id.content_id
        if part_id.create_id == request.env.user:
            seq = part_id.sequence
            next_parts = request.env['open.part'].search(
                [('content_id', '=', content_id.id), ('sequence', '>', seq)])
            for part in next_parts:
                nseq = part.sequence - 1
                part.update({'sequence': nseq})
            self._del_part(part_id)
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/remove/subcontent/<model("open.subcontent"):subcontent_id>'], type='http', auth="user", website=True)
    def remove_subcontent(self, subcontent_id=0):
        content_id = subcontent_id.content_id
        if subcontent_id.create_id == request.env.user:
            seq = subcontent_id.sequence
            next_subcontents = request.env['open.subcontent'].search(
                [('content_id', '=', content_id.id), ('sequence', '>', seq)])
            subcontent_id.unlink()
            for subcontent in next_subcontents:
                nseq = subcontent.sequence - 1
                subcontent.update({'sequence': nseq})
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/remove/line/<model("open.line"):line_id>'], type='http', auth="user", website=True)
    def remove_line(self, line_id=0):
        part_id = line_id.part_id
        if line_id.create_id == request.env.user:
            seq = line_id.sequence
            next_lines = request.env['open.line'].search([('part_id', '=', part_id.id), ('sequence', '>', seq)])
            for line in next_lines:
                nseq = line.sequence - 1
                line.update({'sequence': nseq})
            self._del_line(line_id)
        return request.redirect('/part/%s' % slug(part_id))

    @http.route('/translate/c/<int:content>', type='http', auth="user", website=True)
    def trans_content(self, content=0):
        user_id = request.env.user
        values = {
            'biblica_ids': request.env['open.biblica'].search([('create_id', '=', user_id.id)]),
            'content_ids': request.env['open.content'].search([('create_id', '=', user_id.id)]),
            'content_id': request.env['open.content'].search([('id', '=', content)]),
            'user_id': user_id,
            'languages': request.env['res.lang'].search([]),
        }
        return request.render("website_openbiblica.trans_content", values)

    def _install_content(self, content, content_id, user_id, part_id):
        # raise UserError(content)
        style = 'normal'
        align = 'default'
        insert_paragraph = False
        chapter = 0
        verse = 0
        major_part_id = None
        major_sequence = 1
        part_sequence = 1
        line_sequence = 1

        if part_id:
            last_line_id = request.env['open.line'].search([('part_id', '=', part_id.id)])[-1]
            part_sequence = part_id.sequence + 1
            if last_line_id:
                style = last_line_id.style
                align = last_line_id.align
                insert_paragraph = last_line_id.insert_paragraph
            if part_id.subcontent_id:
                major_part_id = part_id.subcontent_id
                major_sequence = major_part_id.sequence + 1

        for line in content:

            head, _, texts = line.partition(" ")

            # CONTENT
            if head == '\id':
                content_id['title_id'] = texts
            elif head == '\ide':
                content_id['title_ide'] = texts
            elif head == r'\toc1':
                content_id['title'] = texts
            elif head == r'\toc2':
                content_id['title_short'] = texts
            elif head == r'\toc3':
                content_id['title_abrv'] = texts
            elif head == '\mt' or head == '\mt1':
                content_id['name'] = texts
            elif head == '\h' or head == '\mt2' or head == '\mt3':
                if content_id.description:
                    content_id['description'] += texts + '\n'
                else:
                    content_id['description'] = texts + '\n'

            # PART

            elif head == '\ms':
                major_part_id = request.env['open.subcontent'].create({
                    'name': texts,
                    'sequence': major_sequence,
                    'create_id': user_id.id,
                    'content_id': content_id.id,
                })
                major_sequence += 1
            elif head == '\c':
                c, _, temp = texts.partition(" ")
                if c != ' ':
                    chapter = c
                part_id = request.env['open.part'].create({
                    'name': texts,
                    'sequence': part_sequence,
                    'create_id': user_id.id,
                    'content_id': content_id.id,
                })
                part_sequence += 1
                line_sequence = 1
                if major_part_id:
                    part_id.update({'subcontent_id': major_part_id.id})

            # LINE

            elif head == r'\v':
                v, _, texts = texts.partition(" ")
                if v != ' ':
                    verse = v
                request.env['open.line'].create({
                    'chapter': chapter,
                    'verse': verse,
                    'content': texts,
                    'sequence': line_sequence,
                    'create_id': user_id.id,
                    'part_id': part_id.id,
                    'style': style,
                    'align': align,
                    'insert_paragraph': insert_paragraph,
                })
                line_sequence += 1
                insert_paragraph = False
            elif head == '\d':
                request.env['open.line'].create({
                    'content': texts,
                    'sequence': line_sequence,
                    'create_id': user_id.id,
                    'part_id': part_id.id,
                    'style': style,
                    'align': align,
                    'insert_paragraph': insert_paragraph,
                })
                line_sequence += 1
                insert_paragraph = False
            elif head == r'\f' or head == r'\ft':
                request.env['open.line'].create({
                    'content': texts,
                    'sequence': line_sequence,
                    'create_id': user_id.id,
                    'part_id': part_id.id,
                    'style': style,
                    'align': align,
                    'insert_paragraph': insert_paragraph,
                })
                line_sequence += 1
                insert_paragraph = False
            elif head == '\q' or head == '\q1' or head == '\q2' or head == '\q3':
                style = 'italic'
                if texts:
                    request.env['open.line'].create({
                        'content': texts,
                        'sequence': line_sequence,
                        'create_id': user_id.id,
                        'part_id': part_id.id,
                        'style': style,
                        'align': align,
                        'insert_paragraph': insert_paragraph,
                    })
                    line_sequence += 1
            elif head == '\m':
                insert_paragraph = False
                if texts:
                    request.env['open.line'].create({
                        'content': texts,
                        'sequence': line_sequence,
                        'create_id': user_id.id,
                        'part_id': part_id.id,
                        'style': style,
                        'align': align,
                        'insert_paragraph': insert_paragraph,
                    })
                    line_sequence += 1
            elif head == '\qs':
                texts = texts.strip('\qs ').strip('\qs*')
                request.env['open.line'].create({
                    'content': texts,
                    'sequence': line_sequence,
                    'create_id': user_id.id,
                    'part_id': part_id.id,
                    'insert_paragraph': insert_paragraph,
                    'style': style,
                })
                line_sequence += 1

            # COMMANDS

            elif head == '\s5':
                style = 'normal'
            elif head == '\p':
                insert_paragraph = True
            elif head == r'\nb':
                insert_paragraph = False

        next_values = {
            'chapter': chapter,
            'content_id': content_id,
        }
        return next_values

    @http.route(['/cleaning/p/'], type='json', auth="public", methods=['POST'], website=True)
    def cleaning_p(self, **kwargs):
        part_id = request.env['open.part'].search([('id', '=', int(kwargs.get('part_id')))])
        request.env['open.point'].search([("part_id", "=", part_id.id)]).unlink()
        request.env['open.line'].search([("part_id", "=", part_id.id)]).unlink()
        content_id = part_id.content_id
        part_id.unlink()

        while content_id.part_ids:
            vals = {
                'part_id': content_id.part_ids[0].id,
                'content_id': kwargs.get('content_id'),
                'biblica_id': kwargs.get('biblica_id'),
            }
            return vals
        vals = {}
        return vals

    @http.route(['/cleaning/<model("open.content"):content_id>',
                 '/cleaning/<model("open.content"):content_id>/<model("open.biblica"):biblica_id>'
                 ], type='http', auth="user", website=True)
    def cleaning(self, content_id=0, biblica_id=0):
        if content_id.create_id == request.env.user:
            values = {
                'part_id': content_id.part_ids[0].id,
                'content_id': content_id,
                'biblica_id': biblica_id,
            }
            return request.render("website_openbiblica.cleaning", values)
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/install/usfm/<model("open.content"):content_id>',
                 '/install/usfm/<model("open.content"):content_id>/<model("open.biblica"):biblica_id>'
                 ], type='http', auth="user", website=True)
    def install_usfm(self, content_id=0, biblica_id=0):
        user_id = request.env.user
        if content_id.create_id == user_id:
            if content_id.part_ids:
                if biblica_id:
                    return request.redirect('/cleaning/%s/%s' % (slug(content_id), slug(biblica_id)))
                else:
                    return request.redirect('/cleaning/%s' % slug(content_id))
            status, headers, content = binary_content(model='open.content', id=content_id.id, field='files',
                                                          env=request.env(user=SUPERUSER_ID))
            content = base64.b64decode(content).decode('utf-8')
            content, mid, rest = content.partition("\c")
            rest = mid + rest
            content = content.splitlines()

            n_values = self._install_content(content, content_id, user_id, None)

            if rest:
                rest = rest.encode('utf-8')
                content_id.update({
                    'rest': base64.b64encode(rest)
                })
                if biblica_id:
                    return request.render("website_openbiblica.install_next_b", n_values)
                return request.render("website_openbiblica.install_next", n_values)
            else:
                content_id.update({
                    'rest': None,
                    'is_installed': True
                })
        if biblica_id:
            return request.redirect('/install/b/usfm/%s' % slug(biblica_id))
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/install/continue/usfm/<model("open.content"):content_id>',
                 '/install/continue/usfm/<model("open.content"):content_id>/<model("open.biblica"):biblica_id>'
                 ], type='http', auth="user", website=True)
    def cont_install_usfm(self, content_id=0, biblica_id=0):
        user_id = request.env.user
        if content_id.create_id == user_id:
            status, headers, content = binary_content(model='open.content', id=content_id.id, field='rest',
                                                          env=request.env(user=SUPERUSER_ID))
            text = base64.b64decode(content).decode('utf-8')
            _, header, content = text.partition("\c")
            text, mid, rest = content.partition("\c")
            rest = mid + rest
            c, _, temp = text.partition(" ")
            chapter, _, temp = temp.partition(" ")
            content = header + text
            text = content.splitlines()

            if content_id.part_ids:
                last_part_id = request.env['open.part'].search([('content_id', '=', content_id.id)])[-1]
                if chapter == request.env['open.line'].search([('part_id', '=', last_part_id.id), ('chapter', '!=', None)])[0].chapter:
                    request.env['open.line'].search([('part_id', '=', last_part_id.id)]).unlink()
                    prev_part_id = request.env['open.part'].search([('content_id', '=', content_id.id), ('sequence', '=', last_part_id.sequence - 1)])
                    last_part_id.unlink()
                    last_part_id = prev_part_id
            else:
                last_part_id = None

            n_values = self._install_content(text, content_id, user_id, last_part_id)

            if rest:
                rest = rest.encode('utf-8')
                content_id.update({
                    'rest': base64.b64encode(rest)
                })
                if biblica_id:
                    return request.render("website_openbiblica.install_next_b", n_values)
                return request.render("website_openbiblica.install_next", n_values)
            else:
                content_id.update({
                    'rest': None,
                    'is_installed': True
                })
        if biblica_id:
            return request.redirect('/install/b/usfm/%s' % slug(biblica_id))
        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/install/b/usfm/<model("open.biblica"):biblica_id>'], type='http', auth="user", website=True)
    def b_install_usfm(self, biblica_id=0):
        if biblica_id.create_id == request.env.user:
            content_ids = request.env['open.content'].search([
                ('biblica_id', '=', biblica_id.id),
                ('is_installed', '=', False)])
            content_ids = [j for j in content_ids if j.files]
            if not content_ids:
                biblica_id['is_installed'] = True
                return request.redirect('/biblica/%s' % slug(biblica_id))
            content_id = content_ids[0]
            if content_id.rest:
                return request.redirect('/install/continue/usfm/%s/%s' % (slug(content_id), slug(biblica_id)))
            else:
                return request.redirect('/install/usfm/%s/%s' % (slug(content_id), slug(biblica_id)))

    # def _interlinear_line(self, line_id):
    #     if line_id.lang_id.direction == 'rtl':
    #         words = line_id.name.split()
    #     else:
    #         words = re.findall(r'\w+|[\[\]⸂⸃()]|\S+', line_id.name)
    #     sequence = 1
    #     for word in words:
    #         word_id = request.env['open.word'].search([('name', '=', word), ('lang_id', '=', line_id.lang_id.id)])
    #         if not word_id:
    #             word_id = request.env['open.word'].create({
    #                 'name': word,
    #                 'lang_id': line_id.lang_id.id,
    #                 'forum_id': line_id.forum_id.id,
    #                 'create_id': line_id.create_id.id,
    #             })
    #         request.env['open.point'].create({
    #             'line_id': line_id.id,
    #             'word_id': word_id.id,
    #             'create_id': line_id.create_id.id,
    #             'sequence': sequence,
    #         })
    #         sequence += 1
    #     line_id['is_interlinear'] = True
    #     return

    @http.route(['/interlinear/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def install_interlinear(self, content_id=0, **kwargs):
        if not request.env.user.has_group('website.group_website_publisher'):
            return request.redirect('/content/%s' % slug(content_id))
        part_ids = request.env['open.part'].search([('content_id', '=', content_id.id), ('is_interlinear', '=', False)])
        if part_ids:
            part_id = part_ids[0]
        else:
            content_id.is_interlinear = True
            return request.redirect('/content/%s' % slug(content_id))
        line_ids = request.env['open.line'].search([('part_id', '=', part_id.id), ('is_interlinear', '=', False)])
        for line_id in line_ids:
            line_id._interlinear_line()
            # self._interlinear_line(line_id)
        part_id.is_interlinear = True
        values = {
            'content_id': content_id,
            'sequence': part_id.sequence,
        }
        return request.render("website_openbiblica.install_interlinear", values)

    @http.route(['/uninterlinear/<model("open.content"):content_id>'], type='http', auth="user", website=True)
    def uninstall_interlinear(self, content_id=0, **kwargs):
        if not request.env.user.has_group('website.group_website_publisher'):
            return request.redirect('/content/%s' % slug(content_id))

        request.env['open.point'].search([('content_id', '=', content_id.id)]).unlink()
        line_ids = request.env['open.line'].search([('content_id', '=', content_id.id), ('is_interlinear', '=', True)])
        for line_id in line_ids:
            line_id.is_interlinear = False
        part_ids = request.env['open.part'].search([('content_id', '=', content_id.id), ('is_interlinear', '=', True)])
        for part_id in part_ids:
            part_id.is_interlinear = False
        content_id.is_interlinear = False

        return request.redirect('/content/%s' % slug(content_id))

    @http.route(['/interlinear/b/<model("open.biblica"):biblica_id>'], type='http', auth="user", website=True)
    def install_interlinear_b(self, biblica_id=0, **kwargs):
        if not request.env.user.has_group('website.group_website_publisher'):
            return request.redirect('/biblica/%s' % slug(biblica_id))

        content_ids = request.env['open.content'].search([('biblica_id', '=', biblica_id.id), ('is_interlinear', '=', False)])
        if content_ids:
            content_id = content_ids[0]
        else:
            biblica_id.is_interlinear = True
            return request.redirect('/biblica/%s' % slug(biblica_id))

        part_ids = request.env['open.part'].search([('content_id', '=', content_id.id), ('is_interlinear', '=', False)])
        if part_ids:
            part_id = part_ids[0]
        else:
            content_id.is_interlinear = True
            return request.redirect('/interlinear/b/%s' % slug(biblica_id))

        line_ids = request.env['open.line'].search([('part_id', '=', part_id.id), ('is_interlinear', '=', False)])
        for line_id in line_ids:
            line_id._interlinear_line()
            # self._interlinear_line(line_id)
        part_id.is_interlinear = True
        values = {
            'biblica_id': biblica_id,
            'content_id': content_id,
            'sequence': part_id.sequence,
        }

        return request.render("website_openbiblica.install_interlinear_b", values)

    @http.route(['/uninterlinear/b/<model("open.biblica"):biblica_id>'], type='http', auth="user", website=True)
    def uninstall_interlinear_b(self, biblica_id=0, **kwargs):
        if not request.env.user.has_group('website.group_website_publisher'):
            return request.redirect('/biblica/%s' % slug(biblica_id))

        request.env['open.point'].search([('biblica_id', '=', biblica_id.id)]).unlink()
        line_ids = request.env['open.line'].search([('biblica_id', '=', biblica_id.id), ('is_interlinear', '=', True)])
        for line_id in line_ids:
            line_id.is_interlinear = False
        part_ids = request.env['open.part'].search([('biblica_id', '=', biblica_id.id), ('is_interlinear', '=', True)])
        for part_id in part_ids:
            part_id.is_interlinear = False
        content_ids = request.env['open.content'].search([('biblica_id', '=', biblica_id.id), ('is_interlinear', '=', True)])
        for content_id in content_ids:
            content_id.is_interlinear = False
        biblica_id.is_interlinear = False

        return request.redirect('/biblica/%s' % slug(biblica_id))

