from odoo import api, fields, models, tools


class Texts(models.Model):

    _name = "open.text"
    _description = "Texts"
    _inherit = ['mail.thread', 'website.seo.metadata', 'website.multi.mixin']
    _order = "sequence"

    name = fields.Text('Plain Content', compute='_get_plain_content', store=True)
    content = fields.Html('Content', strip_style=True)

    section_id = fields.Many2one('open.section', string='Row')
    biblica_id = fields.Many2one(related='section_id.biblica_id')

    sequence = fields.Integer('Sequence')
    page = fields.Integer('Page Number')

    lang_id = fields.Many2one(related='section_id.lang_id')

    create_id = fields.Many2one('res.users', string='Author', index=True)
    team_ids = fields.Many2many('res.users', string='colaborators')
    approver_ids = fields.Many2many('res.users', string='approvers')

    create_date = fields.Datetime('Started on', index=True, readonly=True)
    write_date = fields.Datetime('Updated on', index=True, readonly=True)

    active = fields.Boolean(default=True)
    open_project = fields.Boolean(default=True)
    forum_id = fields.Many2one(related='biblica_id.forum_id')
    post_ids = fields.One2many('forum.post', 'text_id', string='Comments')

    reputation = fields.Integer('Reputation')
    reputation_total = fields.Integer('Reputation Total')
    favourite_ids = fields.Many2many('res.users', string='Favourite')
    favourite_count = fields.Integer('Favorite Count')
    views = fields.Integer('Views')

    source_ids = fields.Many2many('open.text', 'text_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')
    source_id = fields.Many2one('open.text', 'Main Source')

    @api.one
    @api.depends('content')
    def _get_plain_content(self):
        self.name = tools.html2plaintext(self.content)[0:500] if self.content else False


