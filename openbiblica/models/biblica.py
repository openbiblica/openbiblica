from odoo import api, fields, models


class Biblicas(models.Model):

    _name = "open.biblica"
    _description = "Biblica Project"
    _inherit = ['mail.thread', 'website.seo.metadata', 'website.multi.mixin']
    _order = "write_date desc"

    lang_id = fields.Many2one('res.lang', 'Language', required=True)
    create_id = fields.Many2one('res.users', string='Author', index=True)
    team_ids = fields.Many2many('res.users', string='colaborators')
    approver_ids = fields.Many2many('res.users', string='approvers')
    create_date = fields.Datetime('Project Start Date', index=True, readonly=True)
    write_date = fields.Datetime('Project Last Update', index=True, readonly=True)
    active = fields.Boolean(default=True)
    open_project = fields.Boolean(default=True)
    forum_id = fields.Many2one('forum.forum', string='Discussion Forum')
    post_ids = fields.One2many('forum.post', 'biblica_id', string='Comments')
    reputation = fields.Integer('Reputation')
    reputation_total = fields.Integer('Reputation Total')
    favourite_ids = fields.Many2many('res.users', string='Favourite')
    favourite_count = fields.Integer('Favorite Count')
    views = fields.Integer('Views')

    source_id = fields.Many2one('open.biblica', 'Main Source')
    source_ids = fields.Many2many('open.biblica', 'biblica_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')

    is_interlinear = fields.Boolean('Interlinear')
    is_installed = fields.Boolean('USFM Installed')

    name = fields.Char(string="Biblica Project Name", required=True)
    description = fields.Text('Description')

    cover_ids = fields.One2many('open.cover', 'biblica_id', string='Covers', ondelete='cascade')
    section_ids = fields.One2many('open.section', 'biblica_id', string='Pages', ondelete='cascade')
    content_ids = fields.One2many('open.content', 'biblica_id', string='Contents', ondelete='cascade')




