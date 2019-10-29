from odoo import api, fields, models


class Covers(models.Model):

    _name = "open.cover"
    _description = "Covers"
    _inherit = ['mail.thread', 'website.seo.metadata', 'website.multi.mixin']
    _order = "sequence"

    name = fields.Char(string="Cover Name", required=True)
    sequence = fields.Integer('Sequence')
    status = fields.Selection([
        ('draft', 'First Draft'),
        ('team', 'Team Draft'),
        ('review', 'Reviewed Draft'),
        ('clean', 'Clean')
    ], string='Status', track_visibility='onchange', help='Status of this cover', default='draft')

    biblica_id = fields.Many2one('open.biblica', 'Biblica Project')

    create_id = fields.Many2one('res.users', string='Author', index=True)
    team_ids = fields.Many2many('res.users', string='colaborators')
    approver_ids = fields.Many2many('res.users', string='approvers')

    create_date = fields.Datetime('Started on', index=True, readonly=True)
    write_date = fields.Datetime('Updated on', index=True, readonly=True)

    active = fields.Boolean(default=True)
    open_project = fields.Boolean(default=True)
    forum_id = fields.Many2one(related='biblica_id.forum_id')
    post_ids = fields.One2many('forum.post', 'cover_id', string='Comments')

    reputation = fields.Integer('Reputation')
    reputation_total = fields.Integer('Reputation Total')
    favourite_ids = fields.Many2many('res.users', string='Favourite')
    favourite_count = fields.Integer('Favorite Count')
    views = fields.Integer('Views')

    images = fields.Binary('Image Attachment', attachment=True)
