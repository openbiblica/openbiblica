from odoo import api, models, fields

#class Forum(models.Model):
#    _inherit = ['forum.forum']


class Post(models.Model):
    _inherit = ['forum.post']

    biblica_id = fields.Many2one('open.biblica', string='Commented Biblica Project')
    section_id = fields.Many2one('open.section', string='Commented Section')
    cover_id = fields.Many2one('open.cover', string='Commented Cover')
    content_id = fields.Many2one('open.content', string='Commented Content')
    subcontent_id = fields.Many2one('open.subcontent', string='Commented subContent')
    part_id = fields.Many2one('open.part', string='Commented Part')
    line_id = fields.Many2one('open.line', string='Commented Line')
    text_id = fields.Many2one('open.text', string='Commented Text')
    word_id = fields.Many2one('open.word', string='Commented Word')
    first = fields.Boolean(default=False)
