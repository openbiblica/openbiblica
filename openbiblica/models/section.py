from odoo import api, fields, models


class Sections(models.Model):

    _name = "open.section"
    _description = "Section"
    _inherit = ['mail.thread', 'website.seo.metadata', 'website.multi.mixin']
    _order = "sequence"

    name = fields.Char(string="Section Name", required=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence')
    status = fields.Selection([
        ('draft', 'First Draft'),
        ('team', 'Team Draft'),
        ('review', 'Reviewed Draft'),
        ('clean', 'Clean Text')
    ], string='Status', track_visibility='onchange', help='Status of this section', default='draft')

    type = fields.Selection([
        ('front', 'Front Pages'),
        ('back', 'Back Pages')
    ], string='Type', track_visibility='onchange', help='Type of this section')

    biblica_id = fields.Many2one('open.biblica', 'Biblica Project')
    text_ids = fields.One2many('open.text', 'section_id', string='Text in this Section', ondelete='cascade')

    lang_id = fields.Many2one(related='biblica_id.lang_id')

    create_id = fields.Many2one('res.users', string='Author', index=True)
    team_ids = fields.Many2many('res.users', string='colaborators')
    approver_ids = fields.Many2many('res.users', string='approvers')

    create_date = fields.Datetime('Started on', index=True, readonly=True)
    write_date = fields.Datetime('Updated on', index=True, readonly=True)

    active = fields.Boolean(default=True)
    open_project = fields.Boolean(default=True)
    forum_id = fields.Many2one(related='biblica_id.forum_id')
    post_ids = fields.One2many('forum.post', 'section_id', string='Comments')

    reputation = fields.Integer('Reputation')
    reputation_total = fields.Integer('Reputation Total')
    favourite_ids = fields.Many2many('res.users', string='Favourite')
    favourite_count = fields.Integer('Favorite Count')
    views = fields.Integer('Views')

    source_ids = fields.Many2many('open.section', 'section_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')
    source_id = fields.Many2one('open.section', 'Main Source')

