from odoo import api, fields, models


class Words(models.Model):

    _name = "open.word"
    _description = "Words"
    _inherit = ['mail.thread', 'website.seo.metadata', 'website.multi.mixin']
    _order = "name"

    lang_id = fields.Many2one('res.lang', 'Language', required=True)
    create_id = fields.Many2one('res.users', string='Author', index=True)
    write_id = fields.Many2one('res.users', string='Editor', index=True)
    create_date = fields.Datetime('Started on', index=True, readonly=True)
    write_date = fields.Datetime('Updated on', index=True, readonly=True)
    active = fields.Boolean(default=True)
    forum_id = fields.Many2one('forum.forum', string='Discussion Forum')
    post_ids = fields.One2many('forum.post', 'word_id', string='Comments')

    name = fields.Char(string="Name", required=True)
    description_ids = fields.One2many('open.description', 'word_id', string='Descriptions')
    dictionary_ids = fields.Many2many('open.meaning', 'biblica_dictionary_ids_rel', 'word_id', 'meaning_id',
                                      string='Dictionaries')

class Descriptions(models.Model):
    _name = "open.description"
    _description = "Word Description"
    _order = "name"

    lang_id = fields.Many2one('res.lang', 'Language', required=True)
    create_id = fields.Many2one('res.users', string='Author', index=True)
    write_id = fields.Many2one('res.users', string='Editor', index=True)
    create_date = fields.Datetime('Started on', index=True, readonly=True)
    write_date = fields.Datetime('Updated on', index=True, readonly=True)
    active = fields.Boolean(default=True)

    name = fields.Text(string="Name", required=True)
    word_id = fields.Many2one('open.word', string='Word')
    score = fields.Integer('Score')


class Points(models.Model):
    _name = "open.point"
    _description = "Points"
    _order = "sequence"

    create_id = fields.Many2one('res.users', string='Author', index=True)
    name = fields.Char(related='word_id.name')
    sequence = fields.Integer('Sequence', required=True)
    line_id = fields.Many2one('open.line', 'Line', required=True)
    biblica_id = fields.Many2one(related='line_id.biblica_id')
    content_id = fields.Many2one(related='line_id.content_id')
    part_id = fields.Many2one(related='line_id.part_id')
    word_id = fields.Many2one('open.word', string='Word')


class Meanings(models.Model):
    _name = "open.meaning"
    _description = "Meanings"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    lang_id = fields.Many2one('res.lang', 'Language', required=True)
    word_ids = fields.Many2many('open.word', 'biblica_dictionary_ids_rel', 'meaning_id', 'word_id', string='Dictionaries')

