# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import base64
import re

from odoo import http, modules, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.web.controllers.main import binary_content


class WebsiteExport(http.Controller):

    @http.route('/export/usfm/<model("open.content"):content_id>', type='http', auth="user", website=True)
    def export_usfm(self, content_id=0):
        user_id = request.env.user
        if content_id.create_id == user_id:
            if content_id.rest:
                content_id.update({
                    'rest': None,
                })
            rest = '\id ' + content_id.title_id + ' ' + content_id.biblica_id.name + '\n'
            if content_id.title_ide:
                rest = rest + '\ide ' + content_id.title_ide + '\n'
            if content_id.title:
                rest = rest + r'\toc1 ' + content_id.title + '\n'
            if content_id.title_short:
                rest = rest + r'\toc2 ' + content_id.title_short + '\n'
            if content_id.title_abrv:
                rest = rest + r'\toc3 ' + content_id.title_abrv + '\n'
            if content_id.name:
                rest = rest + r'\mt ' + content_id.name + '\n'
            if content_id.description:
                rest = rest + r'\h ' + content_id.description + '\n'

            rest = rest.encode('utf-8')
            content_id.update({
                'rest': base64.b64encode(rest)
            })
        n_values = {
            'part_id': content_id.part_ids[0],
        }
        return request.render("website_openbiblica.export_usfm", n_values)

    @http.route('/export/continue/usfm/<model("open.part"):part_id>', type='http', auth="user", website=True)
    def cont_export_usfm(self, part_id=0):
        user_id = request.env.user
        if part_id.create_id == user_id:
            content_id = part_id.content_id
            status, headers, rest = binary_content(model='open.content', id=content_id.id, field='rest',
                                                   env=request.env(user=SUPERUSER_ID))
            rest = base64.b64decode(rest).decode('utf-8')

            rest = rest + '\c ' + part_id.name + '\n' + '\p' + '\n'

            for line_id in part_id.line_ids:
                rest = rest + r'\v ' + line_id.verse + ' ' + line_id.name

            rest = rest.encode('utf-8')
            while part_id.sequence < len(content_id.part_ids):
                content_id.update({
                    'rest': base64.b64encode(rest),
                })
                next_part_id = request.env['open.part'].search([
                    ('content_id', '=', content_id.id),
                    ('sequence', '=', part_id.sequence + 1)])
                n_values = {
                    'part_id': next_part_id,
                }
                return request.render("website_openbiblica.export_usfm", n_values)

            content_id.update({
                'files': base64.b64encode(rest),
                'rest': None,
            })
        return request.redirect('/content/%s' % slug(content_id))

    @http.route('/html/<model("open.content"):content_id>', type='http', auth="public", website=True)
    def view_html(self, content_id=0):
        values = {'content_id': content_id}
        return request.render("website_openbiblica.view_html", values)

