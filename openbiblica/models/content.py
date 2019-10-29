from odoo import api, fields, models


class Contents(models.Model):

    _name = "open.content"
    _description = "Contents"
    _inherit = ['mail.thread', 'website.seo.metadata', 'website.multi.mixin']
    _order = "sequence"

    lang_id = fields.Many2one(related='biblica_id.lang_id')
    create_id = fields.Many2one('res.users', string='Author', index=True)
    team_ids = fields.Many2many('res.users', string='colaborators')
    approver_ids = fields.Many2many('res.users', string='approvers')
    create_date = fields.Datetime('Started on', index=True, readonly=True)
    write_date = fields.Datetime('Updated on', index=True, readonly=True)
    active = fields.Boolean(default=True)
    open_project = fields.Boolean(default=True)
    forum_id = fields.Many2one(related='biblica_id.forum_id')
    post_ids = fields.One2many('forum.post', 'content_id', string='Comments')
    reputation = fields.Integer('Reputation')
    reputation_total = fields.Integer('Reputation Total')
    favourite_ids = fields.Many2many('res.users', string='Favourite')
    favourite_count = fields.Integer('Favorite Count')
    views = fields.Integer('Views')

    source_id = fields.Many2one('open.content', 'Main Source')
    source_ids = fields.Many2many('open.content', 'content_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')

    is_interlinear = fields.Boolean('Interlinear')
    is_installed = fields.Boolean('USFM Installed')
    is_transcription = fields.Boolean('Transcription')
    # manuscript_ids = fields.Many2many('slide.slide', string='Manuscript Sources')
    # manuscript_id = fields.Many2one('slide.slide', string='Main Manuscript Source')

    name = fields.Char(string="Content Name", required=True)
    description = fields.Text('Description')
    title_id = fields.Char(string="File Identifier")
    title_ide = fields.Char(string="Encoding specification")
    title = fields.Char(string="Content Title")
    title_short = fields.Char(string="Content Short")
    title_abrv = fields.Char(string="Content Abbreviation")
    sequence = fields.Integer('Sequence', required=True)
    status = fields.Selection([
        ('draft', 'First Draft'),
        ('team', 'Team Draft'),
        ('review', 'Reviewed Draft'),
        ('clean', 'Clean Text')
    ], string='Status', track_visibility='onchange', help='Status of this content', default='draft')

    bundle = fields.Selection([
        ('old', 'Old Testament'),
        ('deu', 'Deuterokanonika'),
        ('new', 'New Testament'),
        ('no', 'None')
    ], string='Bundle', track_visibility='onchange', help='Bible bundle of this content')

    files = fields.Binary('File Attachment', attachment=True)
    rest = fields.Binary('Undone File Attachment', attachment=True)

    biblica_id = fields.Many2one('open.biblica', 'Biblica Project')
    subcontent_ids = fields.One2many('open.subcontent', 'content_id', string='SubContent in this Content', ondelete='cascade')
    part_ids = fields.One2many('open.part', 'content_id', string='Parts in this Content', ondelete='cascade')


class SubContents(models.Model):

    _name = "open.subcontent"
    _description = "SubContents"
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
    post_ids = fields.One2many('forum.post', 'subcontent_id', string='Comments')
    reputation = fields.Integer('Reputation')
    reputation_total = fields.Integer('Reputation Total')
    favourite_ids = fields.Many2many('res.users', string='Favourite')
    favourite_count = fields.Integer('Favorite Count')
    views = fields.Integer('Views')
    source_id = fields.Many2one('open.subcontent', 'Main Source')
    source_ids = fields.Many2many('open.subcontent', 'subcontent_source_ids_rel', 'source_id', 'derivative_id',
                                  string='Sources')

    is_interlinear = fields.Boolean('Interlinear')
    is_transcription = fields.Boolean('Transcription')
    # manuscript_ids = fields.Many2many('slide.slide', string='Manuscript Sources')
    # manuscript_id = fields.Many2one('slide.slide', string='Main Manuscript Source')

    name = fields.Char(string="Subcontent Name", required=True)
    sequence = fields.Integer('Sequence')

    biblica_id = fields.Many2one(related='content_id.biblica_id')
    content_id = fields.Many2one('open.content', 'Content')
    part_ids = fields.One2many('open.part', 'subcontent_id', string='Parts in this SubContent', ondelete='cascade')










