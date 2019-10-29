from odoo import api, models, fields


class Users(models.Model):
    _inherit = ['res.users']

    biblica_ids = fields.One2many('open.biblica', 'create_id')
    section_ids = fields.One2many('open.section', 'create_id')
    content_ids = fields.One2many('open.content', 'create_id')
    cover_ids = fields.One2many('open.cover', 'create_id')
    part_ids = fields.One2many('open.part', 'create_id')
    line_ids = fields.One2many('open.line', 'create_id')
    text_ids = fields.One2many('open.text', 'create_id')

