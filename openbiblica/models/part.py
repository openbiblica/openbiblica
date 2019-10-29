from odoo import api, fields, models


class Parts(models.Model):

    _name = "open.part"
    _description = "Parts"
    _inherit = ['mail.thread', 'website.seo.metadata', 'website.multi.mixin']
    _order = "sequence"

    lang_id = fields.Many2one(related='content_id.lang_id')
    create_id = fields.Many2one('res.users', string='Author', index=True)
    team_ids = fields.Many2many('res.users', string='colaborators')
    approver_ids = fields.Many2many('res.users', string='approvers')
    create_date = fields.Datetime('Started on', index=True, readonly=True)
    write_date = fields.Datetime('Updated on', index=True, readonly=True)
    active = fields.Boolean(default=True)
    open_project = fields.Boolean(default=True)
    forum_id = fields.Many2one(related='content_id.forum_id')
    post_ids = fields.One2many('forum.post', 'part_id', string='Comments')
    reputation = fields.Integer('Reputation')
    reputation_total = fields.Integer('Reputation Total')
    favourite_ids = fields.Many2many('res.users', string='Favourite')
    favourite_count = fields.Integer('Favorite Count')
    views = fields.Integer('Views')

    source_id = fields.Many2one('open.part', 'Main Source')
    source_ids = fields.Many2many('open.part', 'part_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')

    is_interlinear = fields.Boolean('Interlinear')
    is_transcription = fields.Boolean('Transcription')
    # manuscript_ids = fields.Many2many('slide.slide', string='Manuscript Sources')
    # manuscript_id = fields.Many2one('slide.slide', string='Main Manuscript Source')

    name = fields.Char(string="Part Name", required=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', required=True)
    attachment = fields.Binary('Attachment', attachment=True)

    parent_id = fields.Many2one('open.part', string='Parent Part')
    children_ids = fields.One2many('open.part', 'parent_id', string='Children Parts')

    biblica_id = fields.Many2one(related='content_id.biblica_id')
    content_id = fields.Many2one('open.content', string='Content')
    subcontent_id = fields.Many2one('open.subcontent', string='Subcontent')
    line_ids = fields.One2many('open.line', 'part_id', string='Lines', ondelete='cascade')



